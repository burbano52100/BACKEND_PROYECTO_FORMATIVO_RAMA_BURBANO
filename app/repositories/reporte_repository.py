"""Consultas de agregación para los reportes de ventas."""

# Tipo fecha
from datetime import date

# RowMapping = fila tipo diccionario; func = funciones SQL; select = SELECT
from sqlalchemy import RowMapping, func, select
# Sesión de base de datos
from sqlalchemy.orm import Session

# Modelos de las tablas menus y reservas
from app.models import Menu, Reserva
# Estados de reserva
from app.schemas.reserva import EstadoReserva


# Clase con las consultas de los reportes
class ReporteRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión
        self.db = db

    # Consulta genérica de ventas agrupadas por la columna que se indique
    def _ventas(self, desde: date, hasta: date, agrupar_por) -> list[RowMapping]:
        # Arma la consulta
        consulta = (
            # Columnas del resultado
            select(
                # La columna de agrupación (fecha o tipo)
                agrupar_por,
                # Cantidad de almuerzos
                func.count(Reserva.id).label("almuerzos"),
                # Suma de los valores (0 si no hay)
                func.coalesce(func.sum(Reserva.valor), 0).label("ingresos"),
            )
            # FROM reservas
            .select_from(Reserva)
            # JOIN menus para conocer la fecha
            .join(Menu, Menu.id == Reserva.menu_id)
            # Del período y sin las canceladas
            .where(Menu.fecha.between(desde, hasta), Reserva.estado != EstadoReserva.CANCELADA)
            # GROUP BY la columna elegida
            .group_by(agrupar_por)
            # ORDER BY la columna elegida
            .order_by(agrupar_por)
        )
        # Ejecuta y devuelve las filas como diccionarios
        return list(self.db.execute(consulta).mappings())

    # Ventas agrupadas por día
    def ventas_por_dia(self, desde: date, hasta: date) -> list[RowMapping]:
        # Agrupa por la fecha del menú
        return self._ventas(desde, hasta, Menu.fecha.label("fecha"))

    # Ventas agrupadas por tipo de cliente
    def ventas_por_tipo(self, desde: date, hasta: date) -> list[RowMapping]:
        # Agrupa por el tipo de reserva
        return self._ventas(desde, hasta, Reserva.tipo.label("tipo"))
