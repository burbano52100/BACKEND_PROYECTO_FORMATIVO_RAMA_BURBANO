"""Acceso a datos del Menú del Día."""

# Tipo fecha
from datetime import date

# Funciones para armar consultas SQL
from sqlalchemy import exists, select
# Sesión de base de datos
from sqlalchemy.orm import Session

# Modelos de las tablas menus y reservas
from app.models import Menu, Reserva
# Función para paginar
from app.repositories.paginacion import paginar
# Filtros del listado de menús
from app.schemas.menu import FiltrosMenu


# Clase con todas las consultas de menús
class MenuRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión
        self.db = db

    # Busca un menú por su id
    def obtener_por_id(self, menu_id: int) -> Menu | None:
        # SELECT por llave primaria
        return self.db.get(Menu, menu_id)

    # Busca el menú de una fecha
    def obtener_por_fecha(self, fecha: date) -> Menu | None:
        # SELECT * FROM menus WHERE fecha = :fecha
        return self.db.scalar(select(Menu).where(Menu.fecha == fecha))

    # Lee un menú bloqueando su fila
    def obtener_para_actualizar(self, menu_id: int) -> Menu | None:
        """Lee el menú y bloquea su fila (SELECT ... FOR UPDATE) hasta el commit.

        Así dos personas que reservan al mismo tiempo no toman el mismo último cupo.
        """
        # Arma la consulta
        consulta = (
            # SELECT * FROM menus
            select(Menu)
            # WHERE id = :menu_id
            .where(Menu.id == menu_id)
            # FOR UPDATE: bloquea la fila hasta el commit
            .with_for_update()
            .execution_options(populate_existing=True)  # leer el cupo real, no el de memoria
        )
        # Ejecuta y devuelve el menú (o None)
        return self.db.scalar(consulta)

    # Indica si ya hay un menú en esa fecha
    def existe_fecha(self, fecha: date) -> bool:
        # SELECT EXISTS (... WHERE fecha = :fecha)
        return self.db.scalar(select(exists().where(Menu.fecha == fecha)))

    # Indica si el menú tiene reservas (de cualquier estado)
    def tiene_reservas(self, menu_id: int) -> bool:
        # SELECT EXISTS (SELECT ... FROM reservas WHERE menu_id = :id)
        return self.db.scalar(select(exists().where(Reserva.menu_id == menu_id)))

    # Lista menús con filtros y paginación
    def listar(self, filtros: FiltrosMenu) -> tuple[list[Menu], int]:
        # Consulta base: del más reciente al más antiguo
        consulta = select(Menu).order_by(Menu.fecha.desc())
        # Si se envió fecha inicial...
        if filtros.desde:
            # ...WHERE fecha >= :desde
            consulta = consulta.where(Menu.fecha >= filtros.desde)
        # Si se envió fecha final...
        if filtros.hasta:
            # ...WHERE fecha <= :hasta
            consulta = consulta.where(Menu.fecha <= filtros.hasta)
        # Si se filtró por estado...
        if filtros.activo is not None:
            # ...WHERE activo = :activo
            consulta = consulta.where(Menu.activo == filtros.activo)
        # Ejecuta la consulta paginada
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)

    # Lista los menús activos desde una fecha (máximo 14)
    def listar_activos_desde(self, fecha: date, limite: int = 14) -> list[Menu]:
        # SELECT * FROM menus WHERE activo AND fecha >= :fecha ORDER BY fecha LIMIT 14
        consulta = select(Menu).where(Menu.activo, Menu.fecha >= fecha).order_by(Menu.fecha).limit(limite)
        # Ejecuta y convierte el resultado en lista
        return list(self.db.scalars(consulta))

    # Guarda un menú nuevo o modificado
    def guardar(self, menu: Menu) -> Menu:
        # INSERT o UPDATE
        self.db.add(menu)
        # Confirma en PostgreSQL (y libera el bloqueo FOR UPDATE si había)
        self.db.commit()
        # Vuelve a leer la fila
        self.db.refresh(menu)
        # Devuelve el menú guardado
        return menu

    # Borra un menú definitivamente
    def eliminar(self, menu: Menu) -> None:
        # Marca la fila para DELETE
        self.db.delete(menu)
        # Confirma el borrado
        self.db.commit()
