"""Tabla sugerencias (buzón)."""

# Tipo fecha y hora
from datetime import datetime

# Tipos de columna y func (funciones SQL)
from sqlalchemy import DateTime, ForeignKey, String, func
# Herramientas para definir columnas y relaciones
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Clase base de los modelos
from app.models.base import Base
# Modelo Usuario (autor de la sugerencia)
from app.models.usuario import Usuario


# Modelo de la tabla sugerencias
class Sugerencia(Base):
    # Nombre de la tabla
    __tablename__ = "sugerencias"

    # Llave primaria
    id: Mapped[int] = mapped_column(primary_key=True)
    # Quién envió la sugerencia (llave foránea)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    # Tema de la sugerencia
    asunto: Mapped[str] = mapped_column(String(100))
    # Texto de la sugerencia
    mensaje: Mapped[str] = mapped_column(String(500))
    # PENDIENTE (por defecto) o ATENDIDA
    estado: Mapped[str] = mapped_column(String(10), default="PENDIENTE")
    # Respuesta del encargado (opcional)
    respuesta: Mapped[str | None] = mapped_column(String(500))
    # Encargado que la atendió
    atendida_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    # Cuándo se atendió
    atendida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Cuándo se envió
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Permite escribir sugerencia.usuario.nombre
    usuario: Mapped[Usuario] = relationship(foreign_keys=[usuario_id], lazy="joined")
