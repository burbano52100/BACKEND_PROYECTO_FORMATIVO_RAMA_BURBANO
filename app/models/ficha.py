# Tabla de fichas (los grupos de los aprendices)

# Importo los tipos de columnas que voy a usar
from sqlalchemy import Column, Integer, String, Boolean, DateTime
# func.now() sirve para poner la fecha y hora actual
from sqlalchemy.sql import func

# base es la clase de la que heredan todos los modelos y auditoria trae las columnas de quién creó o modificó
from app.models.base import base, auditoria


# Tabla de fichas (los grupos de los aprendices)
class modelo_ficha(base, auditoria):
    # Nombre de la tabla
    __tablename__ = "fichas"

    # Id de la ficha
    id = Column(Integer, primary_key=True, index=True)
    # Número de la ficha, no se puede repetir
    codigo = Column(String(10), unique=True, nullable=False)
    # Nombre del programa de formación
    programa = Column(String(120), nullable=False)
    # Jornada: DIURNA, NOCTURNA, MIXTA o FIN_DE_SEMANA
    jornada = Column(String(15), nullable=False)
    # Nombre del vocero del grupo (puede estar vacío)
    vocero = Column(String(100))
    # Cuántos estudiantes tiene la ficha
    cantidad_estudiantes = Column(Integer, default=0)
    # Si la ficha está activa o no
    activo = Column(Boolean, default=True)
    # Fecha en que se creó (la pone PostgreSQL sola)
    fecha_creacion = Column(DateTime, server_default=func.now())
