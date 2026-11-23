# Rutas de las recetas con su costo de producción (solo el encargado)

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
from app.schemas.receta import receta_crear, receta_actualizar
# Esquema para responder un mensaje
from app.schemas.comunes import mensaje_respuesta
# Servicio con la lógica de las recetas
from app.services import receta_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /recetas
enrutador = APIRouter(prefix="/recetas", tags=["Recetas"])


# Ruta para ver las recetas
@enrutador.get(
    "",
    summary="Ver las recetas con su costo",  # Título corto que sale en /docs
    description="Lista las recetas con el costo de prepararlas y el margen, con filtros y paginación. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def listar_recetas(
    buscar: Optional[str] = None,  # Buscar por nombre
    activo: bool = True,  # Por defecto muestro las activas
    saltar: int = 0,  # Cuántos registros me salto
    limite: int = 100,  # Cuántos registros traigo como máximo
    bd: Session = Depends(obtener_bd),  # Sesión de la base de datos
    usuario_actual: modelo_usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la lista al servicio
    lista = receta_service.listar_recetas(bd, buscar, activo, saltar, limite)
    # Devuelvo la lista
    return lista


# Ruta para ver una receta por su id
@enrutador.get(
    "/{receta_id}",
    summary="Ver una receta",  # Título corto que sale en /docs
    description="Muestra una receta con sus ingredientes, su costo y su margen. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 404, 422),  # Errores que puede responder
)
def ver_receta(receta_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la receta al servicio
    receta = receta_service.ver_receta(bd, receta_id)
    # Devuelvo la receta con su costo
    return receta


# Ruta para crear una receta
@enrutador.post(
    "", status_code=201,
    summary="Crear una receta",  # Título corto que sale en /docs
    description="Registra una receta con sus ingredientes. El nombre no se puede repetir (409) y un material no se puede repetir en la misma receta. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores que puede responder
)
def crear_receta(datos: receta_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear recetas
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que cree la receta
    receta = receta_service.crear_receta(bd, datos)
    # Devuelvo la receta con su costo
    return receta


# Ruta para actualizar una receta
@enrutador.put(
    "/{receta_id}",
    summary="Actualizar una receta",  # Título corto que sale en /docs
    description="Cambia los datos o los ingredientes de una receta. El nombre no se puede repetir (409). **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores que puede responder
)
def actualizar_receta(receta_id: int, datos: receta_actualizar, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar recetas
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que actualice la receta
    receta = receta_service.actualizar_receta(bd, receta_id, datos)
    # Devuelvo la receta con su costo
    return receta


# Ruta para eliminar una receta
@enrutador.delete(
    "/{receta_id}", response_model=mensaje_respuesta,
    summary="Eliminar una receta",  # Título corto que sale en /docs
    description="Borra la receta y sus ingredientes. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 404, 422),  # Errores que puede responder
)
def eliminar_receta(receta_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede eliminar recetas
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que elimine la receta
    respuesta = receta_service.eliminar_receta(bd, receta_id)
    # Devuelvo el mensaje
    return respuesta
