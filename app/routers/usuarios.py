# Rutas para manejar los usuarios y los roles (solo las puede usar el encargado)

# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas y Depends es para dependencias
from fastapi import APIRouter, Depends
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database.conexion import obtener_bd
# Modelo de usuario
from app.models.usuario import modelo_usuario
# Funciones de permisos
from app.core.permisos import obtener_usuario_actual, verificar_rol
# Lista de roles que pueden entrar
from app.core.roles import solo_encargado
# Esquemas que uso
from app.schemas.usuario import usuario_crear, usuario_actualizar, usuario_respuesta, beneficiario_datos, rol_respuesta
# Esquema para responder un mensaje
from app.schemas.comunes import mensaje_respuesta
# Servicio con la lógica de los usuarios
from app.services import usuario_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador (aquí no pongo prefijo porque hay rutas /usuarios y /roles)
enrutador = APIRouter(tags=["Usuarios"])


# Ruta para ver la lista de roles
@enrutador.get(
    "/roles", response_model=list[rol_respuesta],
    summary="Ver los roles",  # Título corto que sale en /docs
    description="Lista los roles del sistema (encargado, instructor, aprendiz e invitado). **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403),  # Errores que puede responder
)
def listar_roles(bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido los roles al servicio
    roles = usuario_service.listar_roles(bd)
    # Devuelvo los roles
    return roles


# Ruta para ver la lista de usuarios (con filtros y paginación)
@enrutador.get(
    "/usuarios", response_model=list[usuario_respuesta],
    summary="Ver los usuarios",  # Título corto que sale en /docs
    description="Lista los usuarios con filtros (buscar por nombre, correo o documento, rol_id y activo) y paginación (saltar y limite). **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def listar_usuarios(
    buscar: Optional[str] = None,  # Buscar por nombre
    rol_id: Optional[int] = None,  # Filtrar por rol
    activo: Optional[bool] = None,  # Filtrar activos o inactivos
    saltar: int = 0,  # Cuántos registros me salto (para paginar)
    limite: int = 100,  # Cuántos registros traigo como máximo
    bd: Session = Depends(obtener_bd),  # Sesión de la base de datos
    usuario_actual: modelo_usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la lista al servicio
    usuarios = usuario_service.listar_usuarios(bd, buscar, rol_id, activo, saltar, limite)
    # Devuelvo la lista
    return usuarios


# Ruta para ver un usuario por su id
@enrutador.get(
    "/usuarios/{usuario_id}", response_model=usuario_respuesta,
    summary="Ver un usuario",  # Título corto que sale en /docs
    description="Busca un usuario por su id. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 404, 422),  # Errores que puede responder
)
def ver_usuario(usuario_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido el usuario al servicio (si no existe responde 404)
    usuario = usuario_service.buscar_usuario_existente(bd, usuario_id)
    # Devuelvo el usuario
    return usuario


# Ruta para crear un usuario
@enrutador.post(
    "/usuarios", response_model=usuario_respuesta, status_code=201,
    summary="Crear un usuario",  # Título corto que sale en /docs
    description="Registra una cuenta nueva. El documento y el correo no se pueden repetir (409), los aprendices necesitan una ficha activa y solo ellos pueden ser beneficiarios. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores que puede responder
)
def crear_usuario(datos: usuario_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear usuarios
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que cree el usuario
    nuevo_usuario = usuario_service.crear_usuario(bd, datos)
    # Devuelvo el usuario creado
    return nuevo_usuario


# Ruta para actualizar un usuario
@enrutador.put(
    "/usuarios/{usuario_id}", response_model=usuario_respuesta,
    summary="Actualizar un usuario",  # Título corto que sale en /docs
    description="Cambia el nombre, el teléfono, el rol, la ficha o el estado. Nadie puede cambiar su propio rol ni desactivar su propia cuenta. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def actualizar_usuario(usuario_id: int, datos: usuario_actualizar, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar usuarios
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que actualice el usuario
    usuario = usuario_service.actualizar_usuario(bd, usuario_id, datos, usuario_actual)
    # Devuelvo el usuario actualizado
    return usuario


# Ruta para desactivar un usuario (no se borra, solo se pone inactivo)
@enrutador.delete(
    "/usuarios/{usuario_id}", response_model=mensaje_respuesta,
    summary="Desactivar un usuario",  # Título corto que sale en /docs
    description="Los usuarios no se borran: quedan inactivos y ya no pueden iniciar sesión (borrado lógico). **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def desactivar_usuario(usuario_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede desactivar usuarios
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que desactive el usuario
    respuesta = usuario_service.desactivar_usuario(bd, usuario_id, usuario_actual)
    # Devuelvo el mensaje
    return respuesta


# Ruta para poner o quitar a un aprendiz como beneficiario (almuerzo gratis)
@enrutador.patch(
    "/usuarios/{usuario_id}/beneficiario", response_model=usuario_respuesta,
    summary="Poner o quitar beneficiario",  # Título corto que sale en /docs
    description="Un aprendiz beneficiario no paga el almuerzo ($0). Solo los aprendices activos pueden ser beneficiarios. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def cambiar_beneficiario(usuario_id: int, datos: beneficiario_datos, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede hacer esto
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que cambie el estado de beneficiario
    usuario = usuario_service.cambiar_beneficiario(bd, usuario_id, datos)
    # Devuelvo el usuario
    return usuario
