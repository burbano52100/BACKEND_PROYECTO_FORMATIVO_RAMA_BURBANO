# En este archivo leo la configuración que está en el archivo .env

# os sirve para leer las variables de entorno
import os

# load_dotenv lee el archivo .env
from dotenv import load_dotenv

# Cargo las variables que están en el archivo .env
load_dotenv()

# Servidor de la base de datos
bd_servidor = os.getenv("bd_servidor", "localhost")
# Puerto de la base de datos
bd_puerto = os.getenv("bd_puerto", "5432")
# Nombre de la base de datos
bd_nombre = os.getenv("bd_nombre", "gastrosena_db")
# Usuario de la base de datos
bd_usuario = os.getenv("bd_usuario", "api_gastrosena")
# Contraseña de la base de datos
bd_contrasena = os.getenv("bd_contrasena", "")

# Clave secreta con la que se firman los tokens
clave_secreta = os.getenv("clave_secreta_jwt")
# Si no pusieron la clave en el .env no dejo que arranque la API
if clave_secreta is None:
    # Muestro un error para que se den cuenta de lo que falta
    raise Exception("Falta poner clave_secreta_jwt en el archivo .env")

# Algoritmo con el que se firman los tokens
algoritmo = "HS256"
# Minutos que dura el token de acceso (int lo convierte de texto a número)
minutos_token_acceso = int(os.getenv("minutos_token_acceso", "30"))
# Días que dura el token para renovar
dias_token_renovar = int(os.getenv("dias_token_renovar", "7"))

# Páginas web que pueden llamar a la API (split las separa por las comas y queda una lista)
origenes_cors = os.getenv("origenes_cors", "http://localhost:5173").split(",")

# Hora desde la que se puede reservar (7 de la mañana)
hora_apertura = int(os.getenv("hora_apertura", "7"))
# Hora hasta la que se puede reservar (9 de la noche)
hora_cierre = int(os.getenv("hora_cierre", "21"))
