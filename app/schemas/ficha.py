# Esquemas de las fichas
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# datetime es una fecha con hora
from datetime import datetime
# Optional quiere decir que el campo puede venir vacío (None)
from typing import Optional

# BaseModel es la clase base y Field sirve para poner reglas
from pydantic import BaseModel, Field


# Datos para crear una ficha
class ficha_crear(BaseModel):
    # Número de la ficha
    codigo: str = Field(min_length=6, max_length=10)
    # Programa de formación
    programa: str = Field(min_length=3, max_length=120)
    # Jornada: DIURNA, NOCTURNA, MIXTA o FIN_DE_SEMANA
    jornada: str
    # Vocero del grupo (opcional)
    vocero: Optional[str] = Field(default=None, max_length=100)
    # Cantidad de estudiantes (de 0 a 60)
    cantidad_estudiantes: int = Field(default=0, ge=0, le=60)


# Datos para actualizar una ficha (todo opcional)
class ficha_actualizar(BaseModel):
    # Programa nuevo
    programa: Optional[str] = Field(default=None, min_length=3, max_length=120)
    # Jornada nueva
    jornada: Optional[str] = None
    # Vocero nuevo
    vocero: Optional[str] = Field(default=None, max_length=100)
    # Cantidad de estudiantes nueva
    cantidad_estudiantes: Optional[int] = Field(default=None, ge=0, le=60)


# Lo que se responde de una ficha
class ficha_respuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id de la ficha
    id: int
    # Número de la ficha
    codigo: str
    # Programa
    programa: str
    # Jornada
    jornada: str
    # Vocero
    vocero: Optional[str] = None
    # Cantidad de estudiantes
    cantidad_estudiantes: int
    # Si está activa
    activo: bool
    # Auditoría: id del usuario que creó el registro
    creado_por: Optional[int] = None
    # Fecha en que se creó
    fecha_creacion: Optional[datetime] = None
    # Auditoría: id del usuario que lo modificó por última vez
    modificado_por: Optional[int] = None
    # Auditoría: fecha de la última modificación
    fecha_modificacion: Optional[datetime] = None
