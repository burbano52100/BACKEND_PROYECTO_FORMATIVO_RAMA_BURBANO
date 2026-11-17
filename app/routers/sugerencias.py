# Rutas del buzón de sugerencias

# datetime es la fecha y hora actual
from datetime import datetime
# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas, Depends es para dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database import get_db
# Modelos que uso
from app.models import Sugerencia, Usuario
# Esquemas que uso
from app.schemas import SugerenciaCrear, AtenderDatos, SugerenciaRespuesta
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol

# Creo el router, todas las rutas empiezan con /sugerencias
router = APIRouter(prefix="/sugerencias", tags=["Sugerencias"])


# Función que convierte una sugerencia en un diccionario con el nombre de quien la mandó
def convertir_sugerencia(sugerencia):
    # Armo el diccionario con los datos de la sugerencia
    return {
        "id": sugerencia.id,  # Id de la sugerencia
        "usuario_id": sugerencia.usuario_id,  # Id de quien la mandó
        "nombre_usuario": sugerencia.usuario.nombre,  # Nombre de quien la mandó
        "asunto": sugerencia.asunto,  # Asunto
        "mensaje": sugerencia.mensaje,  # Mensaje
        "estado": sugerencia.estado,  # PENDIENTE o ATENDIDA
        "respuesta": sugerencia.respuesta,  # Respuesta del encargado
        "fecha_creacion": sugerencia.fecha_creacion,  # Cuándo se mandó
        "fecha_respuesta": sugerencia.fecha_respuesta,  # Cuándo se respondió
    }


# Ruta para mandar una sugerencia (todos los roles)
@router.post("", response_model=SugerenciaRespuesta, status_code=201)
def enviar_sugerencia(datos: SugerenciaCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Creo la sugerencia con el usuario que la manda
    nueva_sugerencia = Sugerencia(
        usuario_id=usuario_actual.id,  # Quién la manda
        asunto=datos.asunto,  # Asunto
        mensaje=datos.mensaje,  # Mensaje
        estado="PENDIENTE",  # Empieza pendiente
    )
    # La agrego a la sesión
    db.add(nueva_sugerencia)
    # La guardo
    db.commit()
    # La vuelvo a leer para tener el id y la fecha
    db.refresh(nueva_sugerencia)
    # Devuelvo la sugerencia
    return nueva_sugerencia


# Ruta para ver mis sugerencias (todos los roles)
@router.get("/mias", response_model=list[SugerenciaRespuesta])
def mis_sugerencias(db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Traigo las sugerencias de la persona de la más nueva a la más vieja
    sugerencias = db.query(Sugerencia).filter(Sugerencia.usuario_id == usuario_actual.id).order_by(Sugerencia.id.desc()).all()
    # Devuelvo la lista
    return sugerencias


# Ruta para ver todas las sugerencias con los contadores (solo el encargado)
@router.get("")
def listar_sugerencias(
    estado: Optional[str] = None,  # Filtrar por PENDIENTE o ATENDIDA
    skip: int = 0,  # Cuántos registros me salto
    limit: int = 100,  # Cuántos registros traigo como máximo
    db: Session = Depends(get_db),  # Sesión de la base de datos
    usuario_actual: Usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede ver el buzón
    verificar_rol(usuario_actual, ["encargado"])
    # Empiezo con todas las sugerencias
    consulta = db.query(Sugerencia)
    # Si mandaron estado
    if estado is not None:
        # Filtro por estado
        consulta = consulta.filter(Sugerencia.estado == estado)
    # Ordeno de la más nueva a la más vieja y pagino
    sugerencias = consulta.order_by(Sugerencia.id.desc()).offset(skip).limit(limit).all()
    # Aquí voy a guardar las sugerencias convertidas
    lista = []
    # Recorro las sugerencias
    for sugerencia in sugerencias:
        # Agrego cada sugerencia convertida
        lista.append(convertir_sugerencia(sugerencia))
    # Cuento todas las sugerencias
    total = db.query(Sugerencia).count()
    # Cuento las pendientes
    pendientes = db.query(Sugerencia).filter(Sugerencia.estado == "PENDIENTE").count()
    # Cuento las atendidas
    atendidas = db.query(Sugerencia).filter(Sugerencia.estado == "ATENDIDA").count()
    # Devuelvo los contadores y la lista
    return {
        "contadores": {  # Cuántas sugerencias hay
            "total": total,  # Todas
            "pendientes": pendientes,  # Sin atender
            "atendidas": atendidas,  # Ya atendidas
        },
        "sugerencias": lista,  # Lista de sugerencias
    }


# Ruta para atender o responder una sugerencia (solo el encargado)
@router.patch("/{sugerencia_id}/atender")
def atender_sugerencia(sugerencia_id: int, datos: AtenderDatos, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede atender sugerencias
    verificar_rol(usuario_actual, ["encargado"])
    # Busco la sugerencia
    sugerencia = db.query(Sugerencia).filter(Sugerencia.id == sugerencia_id).first()
    # Si no existe
    if sugerencia is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La sugerencia no existe")
    # Si ya fue atendida
    if sugerencia.estado == "ATENDIDA":
        # Respondo 400
        raise HTTPException(status_code=400, detail="La sugerencia ya fue atendida")
    # Cambio el estado
    sugerencia.estado = "ATENDIDA"
    # Guardo la respuesta
    sugerencia.respuesta = datos.respuesta
    # Guardo la fecha de hoy como fecha de respuesta
    sugerencia.fecha_respuesta = datetime.now()
    # Guardo los cambios
    db.commit()
    # Vuelvo a leer la sugerencia
    db.refresh(sugerencia)
    # Devuelvo la sugerencia
    return convertir_sugerencia(sugerencia)
