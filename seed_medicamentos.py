import os
import asyncio
import csv
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import Medicamento, CategoriaEnum
from dotenv import load_dotenv

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "medicamentos_db")

async def init_db():
    client = AsyncIOMotorClient(MONGODB_URL)
    # Patch for beanie with newer motor versions
    client.append_metadata = lambda *args, **kwargs: None
    db = client[DB_NAME]
    await init_beanie(database=db, document_models=[Medicamento])

def clean_val(val):
    if not val:
        return None
    val = str(val).strip()
    return val if val != "" else None

async def seed_data():
    print("Iniciando conexión a MongoDB...")
    await init_db()
    
    print("Limpiando colección existente...")
    await Medicamento.find_all().delete()
    
    print("Leyendo archivo CSV...")
    medicamentos_batch = []
    
    with open('medicamentos_estandarizados.csv', mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nombre = clean_val(row.get('nombre'))
            principio_activo = clean_val(row.get('principio_activo'))
            accion_terapeutica = clean_val(row.get('accion_terapeutica'))
            forma_farmaceutica = clean_val(row.get('forma_farmaceutica'))
            laboratorio = clean_val(row.get('laboratorio'))
            distribuido_por = clean_val(row.get('distribuido_por'))
            enlace_detalle = clean_val(row.get('enlace_detalle'))
            formulacion = clean_val(row.get('formulacion'))
            presentaciones = clean_val(row.get('presentaciones'))
            
            categoria_str = clean_val(row.get('categoria'))
            if categoria_str:
                try:
                    categoria = CategoriaEnum(categoria_str)
                except ValueError:
                    categoria = CategoriaEnum.REVISION_PENDIENTE
            else:
                categoria = CategoriaEnum.REVISION_PENDIENTE
            
            
            # Generar Descripción (Enfoque 2)
            desc_parts = []
            if nombre:
                n_part = nombre
                if laboratorio:
                    n_part += f" elaborado por {laboratorio}"
                desc_parts.append(n_part)
                
            if accion_terapeutica:
                desc_parts.append(f"Indicado para {accion_terapeutica}")
                
            if formulacion:
                desc_parts.append(f"Fórmula - {formulacion}")
                
            if presentaciones:
                desc_parts.append(f"Presentaciones comerciales - {presentaciones}")
                
            descripcion = ". ".join(desc_parts) + "." if desc_parts else None
            
            med = Medicamento(
                nombre=nombre if nombre else "SIN NOMBRE",
                principio_activo=principio_activo,
                accion_terapeutica=accion_terapeutica,
                forma_farmaceutica=forma_farmaceutica,
                laboratorio=laboratorio,
                distribuidor=distribuido_por,
                enlace=enlace_detalle,
                formulacion=formulacion,
                presentaciones=presentaciones,
                categoria=categoria,
                descripcion=descripcion,
                # explicitly set codes to None as requested
                codigo_barra=None,
                rs=None
            )
            medicamentos_batch.append(med)
            
    print(f"Total de medicamentos leídos: {len(medicamentos_batch)}")
    
    # Batch Insert
    batch_size = 500
    for i in range(0, len(medicamentos_batch), batch_size):
        batch = medicamentos_batch[i:i + batch_size]
        await Medicamento.insert_many(batch)
        print(f"Insertados {min(i + len(batch), len(medicamentos_batch))} de {len(medicamentos_batch)}")
        
    print("Migración completada exitosamente!")

if __name__ == "__main__":
    asyncio.run(seed_data())
