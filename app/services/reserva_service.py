"""Reglas de negocio de reservas, compras y consumos de almuerzo (RF09 a RF14, RF17, RF42)."""

# Decimal = número decimal exacto (para el valor $0)
from decimal import Decimal

# Sesión de base de datos
from sqlalchemy.orm import Session

# Fecha y hora de Colombia
from app.core import tiempo
# Configuración (horario de reservas)
from app.core.config import settings
# Errores 409, 404, 403 y 400
from app.core.excepciones import ConflictoError, NoEncontradoError, PermisoDenegadoError, ReglaNegocioError
# Nombres de los roles
from app.core.roles import Roles
# Modelos de las tablas menus, reservas y usuarios
from app.models import Menu, Reserva, Usuario
# Consultas de menús
from app.repositories.menu_repository import MenuRepository
# Consultas de reservas
from app.repositories.reserva_repository import ReservaRepository
# Arma la respuesta paginada
from app.schemas.comunes import armar_pagina
# Esquemas de reservas
from app.schemas.reserva import (
    # Entrada para marcar el pago
    EstadoPagoEntrada,
    # Estados posibles
    EstadoReserva,
    # Filtros de "mis reservas"
    FiltrosMisReservas,
    # Filtros del listado general
    FiltrosReserva,
    # Entrada para reservar
    ReservaCrear,
    # Tipos de reserva
    TipoReserva,
)

# Roles que pueden reservar (el encargado no)
ROLES_COMENSALES = (Roles.APRENDIZ, Roles.INSTRUCTOR, Roles.INVITADO)


# Calcula el tipo, el precio y el estado inicial de una reserva según quién reserva
def calcular_tarifa(usuario: Usuario, menu: Menu) -> tuple[TipoReserva, Decimal, EstadoReserva] | None:
    """Precio y estado inicial según el tipo de cuenta (RF08, RF11, RF12).

    - Aprendiz: precio de aprendiz; beneficiario: $0 (queda pagado).
    - Instructor: precio de aprendiz, se carga a su cuenta mensual (PENDIENTE). Regla propuesta.
    - Invitado: precio de invitado.
    - Encargado: no consume almuerzos (None).
    """
    # Nombre del rol de quien reserva
    rol = usuario.rol.nombre
    # Si es aprendiz...
    if rol == Roles.APRENDIZ:
        # ...y además es beneficiario...
        if usuario.es_beneficiario:
            # ...tipo BENEFICIARIO, valor $0 y queda PAGADO
            return TipoReserva.BENEFICIARIO, Decimal(0), EstadoReserva.PAGADO
        # Aprendiz normal: precio de aprendiz y queda RESERVADO
        return TipoReserva.APRENDIZ, menu.precio_aprendiz, EstadoReserva.RESERVADO
    # Si es instructor...
    if rol == Roles.INSTRUCTOR:
        # ...precio de aprendiz y queda PENDIENTE (se paga en la cartera)
        return TipoReserva.INSTRUCTOR, menu.precio_aprendiz, EstadoReserva.PENDIENTE
    # Si es invitado...
    if rol == Roles.INVITADO:
        # ...precio de invitado y queda RESERVADO
        return TipoReserva.INVITADO, menu.precio_invitado, EstadoReserva.RESERVADO
    # El encargado no tiene tarifa
    return None


