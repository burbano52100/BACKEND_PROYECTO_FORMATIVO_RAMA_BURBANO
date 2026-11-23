# Esquemas de los menús
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# date es una fecha
from datetime import date, datetime
# Optional quiere decir que el campo puede venir vacío (None)
from typing import Optional

# BaseModel es la clase base y Field sirve para poner reglas
from pydantic import BaseModel, Field


# Datos para crear un menú
class menu_crear(BaseModel):
    # Fecha del menú (año-mes-día)
    fecha: date
    # Nombre del plato
    nombre: str = Field(min_length=3, max_length=100)
    # Lo que trae el almuerzo
    descripcion: str = Field(min_length=3, max_length=500)
    # Precio para aprendices (no puede ser negativo)
    precio_aprendiz: float = Field(ge=0)
    # Precio para invitados (no puede ser negativo)
    precio_invitado: float = Field(ge=0)
    # Cuántos almuerzos hay (más de 0)
    cantidad_total: int = Field(gt=0, le=1000)


# Datos para actualizar un menú (todo opcional, la fecha no se cambia)
class menu_actualizar(BaseModel):
    # Nombre nuevo
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    # Descripción nueva
    descripcion: Optional[str] = Field(default=None, min_length=3, max_length=500)
    # Precio de aprendiz nuevo
    precio_aprendiz: Optional[float] = Field(default=None, ge=0)
    # Precio de invitado nuevo
    precio_invitado: Optional[float] = Field(default=None, ge=0)
    # Cantidad total nueva
    cantidad_total: Optional[int] = Field(default=None, gt=0, le=1000)


# Lo que se responde de un menú
class menu_respuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id del menú
    id: int
    # Fecha
    fecha: date
    # Nombre
    nombre: str
    # Descripción
    descripcion: str
    # Precio de aprendiz
    precio_aprendiz: float
    # Precio de invitado
    precio_invitado: float
    # Cantidad total
    cantidad_total: int
    # Cantidad que queda
    cantidad_disponible: int
    # Si está activo
    activo: bool
    # Auditoría: id del usuario que creó el registro
    creado_por: Optional[int] = None
    # Fecha en que se creó
    fecha_creacion: Optional[datetime] = None
    # Auditoría: id del usuario que lo modificó por última vez
    modificado_por: Optional[int] = None
    # Auditoría: fecha de la última modificación
    fecha_modificacion: Optional[datetime] = None
