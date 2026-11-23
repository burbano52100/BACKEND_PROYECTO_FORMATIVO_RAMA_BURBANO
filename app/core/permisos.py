# En este archivo está lo de los permisos: saber quién hace la petición y si tiene el rol que se necesita

# Depends sirve para usar dependencias
from fastapi import Depends
# HTTPBearer lee el token que viene en el encabezado "Authorization: Bearer token"
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Traigo el modelo de usuario para buscar el usuario del token
from app.models.usuario import modelo_usuario
# Traigo las funciones que dan la sesión y buscan por id en la base de datos
from app.database.conexion import obtener_bd, buscar_por_id
# Traigo las funciones para responder los errores 401 y 403
from app.core.excepciones import error_no_autenticado, error_sin_permiso
# Traigo la función que lee el token
from app.core.seguridad import leer_token

# Con esto sale el botón "Authorize" en /docs para pegar el token
# auto_error=False es para que si no mandan el token yo mismo responda el error en español
seguridad = HTTPBearer(auto_error=False)


# Esta función se usa en las rutas para saber quién está haciendo la petición
def obtener_usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(seguridad), bd: Session = Depends(obtener_bd)):
    # Si no mandaron el token
    if credenciales is None:
        # Respondo 401
        error_no_autenticado("Falta el token, primero inicie sesión")
    # Saco el token del encabezado
    token = credenciales.credentials
    # Leo el token y saco el id del usuario
    usuario_id = leer_token(token, "acceso")
    # Busco el usuario en la base de datos
    usuario = buscar_por_id(bd, modelo_usuario, usuario_id)
    # Si no existe el usuario
    if usuario is None:
        # Respondo 401
        error_no_autenticado("El usuario del token no existe")
    # Si el usuario está desactivado
    if usuario.activo == False:
        # Respondo 401
        error_no_autenticado("La cuenta está inactiva")
    # Guardo en la sesión quién hace la petición, para la auditoría (quién crea o modifica cada registro)
    bd.info["usuario_id"] = usuario.id
    # Devuelvo el usuario
    return usuario


# Función para revisar si el usuario tiene uno de los roles que se permiten
def verificar_rol(usuario, roles_permitidos):
    # Si el nombre del rol no está en la lista de roles permitidos
    if usuario.rol.nombre not in roles_permitidos:
        # Respondo 403 (no tiene permiso)
        error_sin_permiso("No tiene permiso para hacer esto")
