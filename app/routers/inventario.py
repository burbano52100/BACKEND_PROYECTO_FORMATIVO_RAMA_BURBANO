# Rutas del inventario de la cocina: materiales, movimientos y kardex (solo el encargado)

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
from app.schemas.inventario import material_crear, material_actualizar, movimiento_crear
# Esquema para responder un mensaje
from app.schemas.comunes import mensaje_respuesta
# Servicio con la lógica del inventario
from app.services import inventario_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /inventario
enrutador = APIRouter(prefix="/inventario", tags=["Inventario"])


# Ruta para ver los materiales
@enrutador.get(
    "/materiales",
    summary="Ver los materiales",  # Título corto que sale en /docs
    description="Lista los materiales de la cocina con filtros (buscar, categoría, estado del stock y activo) y paginación. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def listar_materiales(
    buscar: Optional[str] = None,  # Buscar por nombre o código de barras
    categoria: Optional[str] = None,  # Filtrar por categoría
    estado: Optional[str] = None,  # Filtrar por estado del stock
    activo: bool = True,  # Por defecto muestro los activos
    saltar: int = 0,  # Cuántos registros me salto
    limite: int = 100,  # Cuántos registros traigo como máximo
    bd: Session = Depends(obtener_bd),  # Sesión de la base de datos
    usuario_actual: modelo_usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la lista al servicio
    lista = inventario_service.listar_materiales(bd, buscar, categoria, estado, activo, saltar, limite)
    # Devuelvo la lista
    return lista


# Ruta para ver un material por su id
@enrutador.get(
    "/materiales/{material_id}",
    summary="Ver un material",  # Título corto que sale en /docs
    description="Busca un material por su id. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 404, 422),  # Errores que puede responder
)
def ver_material(material_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido el material al servicio
    material = inventario_service.ver_material(bd, material_id)
    # Devuelvo el material
    return material


# Ruta para crear un material
@enrutador.post(
    "/materiales", status_code=201,
    summary="Crear un material",  # Título corto que sale en /docs
    description="Registra un material. El código de barras no se puede repetir (409). Si trae stock inicial queda una ENTRADA en el kardex. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 409, 422),  # Errores que puede responder
)
def crear_material(datos: material_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear materiales
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que cree el material
    material = inventario_service.crear_material(bd, datos, usuario_actual)
    # Devuelvo el material
    return material


# Ruta para actualizar un material (el stock no se cambia aquí)
@enrutador.put(
    "/materiales/{material_id}",
    summary="Actualizar un material",  # Título corto que sale en /docs
    description="Cambia los datos del material. El stock no se cambia aquí: se cambia con los movimientos. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def actualizar_material(material_id: int, datos: material_actualizar, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar materiales
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que actualice el material
    material = inventario_service.actualizar_material(bd, material_id, datos)
    # Devuelvo el material
    return material


# Ruta para eliminar un material
@enrutador.delete(
    "/materiales/{material_id}", response_model=mensaje_respuesta,
    summary="Eliminar un material",  # Título corto que sale en /docs
    description="No se puede eliminar un material que usa una receta activa. Si tiene movimientos solo se desactiva (borrado lógico). **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def eliminar_material(material_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede eliminar materiales
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que elimine el material
    respuesta = inventario_service.eliminar_material(bd, material_id)
    # Devuelvo el mensaje
    return respuesta


# Ruta para hacer una entrada, salida o merma
@enrutador.post(
    "/movimientos", status_code=201,
    summary="Registrar una entrada, salida o merma",  # Título corto que sale en /docs
    description="Una salida o una merma no pueden dejar el stock en negativo. Cada movimiento queda guardado en el kardex con su saldo. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def registrar_movimiento(datos: movimiento_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede hacer movimientos
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que registre el movimiento
    movimiento = inventario_service.registrar_movimiento(bd, datos, usuario_actual)
    # Devuelvo el movimiento
    return movimiento


# Ruta para ver el kardex (historial de movimientos)
@enrutador.get(
    "/kardex",
    summary="Ver el kardex",  # Título corto que sale en /docs
    description="Historial de movimientos del inventario con filtros (material y tipo) y paginación. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def ver_kardex(
    material_id: Optional[int] = None,  # Filtrar por material
    tipo: Optional[str] = None,  # Filtrar por tipo (por ejemplo MERMA)
    saltar: int = 0,  # Cuántos registros me salto
    limite: int = 100,  # Cuántos registros traigo como máximo
    bd: Session = Depends(obtener_bd),  # Sesión de la base de datos
    usuario_actual: modelo_usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido el kardex al servicio
    lista = inventario_service.ver_kardex(bd, material_id, tipo, saltar, limite)
    # Devuelvo la lista
    return lista
