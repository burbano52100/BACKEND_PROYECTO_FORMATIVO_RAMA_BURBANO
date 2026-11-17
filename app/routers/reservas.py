# Rutas para reservar almuerzos, cancelarlos y marcar los pagos

# date es una fecha y datetime es fecha con hora
from datetime import date, datetime
# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas, Depends es para dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Horario en el que se puede reservar
from app.config import HORA_APERTURA, HORA_CIERRE
# Función que da la sesión de la base de datos
from app.database import get_db
# Modelos que uso
from app.models import Menu, Reserva, Usuario
# Esquemas que uso
from app.schemas import ReservaCrear, PagoReservaDatos
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol

# Creo el router, todas las rutas empiezan con /reservas
router = APIRouter(prefix="/reservas", tags=["Reservas"])


# Función que convierte una reserva en un diccionario para responder
def convertir_reserva(reserva):
    # Armo el diccionario con los datos de la reserva
    return {
        "id": reserva.id,  # Id de la reserva
        "menu_id": reserva.menu_id,  # Id del menú
        "fecha_menu": reserva.menu.fecha,  # Fecha del menú
        "nombre_menu": reserva.menu.nombre,  # Nombre del plato
        "usuario_id": reserva.usuario_id,  # Id de quien reservó
        "nombre_usuario": reserva.usuario.nombre,  # Nombre de quien reservó
        "tipo": reserva.tipo,  # APRENDIZ, BENEFICIARIO, INSTRUCTOR o INVITADO
        "valor": reserva.valor,  # Lo que tiene que pagar
        "estado": reserva.estado,  # Estado de la reserva
        "fecha_creacion": reserva.fecha_creacion,  # Cuándo se hizo
    }


# Función que dice si estamos en el horario para reservar o cancelar
def esta_en_horario():
    # Saco la hora de ahora (solo la hora, de 0 a 23)
    hora_actual = datetime.now().hour
    # Si está entre la hora de apertura y la de cierre
    if hora_actual >= HORA_APERTURA and hora_actual < HORA_CIERRE:
        # Sí está en horario
        return True
    # Si no, no está en horario
    return False


