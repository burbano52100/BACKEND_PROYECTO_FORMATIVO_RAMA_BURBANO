"""Esquemas de reservas y consumos de almuerzo."""

# Tipos fecha y fecha-hora
from datetime import date, datetime
# Lista cerrada de valores de texto
from enum import StrEnum
# Literal = solo se aceptan los valores escritos (por ejemplo "PAGADO" o "NO_PAGADO")
from typing import Literal

# Herramientas de Pydantic
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Tipos reutilizables
from app.schemas.comunes import Dinero, EsquemaEntrada, PaginacionBase
# Resumen del menú (para mostrarlo dentro de la reserva)
from app.schemas.menu import MenuResumen
# Resumen del usuario (para mostrarlo dentro de la reserva)
from app.schemas.usuario import UsuarioResumen


# Tipos de reserva
class TipoReserva(StrEnum):
    # Aprendiz que paga
    APRENDIZ = "APRENDIZ"
    # Aprendiz beneficiario ($0)
    BENEFICIARIO = "BENEFICIARIO"
    # Instructor (a cuenta mensual)
    INSTRUCTOR = "INSTRUCTOR"
    # Visitante externo
    INVITADO = "INVITADO"


# Estados de una reserva
class EstadoReserva(StrEnum):
    # Reservada, sin pagar todavía
    RESERVADO = "RESERVADO"
    PENDIENTE = "PENDIENTE"  # consumo de instructor que se paga con la cuenta mensual
    # Pagada
    PAGADO = "PAGADO"
    # El encargado marcó que no pagó
    NO_PAGADO = "NO_PAGADO"
    # Cancelada por la persona (el cupo volvió al menú)
    CANCELADA = "CANCELADA"


# Datos para reservar (POST /reservas)
class ReservaCrear(EsquemaEntrada):
    """El precio y el estado los calcula la API según el rol; no se envían."""

    # Único campo permitido: el id del menú (mayor que 0)
    menu_id: int = Field(gt=0)


# Datos para marcar el pago (PATCH /reservas/{id}/pago)
class EstadoPagoEntrada(EsquemaEntrada):
    # Solo se acepta "PAGADO" o "NO_PAGADO"
    estado: Literal["PAGADO", "NO_PAGADO"]


# Cómo se muestra una reserva
class ReservaSalida(BaseModel):
    # Permite crear el esquema desde el modelo Reserva
    model_config = ConfigDict(from_attributes=True)

    # Id de la reserva
    id: int
    # Menú resumido (id, fecha, nombre)
    menu: MenuResumen
    # Usuario resumido (id, nombre, documento)
    usuario: UsuarioResumen
    # Tipo de reserva
    tipo: str
    # Valor cobrado
    valor: Dinero
    # Estado
    estado: str
    # Cuándo se creó
    creado_en: datetime
    # Cuándo se modificó (null si nunca)
    actualizado_en: datetime | None


# Filtros de GET /reservas (más pagina y tamano heredados)
class FiltrosReserva(PaginacionBase):
    # Fecha exacta del menú
    fecha: date | None = Field(None, description="Fecha del menú")
    # Desde esta fecha
    desde: date | None = None
    # Hasta esta fecha
    hasta: date | None = None
    # Filtra por estado
    estado: EstadoReserva | None = None
    # Filtra por tipo
    tipo: TipoReserva | None = None
    # Filtra por persona
    usuario_id: int | None = None
    # Filtra por ficha
    ficha_id: int | None = None

    # Validación que revisa varios campos juntos
    @model_validator(mode="after")
    # Revisa que el rango de fechas tenga sentido
    def validar_rango(self) -> "FiltrosReserva":
        # Si "desde" es posterior a "hasta"...
        if self.desde and self.hasta and self.desde > self.hasta:
            # ...error 422
            raise ValueError("La fecha 'desde' no puede ser posterior a la fecha 'hasta'.")
        # Rango válido
        return self


# Filtros de GET /reservas/mias
class FiltrosMisReservas(PaginacionBase):
    # Filtra por estado
    estado: EstadoReserva | None = None
