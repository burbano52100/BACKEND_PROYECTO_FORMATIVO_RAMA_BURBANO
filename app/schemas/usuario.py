# Esquemas de los usuarios y los roles
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# datetime es una fecha con hora
from datetime import datetime
# Optional quiere decir que el campo puede venir vacío (None)
from typing import Optional

# BaseModel es la clase base, Field sirve para poner reglas y EmailStr revisa que sea un correo
from pydantic import BaseModel, Field, EmailStr


# Lo que se responde de un rol
class rol_respuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id del rol
    id: int
    # Nombre del rol
    nombre: str
    # Descripción del rol
    descripcion: Optional[str] = None


# Datos para crear un usuario
class usuario_crear(BaseModel):
    # Documento de 6 a 10 números
    documento: str = Field(min_length=6, max_length=10)
    # Nombre completo
    nombre: str = Field(min_length=3, max_length=100)
    # Correo
    correo: EmailStr
    # Teléfono de 10 números (es opcional)
    telefono: Optional[str] = Field(default=None, min_length=10, max_length=10)
    # Contraseña de mínimo 8 caracteres
    contrasena: str = Field(min_length=8, max_length=50)
    # Id del rol
    rol_id: int
    # Id de la ficha (solo para aprendices)
    ficha_id: Optional[int] = None
    # Si es beneficiario (solo para aprendices)
    es_beneficiario: bool = False


# Datos para actualizar un usuario (todo es opcional, solo se cambia lo que se manda)
class usuario_actualizar(BaseModel):
    # Nombre nuevo
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    # Teléfono nuevo
    telefono: Optional[str] = Field(default=None, min_length=10, max_length=10)
    # Rol nuevo
    rol_id: Optional[int] = None
    # Ficha nueva
    ficha_id: Optional[int] = None
    # Activar o desactivar
    activo: Optional[bool] = None


# Datos para poner o quitar a un aprendiz como beneficiario
class beneficiario_datos(BaseModel):
    # True para ponerlo y False para quitarlo
    es_beneficiario: bool


# Lo que se responde de un usuario (no lleva la contraseña)
class usuario_respuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id del usuario
    id: int
    # Documento
    documento: str
    # Nombre
    nombre: str
    # Correo
    correo: str
    # Teléfono
    telefono: Optional[str] = None
    # Id del rol
    rol_id: int
    # Id de la ficha
    ficha_id: Optional[int] = None
    # Si es beneficiario
    es_beneficiario: bool
    # Si está activo
    activo: bool
    # Datos del rol
    rol: rol_respuesta
    # Auditoría: id del usuario que creó el registro
    creado_por: Optional[int] = None
    # Fecha en que se creó
    fecha_creacion: Optional[datetime] = None
    # Auditoría: id del usuario que lo modificó por última vez
    modificado_por: Optional[int] = None
    # Auditoría: fecha de la última modificación
    fecha_modificacion: Optional[datetime] = None
