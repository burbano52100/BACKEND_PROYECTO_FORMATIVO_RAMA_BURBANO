"""Tablas materiales y movimientos_inventario (kardex)."""

# Tipos fecha, fecha-hora y decimal exacto
from datetime import date, datetime
from decimal import Decimal  # Decimal: números exactos para dinero y cantidades

# Tipos de columna y func (funciones SQL)
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
# Herramientas para definir columnas y relaciones
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Clase base y columnas de auditoría
from app.models.base import Auditoria, Base
# Modelo Usuario (responsable de cada movimiento)
from app.models.usuario import Usuario


# Modelo de la tabla materiales; hereda las columnas de auditoría
class Material(Auditoria, Base):
    # Nombre de la tabla
    __tablename__ = "materiales"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Código de barras del producto; único
    codigo_barras: Mapped[str] = mapped_column(String(14), unique=True)
    # Nombre del material, por ejemplo "Arroz blanco"
    nombre: Mapped[str] = mapped_column(String(100))
    # PROTEINA, GRANO, VERDURA, FRUTA, LACTEO, ABARROTE o DESECHABLE
    categoria: Mapped[str] = mapped_column(String(15))
    # KG, G, L, ML o UND
    unidad_medida: Mapped[str] = mapped_column(String(5))
    # Costo de una unidad de medida (por ejemplo, el kilo)
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # Cantidad disponible (hasta 3 decimales, por ejemplo 0.150 KG); solo cambia con movimientos
    stock: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    # Cantidad mínima; por debajo, el estado pasa a BAJO o CRÍTICO
    stock_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    # Fecha de vencimiento (opcional); el tipo sale de la anotación "date | None"
    fecha_vencimiento: Mapped[date | None]
    # False = material desactivado (borrado lógico)
    activo: Mapped[bool] = mapped_column(default=True)


# Modelo de la tabla movimientos_inventario (sin auditoría de actualización: no se edita)
class MovimientoInventario(Base):
    """Fila del kardex: guarda el saldo que quedó después del movimiento."""

    # Nombre de la tabla
    __tablename__ = "movimientos_inventario"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Material afectado (llave foránea)
    material_id: Mapped[int] = mapped_column(ForeignKey("materiales.id"))
    # ENTRADA, SALIDA o MERMA
    tipo: Mapped[str] = mapped_column(String(10))
    # Cantidad que entra o sale
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    # Stock que quedó después del movimiento
    saldo: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    # Motivo del movimiento (en una merma, la razón)
    concepto: Mapped[str] = mapped_column(String(255))
    # Usuario que registró el movimiento
    creado_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    # Fecha y hora del movimiento
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Permite escribir movimiento.material.nombre
    material: Mapped[Material] = relationship(lazy="joined")
    # Permite escribir movimiento.responsable.nombre (el usuario de creado_por)
    responsable: Mapped[Usuario] = relationship(foreign_keys=[creado_por], lazy="joined")
