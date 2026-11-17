# Rutas para manejar las fichas (grupos de formación), solo las usa el encargado

# date es una fecha
from datetime import date
# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas, Depends es para dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database import get_db
# Modelos que uso
from app.models import Ficha, Usuario, Rol, Menu, Reserva
# Esquemas que uso
from app.schemas import FichaCrear, FichaActualizar, FichaRespuesta
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol

# Creo el router, todas las rutas empiezan con /fichas
router = APIRouter(prefix="/fichas", tags=["Fichas"])

# Jornadas que se pueden usar
JORNADAS = ["DIURNA", "NOCTURNA", "MIXTA", "FIN_DE_SEMANA"]


# Ruta para ver la lista de fichas
@router.get("", response_model=list[FichaRespuesta])
def listar_fichas(
    buscar: Optional[str] = None,  # Buscar por código o programa
    jornada: Optional[str] = None,  # Filtrar por jornada
    activo: bool = True,  # Por defecto muestro las activas
    skip: int = 0,  # Cuántos registros me salto
    limit: int = 100,  # Cuántos registros traigo como máximo
    db: Session = Depends(get_db),  # Sesión de la base de datos
    usuario_actual: Usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Traigo las fichas activas o inactivas según el filtro
    consulta = db.query(Ficha).filter(Ficha.activo == activo)
    # Si mandaron algo para buscar
    if buscar:
        # Busco en el código o en el programa
        consulta = consulta.filter((Ficha.codigo.ilike(f"%{buscar}%")) | (Ficha.programa.ilike(f"%{buscar}%")))
    # Si mandaron jornada
    if jornada:
        # Filtro por jornada
        consulta = consulta.filter(Ficha.jornada == jornada)
    # Ordeno por código y pagino
    fichas = consulta.order_by(Ficha.codigo).offset(skip).limit(limit).all()
    # Devuelvo la lista
    return fichas


# Ruta para ver las estadísticas de los grupos en una fecha
@router.get("/estadisticas")
def estadisticas(fecha: Optional[date] = None, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Si no mandaron fecha uso la de hoy
    if fecha is None:
        # Fecha de hoy
        fecha = date.today()
    # Traigo las fichas activas
    fichas_activas = db.query(Ficha).filter(Ficha.activo == True).all()
    # Cuento los grupos
    total_grupos = len(fichas_activas)
    # Aquí voy a sumar los estudiantes
    total_estudiantes = 0
    # Recorro las fichas
    for ficha in fichas_activas:
        # Sumo los estudiantes de cada ficha
        total_estudiantes = total_estudiantes + ficha.cantidad_estudiantes
    # Busco el rol de aprendiz
    rol_aprendiz = db.query(Rol).filter(Rol.nombre == "aprendiz").first()
    # Cuento los aprendices activos que tienen cuenta
    aprendices_con_cuenta = db.query(Usuario).filter(Usuario.rol_id == rol_aprendiz.id, Usuario.activo == True).count()
    # Busco el menú de esa fecha
    menu = db.query(Menu).filter(Menu.fecha == fecha).first()
    # Al principio no hay almuerzos reservados
    almuerzos_reservados = 0
    # Si hay menú ese día
    if menu is not None:
        # Cuento las reservas de aprendices que no están canceladas
        almuerzos_reservados = db.query(Reserva).filter(
            Reserva.menu_id == menu.id,  # Del menú de ese día
            Reserva.tipo.in_(["APRENDIZ", "BENEFICIARIO"]),  # Solo aprendices
            Reserva.estado != "CANCELADA",  # Que no estén canceladas
        ).count()
    # El promedio empieza en 0
    promedio = 0
    # Si hay grupos calculo el promedio (para no dividir entre 0)
    if total_grupos > 0:
        # Promedio de almuerzos por grupo con 2 decimales
        promedio = round(almuerzos_reservados / total_grupos, 2)
    # Devuelvo las estadísticas
    return {
        "fecha": fecha,  # Fecha consultada
        "total_grupos": total_grupos,  # Cantidad de fichas activas
        "total_estudiantes": total_estudiantes,  # Suma de estudiantes
        "aprendices_con_cuenta": aprendices_con_cuenta,  # Aprendices registrados
        "almuerzos_reservados": almuerzos_reservados,  # Almuerzos de aprendices ese día
        "promedio_por_grupo": promedio,  # Promedio por grupo
    }


# Ruta para ver una ficha por su id
@router.get("/{ficha_id}", response_model=FichaRespuesta)
def ver_ficha(ficha_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Busco la ficha
    ficha = db.query(Ficha).filter(Ficha.id == ficha_id).first()
    # Si no existe
    if ficha is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La ficha no existe")
    # Devuelvo la ficha
    return ficha


# Ruta para ver los aprendices de una ficha que reservaron almuerzo en una fecha
@router.get("/{ficha_id}/reservas")
def reservas_de_ficha(ficha_id: int, fecha: Optional[date] = None, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Busco la ficha
    ficha = db.query(Ficha).filter(Ficha.id == ficha_id).first()
    # Si no existe
    if ficha is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La ficha no existe")
    # Si no mandaron fecha uso la de hoy
    if fecha is None:
        # Fecha de hoy
        fecha = date.today()
    # Busco el menú de esa fecha
    menu = db.query(Menu).filter(Menu.fecha == fecha).first()
    # Si no hay menú ese día no hay reservas
    if menu is None:
        # Devuelvo una lista vacía
        return []
    # Traigo las reservas de ese menú que no están canceladas
    reservas = db.query(Reserva).filter(Reserva.menu_id == menu.id, Reserva.estado != "CANCELADA").all()
    # Aquí voy a guardar los aprendices de la ficha
    lista = []
    # Recorro las reservas
    for reserva in reservas:
        # Si el usuario de la reserva es de esta ficha
        if reserva.usuario.ficha_id == ficha_id:
            # Lo agrego a la lista
            lista.append({
                "reserva_id": reserva.id,  # Id de la reserva
                "aprendiz_id": reserva.usuario.id,  # Id del aprendiz
                "nombre": reserva.usuario.nombre,  # Nombre del aprendiz
                "documento": reserva.usuario.documento,  # Documento del aprendiz
                "tipo": reserva.tipo,  # APRENDIZ o BENEFICIARIO
                "valor": reserva.valor,  # Lo que tiene que pagar
                "estado": reserva.estado,  # Si ya pagó o no
            })
    # Devuelvo la lista
    return lista


# Ruta para crear una ficha
@router.post("", response_model=FichaRespuesta, status_code=201)
def crear_ficha(datos: FichaCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear fichas
    verificar_rol(usuario_actual, ["encargado"])
    # El código solo puede tener números
    if not datos.codigo.isdigit():
        # Respondo 400
        raise HTTPException(status_code=400, detail="El código de la ficha solo puede tener números")
    # La jornada tiene que estar en la lista
    if datos.jornada not in JORNADAS:
        # Respondo 400
        raise HTTPException(status_code=400, detail="La jornada debe ser DIURNA, NOCTURNA, MIXTA o FIN_DE_SEMANA")
    # Busco si ya existe una ficha con ese código
    existe = db.query(Ficha).filter(Ficha.codigo == datos.codigo).first()
    # Si ya existe
    if existe is not None:
        # Respondo 400
        raise HTTPException(status_code=400, detail="Ya existe una ficha con ese código")
    # Creo la ficha
    nueva_ficha = Ficha(
        codigo=datos.codigo,  # Código
        programa=datos.programa,  # Programa
        jornada=datos.jornada,  # Jornada
        vocero=datos.vocero,  # Vocero
        cantidad_estudiantes=datos.cantidad_estudiantes,  # Cantidad de estudiantes
    )
    # La agrego a la sesión
    db.add(nueva_ficha)
    # La guardo en la base de datos
    db.commit()
    # La vuelvo a leer para tener el id
    db.refresh(nueva_ficha)
    # Devuelvo la ficha creada
    return nueva_ficha


# Ruta para actualizar una ficha
@router.put("/{ficha_id}", response_model=FichaRespuesta)
def actualizar_ficha(ficha_id: int, datos: FichaActualizar, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar fichas
    verificar_rol(usuario_actual, ["encargado"])
    # Busco la ficha
    ficha = db.query(Ficha).filter(Ficha.id == ficha_id).first()
    # Si no existe
    if ficha is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La ficha no existe")
    # Si mandaron programa
    if datos.programa is not None:
        # Cambio el programa
        ficha.programa = datos.programa
    # Si mandaron jornada
    if datos.jornada is not None:
        # Reviso que la jornada esté en la lista
        if datos.jornada not in JORNADAS:
            # Respondo 400
            raise HTTPException(status_code=400, detail="La jornada debe ser DIURNA, NOCTURNA, MIXTA o FIN_DE_SEMANA")
        # Cambio la jornada
        ficha.jornada = datos.jornada
    # Si mandaron vocero
    if datos.vocero is not None:
        # Cambio el vocero
        ficha.vocero = datos.vocero
    # Si mandaron cantidad de estudiantes
    if datos.cantidad_estudiantes is not None:
        # Cambio la cantidad
        ficha.cantidad_estudiantes = datos.cantidad_estudiantes
    # Guardo los cambios
    db.commit()
    # Vuelvo a leer la ficha
    db.refresh(ficha)
    # Devuelvo la ficha actualizada
    return ficha


# Ruta para eliminar una ficha
@router.delete("/{ficha_id}")
def eliminar_ficha(ficha_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede eliminar fichas
    verificar_rol(usuario_actual, ["encargado"])
    # Busco la ficha
    ficha = db.query(Ficha).filter(Ficha.id == ficha_id).first()
    # Si no existe
    if ficha is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La ficha no existe")
    # Si ya está inactiva
    if ficha.activo == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="La ficha ya está inactiva")
    # Cuento cuántos aprendices tiene la ficha
    cantidad_aprendices = db.query(Usuario).filter(Usuario.ficha_id == ficha_id).count()
    # Si tiene aprendices no la puedo borrar
    if cantidad_aprendices > 0:
        # Solo la desactivo (borrado lógico)
        ficha.activo = False
        # Guardo los cambios
        db.commit()
        # Respondo con un mensaje
        return {"mensaje": "La ficha tiene aprendices, por eso solo se desactivó"}
    # Si no tiene aprendices la borro de verdad
    db.delete(ficha)
    # Guardo los cambios
    db.commit()
    # Respondo con un mensaje
    return {"mensaje": "La ficha se eliminó"}
