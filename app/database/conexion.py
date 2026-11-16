"""Conexión a PostgreSQL con SQLAlchemy y psycopg 3."""

# Generator es el tipo de una función que usa "yield" (entrega un valor y luego continúa)
from collections.abc import Generator
# Annotated permite asociar la dependencia de FastAPI al tipo Session
from typing import Annotated

# Depends: FastAPI ejecuta get_db en cada petición y entrega la sesión
from fastapi import Depends
# URL arma la dirección de conexión; create_engine crea el motor que habla con PostgreSQL
from sqlalchemy import URL, create_engine
# Session = conversación con la base de datos; sessionmaker = fábrica de sesiones
from sqlalchemy.orm import Session, sessionmaker

# Configuración leída del .env (host, puerto, usuario, contraseña...)
from app.core.config import settings

# URL.create escapa los caracteres especiales de la contraseña (@, #, /, ...)
# Arma la URL de conexión: postgresql+psycopg://usuario:clave@host:puerto/base
url = URL.create(
    # Motor PostgreSQL usando el driver psycopg 3
    "postgresql+psycopg",
    # Usuario de la base de datos (api_gastrosena)
    username=settings.DB_USER,
    # Contraseña del usuario
    password=settings.DB_PASSWORD,
    # Servidor de PostgreSQL
    host=settings.DB_HOST,
    # Puerto de PostgreSQL
    port=settings.DB_PORT,
    # Nombre de la base de datos
    database=settings.DB_NAME,
)

# pool_pre_ping comprueba que la conexión siga viva antes de usarla
# El engine mantiene un grupo (pool) de conexiones abiertas para reutilizarlas
engine = create_engine(url, pool_pre_ping=True)

# expire_on_commit=False: los objetos conservan sus datos después del commit
# autoflush=False: los cambios se envían a la base de datos solo cuando se pide (commit o flush)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# Dependencia que entrega una sesión de base de datos a cada petición
def get_db() -> Generator[Session, None, None]:
    """Abre una sesión por cada petición y la cierra al terminar.

    Al cerrarse se deshace cualquier cambio que no se haya confirmado (commit).
    """
    # Abre una sesión nueva
    db = SessionLocal()
    # try/finally garantiza que la sesión se cierre aunque ocurra un error
    try:
        # Entrega la sesión al endpoint; la función se "pausa" aquí hasta que termine la petición
        yield db
    # Se ejecuta siempre al final de la petición
    finally:
        # Cierra la sesión y devuelve la conexión al pool
        db.close()


# Atajo: un parámetro "db: SesionDB" recibe automáticamente una sesión de base de datos
SesionDB = Annotated[Session, Depends(get_db)]
