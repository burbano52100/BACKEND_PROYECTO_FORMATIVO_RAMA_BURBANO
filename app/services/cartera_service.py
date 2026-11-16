"""Reglas de negocio de la cartera de deudas y la cuenta mensual de instructores (RF22 a RF27)."""

# Tipos fecha y duración
from datetime import date, timedelta
# Decimal = número decimal exacto (para el dinero)
from decimal import Decimal

# RowMapping = fila de resultado tipo diccionario
from sqlalchemy import RowMapping
# Sesión de base de datos
from sqlalchemy.orm import Session

# Fecha de hoy y último día del mes
from app.core import tiempo
# Configuración (días de plazo de pago)
from app.core.config import settings
# Errores 404 y 400
from app.core.excepciones import NoEncontradoError, ReglaNegocioError
# Nombres de los roles
from app.core.roles import Roles
# Modelos de las tablas pagos_instructor y usuarios
from app.models import PagoInstructor, Usuario
# Consultas de la cartera
from app.repositories.cartera_repository import CarteraRepository
# Consultas de reservas
from app.repositories.reserva_repository import ReservaRepository
# Consultas de usuarios
from app.repositories.usuario_repository import UsuarioRepository
# Estado de la cuenta y datos de entrada del pago
from app.schemas.cartera import EstadoCuenta, PagoCrear


# Da formato de pesos colombianos a un valor
def pesos(valor: Decimal) -> str:
    """Formato colombiano: 10000 -> $10.000"""
    # {:,.0f} pone comas de miles sin decimales (10,000); luego se cambian las comas por puntos
    return f"${valor:,.0f}".replace(",", ".")


