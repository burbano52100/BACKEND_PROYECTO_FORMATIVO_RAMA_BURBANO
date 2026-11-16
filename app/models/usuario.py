"""Tablas roles y usuarios."""

# Tipo fecha y hora (para bloqueado_hasta)
from datetime import datetime

# Tipos de columna: fecha-hora, llave foránea y texto
from sqlalchemy import DateTime, ForeignKey, String
# Mapped/mapped_column definen columnas; relationship define relaciones entre tablas
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Clase base y columnas de auditoría
from app.models.base import Auditoria, Base
# Modelo Ficha (un aprendiz pertenece a una ficha)
from app.models.ficha import Ficha


# Modelo de la tabla roles (encargado, instructor, aprendiz, invitado)
class Rol(Base):
    # Nombre de la tabla
    __tablename__ = "roles"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Nombre del rol; único
    nombre: Mapped[str] = mapped_column(String(20), unique=True)
    # Descripción del rol (opcional)
    descripcion: Mapped[str | None] = mapped_column(String(150))


# Modelo de la tabla usuarios; hereda las columnas de auditoría
class Usuario(Auditoria, Base):
    # Nombre de la tabla
    __tablename__ = "usuarios"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Número de documento; único
    documento: Mapped[str] = mapped_column(String(10), unique=True)
    # Nombre completo
    nombre: Mapped[str] = mapped_column(String(100))
    # Correo con el que inicia sesión; único
    correo: Mapped[str] = mapped_column(String(120), unique=True)
    # Teléfono (opcional)
    telefono: Mapped[str | None] = mapped_column(String(10))
    # Contraseña cifrada con bcrypt (un hash bcrypt siempre mide 60 caracteres)
    password_hash: Mapped[str] = mapped_column(String(60))
    # Llave foránea al rol del usuario
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    # Llave foránea a la ficha (solo los aprendices tienen ficha)
    ficha_id: Mapped[int | None] = mapped_column(ForeignKey("fichas.id"))
    # True = aprendiz beneficiario (almuerzo a $0)
    es_beneficiario: Mapped[bool] = mapped_column(default=False)
    # False = cuenta desactivada (no puede iniciar sesión)
    activo: Mapped[bool] = mapped_column(default=True)
    # Cantidad de intentos fallidos seguidos de inicio de sesión
    intentos_fallidos: Mapped[int] = mapped_column(default=0)
    # Fecha y hora hasta la que la cuenta está bloqueada (nula si no está bloqueada)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # lazy="joined": al consultar el usuario también trae su rol y su ficha en la misma consulta
    # Permite escribir usuario.rol.nombre
    rol: Mapped[Rol] = relationship(lazy="joined")
    # foreign_keys: entre usuarios y fichas hay varias llaves (la ficha también tiene auditoría)
    # Permite escribir usuario.ficha.codigo (None si no tiene ficha)
    ficha: Mapped[Ficha | None] = relationship(foreign_keys=[ficha_id], lazy="joined")
