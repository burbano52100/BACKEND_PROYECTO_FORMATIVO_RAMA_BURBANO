# En este archivo hago la conexión con la base de datos PostgreSQL

# create_engine sirve para crear la conexión
from sqlalchemy import create_engine
# sessionmaker crea las sesiones y declarative_base sirve para hacer los modelos (tablas)
from sqlalchemy.orm import sessionmaker, declarative_base

# Traigo los datos de conexión que están en config.py
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Armo la dirección de la base de datos así: postgresql+psycopg://usuario:clave@servidor:puerto/nombre_base
URL_BASE_DATOS = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Creo el motor que se conecta a PostgreSQL
# Con options=-csearch_path=gastrosena le digo que busque las tablas en el esquema gastrosena
engine = create_engine(URL_BASE_DATOS, connect_args={"options": "-csearch_path=gastrosena"})

# Creo la fábrica de sesiones (una sesión es como una conversación con la base de datos)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Esta es la clase base de la que heredan todos los modelos
Base = declarative_base()


# Esta función abre una sesión en cada petición y la cierra cuando termina
def get_db():
    # Abro una sesión nueva
    db = SessionLocal()
    # Uso try y finally para que la sesión siempre se cierre aunque haya un error
    try:
        # Le entrego la sesión a la ruta que la pidió
        yield db
    # Esto se ejecuta siempre al final
    finally:
        # Cierro la sesión
        db.close()
