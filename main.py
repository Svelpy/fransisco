from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

import os
import re
import math
import csv
import io
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from beanie import init_beanie, PydanticObjectId
from beanie.operators import Or, RegEx

from models import Medicamento, MedicamentoFarmacia
from schemas import (
    MedicamentoCreate,
    MedicamentoUpdate,
    MedicamentoResponse,
    PaginatedResponse,
)

# Load environment variables
load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")

CSV_COLUMNS = [
    "id",
    "codigo_barra",
    "rs",
    "nombre",
    "forma_farmaceutica",
    "laboratorio",
    "distribuidor",
    "principio_activo",
    "enlace",
    "accion_terapeutica",
    "categoria",
    "formulacion",
    "presentaciones",
    "descripcion",
]


def crear_respuesta_csv(medicamentos, nombre_archivo: str) -> Response:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_COLUMNS,
        extrasaction="ignore",
    )
    writer.writeheader()

    for medicamento in medicamentos:
        datos = medicamento.model_dump(mode="json")
        fila = {}
        for columna in CSV_COLUMNS:
            valor = datos.get(columna) or ""
            if isinstance(valor, str):
                # Una fila visual por medicamento, conservando el resto del texto.
                valor = re.sub(r"[\r\n]+", " ", valor)
            fila[columna] = valor
        writer.writerow(fila)

    # La marca BOM permite que Excel reconozca UTF-8 y conserve los acentos.
    contenido = ("\ufeff" + output.getvalue()).encode("utf-8")
    return Response(
        content=contenido,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
        },
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MongoDB and Beanie
    if not MONGODB_URL:
        # Fallback for dev/testing if not configured in environment
        url = "mongodb://localhost:27017"
    else:
        url = MONGODB_URL
        
    client = AsyncIOMotorClient(url)
    
    # Patch the client instance to prevent Beanie's initialization crash with newer Motor versions
    client.append_metadata = lambda *args, **kwargs: None
    
    # Attempt to get default database from URI, fallback to MONGODB_DB_NAME env var or 'medicamentos_db'
    try:
        db = client.get_default_database()
    except Exception:
        db = None
        
    if db is None:
        db_name = os.getenv("MONGODB_DB_NAME", "medicamentos_db")
        db = client[db_name]
        
    # Remove only obsolete indexes from the first pharmacy model version.
    pharmacy_collection = db["medicamentos_farmacia"]
    existing_indexes = await pharmacy_collection.index_information()
    for obsolete_index in (
        "idx_farmacia_codigo_barra_unico",
        "idx_farmacia_medicamento_base",
    ):
        if obsolete_index in existing_indexes:
            await pharmacy_collection.drop_index(obsolete_index)

    barcode_index = existing_indexes.get("idx_farmacia_codigo_barra")
    if barcode_index and not barcode_index.get("unique", False):
        await pharmacy_collection.drop_index("idx_farmacia_codigo_barra")

    await init_beanie(database=db, document_models=[Medicamento, MedicamentoFarmacia])
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CRUD ENDPOINTS FOR MEDICAMENTO
@app.post("/medicamentos", response_model=MedicamentoResponse, status_code=status.HTTP_201_CREATED)
async def create_medicamento(medicamento_data: MedicamentoCreate):
    medicamento = Medicamento(**medicamento_data.model_dump())
    await medicamento.insert()
    return medicamento

@app.post(
    "/farmacia/medicamentos",
    response_model=MedicamentoResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_medicamento_farmacia(
    medicamento_data: MedicamentoCreate
):
    medicamento = MedicamentoFarmacia(**medicamento_data.model_dump())
    try:
        await medicamento.insert()
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un medicamento con ese codigo de barras"
        )
    return medicamento

@app.get(
    "/farmacia/medicamentos",
    response_model=PaginatedResponse[MedicamentoResponse]
)
async def list_medicamentos_farmacia(
    q: str | None = None,
    laboratorio: str | None = None,
    distribuidor: str | None = None,
    forma_farmaceutica: str | None = None,
    categoria: str | None = None,
    page: int = 1,
    per_page: int = 20
):
    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)
    query = MedicamentoFarmacia.find_all()

    if q:
        safe_q = re.escape(q.strip())
        query = query.find(Or(
            RegEx(MedicamentoFarmacia.codigo_barra, safe_q, "i"),
            RegEx(MedicamentoFarmacia.nombre, safe_q, "i"),
            RegEx(MedicamentoFarmacia.principio_activo, safe_q, "i")
        ))

    if laboratorio is not None:
        query = query.find(MedicamentoFarmacia.laboratorio == laboratorio)
    if distribuidor is not None:
        query = query.find(MedicamentoFarmacia.distribuidor == distribuidor)
    if forma_farmaceutica is not None:
        query = query.find(MedicamentoFarmacia.forma_farmaceutica == forma_farmaceutica)
    if categoria is not None:
        query = query.find(MedicamentoFarmacia.categoria == categoria)

    total_count = await query.count()
    medicamentos = await (
        query.sort(+MedicamentoFarmacia.nombre)
        .skip((page - 1) * per_page)
        .limit(per_page)
        .to_list()
    )
    total_pages = math.ceil(total_count / per_page) if total_count else 0

    return {
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": medicamentos
    }


