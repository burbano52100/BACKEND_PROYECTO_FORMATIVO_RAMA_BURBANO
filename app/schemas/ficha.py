"""Esquemas de fichas (grupos de formación)."""

# Tipos fecha y fecha-hora
from datetime import date, datetime
# Lista cerrada de valores de texto
from enum import StrEnum

# Herramientas de Pydantic
from pydantic import BaseModel, ConfigDict, Field

# Tipos reutilizables: dinero de salida, esquema base de entrada y paginación
from app.schemas.comunes import Dinero, EsquemaEntrada, PaginacionBase


# Jornadas permitidas
class Jornada(StrEnum):
    # Jornada de día
    DIURNA = "DIURNA"
    # Jornada de noche
    NOCTURNA = "NOCTURNA"
    # Combina día y noche
    MIXTA = "MIXTA"
    # Sábados y domingos
    FIN_DE_SEMANA = "FIN_DE_SEMANA"


# Datos para crear una ficha
class FichaCrear(EsquemaEntrada):
    # Código de 6 a 10 dígitos (pattern = expresión regular que debe cumplir)
    codigo: str = Field(pattern=r"^[0-9]{6,10}$", description="Número de ficha, por ejemplo 2847251")
    # Nombre del programa: entre 3 y 120 caracteres
    programa: str = Field(min_length=3, max_length=120)
    # Una de las 4 jornadas
    jornada: Jornada
    # Vocero opcional
    vocero: str | None = Field(None, max_length=100, description="Dato informativo (ya no es un rol)")
    # Cantidad de estudiantes entre 0 y 60 (0 por defecto)
    cantidad_estudiantes: int = Field(0, ge=0, le=60)


# Datos para actualizar una ficha (todos opcionales)
class FichaActualizar(EsquemaEntrada):
    """El código de la ficha no se puede cambiar."""

    # Nuevo programa
    programa: str | None = Field(None, min_length=3, max_length=120)
    # Nueva jornada
    jornada: Jornada | None = None
    # Nuevo vocero
    vocero: str | None = Field(None, max_length=100)
    # Nueva cantidad de estudiantes
    cantidad_estudiantes: int | None = Field(None, ge=0, le=60)


# Datos mínimos de una ficha (se usan dentro de la respuesta del usuario)
class FichaResumen(BaseModel):
    # Permite crear el esquema desde el modelo Ficha
    model_config = ConfigDict(from_attributes=True)

    # Id de la ficha
    id: int
    # Número de ficha
    codigo: str
    # Programa de formación
    programa: str


# Respuesta completa de una ficha (hereda id, codigo y programa)
class FichaSalida(FichaResumen):
    # Jornada
    jornada: str
    # Vocero
    vocero: str | None
    # Cantidad de estudiantes
    cantidad_estudiantes: int
    # Si está activa
    activo: bool
    # Cuándo se creó
    creado_en: datetime


# Filtros de GET /fichas (más pagina y tamano heredados)
class FiltrosFicha(PaginacionBase):
    # Busca por código o programa
    buscar: str | None = Field(None, description="Código o programa (coincidencia parcial)")
    # Filtra por jornada
    jornada: Jornada | None = None
    # Por defecto muestra solo las activas
    activo: bool = True


# Respuesta de GET /fichas/estadisticas
class EstadisticasGrupos(BaseModel):
    # Fecha consultada
    fecha: date
    # Fichas activas
    total_grupos: int
    # Suma de estudiantes de las fichas activas
    total_estudiantes: int
    # Aprendices activos con cuenta en el sistema
    aprendices_con_cuenta: int
    # Almuerzos reservados por aprendices en la fecha
    almuerzos_reservados: int
    # Almuerzos reservados / total de grupos
    promedio_por_grupo: float


# Cada aprendiz de la lista de GET /fichas/{id}/reservas
class ReservaDeFicha(BaseModel):
    """Aprendiz de la ficha que reservó almuerzo en la fecha consultada (RF41)."""

    # Id de la reserva
    reserva_id: int
    # Id del aprendiz
    aprendiz_id: int
    # Nombre del aprendiz
    nombre: str
    # Documento del aprendiz
    documento: str
    # APRENDIZ o BENEFICIARIO
    tipo: str
    # Valor de la reserva
    valor: Dinero
    # Estado de pago
    estado: str
