"""Clase base de los modelos y columnas de auditoría."""

# Tipo fecha y hora, para las columnas creado_en y actualizado_en
from datetime import datetime

# DateTime = tipo de columna fecha-hora; ForeignKey = llave foránea;
# MetaData = catálogo de tablas; func = funciones SQL como now()
from sqlalchemy import DateTime, ForeignKey, MetaData, func
# DeclarativeBase = clase base de los modelos; Mapped y mapped_column definen columnas
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Configuración (de aquí sale el nombre del esquema: gastrosena)
from app.core.config import settings


# Clase padre de todos los modelos (cada modelo = una tabla)
class Base(DeclarativeBase):
    """Todas las tablas viven en el esquema del proyecto, no en public."""

    # Indica que todas las tablas están en el esquema del .env (DB_SCHEMA = gastrosena)
    metadata = MetaData(schema=settings.DB_SCHEMA)


# Clase "mixin": no es una tabla, solo agrega 4 columnas a las tablas que la heredan
class Auditoria:
    """Columnas que registran quién creó o modificó el registro y cuándo."""

    # Id del usuario que creó el registro (llave foránea a usuarios; puede ser nulo)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    # Fecha y hora de creación; server_default=now() hace que PostgreSQL la llene solo
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Id del usuario que modificó el registro por última vez
    actualizado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    # onupdate: SQLAlchemy pone la fecha actual cada vez que se actualiza la fila
    # Fecha y hora de la última modificación (nula si nunca se modificó)
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
