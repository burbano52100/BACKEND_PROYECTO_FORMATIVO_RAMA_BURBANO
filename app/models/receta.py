"""Tablas recetas y receta_ingredientes."""

# Decimal = número decimal exacto
from decimal import Decimal

# Tipos de columna
from sqlalchemy import ForeignKey, Numeric, String
# Herramientas para definir columnas y relaciones
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Clase base y columnas de auditoría
from app.models.base import Auditoria, Base
# Modelo Material (cada ingrediente es un material del inventario)
from app.models.inventario import Material


# Modelo de la tabla receta_ingredientes (la fórmula: qué material y cuánto lleva cada plato)
class RecetaIngrediente(Base):
    # Nombre de la tabla
    __tablename__ = "receta_ingredientes"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Receta a la que pertenece; ondelete="CASCADE": si se borra la receta, se borra esta fila
    receta_id: Mapped[int] = mapped_column(ForeignKey("recetas.id", ondelete="CASCADE"))
    # Material usado como ingrediente
    material_id: Mapped[int] = mapped_column(ForeignKey("materiales.id"))
    # Cantidad por plato, en la unidad del material
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 3))

    # Permite escribir ingrediente.material.costo_unitario
    material: Mapped[Material] = relationship(lazy="joined")


# Modelo de la tabla recetas; hereda las columnas de auditoría
class Receta(Auditoria, Base):
    # Nombre de la tabla
    __tablename__ = "recetas"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Nombre del plato; único
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    # Descripción del plato (opcional)
    descripcion: Mapped[str | None] = mapped_column(String(500))
    # Precio al que se vende el plato
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # False = receta inactiva
    activo: Mapped[bool] = mapped_column(default=True)

    # delete-orphan: al quitar un ingrediente de la lista se borra de la tabla
    # Lista de ingredientes; selectin los carga en una segunda consulta y order_by los ordena por id
    ingredientes: Mapped[list[RecetaIngrediente]] = relationship(
        # cascade: guardar/borrar la receta también guarda/borra sus ingredientes
        cascade="all, delete-orphan", lazy="selectin", order_by=RecetaIngrediente.id
    )
