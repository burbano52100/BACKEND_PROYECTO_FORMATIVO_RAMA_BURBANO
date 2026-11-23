# Esquemas de las sugerencias
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# datetime es una fecha con hora
from datetime import datetime
# Optional quiere decir que el campo puede venir vacío (None)
from typing import Optional

# BaseModel es la clase base y Field sirve para poner reglas
from pydantic import BaseModel, Field


# Datos para mandar una sugerencia
class sugerencia_crear(BaseModel):
    # Tema de la sugerencia
    asunto: str = Field(min_length=3, max_length=100)
    # Lo que quiere decir (máximo 500 letras)
    mensaje: str = Field(min_length=3, max_length=500)


# Datos para atender una sugerencia
class atender_datos(BaseModel):
    # Respuesta del encargado (opcional)
    respuesta: Optional[str] = Field(default=None, max_length=500)


# Lo que se responde de una sugerencia
class sugerencia_respuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id de la sugerencia
    id: int
    # Id del usuario que la mandó
    usuario_id: int
    # Asunto
    asunto: str
    # Mensaje
    mensaje: str
    # Estado
    estado: str
    # Respuesta del encargado
    respuesta: Optional[str] = None
    # Fecha en que se mandó
    fecha_creacion: datetime
    # Fecha en que se respondió
    fecha_respuesta: Optional[datetime] = None
    # Auditoría: id del usuario que creó el registro
    creado_por: Optional[int] = None
    # Auditoría: id del usuario que lo modificó por última vez
    modificado_por: Optional[int] = None
    # Auditoría: fecha de la última modificación
    fecha_modificacion: Optional[datetime] = None
