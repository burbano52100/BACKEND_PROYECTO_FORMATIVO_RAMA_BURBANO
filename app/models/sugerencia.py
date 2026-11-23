# Tabla de sugerencias (el buzón)

# Importo los tipos de columnas que voy a usar
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
# relationship sirve para unir una tabla con otra
from sqlalchemy.orm import relationship
# func.now() sirve para poner la fecha y hora actual
from sqlalchemy.sql import func

# base es la clase de la que heredan todos los modelos y auditoria trae las columnas de quién creó o modificó
from app.models.base import base, auditoria


# Tabla de sugerencias (el buzón)
class modelo_sugerencia(base, auditoria):
    # Nombre de la tabla
    __tablename__ = "sugerencias"

    # Id de la sugerencia
    id = Column(Integer, primary_key=True, index=True)
    # Id del usuario que la mandó
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # Tema de la sugerencia
    asunto = Column(String(100), nullable=False)
    # Lo que escribió el usuario
    mensaje = Column(String(500), nullable=False)
    # Estado: PENDIENTE o ATENDIDA
    estado = Column(String(10), default="PENDIENTE")
    # Respuesta del encargado (puede estar vacía)
    respuesta = Column(String(500))
    # Fecha en que se mandó
    fecha_creacion = Column(DateTime, server_default=func.now())
    # Fecha en que el encargado la atendió
    fecha_respuesta = Column(DateTime)

    # Con esto puedo escribir sugerencia.usuario.nombre
    usuario = relationship("modelo_usuario")
