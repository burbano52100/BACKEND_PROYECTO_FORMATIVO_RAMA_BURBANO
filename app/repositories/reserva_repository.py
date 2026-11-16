"""Acceso a datos de reservas y consumos."""

# Tipo fecha
from datetime import date
# Decimal = número decimal exacto
from decimal import Decimal

# func = funciones SQL (count, sum, coalesce); select = SELECT
from sqlalchemy import func, select
# Sesión de base de datos
from sqlalchemy.orm import Session

# Modelos de las tablas menus, reservas y usuarios
from app.models import Menu, Reserva, Usuario
# Función para paginar
from app.repositories.paginacion import paginar
# Estados, filtros y tipos de reserva
from app.schemas.reserva import EstadoReserva, FiltrosMisReservas, FiltrosReserva, TipoReserva

# Tipos de reserva que corresponden a aprendices (pagan o son beneficiarios)
TIPOS_APRENDIZ = (TipoReserva.APRENDIZ, TipoReserva.BENEFICIARIO)


# Clase con todas las consultas de reservas
class ReservaRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión
        self.db = db

    # Busca una reserva por su id
    def obtener_por_id(self, reserva_id: int) -> Reserva | None:
        # SELECT por llave primaria
        return self.db.get(Reserva, reserva_id)

    # Busca la reserva vigente (no cancelada) de una persona para un menú
    def vigente_de(self, menu_id: int, usuario_id: int) -> Reserva | None:
        """Reserva no cancelada de la persona para ese menú."""
        # SELECT * FROM reservas WHERE ...
        consulta = select(Reserva).where(
            # ... del menú indicado
            Reserva.menu_id == menu_id,
            # ... de la persona indicada
            Reserva.usuario_id == usuario_id,
            # ... que no esté cancelada
            Reserva.estado != EstadoReserva.CANCELADA,
        )
        # Ejecuta y devuelve la reserva (o None si no tiene)
        return self.db.scalar(consulta)

    # Lista todas las reservas con filtros (vista del encargado)
    def listar(self, filtros: FiltrosReserva) -> tuple[list[Reserva], int]:
        # Arma la consulta base
        consulta = (
            # SELECT * FROM reservas
            select(Reserva)
            # JOIN menus: se necesita la fecha del menú para filtrar y ordenar
            .join(Menu, Menu.id == Reserva.menu_id)
            # Ordena por fecha del menú (más reciente primero) y luego por id
            .order_by(Menu.fecha.desc(), Reserva.id.desc())
        )
        # Filtro por fecha exacta del menú
        if filtros.fecha:
            # WHERE menus.fecha = :fecha
            consulta = consulta.where(Menu.fecha == filtros.fecha)
        # Filtro desde una fecha
        if filtros.desde:
            # WHERE menus.fecha >= :desde
            consulta = consulta.where(Menu.fecha >= filtros.desde)
        # Filtro hasta una fecha
        if filtros.hasta:
            # WHERE menus.fecha <= :hasta
            consulta = consulta.where(Menu.fecha <= filtros.hasta)
        # Filtro por estado
        if filtros.estado:
            # WHERE reservas.estado = :estado
            consulta = consulta.where(Reserva.estado == filtros.estado)
        # Filtro por tipo
        if filtros.tipo:
            # WHERE reservas.tipo = :tipo
            consulta = consulta.where(Reserva.tipo == filtros.tipo)
        # Filtro por persona
        if filtros.usuario_id is not None:
            # WHERE reservas.usuario_id = :usuario_id
            consulta = consulta.where(Reserva.usuario_id == filtros.usuario_id)
        # Filtro por ficha
        if filtros.ficha_id is not None:
            # JOIN usuarios para conocer la ficha de quien reservó y filtra por ella
            consulta = consulta.join(Usuario, Usuario.id == Reserva.usuario_id).where(Usuario.ficha_id == filtros.ficha_id)
        # Ejecuta la consulta paginada
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)

    # Lista las reservas de una persona (sus consumos)
    def listar_de_usuario(self, usuario_id: int, filtros: FiltrosMisReservas) -> tuple[list[Reserva], int]:
        """Historial de la persona, del más reciente al más antiguo (RF14, RF27)."""
        # Arma la consulta
        consulta = (
            # SELECT * FROM reservas
            select(Reserva)
            # JOIN menus para ordenar por la fecha del menú
            .join(Menu, Menu.id == Reserva.menu_id)
            # Solo las reservas de esta persona
            .where(Reserva.usuario_id == usuario_id)
            # Más recientes primero
            .order_by(Menu.fecha.desc(), Reserva.id.desc())
        )
        # Si se filtró por estado...
        if filtros.estado:
            # ...WHERE estado = :estado
            consulta = consulta.where(Reserva.estado == filtros.estado)
        # Ejecuta la consulta paginada
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)

    # Lista los aprendices de una ficha que reservaron en una fecha
    def listar_aprendices_de_ficha(self, ficha_id: int, fecha: date) -> list[Reserva]:
        """Aprendices de la ficha que tienen reserva vigente para el menú de esa fecha (RF41)."""
        # Arma la consulta
        consulta = (
            # SELECT * FROM reservas
            select(Reserva)
            # JOIN menus para filtrar por fecha
            .join(Menu, Menu.id == Reserva.menu_id)
            # JOIN usuarios para filtrar por ficha y ordenar por nombre
            .join(Usuario, Usuario.id == Reserva.usuario_id)
            # Condiciones (todas deben cumplirse)
            .where(
                # El aprendiz pertenece a la ficha
                Usuario.ficha_id == ficha_id,
                # El menú es de la fecha pedida
                Menu.fecha == fecha,
                # La reserva es de aprendiz o beneficiario
                Reserva.tipo.in_(TIPOS_APRENDIZ),
                # La reserva no está cancelada
                Reserva.estado != EstadoReserva.CANCELADA,
            )
            # Ordenadas por nombre del aprendiz
            .order_by(Usuario.nombre)
        )
        # Ejecuta y convierte el resultado en lista
        return list(self.db.scalars(consulta))

    # Cuenta las reservas de aprendices de una fecha
    def contar_aprendices_del_dia(self, fecha: date) -> int:
        # Arma la consulta
        consulta = (
            # SELECT count(reservas.id)
            select(func.count(Reserva.id))
            # JOIN menus para filtrar por fecha
            .join(Menu, Menu.id == Reserva.menu_id)
            # Del día pedido, de aprendices y no canceladas
            .where(Menu.fecha == fecha, Reserva.tipo.in_(TIPOS_APRENDIZ), Reserva.estado != EstadoReserva.CANCELADA)
        )
        # Ejecuta y devuelve el número
        return self.db.scalar(consulta)

    # Cuenta y suma los consumos de una persona entre dos fechas
    def consumo_en_rango(self, usuario_id: int, desde: date, hasta: date) -> tuple[int, Decimal]:
        """Cantidad y valor de los consumos vigentes de una persona entre dos fechas."""
        # Ejecuta la consulta y toma la única fila del resultado
        fila = self.db.execute(
            # SELECT count(id), coalesce(sum(valor), 0)
            select(func.count(Reserva.id), func.coalesce(func.sum(Reserva.valor), 0))
            # JOIN menus para filtrar por fecha
            .join(Menu, Menu.id == Reserva.menu_id)
            # Condiciones
            .where(
                # De la persona
                Reserva.usuario_id == usuario_id,
                # No canceladas
                Reserva.estado != EstadoReserva.CANCELADA,
                # Entre las dos fechas (incluidas)
                Menu.fecha.between(desde, hasta),
            )
        ).one()  # .one(): exige exactamente una fila de resultado
        # Devuelve (cantidad, valor total)
        return fila[0], fila[1]

    # Guarda una reserva nueva
    def registrar(self, reserva: Reserva) -> Reserva:
        """Guarda la reserva y el nuevo cupo del menú en UNA sola transacción.

        El servicio ya descontó menu.cantidad_disponible; el commit confirma
        ambos cambios juntos: o se guardan los dos, o ninguno.
        """
        # INSERT de la reserva (el UPDATE del cupo ya está pendiente en la sesión)
        self.db.add(reserva)
        # Confirma los dos cambios juntos
        self.db.commit()
        # Vuelve a leer la reserva (id y fecha de creación)
        self.db.refresh(reserva)
        # Devuelve la reserva guardada
        return reserva

    # Guarda una reserva modificada (cancelación o pago)
    def guardar(self, reserva: Reserva) -> Reserva:
        # UPDATE
        self.db.add(reserva)
        # Confirma
        self.db.commit()
        # Vuelve a leer la fila
        self.db.refresh(reserva)
        # Devuelve la reserva
        return reserva
