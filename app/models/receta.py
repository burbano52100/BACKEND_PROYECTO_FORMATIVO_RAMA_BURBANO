# Tablas de recetas y sus ingredientes

# Importo los tipos de columnas que voy a usar
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
# relationship sirve para unir una tabla con otra
from sqlalchemy.orm import relationship
# func.now() sirve para poner la fecha y hora actual
from sqlalchemy.sql import func

# base es la clase de la que heredan todos los modelos y auditoria trae las columnas de quién creó o modificó
from app.models.base import base, auditoria


# Tabla de recetas (los platos)
class modelo_receta(base, auditoria):
    # Nombre de la tabla
    __tablename__ = "recetas"

    # Id de la receta
    id = Column(Integer, primary_key=True, index=True)
    # Nombre del plato, no se puede repetir
    nombre = Column(String(100), unique=True, nullable=False)
    # Descripción del plato (puede estar vacía)
    descripcion = Column(String(500))
    # Precio al que se vende el plato
    precio_venta = Column(Float, nullable=False)
    # Si la receta está activa o no
    activo = Column(Boolean, default=True)
    # Fecha en que se creó
    fecha_creacion = Column(DateTime, server_default=func.now())


# Tabla de ingredientes de cada receta
class modelo_receta_ingrediente(base):
    # Nombre de la tabla
    __tablename__ = "receta_ingredientes"

    # Id del ingrediente
    id = Column(Integer, primary_key=True, index=True)
    # Id de la receta a la que pertenece
    receta_id = Column(Integer, ForeignKey("recetas.id"), nullable=False)
    # Id del material que se usa
    material_id = Column(Integer, ForeignKey("materiales.id"), nullable=False)
    # Cuánto se usa del material en un plato
    cantidad = Column(Float, nullable=False)

    # Con esto puedo escribir ingrediente.material.costo_unitario
    material = relationship("modelo_material")
