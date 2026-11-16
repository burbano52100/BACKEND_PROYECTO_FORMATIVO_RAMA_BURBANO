"""Cifrado de contraseñas con bcrypt y generación/validación de tokens JWT."""

# Tipos para manejar la hora actual (en UTC) y duraciones
from datetime import datetime, timedelta, timezone

# Librería que cifra contraseñas con el algoritmo bcrypt
import bcrypt
# Librería PyJWT: crea y lee tokens JWT
import jwt

# Configuración leída del .env (clave secreta, algoritmo y duraciones)
from app.core.config import settings
# Error 401 que se lanza cuando el token no sirve
from app.core.excepciones import NoAutenticadoError

# Valor del campo "tipo" de un token de acceso
TOKEN_ACCESO = "access"
# Valor del campo "tipo" de un token de actualización
TOKEN_ACTUALIZACION = "refresh"

# RNF14 de la especificación: bcrypt con 10 rondas
# Más rondas = más seguro pero más lento; 10 es un buen equilibrio
RONDAS_BCRYPT = 10


# Recibe la contraseña escrita por el usuario y devuelve su versión cifrada
def cifrar_password(password: str) -> str:
    """Devuelve el hash bcrypt de la contraseña. La sal aleatoria queda dentro del hash."""
    # encode convierte el texto a bytes; gensalt crea una sal aleatoria; decode vuelve el hash a texto
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=RONDAS_BCRYPT)).decode("utf-8")


# Comprueba si una contraseña escrita corresponde al hash guardado
def verificar_password(password: str, password_hash: str) -> bool:
    """Compara la contraseña escrita con el hash guardado en la base de datos."""
    # Intenta la comparación; si bcrypt lanza un error, se atrapa en el except
    try:
        # checkpw cifra la contraseña con la misma sal del hash y compara; devuelve True o False
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    # ValueError ocurre, por ejemplo, con contraseñas de más de 72 bytes
    except ValueError:
        # bcrypt rechaza contraseñas de más de 72 bytes
        # En ese caso la contraseña se considera incorrecta
        return False


# Función interna (empieza con "_") que arma y firma un token JWT
def _crear_token(usuario_id: int, tipo: str, duracion: timedelta) -> str:
    # Momento actual en UTC (el estándar JWT usa UTC)
    ahora = datetime.now(timezone.utc)
    # payload = datos que viajan dentro del token
    payload = {
        # "sub" (subject) = id del usuario dueño del token
        "sub": str(usuario_id),  # el estándar JWT exige que "sub" sea texto
        # Tipo del token: "access" o "refresh"
        "tipo": tipo,
        # "iat" (issued at) = cuándo se creó el token
        "iat": ahora,
        # "exp" (expiration) = cuándo vence el token
        "exp": ahora + duracion,
    }
    # Firma el payload con la clave secreta; sin esa clave nadie puede falsificar el token
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# Crea el token de acceso; "duracion" es opcional (las pruebas la usan para crear un token vencido)
def crear_access_token(usuario_id: int, duracion: timedelta | None = None) -> str:
    """Token corto que se envía en cada petición (Authorization: Bearer ...)."""
    # Si no se envía duración, usa los minutos del .env (30 por defecto)
    duracion = duracion or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Crea el token con tipo "access"
    return _crear_token(usuario_id, TOKEN_ACCESO, duracion)


# Crea el token de actualización
def crear_refresh_token(usuario_id: int) -> str:
    """Token largo que solo sirve para pedir un nuevo access token."""
    # Crea el token con tipo "refresh" y la duración en días del .env (7 por defecto)
    return _crear_token(usuario_id, TOKEN_ACTUALIZACION, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


# Lee un token, lo valida y devuelve el id del usuario
def decodificar_token(token: str, tipo_esperado: str) -> int:
    """Valida la firma, la expiración y el tipo del token. Devuelve el id del usuario."""
    # Intenta leer el token; si algo falla se atrapa en los except
    try:
        # decode verifica la firma con la clave secreta y que el token no esté vencido
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    # El token tenía una firma válida pero ya venció
    except jwt.ExpiredSignatureError:
        # "from None" oculta el error técnico original; el usuario solo ve el mensaje en español
        raise NoAutenticadoError("El token ha expirado. Inicie sesión de nuevo o renueve el token.") from None
    # Cualquier otro problema: firma falsa, texto que no es un JWT, etc.
    except jwt.InvalidTokenError:
        # Responde 401 con un mensaje genérico
        raise NoAutenticadoError("El token no es válido.") from None

    # Un token "refresh" no sirve donde se espera uno "access" (y al revés)
    if payload.get("tipo") != tipo_esperado:
        # Responde 401
        raise NoAutenticadoError("El token no es válido para esta operación.")
    # Devuelve el id del usuario convertido de texto a número
    return int(payload["sub"])
