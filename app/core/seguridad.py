# En este archivo está lo de seguridad: las contraseñas y los tokens

# datetime es la fecha y hora, timedelta sirve para sumar tiempo y timezone para la zona horaria
from datetime import datetime, timedelta, timezone

# bcrypt sirve para encriptar las contraseñas
import bcrypt
# jwt sirve para crear y leer los tokens
import jwt

# Traigo la configuración de los tokens
from app.core.config import clave_secreta, algoritmo, minutos_token_acceso, dias_token_renovar
# Traigo la función para responder el error 401
from app.core.excepciones import error_no_autenticado


# Función para encriptar una contraseña
def encriptar_contrasena(contrasena):
    # bcrypt trabaja con bytes, por eso convierto el texto con encode
    contrasena_bytes = contrasena.encode("utf-8")
    # gensalt crea una "sal" aleatoria para que cada hash sea diferente
    sal = bcrypt.gensalt()
    # hashpw encripta la contraseña con la sal
    encriptada_bytes = bcrypt.hashpw(contrasena_bytes, sal)
    # Lo vuelvo a texto para guardarlo en la base de datos
    return encriptada_bytes.decode("utf-8")


# Función para revisar si una contraseña es igual a la que está encriptada
def verificar_contrasena(contrasena, contrasena_encriptada):
    # Uso try por si bcrypt da algún error
    try:
        # checkpw compara la contraseña escrita con la encriptada y devuelve True o False
        return bcrypt.checkpw(contrasena.encode("utf-8"), contrasena_encriptada.encode("utf-8"))
    # Si hay error (por ejemplo una contraseña muy larga)
    except ValueError:
        # Digo que no coincide
        return False


# Función para revisar que la contraseña sea segura (mayúscula, minúscula y número)
def contrasena_es_segura(contrasena):
    # Al principio digo que no tiene nada
    tiene_mayuscula = False
    # No tiene minúscula todavía
    tiene_minuscula = False
    # No tiene número todavía
    tiene_numero = False
    # Reviso letra por letra
    for letra in contrasena:
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
    if len(contrasena) >= 8 and tiene_mayuscula and tiene_minuscula and tiene_numero:
        # Devuelvo que sí es segura
        return True
    # Si falta algo devuelvo que no es segura
    return False


# Función para crear un token (tipo puede ser "acceso" o "renovar")
def crear_token(usuario_id, tipo):
    # Si es el token de acceso
    if tipo == "acceso":
        # Se vence en los minutos que dice el .env
        vence = datetime.now(timezone.utc) + timedelta(minutes=minutos_token_acceso)
    # Si es el token para renovar
    else:
        # Se vence en los días que dice el .env
        vence = datetime.now(timezone.utc) + timedelta(days=dias_token_renovar)
    # Datos que van dentro del token
    datos = {
        "usuario_id": str(usuario_id),  # Id del usuario (lo guardo como texto)
        "tipo": tipo,  # Si es acceso o renovar
        "exp": vence,  # Cuándo se vence
    }
    # Creo el token firmado con la clave secreta
    token = jwt.encode(datos, clave_secreta, algorithm=algoritmo)
    # Devuelvo el token
    return token


# Función para leer un token y sacar el id del usuario
def leer_token(token, tipo_esperado):
    # Uso try porque si el token está malo jwt.decode da error
    try:
        # Leo el token con la clave secreta (también revisa que no esté vencido)
        datos = jwt.decode(token, clave_secreta, algorithms=[algoritmo])
    # Si el token ya se venció
    except jwt.ExpiredSignatureError:
        # Respondo 401
        error_no_autenticado("El token ya se venció, inicie sesión otra vez")
    # Si el token es falso o está mal escrito
    except jwt.InvalidTokenError:
        # Respondo 401
        error_no_autenticado("El token no es válido")
    # Reviso que sea el tipo de token correcto (el de renovar no sirve como el de acceso)
    if datos.get("tipo") != tipo_esperado:
        # Respondo 401
        error_no_autenticado("El token no es válido")
    # Devuelvo el id del usuario convertido a número
    return int(datos["usuario_id"])
