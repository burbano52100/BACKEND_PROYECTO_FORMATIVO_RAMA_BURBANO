"""Endpoints de autenticación."""

# Annotated asocia la dependencia (Depends) al tipo
from typing import Annotated

# APIRouter agrupa endpoints; Depends inyecta dependencias
from fastapi import APIRouter, Depends

# Documenta en Swagger los errores de cada endpoint
from app.core.errores import respuestas_error
# Usuario autenticado de cualquier rol
from app.core.permisos import UsuarioActual
# Sesión de base de datos por petición
from app.database.conexion import SesionDB
# Esquemas de entrada y salida de autenticación
from app.schemas.auth import CambioPasswordEntrada, LoginEntrada, RefreshEntrada, TokenRespuesta
# Respuesta con un mensaje
from app.schemas.comunes import Mensaje
# Respuesta con los datos del usuario (sin contraseña)
from app.schemas.usuario import UsuarioSalida
# Servicio con las reglas de autenticación
from app.services.auth_service import AuthService

# Router con prefijo /auth; "tags" agrupa estos endpoints en Swagger
router = APIRouter(prefix="/auth", tags=["Autenticación"])


# Dependencia que crea el servicio con la sesión de la petición
def obtener_servicio(db: SesionDB) -> AuthService:
    # Devuelve un AuthService nuevo
    return AuthService(db)


# Atajo: un parámetro "servicio: Servicio" recibe el AuthService listo
Servicio = Annotated[AuthService, Depends(obtener_servicio)]


# Endpoint POST /api/v1/auth/login (público: no exige token)
@router.post(
    "/login",  # Ruta, que se suma al prefijo /auth
    response_model=TokenRespuesta,  # Forma de la respuesta exitosa (200)
    summary="Iniciar sesión (RF02)",  # Título corto en Swagger
    description=(  # Explicación larga en Swagger (Markdown)
        "Valida correo y contraseña y devuelve un **access_token** (corto), un **refresh_token** (largo) y el "
        "**rol**, para que el frontend abra el panel correcto (RF03). Tras 5 intentos fallidos la cuenta se "
        "bloquea 15 minutos. Una cuenta inactiva no puede ingresar.\n\n**Rol requerido:** ninguno (público)."
    ),
    responses=respuestas_error(401, 403, 422),  # Errores posibles, documentados en Swagger
)
# Recibe el cuerpo validado con LoginEntrada y el servicio
def iniciar_sesion(datos: LoginEntrada, servicio: Servicio):
    # Ejecuta el inicio de sesión y devuelve los tokens
    return servicio.iniciar_sesion(datos)


# Endpoint POST /api/v1/auth/refresh
@router.post(
    "/refresh",  # Ruta
    response_model=TokenRespuesta,  # Respuesta: tokens nuevos
    summary="Renovar el token de acceso",  # Título en Swagger
    description="Recibe el refresh_token y entrega tokens nuevos.\n\n**Rol requerido:** refresh_token válido.",  # Explicación
    responses=respuestas_error(401, 422),  # Errores posibles
)
# Recibe el refresh token en el cuerpo
def renovar_token(datos: RefreshEntrada, servicio: Servicio):
    # Valida el refresh token y devuelve tokens nuevos
    return servicio.renovar_tokens(datos.refresh_token)


# Endpoint GET /api/v1/auth/perfil
@router.get(
    "/perfil",  # Ruta
    response_model=UsuarioSalida,  # Respuesta: datos del usuario sin contraseña
    summary="Ver mi perfil (RF04)",  # Título en Swagger
    description="Datos de la cuenta dueña del token; nunca incluye la contraseña.\n\n**Rol requerido:** cualquiera.",  # Explicación
    responses=respuestas_error(401),  # Error posible: sin token
)
# UsuarioActual exige token válido y entrega el usuario
def ver_perfil(usuario: UsuarioActual):
    # Devuelve el usuario; FastAPI lo filtra con UsuarioSalida (sin password_hash)
    return usuario


# Endpoint PUT /api/v1/auth/password
@router.put(
    "/password",  # Ruta
    response_model=Mensaje,  # Respuesta: un mensaje
    summary="Cambiar mi contraseña",  # Título en Swagger
    description=(  # Explicación
        "La nueva contraseña debe tener mínimo 8 caracteres, con mayúsculas, minúsculas y números.\n\n"
        "**Rol requerido:** cualquiera."
    ),
    responses=respuestas_error(400, 401, 422),  # Errores posibles
)
# Recibe las contraseñas, el usuario autenticado y el servicio
def cambiar_password(datos: CambioPasswordEntrada, usuario: UsuarioActual, servicio: Servicio):
    # Cambia la contraseña (lanza error si la actual no coincide)
    servicio.cambiar_password(usuario, datos)
    # Mensaje de confirmación
    return {"mensaje": "La contraseña se cambió correctamente."}
