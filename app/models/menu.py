# Tabla de menús (el menú de cada día)

# Importo los tipos de columnas que voy a usar
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Float
# func.now() sirve para poner la fecha y hora actual
from sqlalchemy.sql import func

# base es la clase de la que heredan todos los modelos y auditoria trae las columnas de quién creó o modificó
from app.models.base import base, auditoria


# Tabla de menús (el menú de cada día)
class modelo_menu(base, auditoria):
    # Nombre de la tabla
    __tablename__ = "menus"

    # Id del menú
    id = Column(Integer, primary_key=True, index=True)
    # Fecha del menú, solo puede haber un menú por día
    fecha = Column(Date, unique=True, nullable=False)
    # Nombre del plato
    nombre = Column(String(100), nullable=False)
    # Lo que trae el almuerzo
    descripcion = Column(String(500), nullable=False)
    # Precio para aprendices e instructores
    precio_aprendiz = Column(Float, nullable=False)
    # Precio para invitados
    precio_invitado = Column(Float, nullable=False)
    # Cuántos almuerzos se van a hacer en total
    cantidad_total = Column(Integer, nullable=False)
    # Cuántos almuerzos quedan
    cantidad_disponible = Column(Integer, nullable=False)
    # Si el menú está activo o no
    activo = Column(Boolean, default=True)
    # Fecha en que se creó
    fecha_creacion = Column(DateTime, server_default=func.now())
