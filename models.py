from enum import Enum
from beanie import Document
from pymongo import IndexModel, ASCENDING, TEXT

class CategoriaEnum(str, Enum):
    DOLOR_FIEBRE_INFLAMACION = "DOLOR, FIEBRE E INFLAMACIÓN"
    ANTIBIOTICOS_INFECTOLOGIA = "ANTIBIÓTICOS E INFECTOLOGÍA"
    VITAMINAS_MINERALES = "VITAMINAS Y MINERALES"
    SALUD_DIGESTIVA_ESTOMAGO = "SALUD DIGESTIVA Y ESTÓMAGO"
    CORAZON_CIRCULACION_SANGRE = "CORAZÓN, CIRCULACIÓN Y SANGRE"
    SISTEMA_RESPIRATORIO_GRIPE_TOS = "SISTEMA RESPIRATORIO, GRIPE Y TOS"
    SISTEMA_NERVIOSO_SALUD_MENTAL = "SISTEMA NERVIOSO Y SALUD MENTAL"
    ONCOLOGIA_MEDICAMENTOS_ESPECIALIZADOS = "ONCOLOGÍA Y MEDICAMENTOS ESPECIALIZADOS"
    HIGIENE_CUIDADO_CORPORAL = "HIGIENE Y CUIDADO CORPORAL"
    SALUD_OCULAR_OTICA = "SALUD OCULAR Y ÓTICA"
    DIABETES_HORMONAS_ENDOCRINOLOGIA = "DIABETES, HORMONAS Y ENDOCRINOLOGÍA"
    DERMATOLOGIA_TRATAMIENTOS_PIEL = "DERMATOLOGÍA Y TRATAMIENTOS DE LA PIEL"
    SALUD_FEMENINA_SALUD_SEXUAL = "SALUD FEMENINA Y SALUD SEXUAL"
    DISPOSITIVOS_EQUIPOS_MEDICOS = "DISPOSITIVOS Y EQUIPOS MÉDICOS"
    CUIDADO_BUCAL = "CUIDADO BUCAL"
    MATERIAL_CURACION_ANTISEPTICOS = "MATERIAL DE CURACIÓN Y ANTISÉPTICOS"
    SUPLEMENTOS_NUTRICION_ESPECIAL = "SUPLEMENTOS Y NUTRICIÓN ESPECIAL"
    REVISION_PENDIENTE = "REVISIÓN PENDIENTE"
    UROLOGIA_SALUD_PROSTATICA = "UROLOGÍA Y SALUD PROSTÁTICA"
    PROTECCION_SOLAR = "PROTECCIÓN SOLAR"
    CUIDADO_BEBE_NUTRICION_INFANTIL = "CUIDADO DEL BEBÉ Y NUTRICIÓN INFANTIL"
    CUIDADO_CAPILAR = "CUIDADO CAPILAR"
    CUIDADO_TRATAMIENTO_FACIAL = "CUIDADO Y TRATAMIENTO FACIAL"
#---------------------------------------------------------------------
class Medicamento(Document):
    #CODIGOS
    codigo_barra:str | None=None
    rs: str | None=None
    #DATOS PRIMARIOS (DATOS CORTOS SACADOS DE INFOMERC)
    nombre:str
    forma_farmaceutica: str | None = None
    laboratorio: str | None=None
    distribuidor: str | None=None
    principio_activo: str | None=None
    #URL
    enlace: str | None=None

    #DATOS SECUNDARIOS (DATOS ELABORADOS USANDO LOS DATOS PRIMARIOS)
    accion_terapeutica: str | None=None
    categoria: CategoriaEnum | None=None

    #DATOS PRIMARIOS EXTRAS (DATOS LARGOS SACADOS DE INFOMERC)
    formulacion: str | None=None
    presentaciones: str | None=None
    #CONCATENACION DE ALGUNOS DATOS PARA CREAR UN RESUMEN MAS COMPLETO
    descripcion:str | None=None
    class Settings:
        name = "medicamentos"
        
        indexes = [
            # =========================================================
            # A) ÍNDICE PARA LA BARRA DE BÚSQUEDA (Unifica 3 campos)
            # =========================================================
            IndexModel(
                [("codigo_barra", TEXT),("nombre", TEXT),("principio_activo", TEXT)],
                weights={
                    "codigo_barra": 100, # Prioridad MÁXIMA si escriben o escanean el código
                    "nombre": 10,        # Prioridad alta para el nombre
                    "principio_activo": 5 # Prioridad media
                },
                name="idx_barra_busqueda_unificada"
            ),

            # =========================================================
            # B) ÍNDICES SIMPLES PARA FILTROS
            # =========================================================
            IndexModel([("laboratorio", ASCENDING)], name="idx_filtro_laboratorio"),
            IndexModel([("forma_farmaceutica", ASCENDING)], name="idx_filtro_forma_farmaceutica"),
            IndexModel([("categoria", ASCENDING)], name="idx_filtro_categoria"),
            IndexModel([("distribuidor", ASCENDING)], name="idx_filtro_distribuidor"),

            # Auxiliar: Para cuando escanean directamente sin pasar por $text
            IndexModel([("codigo_barra", ASCENDING)],partialFilterExpression={"codigo_barra": {"$type": "string"}},name="idx_codigo_barra_exacto")
        ]
class MedicamentoFarmacia(Document):
    codigo_barra: str | None = None
    rs: str | None = None
    nombre: str
    forma_farmaceutica: str | None = None
    laboratorio: str | None = None
    distribuidor: str | None = None
    principio_activo: str | None = None
    enlace: str | None = None
    accion_terapeutica: str | None = None
    categoria: CategoriaEnum | None = None
    formulacion: str | None = None
    presentaciones: str | None = None
    descripcion: str | None = None

    class Settings:
        name = "medicamentos_farmacia"
        indexes = [
            IndexModel(
                [("codigo_barra", ASCENDING)],
                partialFilterExpression={"codigo_barra": {"$type": "string"}},
                unique=True,
                name="idx_farmacia_codigo_barra"
            ),
        ]
