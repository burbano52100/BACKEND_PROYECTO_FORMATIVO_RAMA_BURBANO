# Tablas de materiales y movimientos del inventario (kardex)

# Importo los tipos de columnas que voy a usar
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Float, ForeignKey
# relationship sirve para unir una tabla con otra
from sqlalchemy.orm import relationship
# func.now() sirve para poner la fecha y hora actual
from sqlalchemy.sql import func

# base es la clase de la que heredan todos los modelos y auditoria trae las columnas de quién creó o modificó
from app.models.base import base, auditoria


# Tabla de materiales del inventario de la cocina
class modelo_material(base, auditoria):
    # Nombre de la tabla
    __tablename__ = "materiales"

    # Id del material
    id = Column(Integer, primary_key=True, index=True)
    # Código de barras, no se puede repetir
    codigo_barras = Column(String(14), unique=True, nullable=False)
    # Nombre del material
    nombre = Column(String(100), nullable=False)
    # Categoría: PROTEINA, GRANO, VERDURA, FRUTA, LACTEO, ABARROTE o DESECHABLE
    categoria = Column(String(15), nullable=False)
    # Unidad de medida: KG, G, L, ML o UND
    unidad_medida = Column(String(5), nullable=False)
    # Lo que cuesta una unidad
    costo_unitario = Column(Float, nullable=False)
    # Cantidad que hay
    stock = Column(Float, default=0)
    # Cantidad mínima que debería haber
    stock_minimo = Column(Float, default=0)
    # Fecha de vencimiento (puede estar vacía)
    fecha_vencimiento = Column(Date)
    # Si el material está activo o no
    activo = Column(Boolean, default=True)
    # Fecha en que se creó
    fecha_creacion = Column(DateTime, server_default=func.now())


# Tabla de movimientos del inventario (el kardex)
class modelo_movimiento_inventario(base):
    # Nombre de la tabla
    __tablename__ = "movimientos_inventario"

    # Id del movimiento
    id = Column(Integer, primary_key=True, index=True)
    # Id del material que se movió
    material_id = Column(Integer, ForeignKey("materiales.id"), nullable=False)
    # Id del usuario que hizo el movimiento
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # Tipo: ENTRADA, SALIDA o MERMA
    tipo = Column(String(10), nullable=False)
    # Cantidad que entró o salió
    cantidad = Column(Float, nullable=False)
    # Lo que quedó de stock después del movimiento
    saldo = Column(Float, nullable=False)
    # Por qué se hizo el movimiento
    concepto = Column(String(255), nullable=False)
    # Fecha del movimiento
    fecha = Column(DateTime, server_default=func.now())

    # Con esto puedo escribir movimiento.material.nombre
    material = relationship("modelo_material")
    # Con esto puedo escribir movimiento.usuario.nombre
    usuario = relationship("modelo_usuario")
