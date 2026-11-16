"""Esquemas de la cartera de deudas y la cuenta mensual de los instructores."""

# Tipos fecha y fecha-hora
from datetime import date, datetime
# StrEnum = lista cerrada de valores de texto
from enum import StrEnum

# Herramientas de Pydantic
from pydantic import BaseModel, ConfigDict, Field

# Tipos reutilizables: dinero de salida, esquema base de entrada y valor monetario de entrada
from app.schemas.comunes import Dinero, EsquemaEntrada, Valor


# Métodos de pago permitidos
class MetodoPago(StrEnum):
    # Pago en efectivo
    EFECTIVO = "EFECTIVO"
    # Pago por transferencia bancaria
    TRANSFERENCIA = "TRANSFERENCIA"
    # Descuento por nómina
    NOMINA = "NOMINA"


# Estado de la cuenta de un instructor
class EstadoCuenta(StrEnum):
    # No debe nada
    AL_DIA = "AL_DIA"
    ACTIVA = "ACTIVA"    # tiene deuda dentro del plazo
    VENCIDA = "VENCIDA"  # tiene consumos de un mes ya cerrado y sin pagar


# Datos que envía el encargado para registrar un pago
class PagoCrear(EsquemaEntrada):
    # Valor mayor que 0
    valor: Valor
    # EFECTIVO, TRANSFERENCIA o NOMINA (otro valor -> 422)
    metodo: MetodoPago
    # Nota opcional de máximo 255 caracteres
    observacion: str | None = Field(None, max_length=255)


# Cómo se muestra un pago en las respuestas
class PagoSalida(BaseModel):
    # from_attributes permite crear este esquema a partir del modelo PagoInstructor
    model_config = ConfigDict(from_attributes=True)

    # Id del pago
    id: int
    # Valor pagado
    valor: Dinero
    # Método de pago
    metodo: str
    # Observación (puede ser null)
    observacion: str | None
    # Fecha y hora del pago
    creado_en: datetime


# Deuda de un instructor (calculada por el servicio)
class DeudaInstructor(BaseModel):
    # Id del instructor
    instructor_id: int
    # Nombre del instructor
    nombre: str
    # Documento del instructor
    documento: str
    # Suma de sus consumos no cancelados
    total_consumido: Dinero
    # Suma de sus pagos
    total_pagado: Dinero
    # Lo que debe: consumido - pagado
    saldo: Dinero
    # Cantidad de almuerzos en estado PENDIENTE
    almuerzos_pendientes: int
    # Días que lleva vencida la deuda (0 si no está vencida)
    dias_vencidos: int
    # AL_DIA, ACTIVA o VENCIDA
    estado: EstadoCuenta


# Resumen de toda la cartera
class ResumenCartera(BaseModel):
    # Cantidad de instructores que deben algo
    total_deudores: int
    # Suma de todas las deudas
    deuda_total: Dinero
    # Promedio de deuda entre los deudores
    promedio_deuda: Dinero
    # La deuda más alta
    mayor_deuda: Dinero


# Respuesta de GET /cartera
class CarteraSalida(BaseModel):
    # Resumen general
    resumen: ResumenCartera
    # Lista de instructores con deuda
    deudores: list[DeudaInstructor]


# Respuesta de GET /cartera/{id}: la deuda (hereda sus campos) más el historial de pagos
class DetalleCartera(DeudaInstructor):
    # Pagos del instructor, del más reciente al más antiguo
    pagos: list[PagoSalida]


# Respuesta de POST /cartera/{id}/pagos
class PagoRegistrado(BaseModel):
    # El pago guardado
    pago: PagoSalida
    # Deuda antes del pago
    saldo_anterior: Dinero
    # Deuda después del pago
    saldo_actual: Dinero
    # Estado de la cuenta después del pago
    estado: EstadoCuenta


# Respuesta de GET /cartera/mi-cuenta
class MiCuenta(BaseModel):
    """Cuenta mensual del instructor (RF26)."""

    # Total consumido histórico
    total_consumido: Dinero
    # Total pagado histórico
    total_pagado: Dinero
    # Lo que debe
    saldo: Dinero
    # AL_DIA, ACTIVA o VENCIDA
    estado: EstadoCuenta
    # Días vencidos
    dias_vencidos: int
    # Almuerzos consumidos en el mes actual
    almuerzos_mes: int
    # Valor consumido en el mes actual
    valor_mes: Dinero
    # Siempre "MENSUAL"
    frecuencia_pago: str = "MENSUAL"
    # Último día del mes actual
    proximo_corte: date
    # Método del último pago (null si nunca ha pagado)
    ultimo_metodo_pago: str | None
