# Rutas para manejar las fichas (grupos de formación), solo las usa el encargado

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
from app.schemas.ficha import ficha_crear, ficha_actualizar, ficha_respuesta
# Esquema para responder un mensaje
from app.schemas.comunes import mensaje_respuesta
# Servicio con la lógica de las fichas
from app.services import ficha_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /fichas
enrutador = APIRouter(prefix="/fichas", tags=["Fichas"])


# Ruta para ver la lista de fichas
@enrutador.get(
    "", response_model=list[ficha_respuesta],
    summary="Ver las fichas",  # Título corto que sale en /docs
    description="Lista las fichas (grupos de aprendices) con filtros y paginación. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def listar_fichas(
    buscar: Optional[str] = None,  # Buscar por código o programa
    jornada: Optional[str] = None,  # Filtrar por jornada
    activo: bool = True,  # Por defecto muestro las activas
    saltar: int = 0,  # Cuántos registros me salto
    limite: int = 100,  # Cuántos registros traigo como máximo
    bd: Session = Depends(obtener_bd),  # Sesión de la base de datos
    usuario_actual: modelo_usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la lista al servicio
    fichas = ficha_service.listar_fichas(bd, buscar, jornada, activo, saltar, limite)
    # Devuelvo la lista
    return fichas


# Ruta para ver las estadísticas de los grupos en una fecha
@enrutador.get(
    "/estadisticas",
    summary="Estadísticas de los grupos",  # Título corto que sale en /docs
    description="Por cada ficha muestra cuántos aprendices tiene, cuántos reservaron en la fecha y cómo va el pago. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def estadisticas(fecha: Optional[date] = None, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido las estadísticas al servicio
    resultado = ficha_service.estadisticas(bd, fecha)
    # Devuelvo las estadísticas
    return resultado


# Ruta para ver una ficha por su id
@enrutador.get(
    "/{ficha_id}", response_model=ficha_respuesta,
    summary="Ver una ficha",  # Título corto que sale en /docs
    description="Busca una ficha por su id. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 404, 422),  # Errores que puede responder
)
def ver_ficha(ficha_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la ficha al servicio (si no existe responde 404)
    ficha = ficha_service.buscar_ficha_existente(bd, ficha_id)
    # Devuelvo la ficha
    return ficha


# Ruta para ver los aprendices de una ficha que reservaron almuerzo en una fecha
@enrutador.get(
    "/{ficha_id}/reservas",
    summary="Aprendices de la ficha que reservaron",  # Título corto que sale en /docs
    description="Lista los aprendices de la ficha que reservaron almuerzo en una fecha y el estado de pago de cada uno. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 404, 422),  # Errores que puede responder
)
def reservas_de_ficha(ficha_id: int, fecha: Optional[date] = None, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la lista al servicio
    lista = ficha_service.reservas_de_ficha(bd, ficha_id, fecha)
    # Devuelvo la lista
    return lista


# Ruta para crear una ficha
@enrutador.post(
    "", response_model=ficha_respuesta, status_code=201,
    summary="Crear una ficha",  # Título corto que sale en /docs
    description="Registra una ficha. El código no se puede repetir (409). **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 409, 422),  # Errores que puede responder
)
def crear_ficha(datos: ficha_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear fichas
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que cree la ficha
    nueva_ficha = ficha_service.crear_ficha(bd, datos)
    # Devuelvo la ficha creada
    return nueva_ficha


# Ruta para actualizar una ficha
@enrutador.put(
    "/{ficha_id}", response_model=ficha_respuesta,
    summary="Actualizar una ficha",  # Título corto que sale en /docs
    description="Cambia el programa, la jornada, el vocero o la cantidad de estudiantes. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def actualizar_ficha(ficha_id: int, datos: ficha_actualizar, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar fichas
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que actualice la ficha
    ficha = ficha_service.actualizar_ficha(bd, ficha_id, datos)
    # Devuelvo la ficha actualizada
    return ficha


# Ruta para eliminar una ficha
@enrutador.delete(
    "/{ficha_id}", response_model=mensaje_respuesta,
    summary="Eliminar una ficha",  # Título corto que sale en /docs
    description="Si la ficha tiene aprendices solo se desactiva (borrado lógico); si no tiene, se borra. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def eliminar_ficha(ficha_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede eliminar fichas
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que elimine la ficha
    respuesta = ficha_service.eliminar_ficha(bd, ficha_id)
    # Devuelvo el mensaje
    return respuesta
