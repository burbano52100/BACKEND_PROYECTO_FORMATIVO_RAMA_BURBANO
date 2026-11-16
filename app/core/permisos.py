"""Identificación del usuario (token) y verificación de permisos por rol."""

# Annotated permite "pegarle" información extra a un tipo (aquí, la dependencia de FastAPI)
from typing import Annotated

# Depends le dice a FastAPI que ejecute una función antes del endpoint y le pase su resultado
from fastapi import Depends
# HTTPBearer lee el encabezado "Authorization: Bearer <token>"
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Errores 401 (no autenticado) y 403 (sin permiso)
from app.core.excepciones import NoAutenticadoError, PermisoDenegadoError
# Nombres de los roles
from app.core.roles import Roles
# Sesión de base de datos que FastAPI entrega en cada petición
from app.database.conexion import SesionDB
# Modelo del usuario (tabla usuarios)
from app.models import Usuario
# Servicio que valida el token y busca al usuario
from app.services.auth_service import AuthService

# Agrega el botón "Authorize" en Swagger.
# auto_error=False: si falta el token respondemos con el formato de error de la API.
# Crea el lector del token Bearer (con un texto de ayuda para Swagger)
esquema_bearer = HTTPBearer(auto_error=False, description="Pegue el access_token de /api/v1/auth/login")


# Dependencia que identifica al usuario que hace la petición
def obtener_usuario_actual(
    # Sesión de base de datos (FastAPI la crea con get_db)
    db: SesionDB,
    # Token leído del encabezado Authorization (None si no se envió)
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)],
) -> Usuario:  # La función devuelve el usuario autenticado
    """Lee el header 'Authorization: Bearer <token>' y devuelve el usuario dueño del token."""
    # Si la petición no trae token...
    if credenciales is None:
        # ...responde 401
        raise NoAutenticadoError("Debe iniciar sesión: no se envió el token de acceso.")
    # Valida el token y devuelve el usuario activo dueño del token
    return AuthService(db).obtener_usuario_desde_token(credenciales.credentials)


# Atajo: un parámetro "usuario: UsuarioActual" recibe al usuario autenticado (cualquier rol)
UsuarioActual = Annotated[Usuario, Depends(obtener_usuario_actual)]


# Fábrica de dependencias: recibe los roles permitidos y devuelve una función que los verifica
def requiere_roles(*roles: Roles):
    """Crea una dependencia que solo deja pasar a los usuarios con alguno de esos roles."""

    # Función que FastAPI ejecutará: primero obtiene el usuario (UsuarioActual) y luego revisa su rol
    def verificar_rol(usuario: UsuarioActual) -> Usuario:
        # Si el nombre del rol del usuario no está en la lista de roles permitidos...
        if usuario.rol.nombre not in roles:
            # ...responde 403
            raise PermisoDenegadoError("Su rol no tiene permiso para realizar esta operación.")
        # Si tiene permiso, entrega el usuario al endpoint
        return usuario

    # Devuelve la función verificadora para usarla con Depends
    return verificar_rol


# Atajos que reflejan la matriz de roles y permisos
# Solo el encargado
Encargado = Annotated[Usuario, Depends(requiere_roles(Roles.ENCARGADO))]
# Solo el instructor
Instructor = Annotated[Usuario, Depends(requiere_roles(Roles.INSTRUCTOR))]
# Quienes comen: aprendiz, instructor e invitado (el encargado no reserva)
Comensal = Annotated[Usuario, Depends(requiere_roles(Roles.APRENDIZ, Roles.INSTRUCTOR, Roles.INVITADO))]
# Cualquiera de los 4 roles (solo exige haber iniciado sesión)
CualquierRol = Annotated[
    # Lista con los 4 roles
    Usuario, Depends(requiere_roles(Roles.ENCARGADO, Roles.INSTRUCTOR, Roles.APRENDIZ, Roles.INVITADO))
]
