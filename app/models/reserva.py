"""Tablas reservas (consumos de almuerzo) y pagos_instructor (cartera)."""

# Tipos fecha-hora y decimal exacto
from datetime import datetime
from decimal import Decimal  # Decimal: números exactos para dinero y cantidades

# Tipos de columna y func (funciones SQL como now())
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
# Herramientas para definir columnas y relaciones
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Clase base de los modelos
from app.models.base import Base
# Modelo Menu (cada reserva es de un menú)
from app.models.menu import Menu
# Modelo Usuario (cada reserva es de una persona)
from app.models.usuario import Usuario


# Modelo de la tabla reservas (reservas, compras y consumos)
class Reserva(Base):
    # Nombre de la tabla
    __tablename__ = "reservas"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Menú reservado (llave foránea)
    menu_id: Mapped[int] = mapped_column(ForeignKey("menus.id"))
    # Persona que reservó (llave foránea)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    # APRENDIZ, BENEFICIARIO, INSTRUCTOR o INVITADO
    tipo: Mapped[str] = mapped_column(String(15))
    # Valor cobrado (lo calcula la API según el rol)
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # RESERVADO, PENDIENTE, PAGADO, NO_PAGADO o CANCELADA
    estado: Mapped[str] = mapped_column(String(10))
    # Auditoría: quién reservó y quién marcó el pago (RF42)
    # Quién creó la reserva
    creado_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    # Cuándo se creó (PostgreSQL pone la fecha con now())
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Quién la modificó por última vez (por ejemplo, el encargado al marcar el pago)
    actualizado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    # Cuándo se modificó por última vez
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    # Permite escribir reserva.menu.fecha; lazy="joined" lo trae en la misma consulta
    menu: Mapped[Menu] = relationship(lazy="joined")
    # Permite escribir reserva.usuario.nombre; se indica la llave porque hay varias hacia usuarios
    usuario: Mapped[Usuario] = relationship(foreign_keys=[usuario_id], lazy="joined")


# Modelo de la tabla pagos_instructor
class PagoInstructor(Base):
    """Pagos a la cuenta mensual de un instructor: no se editan ni se borran."""

    # Nombre de la tabla
    __tablename__ = "pagos_instructor"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Instructor que paga (llave foránea a usuarios)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    # Valor pagado: hasta 12 dígitos con 2 decimales
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # EFECTIVO, TRANSFERENCIA o NOMINA
    metodo: Mapped[str] = mapped_column(String(15))
    # Nota opcional del pago
    observacion: Mapped[str | None] = mapped_column(String(255))
    # Encargado que registró el pago
    creado_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    # Fecha y hora del pago
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
