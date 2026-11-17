# Rutas para manejar el menú del día

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
from app.models import Menu, Reserva, Usuario
# Esquemas que uso
from app.schemas import MenuCrear, MenuActualizar, MenuRespuesta
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol

# Creo el router, todas las rutas empiezan con /menus
router = APIRouter(prefix="/menus", tags=["Menús"])


# Función que dice cuánto le toca pagar a un usuario según su rol
def calcular_precio(usuario, menu):
    # Si es aprendiz
    if usuario.rol.nombre == "aprendiz":
        # Si es beneficiario no paga nada
        if usuario.es_beneficiario == True:
            # Precio 0
            return 0
        # Si no es beneficiario paga el precio de aprendiz
        return menu.precio_aprendiz
    # El instructor paga lo mismo que el aprendiz (se le carga a su cuenta del mes)
    if usuario.rol.nombre == "instructor":
        # Precio de aprendiz
        return menu.precio_aprendiz
    # El invitado paga el precio de invitado
    if usuario.rol.nombre == "invitado":
        # Precio de invitado
        return menu.precio_invitado
    # El encargado no compra almuerzo
    return None


# Función que arma el menú con el precio que le toca a la persona que consulta
def menu_con_mi_precio(menu, usuario, db):
    # Busco si la persona ya tiene una reserva para ese menú
    mi_reserva = db.query(Reserva).filter(
        Reserva.menu_id == menu.id,  # De este menú
        Reserva.usuario_id == usuario.id,  # De esta persona
        Reserva.estado != "CANCELADA",  # Que no esté cancelada
    ).first()
    # Al principio digo que no tiene reserva
    mi_reserva_id = None
    # Si sí tiene reserva
    if mi_reserva is not None:
        # Guardo el id de la reserva
        mi_reserva_id = mi_reserva.id
    # Devuelvo el menú con los datos extra
    return {
        "id": menu.id,  # Id del menú
        "fecha": menu.fecha,  # Fecha
        "nombre": menu.nombre,  # Nombre del plato
        "descripcion": menu.descripcion,  # Lo que trae
        "precio_aprendiz": menu.precio_aprendiz,  # Precio de aprendiz
        "precio_invitado": menu.precio_invitado,  # Precio de invitado
        "cantidad_total": menu.cantidad_total,  # Cuántos hay en total
        "cantidad_disponible": menu.cantidad_disponible,  # Cuántos quedan
        "vendidos": menu.cantidad_total - menu.cantidad_disponible,  # Cuántos se vendieron
        "agotado": menu.cantidad_disponible == 0,  # True si ya no quedan
        "precio_para_mi": calcular_precio(usuario, menu),  # Lo que me toca pagar a mí
        "mi_reserva_id": mi_reserva_id,  # Id de mi reserva (None si no he reservado)
    }


# Ruta para ver el menú de hoy (todos los roles)
@router.get("/hoy")
def menu_de_hoy(db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Busco el menú activo de hoy
    menu = db.query(Menu).filter(Menu.fecha == date.today(), Menu.activo == True).first()
    # Si no hay menú hoy
    if menu is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="Todavía no hay menú para hoy")
    # Devuelvo el menú con mi precio
    return menu_con_mi_precio(menu, usuario_actual, db)


