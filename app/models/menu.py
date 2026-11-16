"""Tabla menus (Menú del Día)."""

# date = solo fecha; Decimal = número decimal exacto (para dinero)
from datetime import date
from decimal import Decimal  # Decimal: números exactos para dinero y cantidades

# Numeric = columna decimal exacta; String = texto
from sqlalchemy import Numeric, String
# Herramientas para definir columnas
from sqlalchemy.orm import Mapped, mapped_column

# Clase base y columnas de auditoría
from app.models.base import Auditoria, Base


# Modelo de la tabla menus; hereda las columnas de auditoría
class Menu(Auditoria, Base):
    # Nombre de la tabla
    __tablename__ = "menus"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Fecha del menú; única (un solo menú por día)
    fecha: Mapped[date] = mapped_column(unique=True)
    # Nombre del plato, por ejemplo "Bandeja campesina"
    nombre: Mapped[str] = mapped_column(String(100))
    # Qué incluye el almuerzo
    descripcion: Mapped[str] = mapped_column(String(500))
    # Numeric (Decimal) y no float: el dinero no debe tener errores de redondeo
    # Precio para aprendices e instructores: hasta 10 dígitos con 2 decimales
    precio_aprendiz: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # Precio para invitados
    precio_invitado: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # Cupo total de almuerzos
    cantidad_total: Mapped[int]
    # Cupo que queda (baja con cada reserva y sube al cancelar)
    cantidad_disponible: Mapped[int]
    # False = menú desactivado (no recibe reservas)
    activo: Mapped[bool] = mapped_column(default=True)
