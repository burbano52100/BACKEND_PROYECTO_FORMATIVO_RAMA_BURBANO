# En este archivo está todo lo de seguridad: contraseñas, tokens y permisos

# datetime es la fecha y hora, timedelta sirve para sumar tiempo y timezone para la zona horaria
from datetime import datetime, timedelta, timezone

# bcrypt sirve para encriptar las contraseñas
import bcrypt
# jwt sirve para crear y leer los tokens
import jwt
# Depends sirve para usar dependencias y HTTPException para responder errores
from fastapi import Depends, HTTPException
# HTTPBearer lee el token que viene en el encabezado "Authorization: Bearer token"
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Traigo la configuración de los tokens
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
# Traigo la función que da la sesión de la base de datos
from app.database import get_db
# Traigo el modelo de usuario
from app.models import Usuario

# Con esto sale el botón "Authorize" en /docs para pegar el token
seguridad = HTTPBearer()


# Función para encriptar una contraseña
def encriptar_password(password):
    # bcrypt trabaja con bytes, por eso convierto el texto con encode
    password_bytes = password.encode("utf-8")
    # gensalt crea una "sal" aleatoria para que cada hash sea diferente
    sal = bcrypt.gensalt()
    # hashpw encripta la contraseña con la sal
    hash_bytes = bcrypt.hashpw(password_bytes, sal)
    # Lo vuelvo a texto para guardarlo en la base de datos
    return hash_bytes.decode("utf-8")


# Función para revisar si una contraseña es igual a la que está encriptada
def verificar_password(password, password_encriptada):
    # Uso try por si bcrypt da algún error
    try:
        # checkpw compara la contraseña escrita con la encriptada y devuelve True o False
        return bcrypt.checkpw(password.encode("utf-8"), password_encriptada.encode("utf-8"))
    # Si hay error (por ejemplo una contraseña muy larga)
    except ValueError:
        # Digo que no coincide
        return False


# Función para revisar que la contraseña sea segura (mayúscula, minúscula y número)
def password_es_segura(password):
    # Al principio digo que no tiene nada
    tiene_mayuscula = False
    # No tiene minúscula todavía
    tiene_minuscula = False
    # No tiene número todavía
    tiene_numero = False
    # Reviso letra por letra
    for letra in password:
        # Si la letra es mayúscula
        if letra.isupper():
            # Marco que sí tiene mayúscula
            tiene_mayuscula = True
        # Si la letra es minúscula
        if letra.islower():
            # Marco que sí tiene minúscula
            tiene_minuscula = True
        # Si es un número
        if letra.isdigit():
            # Marco que sí tiene número
            tiene_numero = True
    # Es segura si tiene 8 o más caracteres y tiene las tres cosas
    if len(password) >= 8 and tiene_mayuscula and tiene_minuscula and tiene_numero:
        # Devuelvo que sí es segura
        return True
    # Si falta algo devuelvo que no es segura
    return False


# Función para crear un token (tipo puede ser "access" o "refresh")
def crear_token(usuario_id, tipo):
    # Si es el token de acceso
    if tipo == "access":
        # Se vence en los minutos que dice el .env
        vence = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Si es el refresh token
    else:
        # Se vence en los días que dice el .env
        vence = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    # Datos que van dentro del token
    datos = {
        "sub": str(usuario_id),  # Id del usuario (tiene que ser texto)
        "tipo": tipo,  # Si es access o refresh
        "exp": vence,  # Cuándo se vence
    }
    # Creo el token firmado con la clave secreta
    token = jwt.encode(datos, SECRET_KEY, algorithm=ALGORITHM)
    # Devuelvo el token
    return token


# Función para leer un token y sacar el id del usuario
def leer_token(token, tipo_esperado):
    # Uso try porque si el token está malo jwt.decode da error
    try:
        # Leo el token con la clave secreta (también revisa que no esté vencido)
        datos = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # Si el token ya se venció
    except jwt.ExpiredSignatureError:
        # Respondo 401
        raise HTTPException(status_code=401, detail="El token ya se venció, inicie sesión otra vez")
    # Si el token es falso o está mal escrito
    except jwt.InvalidTokenError:
        # Respondo 401
        raise HTTPException(status_code=401, detail="El token no es válido")
    # Reviso que sea el tipo de token correcto (un refresh no sirve como access)
    if datos.get("tipo") != tipo_esperado:
        # Respondo 401
        raise HTTPException(status_code=401, detail="El token no es válido")
    # Devuelvo el id del usuario convertido a número
    return int(datos["sub"])


# Esta función se usa en las rutas para saber quién está haciendo la petición
def obtener_usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(seguridad), db: Session = Depends(get_db)):
    # Saco el token del encabezado
    token = credenciales.credentials
    # Leo el token y saco el id del usuario
    usuario_id = leer_token(token, "access")
    # Busco el usuario en la base de datos
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    # Si no existe el usuario
    if usuario is None:
        # Respondo 401
        raise HTTPException(status_code=401, detail="El usuario del token no existe")
    # Si el usuario está desactivado
    if usuario.activo == False:
        # Respondo 401
        raise HTTPException(status_code=401, detail="La cuenta está inactiva")
    # Devuelvo el usuario
    return usuario


# Función para revisar si el usuario tiene uno de los roles que se permiten
def verificar_rol(usuario, roles_permitidos):
    # Si el nombre del rol no está en la lista de roles permitidos
    if usuario.rol.nombre not in roles_permitidos:
        # Respondo 403 (no tiene permiso)
        raise HTTPException(status_code=403, detail="No tiene permiso para hacer esto")