# Ruta para ver los menús de hoy en adelante (todos los roles)
@router.get("/proximos")
def proximos_menus(db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Traigo los menús activos desde hoy ordenados por fecha
    menus = db.query(Menu).filter(Menu.fecha >= date.today(), Menu.activo == True).order_by(Menu.fecha).all()
    # Aquí voy a guardar los menús con mi precio
    lista = []
    # Recorro los menús
    for menu in menus:
        # Agrego cada menú con mi precio
        lista.append(menu_con_mi_precio(menu, usuario_actual, db))
    # Devuelvo la lista
    return lista


# Ruta para ver todos los menús (historial, solo el encargado)
@router.get("", response_model=list[MenuRespuesta])
def listar_menus(
    desde: Optional[date] = None,  # Fecha inicial
    hasta: Optional[date] = None,  # Fecha final
    activo: Optional[bool] = None,  # Filtrar activos o inactivos
    skip: int = 0,  # Cuántos registros me salto
    limit: int = 100,  # Cuántos registros traigo como máximo
    db: Session = Depends(get_db),  # Sesión de la base de datos
    usuario_actual: Usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Empiezo con todos los menús
    consulta = db.query(Menu)
    # Si mandaron fecha inicial
    if desde is not None:
        # Solo los menús desde esa fecha
        consulta = consulta.filter(Menu.fecha >= desde)
    # Si mandaron fecha final
    if hasta is not None:
        # Solo los menús hasta esa fecha
        consulta = consulta.filter(Menu.fecha <= hasta)
    # Si mandaron activo
    if activo is not None:
        # Filtro por activo
        consulta = consulta.filter(Menu.activo == activo)
    # Ordeno del más nuevo al más viejo y pagino
    menus = consulta.order_by(Menu.fecha.desc()).offset(skip).limit(limit).all()
    # Devuelvo la lista
    return menus


# Ruta para ver un menú por su id (todos los roles)
@router.get("/{menu_id}", response_model=MenuRespuesta)
def ver_menu(menu_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Busco el menú
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    # Si no existe
    if menu is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El menú no existe")
    # Devuelvo el menú
    return menu


# Ruta para crear un menú
@router.post("", response_model=MenuRespuesta, status_code=201)
def crear_menu(datos: MenuCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear menús
    verificar_rol(usuario_actual, ["encargado"])
    # La fecha no puede ser de un día que ya pasó
    if datos.fecha < date.today():
        # Respondo 400
        raise HTTPException(status_code=400, detail="No se puede crear un menú para un día que ya pasó")
    # Busco si ya hay un menú en esa fecha
    existe = db.query(Menu).filter(Menu.fecha == datos.fecha).first()
    # Si ya hay uno
    if existe is not None:
        # Respondo 400 porque solo puede haber un menú por día
        raise HTTPException(status_code=400, detail="Ya existe un menú para esa fecha")
    # Creo el menú
    nuevo_menu = Menu(
        fecha=datos.fecha,  # Fecha
        nombre=datos.nombre,  # Nombre
        descripcion=datos.descripcion,  # Descripción
        precio_aprendiz=datos.precio_aprendiz,  # Precio de aprendiz
        precio_invitado=datos.precio_invitado,  # Precio de invitado
        cantidad_total=datos.cantidad_total,  # Cantidad total
        cantidad_disponible=datos.cantidad_total,  # Al principio están todos disponibles
    )
    # Lo agrego a la sesión
    db.add(nuevo_menu)
    # Lo guardo en la base de datos
    db.commit()
    # Lo vuelvo a leer para tener el id
    db.refresh(nuevo_menu)
    # Devuelvo el menú creado
    return nuevo_menu


# Ruta para actualizar un menú
@router.put("/{menu_id}", response_model=MenuRespuesta)
def actualizar_menu(menu_id: int, datos: MenuActualizar, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar menús
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el menú
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    # Si no existe
    if menu is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El menú no existe")
    # No se puede cambiar un menú de un día que ya pasó
    if menu.fecha < date.today():
        # Respondo 400
        raise HTTPException(status_code=400, detail="No se puede cambiar el menú de un día que ya pasó")
    # Si mandaron nombre
    if datos.nombre is not None:
        # Cambio el nombre
        menu.nombre = datos.nombre
    # Si mandaron descripción
    if datos.descripcion is not None:
        # Cambio la descripción
        menu.descripcion = datos.descripcion
    # Si mandaron precio de aprendiz
    if datos.precio_aprendiz is not None:
        # Cambio el precio
        menu.precio_aprendiz = datos.precio_aprendiz
    # Si mandaron precio de invitado
    if datos.precio_invitado is not None:
        # Cambio el precio
        menu.precio_invitado = datos.precio_invitado
    # Si mandaron cantidad total
    if datos.cantidad_total is not None:
        # Calculo cuántos almuerzos ya se vendieron
        vendidos = menu.cantidad_total - menu.cantidad_disponible
        # La cantidad nueva no puede ser menor que lo vendido
        if datos.cantidad_total < vendidos:
            # Respondo 400
            raise HTTPException(status_code=400, detail="La cantidad no puede ser menor que los " + str(vendidos) + " almuerzos ya vendidos")
        # Cambio la cantidad total
        menu.cantidad_total = datos.cantidad_total
        # Lo disponible es lo nuevo menos lo vendido
        menu.cantidad_disponible = datos.cantidad_total - vendidos
    # Guardo los cambios
    db.commit()
    # Vuelvo a leer el menú
    db.refresh(menu)
    # Devuelvo el menú actualizado
    return menu


# Ruta para eliminar un menú
@router.delete("/{menu_id}")
def eliminar_menu(menu_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede eliminar menús
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el menú
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    # Si no existe
    if menu is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El menú no existe")
    # Si ya está inactivo
    if menu.activo == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El menú ya está inactivo")
    # Cuento las reservas que tiene el menú
    cantidad_reservas = db.query(Reserva).filter(Reserva.menu_id == menu_id).count()
    # Si tiene reservas no lo puedo borrar
    if cantidad_reservas > 0:
        # Solo lo desactivo (borrado lógico)
        menu.activo = False
        # Guardo los cambios
        db.commit()
        # Respondo con un mensaje
        return {"mensaje": "El menú tiene reservas, por eso solo se desactivó"}
    # Si no tiene reservas lo borro de verdad
    db.delete(menu)
    # Guardo los cambios
    db.commit()
    # Respondo con un mensaje
    return {"mensaje": "El menú se eliminó"}
