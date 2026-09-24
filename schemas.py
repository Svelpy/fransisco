from pydantic import BaseModel, field_validator
from typing import Optional, Generic, TypeVar, List
from beanie import PydanticObjectId
from models import CategoriaEnum

T = TypeVar("T")

class MedicamentoBase(BaseModel):
    codigo_barra: Optional[str] = None
    rs: Optional[str] = None
    nombre: str
    forma_farmaceutica: Optional[str] = None
    laboratorio: Optional[str] = None
    distribuidor: Optional[str] = None
    principio_activo: Optional[str] = None
    enlace: Optional[str] = None
    accion_terapeutica: Optional[str] = None
    categoria: Optional[CategoriaEnum] = None
    formulacion: Optional[str] = None
    presentaciones: Optional[str] = None
    descripcion: Optional[str] = None

    @field_validator("codigo_barra")
    @classmethod
    def normalizar_codigo_barra(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

class MedicamentoCreate(MedicamentoBase):
    pass

class MedicamentoUpdate(BaseModel):
    codigo_barra: Optional[str] = None
    rs: Optional[str] = None
    nombre: Optional[str] = None
    forma_farmaceutica: Optional[str] = None
    laboratorio: Optional[str] = None
    distribuidor: Optional[str] = None
    principio_activo: Optional[str] = None
    enlace: Optional[str] = None
    accion_terapeutica: Optional[str] = None
    categoria: Optional[CategoriaEnum] = None
    formulacion: Optional[str] = None
    presentaciones: Optional[str] = None
    descripcion: Optional[str] = None

    @field_validator("codigo_barra")
    @classmethod
    def normalizar_codigo_barra(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

class MedicamentoResponse(MedicamentoBase):
    id: PydanticObjectId



class PaginatedResponse(BaseModel, Generic[T]):
    """Schema genérico de respuesta paginada. Uso: PaginatedResponse[UserResponse]"""
    total: int          # Total de registros encontrados
    page: int           # Página actual (empieza en 1)
    per_page: int       # Registros por página
    total_pages: int    # Total de páginas
    data: List[T]       # Lista de objetos tipados
