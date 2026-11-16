"""Reglas de negocio del Menú del Día (RF08, RF15, RF16, RF17)."""

# Sesión de base de datos
from sqlalchemy.orm import Session

# Fecha de hoy en Colombia
from app.core import tiempo
# Errores 409, 404 y 400
from app.core.excepciones import ConflictoError, NoEncontradoError, ReglaNegocioError
# Modelos de las tablas menus y usuarios
from app.models import Menu, Usuario
# Consultas de menús
from app.repositories.menu_repository import MenuRepository
# Consultas de reservas
from app.repositories.reserva_repository import ReservaRepository
# Arma la respuesta paginada
from app.schemas.comunes import armar_pagina
# Esquemas de menús
from app.schemas.menu import FiltrosMenu, MenuActualizar, MenuCrear, MenuParaComensal, MiReserva
# Función que calcula el precio según el rol
from app.services.reserva_service import calcular_tarifa


# Clase con las reglas del Menú del Día
class MenuService:
    # Constructor: recibe la sesión y crea los repositorios
    def __init__(self, db: Session) -> None:
        # Repositorio de menús
        self.menus = MenuRepository(db)
        # Repositorio de reservas
        self.reservas = ReservaRepository(db)

    # Lista menús con filtros
    def listar(self, filtros: FiltrosMenu) -> dict:
        # Consulta (menús, total)
        items, total = self.menus.listar(filtros)
        # Respuesta paginada
        return armar_pagina(items, total, filtros)

    # Busca un menú o responde 404
    def obtener(self, menu_id: int) -> Menu:
        # Busca por id
        menu = self.menus.obtener_por_id(menu_id)
        # Si no existe...
        if menu is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un menú con id {menu_id}.")
        # Devuelve el menú
        return menu

    # Crea un menú
    def crear(self, datos: MenuCrear, actor: Usuario) -> Menu:
        """Solo puede existir un menú por fecha; el cupo disponible inicia igual al total."""
        # Si ya hay un menú en esa fecha...
        if self.menus.existe_fecha(datos.fecha):
            # ...responde 409 (la fecha se muestra como día/mes/año)
            raise ConflictoError(f"Ya existe un menú para el {datos.fecha:%d/%m/%Y}.")
        # Crea el menú: cupo disponible = cupo total, y auditoría
        menu = Menu(**datos.model_dump(), cantidad_disponible=datos.cantidad_total, creado_por=actor.id)
        # Guarda y devuelve el menú
        return self.menus.guardar(menu)

    # Actualiza un menú
    def actualizar(self, menu_id: int, datos: MenuActualizar, actor: Usuario) -> Menu:
        # Lee el menú bloqueando su fila (nadie reserva mientras se cambia el cupo)
        menu = self.menus.obtener_para_actualizar(menu_id)
        # Si no existe...
        if menu is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un menú con id {menu_id}.")
        # Si el menú es de una fecha pasada...
        if menu.fecha < tiempo.hoy():
            # ...responde 400
            raise ReglaNegocioError("No se puede modificar el menú de una fecha que ya pasó.")

        # Solo los campos enviados
        cambios = datos.model_dump(exclude_none=True)
        # Si se quiere cambiar el cupo...
        if "cantidad_total" in cambios:
            # Almuerzos ya vendidos = total - disponible
            vendidos = menu.cantidad_total - menu.cantidad_disponible
            # Saca el nuevo cupo del diccionario de cambios
            nuevo_total = cambios.pop("cantidad_total")
            # Si el nuevo cupo es menor que lo vendido...
            if nuevo_total < vendidos:
                # ...responde 400
                raise ReglaNegocioError(f"El cupo no puede ser menor que los {vendidos} almuerzos ya vendidos.")
            # Asigna el nuevo cupo total
            menu.cantidad_total = nuevo_total
            # Recalcula el disponible
            menu.cantidad_disponible = nuevo_total - vendidos

        # Copia los demás cambios (nombre, descripción, precios)
        for campo, valor in cambios.items():
            # Asigna el valor
            setattr(menu, campo, valor)
        # Auditoría
        menu.actualizado_por = actor.id
        # Guarda y devuelve el menú
        return self.menus.guardar(menu)

    # Elimina un menú (lógico o físico)
    def eliminar(self, menu_id: int, actor: Usuario) -> str:
        """Borrado lógico si el menú tiene reservas; físico si no tiene."""
        # Busca el menú (404 si no existe)
        menu = self.obtener(menu_id)
        # Si ya está inactivo...
        if not menu.activo:
            # ...responde 400
            raise ReglaNegocioError("El menú ya está inactivo.")
        # Fecha en formato día/mes/año para el mensaje
        fecha = f"{menu.fecha:%d/%m/%Y}"
        # Si tiene reservas...
        if self.menus.tiene_reservas(menu.id):
            # ...solo se desactiva
            menu.activo = False
            # Auditoría
            menu.actualizado_por = actor.id
            # Guarda el cambio
            self.menus.guardar(menu)
            # Mensaje de borrado lógico
            return f"El menú del {fecha} tiene reservas: se desactivó (borrado lógico) y ya no recibe reservas."
        # Si no tiene reservas, se borra definitivamente
        self.menus.eliminar(menu)
        # Mensaje de borrado físico
        return f"El menú del {fecha} se eliminó definitivamente."

    # Menú de hoy para quien consulta
    def del_dia(self, actor: Usuario) -> MenuParaComensal:
        """Menú de hoy con el precio que le corresponde a quien consulta (RF08)."""
        # Busca el menú de la fecha de hoy
        menu = self.menus.obtener_por_fecha(tiempo.hoy())
        # Si no hay menú o está inactivo...
        if menu is None or not menu.activo:
            # ...responde 404
            raise NoEncontradoError("Aún no hay menú para hoy.")
        # Devuelve el menú con el precio y la reserva de quien consulta
        return self._para_comensal(menu, actor)

    # Próximos menús para quien consulta
    def proximos(self, actor: Usuario) -> list[MenuParaComensal]:
        """Menús activos desde hoy, para elegir cuál reservar."""
        # Convierte cada menú activo desde hoy en la versión con precio propio
        return [self._para_comensal(menu, actor) for menu in self.menus.listar_activos_desde(tiempo.hoy())]

    # Agrega al menú el precio y la reserva de quien consulta
    def _para_comensal(self, menu: Menu, actor: Usuario) -> MenuParaComensal:
        # Calcula (tipo, valor, estado) según el rol; None si es el encargado
        tarifa = calcular_tarifa(actor, menu)
        # Busca si la persona ya tiene una reserva vigente para este menú
        reserva = self.reservas.vigente_de(menu.id, actor.id)
        # Convierte el menú en esquema y le agrega los dos campos personales
        return MenuParaComensal.model_validate(menu).model_copy(update={
            # El valor de la tarifa (posición 1) o None
            "precio_para_mi": tarifa[1] if tarifa else None,
            # La reserva convertida a esquema o None
            "mi_reserva": MiReserva.model_validate(reserva) if reserva else None,
        })
