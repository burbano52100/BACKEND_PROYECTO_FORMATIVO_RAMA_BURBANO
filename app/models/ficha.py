"""Tabla fichas (grupos de formación)."""

# String = columna de texto con longitud máxima (VARCHAR)
from sqlalchemy import String
# Mapped indica el tipo de Python de la columna; mapped_column define la columna
from sqlalchemy.orm import Mapped, mapped_column

# Base (clase padre de los modelos) y Auditoria (columnas creado_por, creado_en, ...)
from app.models.base import Auditoria, Base


# Modelo de la tabla fichas; hereda las columnas de auditoría
class Ficha(Auditoria, Base):
    # Nombre de la tabla en PostgreSQL
    __tablename__ = "fichas"

    # Llave primaria (PostgreSQL genera el número)
    id: Mapped[int] = mapped_column(primary_key=True)
    # Número de ficha, por ejemplo "2847251"; único (no se repite)
    codigo: Mapped[str] = mapped_column(String(10), unique=True)
    # Nombre del programa de formación
    programa: Mapped[str] = mapped_column(String(120))
    # DIURNA, NOCTURNA, MIXTA o FIN_DE_SEMANA
    jornada: Mapped[str] = mapped_column(String(15))
    # Nombre del vocero del grupo (opcional: "| None" significa que puede ser nulo)
    vocero: Mapped[str | None] = mapped_column(String(100))
    # Cantidad de estudiantes del grupo (0 si no se indica)
    cantidad_estudiantes: Mapped[int] = mapped_column(default=0)
    # False = ficha desactivada (borrado lógico)
    activo: Mapped[bool] = mapped_column(default=True)
