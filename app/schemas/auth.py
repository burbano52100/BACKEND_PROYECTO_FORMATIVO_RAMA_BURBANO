"""Esquemas de autenticación."""

# BaseModel = clase base de los esquemas; Field = reglas de un campo
from pydantic import BaseModel, Field

# Tipos reutilizables: correo, esquema base de entrada y contraseña segura
from app.schemas.comunes import Correo, EsquemaEntrada, Password


# Datos que se envían para iniciar sesión
class LoginEntrada(EsquemaEntrada):
    # Correo con formato válido
    correo: Correo
    # Contraseña: no vacía y máximo 64 caracteres (aquí no se exige la política: se compara con el hash)
    password: str = Field(min_length=1, max_length=64)


# Datos que se envían para renovar los tokens
class RefreshEntrada(EsquemaEntrada):
    # Token de actualización recibido en el login (no vacío)
    refresh_token: str = Field(min_length=1)


# Datos que se envían para cambiar la propia contraseña
class CambioPasswordEntrada(EsquemaEntrada):
    # Contraseña actual (para confirmar que es el dueño de la cuenta)
    password_actual: str = Field(min_length=1, max_length=64)
    # Contraseña nueva: debe cumplir la política (8+ caracteres, mayúscula, minúscula y número)
    password_nueva: Password


# Respuesta del login y del refresh
class TokenRespuesta(BaseModel):
    # Token corto para enviar en cada petición
    access_token: str
    # Token largo para pedir tokens nuevos
    refresh_token: str
    # Tipo de token (siempre "bearer")
    token_type: str = "bearer"
    # Segundos que dura el access_token
    expira_en: int = Field(description="Segundos de vigencia del access_token")
    # Rol del usuario
    rol: str = Field(description="Rol del usuario, para que el frontend abra el panel correcto (RF03)")