# Clase con las reglas de la cartera
class CarteraService:
    # Constructor: recibe la sesión y crea los repositorios
    def __init__(self, db: Session) -> None:
        # Repositorio de la cartera
        self.cartera = CarteraRepository(db)
        # Repositorio de usuarios
        self.usuarios = UsuarioRepository(db)
        # Repositorio de reservas
        self.reservas = ReservaRepository(db)

    # Lista los instructores con deuda
    def listar(self, solo_vencidas: bool = False) -> dict:
        """Instructores con deuda, de mayor a menor saldo, y resumen de la cartera (RF22, RF25)."""
        # Fecha de hoy
        hoy = tiempo.hoy()
        # Calcula la deuda de cada instructor y se queda solo con los que deben algo (saldo > 0)
        deudores = [deuda for deuda in (self._calcular_deuda(fila, hoy) for fila in self.cartera.resumen_instructores())
                    if deuda["saldo"] > 0]  # Filtro: solo saldos mayores que cero
        # Si se pidieron solo las vencidas...
        if solo_vencidas:
            # ...filtra por estado VENCIDA
            deudores = [deuda for deuda in deudores if deuda["estado"] == EstadoCuenta.VENCIDA]
        # Ordena de mayor a menor saldo
        deudores.sort(key=lambda deuda: deuda["saldo"], reverse=True)

        # Lista solo con los saldos
        saldos = [deuda["saldo"] for deuda in deudores]
        # Suma de los saldos (empieza en Decimal 0 para no mezclar tipos)
        total = sum(saldos, Decimal(0))
        # Resumen de la cartera
        resumen = {
            # Cantidad de deudores
            "total_deudores": len(saldos),
            # Deuda total
            "deuda_total": total,
            # RF25: el promedio solo considera instructores con deuda mayor a 0
            # Promedio redondeado a 2 decimales (0 si no hay deudores)
            "promedio_deuda": (total / len(saldos)).quantize(Decimal("0.01")) if saldos else Decimal(0),
            # La deuda más alta (0 si la lista está vacía)
            "mayor_deuda": max(saldos, default=Decimal(0)),
        }
        # Devuelve el resumen y la lista
        return {"resumen": resumen, "deudores": deudores}

    # Deuda e historial de pagos de un instructor
    def detalle(self, instructor_id: int) -> dict:
        # Verifica que exista y sea instructor
        self._obtener_instructor(instructor_id)
        # Une la deuda (** copia sus campos) con la lista de pagos
        return {**self._deuda_de(instructor_id), "pagos": self.cartera.pagos_de(instructor_id)}

    # Registra un pago
    def registrar_pago(self, instructor_id: int, datos: PagoCrear, actor: Usuario) -> dict:
        """Proceso de negocio: el Encargado registra un pago (RF23).

        - El pago no puede ser mayor que la deuda.
        - Si salda la deuda, todos los consumos pendientes quedan PAGADOS.
        """
        # Verifica que exista (404) y sea instructor (400)
        self._obtener_instructor(instructor_id)
        self.usuarios.bloquear(instructor_id)  # dos pagos simultáneos no pueden superar la deuda
        # Calcula la deuda actual
        deuda = self._deuda_de(instructor_id)
        # Saldo pendiente
        saldo = deuda["saldo"]
        # Si no debe nada...
        if saldo <= 0:
            # ...responde 400
            raise ReglaNegocioError("El instructor no tiene deuda pendiente.")
        # Si el pago es mayor que la deuda...
        if datos.valor > saldo:
            # ...responde 400 con los valores en pesos
            raise ReglaNegocioError(f"El pago ({pesos(datos.valor)}) no puede ser mayor que la deuda ({pesos(saldo)}).")

        # True si el pago deja la deuda exactamente en cero
        saldar = datos.valor == saldo
        # Crea el pago
        pago = PagoInstructor(
            # Instructor que paga
            instructor_id=instructor_id,
            # Valor
            valor=datos.valor,
            # Método de pago
            metodo=datos.metodo,
            # Observación
            observacion=datos.observacion,
            # Encargado que lo registra
            creado_por=actor.id,
        )
        # Guarda el pago (y si salda, marca los consumos como PAGADO)
        pago = self.cartera.registrar_pago(pago, saldar, actor.id)
        # Devuelve el resultado del pago
        return {
            # El pago guardado
            "pago": pago,
            # Deuda antes
            "saldo_anterior": saldo,
            # Deuda después
            "saldo_actual": saldo - datos.valor,
            # AL_DIA si saldó; si no, el mismo estado que tenía
            "estado": EstadoCuenta.AL_DIA if saldar else deuda["estado"],
        }

    # Cuenta mensual del instructor que consulta
    def mi_cuenta(self, instructor: Usuario) -> dict:
        """Cuenta mensual del instructor: saldo, consumos del mes y próximo corte (RF26)."""
        # Fecha de hoy
        hoy = tiempo.hoy()
        # Deuda del instructor
        deuda = self._deuda_de(instructor.id)
        # El corte es el último día del mes actual
        corte = tiempo.ultimo_dia_del_mes(hoy)
        # Almuerzos y valor consumidos desde el día 1 del mes hasta el corte
        almuerzos, valor = self.reservas.consumo_en_rango(instructor.id, hoy.replace(day=1), corte)
        # Pagos del instructor (el más reciente primero)
        pagos = self.cartera.pagos_de(instructor.id)
        # Devuelve la cuenta mensual
        return {
            # Total consumido
            "total_consumido": deuda["total_consumido"],
            # Total pagado
            "total_pagado": deuda["total_pagado"],
            # Saldo
            "saldo": deuda["saldo"],
            # Estado
            "estado": deuda["estado"],
            # Días vencidos
            "dias_vencidos": deuda["dias_vencidos"],
            # Almuerzos del mes
            "almuerzos_mes": almuerzos,
            # Valor del mes
            "valor_mes": valor,
            # Frecuencia de pago
            "frecuencia_pago": "MENSUAL",
            # Fecha del próximo corte
            "proximo_corte": corte,
            # Método del pago más reciente (None si no hay pagos)
            "ultimo_metodo_pago": pagos[0].metodo if pagos else None,
        }

    # ----- Métodos internos -----

    # Busca un usuario y verifica que sea instructor
    def _obtener_instructor(self, instructor_id: int) -> Usuario:
        # Busca por id
        usuario = self.usuarios.obtener_por_id(instructor_id)
        # Si no existe...
        if usuario is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un usuario con id {instructor_id}.")
        # Si no es instructor...
        if usuario.rol.nombre != Roles.INSTRUCTOR:
            # ...responde 400
            raise ReglaNegocioError("El usuario no es instructor: solo los instructores tienen cuenta mensual.")
        # Devuelve el instructor
        return usuario

    # Calcula la deuda de un instructor
    def _deuda_de(self, instructor_id: int) -> dict:
        # Consulta el resumen de ese instructor ([0] = la única fila) y calcula su deuda
        return self._calcular_deuda(self.cartera.resumen_instructores(instructor_id)[0], tiempo.hoy())

    # Método estático: no usa datos del objeto
    @staticmethod
    # Calcula saldo, días vencidos y estado a partir de una fila del resumen
    def _calcular_deuda(fila: RowMapping, hoy: date) -> dict:
        """Saldo = consumido - pagado (RF26).

        Regla propuesta (RF22): el corte es el último día del mes del consumo y hay
        DIAS_PLAZO_PAGO días para pagar; después la deuda está VENCIDA.
        """
        # Total consumido como Decimal
        total = Decimal(fila["total_consumido"])
        # Total pagado como Decimal
        pagado = Decimal(fila["total_pagado"])
        # Lo que debe
        saldo = total - pagado
        # Por defecto no tiene días vencidos
        dias_vencidos = 0
        # Si debe algo y tiene consumos pendientes...
        if saldo > 0 and fila["pendiente_desde"] is not None:
            # Fecha límite = último día del mes del consumo más antiguo + días de plazo
            limite = tiempo.ultimo_dia_del_mes(fila["pendiente_desde"]) + timedelta(days=settings.DIAS_PLAZO_PAGO)
            # Días vencidos = días desde el límite hasta hoy (nunca negativos)
            dias_vencidos = max(0, (hoy - limite).days)

        # Si no debe nada...
        if saldo <= 0:
            # ...está al día
            estado = EstadoCuenta.AL_DIA
        # Si debe algo...
        else:
            # ...VENCIDA si tiene días vencidos; si no, ACTIVA
            estado = EstadoCuenta.VENCIDA if dias_vencidos > 0 else EstadoCuenta.ACTIVA
        # Devuelve la deuda con la forma de DeudaInstructor
        return {
            # Id
            "instructor_id": fila["instructor_id"],
            # Nombre
            "nombre": fila["nombre"],
            # Documento
            "documento": fila["documento"],
            # Consumido
            "total_consumido": total,
            # Pagado
            "total_pagado": pagado,
            # Saldo
            "saldo": saldo,
            # Pendientes
            "almuerzos_pendientes": fila["almuerzos_pendientes"],
            # Días vencidos
            "dias_vencidos": dias_vencidos,
            # Estado
            "estado": estado,
        }
