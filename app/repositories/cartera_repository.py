"""Acceso a datos de la cartera: consumos y pagos de los instructores."""

# RowMapping = fila de resultado tipo diccionario; func, select y update arman SQL
from sqlalchemy import RowMapping, func, select, update
# Sesión de base de datos
from sqlalchemy.orm import Session

# Nombres de los roles
from app.core.roles import Roles
# Modelos de las tablas usadas
from app.models import Menu, PagoInstructor, Reserva, Rol, Usuario
# Estados y tipos de reserva
from app.schemas.reserva import EstadoReserva, TipoReserva


# Clase con las consultas de la cartera
class CarteraRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión
        self.db = db

    # Calcula por instructor lo consumido, lo pagado y lo pendiente
    def resumen_instructores(self, instructor_id: int | None = None) -> list[RowMapping]:
        """Por instructor: total consumido, total pagado, almuerzos pendientes y
        fecha del consumo pendiente más antiguo (consulta combinada con subconsultas)."""
        # Subconsulta 1: consumos de cada instructor
        consumos = (
            # Columnas que calcula
            select(
                # Id del instructor
                Reserva.usuario_id.label("instructor_id"),
                # Suma de los valores de sus consumos
                func.sum(Reserva.valor).label("total"),
                # Cuántos consumos están PENDIENTE (count con FILTER)
                func.count(Reserva.id).filter(Reserva.estado == EstadoReserva.PENDIENTE).label("pendientes"),
                # Fecha del consumo pendiente más antiguo (min con FILTER)
                func.min(Menu.fecha).filter(Reserva.estado == EstadoReserva.PENDIENTE).label("pendiente_desde"),
            )
            # JOIN menus para conocer la fecha de cada consumo
            .join(Menu, Menu.id == Reserva.menu_id)
            # Solo consumos de instructores que no estén cancelados
            .where(Reserva.tipo == TipoReserva.INSTRUCTOR, Reserva.estado != EstadoReserva.CANCELADA)
            # Un resultado por instructor
            .group_by(Reserva.usuario_id)
            # La convierte en subconsulta para unirla después
            .subquery()
        )
        # Subconsulta 2: pagos de cada instructor
        pagos = (
            # Id del instructor y suma de sus pagos
            select(PagoInstructor.instructor_id, func.sum(PagoInstructor.valor).label("pagado"))
            # Un resultado por instructor
            .group_by(PagoInstructor.instructor_id)
            # La convierte en subconsulta
            .subquery()
        )
        # Consulta principal: todos los instructores con sus consumos y pagos
        consulta = (
            # Columnas del resultado
            select(
                # Id del instructor
                Usuario.id.label("instructor_id"),
                # Nombre
                Usuario.nombre,
                # Documento
                Usuario.documento,
                # Total consumido (0 si no tiene consumos)
                func.coalesce(consumos.c.total, 0).label("total_consumido"),
                # Total pagado (0 si no tiene pagos)
                func.coalesce(pagos.c.pagado, 0).label("total_pagado"),
                # Almuerzos pendientes (0 si no tiene)
                func.coalesce(consumos.c.pendientes, 0).label("almuerzos_pendientes"),
                # Fecha del consumo pendiente más antiguo (NULL si no tiene)
                consumos.c.pendiente_desde,
            )
            # JOIN roles para filtrar solo instructores
            .join(Rol, Rol.id == Usuario.rol_id)
            # LEFT JOIN consumos: incluye instructores aunque no hayan consumido
            .outerjoin(consumos, consumos.c.instructor_id == Usuario.id)
            # LEFT JOIN pagos: incluye instructores aunque no hayan pagado
            .outerjoin(pagos, pagos.c.instructor_id == Usuario.id)
            # Solo usuarios con rol instructor
            .where(Rol.nombre == Roles.INSTRUCTOR)
            # Ordenados por nombre
            .order_by(Usuario.nombre)
        )
        # Si se pidió un instructor en particular...
        if instructor_id is not None:
            # ...filtra por su id
            consulta = consulta.where(Usuario.id == instructor_id)
        # Ejecuta y devuelve las filas como diccionarios (mappings)
        return list(self.db.execute(consulta).mappings())

    # Lista los pagos de un instructor
    def pagos_de(self, instructor_id: int) -> list[PagoInstructor]:
        # Arma la consulta
        consulta = (
            # SELECT * FROM pagos_instructor
            select(PagoInstructor)
            # Del instructor indicado
            .where(PagoInstructor.instructor_id == instructor_id)
            # Del más reciente al más antiguo
            .order_by(PagoInstructor.creado_en.desc(), PagoInstructor.id.desc())
        )
        # Ejecuta y convierte el resultado en lista
        return list(self.db.scalars(consulta))

    # Guarda un pago y, si salda la deuda, marca los consumos como pagados
    def registrar_pago(self, pago: PagoInstructor, saldar: bool, actor_id: int) -> PagoInstructor:
        """Guarda el pago y, si deja la cuenta en cero, marca los consumos
        pendientes como pagados. Todo en una sola transacción (RNF09)."""
        # INSERT del pago
        self.db.add(pago)
        # Si el pago deja la deuda en cero...
        if saldar:
            # ...ejecuta un UPDATE sobre las reservas
            self.db.execute(
                # UPDATE reservas
                update(Reserva)
                # WHERE usuario_id = instructor AND estado = 'PENDIENTE'
                .where(Reserva.usuario_id == pago.instructor_id, Reserva.estado == EstadoReserva.PENDIENTE)
                # SET estado = 'PAGADO', actualizado_por = encargado, actualizado_en = now()
                .values(estado=EstadoReserva.PAGADO, actualizado_por=actor_id, actualizado_en=func.now())
            )
        # Confirma el pago y el UPDATE juntos (o ninguno)
        self.db.commit()
        # Vuelve a leer el pago (id y fecha)
        self.db.refresh(pago)
        # Devuelve el pago guardado
        return pago