# Ruta para reservar o comprar un almuerzo (aprendiz, instructor e invitado)
@router.post("", status_code=201)
def reservar(datos: ReservaCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo los que comen pueden reservar (el encargado no)
    verificar_rol(usuario_actual, ["aprendiz", "instructor", "invitado"])
    # Reviso que esté en el horario
    if not esta_en_horario():
        # Respondo 400
        raise HTTPException(status_code=400, detail="Solo se puede reservar entre las " + str(HORA_APERTURA) + ":00 y las " + str(HORA_CIERRE) + ":00")
    # Busco el menú
    menu = db.query(Menu).filter(Menu.id == datos.menu_id).first()
    # Si no existe
    if menu is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El menú no existe")
    # Si el menú está inactivo
    if menu.activo == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El menú no está disponible")
    # Si el menú es de un día que ya pasó
    if menu.fecha < date.today():
        # Respondo 400
        raise HTTPException(status_code=400, detail="No se puede reservar el menú de un día que ya pasó")
    # Si ya no quedan almuerzos
    if menu.cantidad_disponible <= 0:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El menú está agotado")
    # Busco si la persona ya tiene una reserva para este menú
    reserva_existente = db.query(Reserva).filter(
        Reserva.menu_id == menu.id,  # De este menú
        Reserva.usuario_id == usuario_actual.id,  # De esta persona
        Reserva.estado != "CANCELADA",  # Que no esté cancelada
    ).first()
    # Si ya tiene una reserva
    if reserva_existente is not None:
        # Respondo 400 porque solo puede tener una
        raise HTTPException(status_code=400, detail="Ya tiene una reserva para este menú")
    # Saco el nombre del rol
    rol = usuario_actual.rol.nombre
    # Si es aprendiz
    if rol == "aprendiz":
        # Si es beneficiario
        if usuario_actual.es_beneficiario == True:
            # El tipo es beneficiario
            tipo = "BENEFICIARIO"
            # No paga nada
            valor = 0
            # Queda pagado de una vez
            estado = "PAGADO"
        # Si no es beneficiario
        else:
            # El tipo es aprendiz
            tipo = "APRENDIZ"
            # Paga el precio de aprendiz
            valor = menu.precio_aprendiz
            # Queda reservado hasta que pague
            estado = "RESERVADO"
    # Si es instructor
    elif rol == "instructor":
        # El tipo es instructor
        tipo = "INSTRUCTOR"
        # Paga el precio de aprendiz
        valor = menu.precio_aprendiz
        # Queda pendiente porque lo paga en su cuenta del mes
        estado = "PENDIENTE"
    # Si es invitado
    else:
        # El tipo es invitado
        tipo = "INVITADO"
        # Paga el precio de invitado
        valor = menu.precio_invitado
        # Queda reservado hasta que pague
        estado = "RESERVADO"
    # Le quito un almuerzo a los disponibles
    menu.cantidad_disponible = menu.cantidad_disponible - 1
    # Creo la reserva
    nueva_reserva = Reserva(
        menu_id=menu.id,  # Menú
        usuario_id=usuario_actual.id,  # Persona
        tipo=tipo,  # Tipo
        valor=valor,  # Valor
        estado=estado,  # Estado
    )
    # La agrego a la sesión
    db.add(nueva_reserva)
    # Guardo la reserva y el menú al mismo tiempo
    db.commit()
    # Vuelvo a leer la reserva para tener el id
    db.refresh(nueva_reserva)
    # Devuelvo la reserva
    return convertir_reserva(nueva_reserva)


# Ruta para ver mis reservas (aprendiz, instructor e invitado)
@router.get("/mias")
def mis_reservas(estado: Optional[str] = None, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo los que comen tienen reservas
    verificar_rol(usuario_actual, ["aprendiz", "instructor", "invitado"])
    # Traigo las reservas de la persona
    consulta = db.query(Reserva).filter(Reserva.usuario_id == usuario_actual.id)
    # Si mandaron estado
    if estado is not None:
        # Filtro por estado
        consulta = consulta.filter(Reserva.estado == estado)
    # Ordeno de la más nueva a la más vieja
    reservas = consulta.order_by(Reserva.id.desc()).all()
    # Aquí voy a guardar las reservas convertidas
    lista = []
    # Recorro las reservas
    for reserva in reservas:
        # Agrego cada reserva convertida
        lista.append(convertir_reserva(reserva))
    # Devuelvo la lista
    return lista


# Ruta para ver todas las reservas (solo el encargado)
@router.get("")
def listar_reservas(
    fecha: Optional[date] = None,  # Fecha del menú
    estado: Optional[str] = None,  # Estado de la reserva
    tipo: Optional[str] = None,  # Tipo de reserva
    skip: int = 0,  # Cuántos registros me salto
    limit: int = 100,  # Cuántos registros traigo como máximo
    db: Session = Depends(get_db),  # Sesión de la base de datos
    usuario_actual: Usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede ver todas las reservas
    verificar_rol(usuario_actual, ["encargado"])
    # Empiezo con todas las reservas
    consulta = db.query(Reserva)
    # Si mandaron fecha
    if fecha is not None:
        # Busco el menú de esa fecha
        menu = db.query(Menu).filter(Menu.fecha == fecha).first()
        # Si no hay menú ese día
        if menu is None:
            # No hay reservas
            return []
        # Filtro por el menú de ese día
        consulta = consulta.filter(Reserva.menu_id == menu.id)
    # Si mandaron estado
    if estado is not None:
        # Filtro por estado
        consulta = consulta.filter(Reserva.estado == estado)
    # Si mandaron tipo
    if tipo is not None:
        # Filtro por tipo
        consulta = consulta.filter(Reserva.tipo == tipo)
    # Ordeno de la más nueva a la más vieja y pagino
    reservas = consulta.order_by(Reserva.id.desc()).offset(skip).limit(limit).all()
    # Aquí voy a guardar las reservas convertidas
    lista = []
    # Recorro las reservas
    for reserva in reservas:
        # Agrego cada reserva convertida
        lista.append(convertir_reserva(reserva))
    # Devuelvo la lista
    return lista


# Ruta para ver una reserva por su id
@router.get("/{reserva_id}")
def ver_reserva(reserva_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Busco la reserva
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    # Si no existe
    if reserva is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La reserva no existe")
    # Si no es el encargado solo puede ver sus propias reservas
    if usuario_actual.rol.nombre != "encargado" and reserva.usuario_id != usuario_actual.id:
        # Respondo 403
        raise HTTPException(status_code=403, detail="Solo puede ver sus propias reservas")
    # Devuelvo la reserva
    return convertir_reserva(reserva)


# Ruta para cancelar mi reserva
@router.patch("/{reserva_id}/cancelar")
def cancelar_reserva(reserva_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo los que comen pueden cancelar
    verificar_rol(usuario_actual, ["aprendiz", "instructor", "invitado"])
    # Busco la reserva
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    # Si no existe
    if reserva is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La reserva no existe")
    # Solo puede cancelar sus propias reservas
    if reserva.usuario_id != usuario_actual.id:
        # Respondo 403
        raise HTTPException(status_code=403, detail="Solo puede cancelar sus propias reservas")
    # Al principio digo que no se puede cancelar
    se_puede_cancelar = False
    # Si está reservada o pendiente sí se puede
    if reserva.estado == "RESERVADO" or reserva.estado == "PENDIENTE":
        # Sí se puede
        se_puede_cancelar = True
    # Si es de un beneficiario (no pagó nada) también se puede
    if reserva.tipo == "BENEFICIARIO" and reserva.estado == "PAGADO":
        # Sí se puede
        se_puede_cancelar = True
    # Si no se puede cancelar
    if se_puede_cancelar == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="No se puede cancelar una reserva en estado " + reserva.estado)
    # Si el menú es de un día que ya pasó
    if reserva.menu.fecha < date.today():
        # Respondo 400
        raise HTTPException(status_code=400, detail="No se puede cancelar la reserva de un día que ya pasó")
    # Reviso que esté en el horario
    if not esta_en_horario():
        # Respondo 400
        raise HTTPException(status_code=400, detail="Solo se puede cancelar entre las " + str(HORA_APERTURA) + ":00 y las " + str(HORA_CIERRE) + ":00")
    # Le devuelvo el almuerzo al menú
    reserva.menu.cantidad_disponible = reserva.menu.cantidad_disponible + 1
    # Cambio el estado a cancelada
    reserva.estado = "CANCELADA"
    # Guardo los cambios
    db.commit()
    # Vuelvo a leer la reserva
    db.refresh(reserva)
    # Devuelvo la reserva
    return convertir_reserva(reserva)


# Ruta para marcar si una reserva se pagó o no (solo el encargado)
@router.patch("/{reserva_id}/pago")
def marcar_pago(reserva_id: int, datos: PagoReservaDatos, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede marcar pagos
    verificar_rol(usuario_actual, ["encargado"])
    # El estado solo puede ser PAGADO o NO_PAGADO
    if datos.estado != "PAGADO" and datos.estado != "NO_PAGADO":
        # Respondo 400
        raise HTTPException(status_code=400, detail="El estado debe ser PAGADO o NO_PAGADO")
    # Busco la reserva
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    # Si no existe
    if reserva is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La reserva no existe")
    # Los instructores pagan en la cartera, no aquí
    if reserva.tipo == "INSTRUCTOR":
        # Respondo 400
        raise HTTPException(status_code=400, detail="Los consumos de los instructores se pagan en la cartera")
    # Los beneficiarios no pagan
    if reserva.tipo == "BENEFICIARIO":
        # Respondo 400
        raise HTTPException(status_code=400, detail="La reserva de un beneficiario no tiene costo")
    # Si la reserva está cancelada
    if reserva.estado == "CANCELADA":
        # Respondo 400
        raise HTTPException(status_code=400, detail="La reserva está cancelada")
    # Cambio el estado
    reserva.estado = datos.estado
    # Guardo los cambios
    db.commit()
    # Vuelvo a leer la reserva
    db.refresh(reserva)
    # Devuelvo la reserva
    return convertir_reserva(reserva)
