# Tablas de roles y usuarios

# Importo los tipos de columnas que voy a usar
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
# relationship sirve para unir una tabla con otra
from sqlalchemy.orm import relationship
# func.now() sirve para poner la fecha y hora actual
from sqlalchemy.sql import func

# base es la clase de la que heredan todos los modelos y auditoria trae las columnas de quién creó o modificó
from app.models.base import base, auditoria


# Tabla de roles (encargado, instructor, aprendiz e invitado)
class modelo_rol(base):
    # Nombre de la tabla en PostgreSQL
    __tablename__ = "roles"

    # Id del rol (llave primaria)
    id = Column(Integer, primary_key=True, index=True)
    # Nombre del rol, no se puede repetir
    nombre = Column(String(20), unique=True, nullable=False)
    # Descripción del rol
    descripcion = Column(String(150))


# Tabla de usuarios
class modelo_usuario(base, auditoria):
    # Nombre de la tabla
    __tablename__ = "usuarios"

    # Id del usuario
    id = Column(Integer, primary_key=True, index=True)
    # Número de documento, no se puede repetir
    documento = Column(String(10), unique=True, nullable=False)
    # Nombre completo
    nombre = Column(String(100), nullable=False)
    # Correo con el que inicia sesión, no se puede repetir
    correo = Column(String(120), unique=True, nullable=False)
    # Teléfono (puede estar vacío)
    telefono = Column(String(10))
    # Contraseña encriptada con bcrypt (nunca se guarda la contraseña normal)
    contrasena = Column(String(100), nullable=False)
    # Id del rol del usuario (llave foránea a la tabla roles)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    # Id de la ficha (solo los aprendices tienen ficha)
    ficha_id = Column(Integer, ForeignKey("fichas.id"))
    # Si es beneficiario el almuerzo le sale gratis
    es_beneficiario = Column(Boolean, default=False)
    # Si está activo puede iniciar sesión
    activo = Column(Boolean, default=True)
    # Cuántas veces seguidas se equivocó en la contraseña
    intentos_fallidos = Column(Integer, default=0)
    # Hasta qué hora está bloqueada la cuenta (vacío si no está bloqueada)
    bloqueado_hasta = Column(DateTime)
    # Fecha en que se creó
    fecha_creacion = Column(DateTime, server_default=func.now())

    # Con esto puedo escribir usuario.rol.nombre
    rol = relationship("modelo_rol")
    # Con esto puedo escribir usuario.ficha.codigo
    ficha = relationship("modelo_ficha")