@app.get("/farmacia/exportar-medicamentos.csv")
async def exportar_medicamentos_farmacia_csv():
    """Exporta todos los documentos de medicamentos_farmacia, sin paginacion."""
    medicamentos = await (
        MedicamentoFarmacia.find_all()
        # Los ObjectId de MongoDB contienen la fecha de creacion.
        # Orden ascendente: del registro mas antiguo al mas reciente.
        .sort("_id")
        .to_list()
    )

    return crear_respuesta_csv(medicamentos, "medicamentos_farmacia.csv")


@app.patch(
    "/farmacia/medicamentos/{id}",
    response_model=MedicamentoResponse
)
async def update_medicamento_farmacia(id: str, update_data: MedicamentoUpdate):
    """Actualiza exclusivamente un documento de medicamentos_farmacia."""
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de ID invalido"
        )

    medicamento = await MedicamentoFarmacia.get(id)
    if not medicamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicamento de farmacia no encontrado"
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    if "nombre" in update_dict:
        nombre = (update_dict["nombre"] or "").strip()
        if not nombre:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El nombre no puede quedar vacio"
            )
        update_dict["nombre"] = nombre

    try:
        if update_dict:
            await medicamento.update({"$set": update_dict})
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un medicamento con ese codigo de barras"
        )

    return await MedicamentoFarmacia.get(id)


@app.get("/farmacia/laboratorios", response_model=list[str])
async def get_laboratorios_farmacia():
    values = await MedicamentoFarmacia.distinct("laboratorio")
    return sorted([value for value in values if value])


@app.get("/farmacia/distribuidores", response_model=list[str])
async def get_distribuidores_farmacia():
    values = await MedicamentoFarmacia.distinct("distribuidor")
    return sorted([value for value in values if value])

@app.get("/medicamentos", response_model=PaginatedResponse[MedicamentoResponse])
async def list_medicamentos(
    q: str | None = None,
    laboratorio: str | None = None,
    distribuidor: str | None = None,
    forma_farmaceutica: str | None = None,
    categoria: str | None = None,
    page: int = 1,
    per_page: int = 20
):
    # Validaciones de paginación
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20

    # Iniciamos la consulta buscando todos los registros
    query = Medicamento.find_all()

    # Búsqueda insensible a mayúsculas y parcial en campos clave
    if q:
        safe_q = re.escape(q)
        query = query.find(Or(
            RegEx(Medicamento.codigo_barra, safe_q, "i"),
            RegEx(Medicamento.nombre, safe_q, "i"),
            RegEx(Medicamento.principio_activo, safe_q, "i")
        ))

    # Filtros exactos
    if laboratorio is not None:
        query = query.find(Medicamento.laboratorio == laboratorio)
    if distribuidor is not None:
        query = query.find(Medicamento.distribuidor == distribuidor)
    if forma_farmaceutica is not None:
        query = query.find(Medicamento.forma_farmaceutica == forma_farmaceutica)
    if categoria is not None:
        query = query.find(Medicamento.categoria == categoria)

    total_count = await query.count()
    skip = (page - 1) * per_page
    
    # Ordenamos de forma ascendente por el nombre del medicamento
    medicamentos = await query.sort(+Medicamento.nombre).skip(skip).limit(per_page).to_list()
    total_pages = math.ceil(total_count / per_page) if per_page > 0 else 0

    return {
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": medicamentos
    }


@app.get("/exportar-medicamentos.csv")
async def exportar_medicamentos_csv():
    """Exporta todos los documentos de la coleccion principal medicamentos."""
    medicamentos = await Medicamento.find_all().sort("_id").to_list()
    return crear_respuesta_csv(medicamentos, "medicamentos.csv")

@app.get("/laboratorios", response_model=list[str])
async def get_laboratorios():
    labs = await Medicamento.distinct("laboratorio")
    return sorted([lab for lab in labs if lab])

@app.get("/distribuidores", response_model=list[str])
async def get_distribuidores():
    distribuidores = await Medicamento.distinct("distribuidor")
    return sorted([d for d in distribuidores if d])

@app.get("/medicamentos/{id}", response_model=MedicamentoResponse)
async def get_medicamento(id: str):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    medicamento = await Medicamento.get(id)
    if not medicamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento no encontrado")
    return medicamento

@app.put("/medicamentos/{id}", response_model=MedicamentoResponse)
async def update_medicamento(id: str, update_data: MedicamentoUpdate):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    medicamento = await Medicamento.get(id)
    if not medicamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento no encontrado")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    if update_dict:
        await medicamento.update({"$set": update_dict})
    
    # Fetch updated state
    updated_medicamento = await Medicamento.get(id)
    return updated_medicamento

@app.delete("/medicamentos/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicamento(id: str):
    if not PydanticObjectId.is_valid(id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    medicamento = await Medicamento.get(id)
    if not medicamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicamento no encontrado")
    await medicamento.delete()
    return None

@app.get("/farmacia", include_in_schema=False)
async def farmacia_page():
    return FileResponse(BASE_DIR / "frontend" / "farmacia.html")
# Montar el frontend en la raíz estática (Debe ir al final para que no sobreescriba las rutas de la API)
app.mount("/", StaticFiles(directory=BASE_DIR / "frontend", html=True), name="frontend")
