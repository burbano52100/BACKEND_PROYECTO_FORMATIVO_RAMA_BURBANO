"""Esquemas del buzón de sugerencias."""

# Tipo fecha-hora
from datetime import datetime
# Lista cerrada de valores de texto
from enum import StrEnum

# Herramientas de Pydantic
from pydantic import BaseModel, ConfigDict, Field

# Tipos reutilizables
from app.schemas.comunes import EsquemaEntrada, Pagina, PaginacionBase
# Resumen del usuario (autor de la sugerencia)
from app.schemas.usuario import UsuarioResumen


# Estados de una sugerencia
class EstadoSugerencia(StrEnum):
    # Sin atender
    PENDIENTE = "PENDIENTE"
    # Atendida por el encargado
    ATENDIDA = "ATENDIDA"


# Datos para enviar una sugerencia (POST /sugerencias)
class SugerenciaCrear(EsquemaEntrada):
    # Asunto: 3 a 100 caracteres
    asunto: str = Field(min_length=3, max_length=100)
    # Mensaje: 3 a 500 caracteres
    mensaje: str = Field(min_length=3, max_length=500)


# Datos para atender una sugerencia
class AtenderEntrada(EsquemaEntrada):
    # Respuesta opcional: 2 a 500 caracteres
    respuesta: str | None = Field(None, min_length=2, max_length=500, description="Opcional")


# Cómo se muestra una sugerencia
class SugerenciaSalida(BaseModel):
    # Permite crear el esquema desde el modelo Sugerencia
    model_config = ConfigDict(from_attributes=True)

    # Id
    id: int
    # Asunto
    asunto: str
    # Mensaje
    mensaje: str
    # PENDIENTE o ATENDIDA
    estado: str
    # Respuesta del encargado
    respuesta: str | None
    # Autor
    usuario: UsuarioResumen
    # Cuándo se envió
    creado_en: datetime
    # Cuándo se atendió
    atendida_en: datetime | None


# Contadores del buzón
class ContadoresSugerencias(BaseModel):
    # Total recibidas
    total: int
    # Atendidas
    atendidas: int
    # Pendientes
    pendientes: int


# Respuesta del buzón: una página de sugerencias más los contadores
class PaginaSugerencias(Pagina[SugerenciaSalida]):
    # Contadores del buzón
    contadores: ContadoresSugerencias


# Filtros de GET /sugerencias (más pagina y tamano heredados)
class FiltrosSugerencia(PaginacionBase):
    # Filtra por estado
    estado: EstadoSugerencia | None = None
