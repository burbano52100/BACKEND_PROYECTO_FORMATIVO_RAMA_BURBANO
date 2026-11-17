# En este archivo leo la configuración que está en el archivo .env

# os sirve para leer las variables de entorno
import os

# load_dotenv lee el archivo .env
from dotenv import load_dotenv

# Cargo las variables que están en el archivo .env
load_dotenv()

# Servidor de la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
# Puerto de la base de datos
DB_PORT = os.getenv("DB_PORT", "5432")
# Nombre de la base de datos
DB_NAME = os.getenv("DB_NAME", "gastrosena_db")
# Usuario de la base de datos
DB_USER = os.getenv("DB_USER", "api_gastrosena")
# Contraseña de la base de datos
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Clave secreta con la que se firman los tokens
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
# Si no pusieron la clave en el .env no dejo que arranque la API
if SECRET_KEY is None:
    # Muestro un error para que se den cuenta de lo que falta
    raise Exception("Falta poner JWT_SECRET_KEY en el archivo .env")

# Algoritmo con el que se firman los tokens
ALGORITHM = "HS256"
# Minutos que dura el token de acceso (int lo convierte de texto a número)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
# Días que dura el refresh token
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Páginas web que pueden llamar a la API (split las separa por las comas y queda una lista)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# Hora desde la que se puede reservar (7 de la mañana)
HORA_APERTURA = int(os.getenv("HORA_APERTURA", "7"))
# Hora hasta la que se puede reservar (9 de la noche)
HORA_CIERRE = int(os.getenv("HORA_CIERRE", "21"))
