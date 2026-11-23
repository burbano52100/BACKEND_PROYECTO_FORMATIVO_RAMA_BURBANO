# Rutas para manejar el menú del día

# date es una fecha
from datetime import date
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
from app.schemas.menu import menu_crear, menu_actualizar, menu_respuesta
# Esquema para responder un mensaje
from app.schemas.comunes import mensaje_respuesta
# Servicio con la lógica de los menús
from app.services import menu_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /menus
enrutador = APIRouter(prefix="/menus", tags=["Menús"])


# Ruta para ver el menú de hoy (todos los roles)
@enrutador.get(
    "/hoy",
    summary="Menú de hoy",  # Título corto que sale en /docs
    description="Devuelve el menú de hoy con el precio que le toca a quien consulta y si ya tiene reserva. Responde 404 si todavía no hay menú para hoy. **Rol requerido:** cualquiera con sesión iniciada.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 404),  # Errores que puede responder
)
def menu_de_hoy(bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Le pido al servicio el menú de hoy con mi precio
    menu = menu_service.menu_de_hoy(bd, usuario_actual)
    # Devuelvo el menú
    return menu


# Ruta para ver los menús de hoy en adelante (todos los roles)
@enrutador.get(
    "/proximos",
    summary="Menús de hoy en adelante",  # Título corto que sale en /docs
    description="Lista los menús activos desde hoy con el precio de quien consulta. **Rol requerido:** cualquiera con sesión iniciada.",  # Explicación y rol que se necesita
    responses=respuestas_error(401),  # Errores que puede responder
)
def proximos_menus(bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Le pido al servicio los próximos menús con mi precio
    lista = menu_service.proximos_menus(bd, usuario_actual)
    # Devuelvo la lista
    return lista


# Ruta para ver todos los menús (historial, solo el encargado)
@enrutador.get(
    "", response_model=list[menu_respuesta],
    summary="Ver todos los menús",  # Título corto que sale en /docs
    description="Historial de menús con filtros por fecha (desde, hasta) y activo, y paginación. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def listar_menus(
    desde: Optional[date] = None,  # Fecha inicial
    hasta: Optional[date] = None,  # Fecha final
    activo: Optional[bool] = None,  # Filtrar activos o inactivos
    saltar: int = 0,  # Cuántos registros me salto
    limite: int = 100,  # Cuántos registros traigo como máximo
    bd: Session = Depends(obtener_bd),  # Sesión de la base de datos
    usuario_actual: modelo_usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la lista al servicio
    menus = menu_service.listar_menus(bd, desde, hasta, activo, saltar, limite)
    # Devuelvo la lista
    return menus


# Ruta para ver un menú por su id (todos los roles)
@enrutador.get(
    "/{menu_id}", response_model=menu_respuesta,
    summary="Ver un menú",  # Título corto que sale en /docs
    description="Busca un menú por su id. **Rol requerido:** cualquiera con sesión iniciada.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 404, 422),  # Errores que puede responder
)
def ver_menu(menu_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Le pido el menú al servicio (si no existe responde 404)
    menu = menu_service.buscar_menu_existente(bd, menu_id)
    # Devuelvo el menú
    return menu


# Ruta para crear un menú
@enrutador.post(
    "", response_model=menu_respuesta, status_code=201,
    summary="Crear un menú",  # Título corto que sale en /docs
    description="Crea el menú de un día. Solo puede haber un menú por día (409) y no se crean menús de días que ya pasaron. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 409, 422),  # Errores que puede responder
)
def crear_menu(datos: menu_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear menús
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que cree el menú
    nuevo_menu = menu_service.crear_menu(bd, datos)
    # Devuelvo el menú creado
    return nuevo_menu


# Ruta para actualizar un menú
@enrutador.put(
    "/{menu_id}", response_model=menu_respuesta,
    summary="Actualizar un menú",  # Título corto que sale en /docs
    description="Cambia el nombre, la descripción, los precios o la cantidad. La cantidad no puede quedar menor que los almuerzos ya vendidos. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def actualizar_menu(menu_id: int, datos: menu_actualizar, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar menús
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que actualice el menú
    menu = menu_service.actualizar_menu(bd, menu_id, datos)
    # Devuelvo el menú actualizado
    return menu


# Ruta para eliminar un menú
@enrutador.delete(
    "/{menu_id}", response_model=mensaje_respuesta,
    summary="Eliminar un menú",  # Título corto que sale en /docs
    description="Si el menú ya tiene reservas solo se desactiva (borrado lógico); si no tiene, se borra. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def eliminar_menu(menu_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede eliminar menús
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que elimine el menú
    respuesta = menu_service.eliminar_menu(bd, menu_id)
    # Devuelvo el mensaje
    return respuesta
