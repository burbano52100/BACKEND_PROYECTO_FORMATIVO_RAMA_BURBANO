# Esquemas para iniciar sesión, renovar el token y cambiar la contraseña
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# BaseModel es la clase base, Field sirve para poner reglas y EmailStr revisa que sea un correo
from pydantic import BaseModel, Field, EmailStr


# Datos que se mandan para iniciar sesión
class ingreso_datos(BaseModel):
    # Correo del usuario
    correo: EmailStr
    # Contraseña del usuario
    contrasena: str = Field(min_length=1, max_length=50)


# Lo que responde el inicio de sesión
class token_respuesta(BaseModel):
    # Token para hacer las peticiones
    token_acceso: str
    # Token para pedir un token nuevo cuando se venza
    token_renovar: str
    # Tipo de token (siempre es bearer)
    tipo_token: str
    # Rol del usuario para saber qué pantalla mostrar
    rol: str


# Datos para pedir un token nuevo
class renovar_datos(BaseModel):
    # El token para renovar que dio el inicio de sesión
    token_renovar: str


# Datos para cambiar la contraseña
class cambiar_contrasena_datos(BaseModel):
    # La contraseña que tiene ahora
    contrasena_actual: str = Field(min_length=1, max_length=50)
    # La contraseña nueva
    contrasena_nueva: str = Field(min_length=8, max_length=50)