# Clase con las reglas de reservas
class ReservaService:
    # Constructor: recibe la sesión y crea los repositorios
    def __init__(self, db: Session) -> None:
        # Repositorio de reservas
        self.reservas = ReservaRepository(db)
        # Repositorio de menús
        self.menus = MenuRepository(db)

    # Proceso de reservar o comprar
    def reservar(self, datos: ReservaCrear, actor: Usuario) -> Reserva:
        """Proceso de negocio: reservar (aprendiz/instructor) o comprar (invitado) un almuerzo."""
        # Si el rol no puede reservar...
        if actor.rol.nombre not in ROLES_COMENSALES:
            # ...responde 403
            raise PermisoDenegadoError("Su tipo de cuenta no puede reservar almuerzos.")
        # Verifica el horario (7:00 a 21:00); si está fuera responde 400
        self._validar_horario("reservar")

        # Lee el menú bloqueando su fila (evita que dos personas tomen el último cupo)
        menu = self.menus.obtener_para_actualizar(datos.menu_id)
        # Si el menú no existe...
        if menu is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un menú con id {datos.menu_id}.")
        # Si el menú está inactivo...
        if not menu.activo:
            # ...responde 400
            raise ReglaNegocioError("El menú no está disponible.")
        # Si el menú es de un día que ya pasó...
        if menu.fecha < tiempo.hoy():
            # ...responde 400
            raise ReglaNegocioError("No se puede reservar el menú de una fecha que ya pasó.")
        # Si no queda cupo...
        if menu.cantidad_disponible <= 0:
            # ...responde 400
            raise ReglaNegocioError("El menú está agotado.")
        # Si la persona ya tiene una reserva vigente para este menú...
        if self.reservas.vigente_de(menu.id, actor.id):
            # ...responde 409
            raise ConflictoError(f"Ya tiene una reserva para el menú del {menu.fecha:%d/%m/%Y}.")

        # Calcula tipo, valor y estado según el rol (desempaqueta la tupla en 3 variables)
        tipo, valor, estado = calcular_tarifa(actor, menu)
        menu.cantidad_disponible -= 1  # RF17: descontar el cupo
        # Crea la reserva
        reserva = Reserva(
            # Menú, persona, tipo, valor, estado y auditoría
            menu_id=menu.id, usuario_id=actor.id, tipo=tipo, valor=valor, estado=estado, creado_por=actor.id
        )
        # Guarda la reserva y el nuevo cupo en una sola transacción
        return self.reservas.registrar(reserva)

    # Cancela una reserva propia
    def cancelar(self, reserva_id: int, actor: Usuario) -> Reserva:
        """Cambio de estado: la persona cancela su propia reserva y el cupo vuelve al menú."""
        # Busca la reserva (404 si no existe)
        reserva = self._obtener(reserva_id)
        # Si la reserva es de otra persona...
        if reserva.usuario_id != actor.id:
            # ...responde 403
            raise PermisoDenegadoError("Solo puede cancelar sus propias reservas.")
        # Las reservas de beneficiario están PAGADO con valor 0 y sí se pueden cancelar
        sin_costo = reserva.estado == EstadoReserva.PAGADO and reserva.valor == 0
        # Solo se cancelan las RESERVADO, PENDIENTE o las sin costo
        if reserva.estado not in (EstadoReserva.RESERVADO, EstadoReserva.PENDIENTE) and not sin_costo:
            # Si no, responde 400
            raise ReglaNegocioError(f"No se puede cancelar una reserva en estado {reserva.estado}.")
        # Si el menú ya pasó...
        if reserva.menu.fecha < tiempo.hoy():
            # ...responde 400
            raise ReglaNegocioError("No se puede cancelar la reserva de un día que ya pasó.")
        # Verifica el horario
        self._validar_horario("cancelar")

        # Lee el menú bloqueando su fila
        menu = self.menus.obtener_para_actualizar(reserva.menu_id)
        # Devuelve el cupo al menú
        menu.cantidad_disponible += 1
        # Cambia el estado de la reserva
        reserva.estado = EstadoReserva.CANCELADA
        # Auditoría
        reserva.actualizado_por = actor.id
        # Guarda la reserva y el cupo juntos
        return self.reservas.guardar(reserva)

    # El encargado marca una reserva como pagada o no pagada
    def marcar_pago(self, reserva_id: int, datos: EstadoPagoEntrada, actor: Usuario) -> Reserva:
        """El Encargado marca Pagado o No pagado (RF42). Los instructores van por la cartera."""
        # Busca la reserva (404 si no existe)
        reserva = self._obtener(reserva_id)
        # Si es de un instructor...
        if reserva.tipo == TipoReserva.INSTRUCTOR:
            # ...responde 400 (se paga en la cartera)
            raise ReglaNegocioError("Los consumos de instructores se pagan en la Cartera de Deudas.")
        # Si es de un beneficiario...
        if reserva.tipo == TipoReserva.BENEFICIARIO:
            # ...responde 400 (no cuesta nada)
            raise ReglaNegocioError("La reserva de un beneficiario no tiene costo.")
        # Si está cancelada...
        if reserva.estado == EstadoReserva.CANCELADA:
            # ...responde 400
            raise ReglaNegocioError("La reserva está cancelada.")
        # Asigna PAGADO o NO_PAGADO
        reserva.estado = datos.estado
        # Auditoría: queda registrado qué encargado marcó el pago
        reserva.actualizado_por = actor.id
        # Guarda y devuelve la reserva
        return self.reservas.guardar(reserva)

    # Consulta una reserva respetando los permisos
    def obtener(self, reserva_id: int, actor: Usuario) -> Reserva:
        # Busca la reserva (404 si no existe)
        reserva = self._obtener(reserva_id)
        # Si quien consulta no es encargado y la reserva no es suya...
        if actor.rol.nombre != Roles.ENCARGADO and reserva.usuario_id != actor.id:
            # ...responde 403
            raise PermisoDenegadoError("Solo puede consultar sus propias reservas.")
        # Devuelve la reserva
        return reserva

    # Lista todas las reservas (encargado)
    def listar(self, filtros: FiltrosReserva) -> dict:
        # Consulta (reservas, total)
        items, total = self.reservas.listar(filtros)
        # Respuesta paginada
        return armar_pagina(items, total, filtros)

    # Lista las reservas propias
    def listar_mias(self, actor: Usuario, filtros: FiltrosMisReservas) -> dict:
        # Consulta las reservas de la persona
        items, total = self.reservas.listar_de_usuario(actor.id, filtros)
        # Respuesta paginada
        return armar_pagina(items, total, filtros)

    # ----- Métodos internos -----

    # Busca una reserva o responde 404
    def _obtener(self, reserva_id: int) -> Reserva:
        # Busca por id
        reserva = self.reservas.obtener_por_id(reserva_id)
        # Si no existe...
        if reserva is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe una reserva con id {reserva_id}.")
        # Devuelve la reserva
        return reserva

    # Método estático: no usa datos del objeto
    @staticmethod
    # Verifica que la hora actual esté dentro del horario permitido
    def _validar_horario(accion: str) -> None:
        """Solo se reserva o cancela entre las 7:00 a. m. y las 9:00 p. m. (RF09)."""
        # Hora de inicio y de fin del .env
        inicio, fin = settings.HORA_INICIO_RESERVAS, settings.HORA_FIN_RESERVAS
        # Si la hora actual de Colombia está fuera del horario...
        if not tiempo.en_horario(tiempo.ahora(), inicio, fin):
            # ...responde 400 con el horario (formato HH:MM)
            raise ReglaNegocioError(f"Solo se puede {accion} entre las {inicio:%H:%M} y las {fin:%H:%M}.")
