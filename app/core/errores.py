"""Manejo de errores: todas las respuestas de error tienen la misma estructura.

    {"estado": 404, "mensaje": "No existe un menú con id 99.", "detalles": null}
"""

# logging escribe mensajes en la consola del servidor (el log)
import logging

# FastAPI (la aplicación) y Request (datos de la petición que causó el error)
from fastapi import FastAPI, Request
# Error que lanza FastAPI cuando los datos enviados no cumplen el esquema (422)
from fastapi.exceptions import RequestValidationError
# Permite construir una respuesta JSON con el código de estado que queramos
from fastapi.responses import JSONResponse
# Error de PostgreSQL cuando se viola una restricción (UNIQUE, llave foránea, CHECK)
from sqlalchemy.exc import IntegrityError
# Errores HTTP de Starlette (la base de FastAPI), por ejemplo "ruta no existe" (404)
from starlette.exceptions import HTTPException as StarletteHTTPException

# Importa las excepciones propias de la aplicación
from app.core.excepciones import (
    # 409
    ConflictoError,
    # Clase padre de todas
    ErrorAplicacion,
    # 401
    NoAutenticadoError,
    # 404
    NoEncontradoError,
    # 403
    PermisoDenegadoError,
    # 400
    ReglaNegocioError,
)
# Esquema con la forma única de las respuestas de error
from app.schemas.comunes import ErrorRespuesta

# Crea un "logger" llamado "api" para escribir en el log
logger = logging.getLogger("api")

# Traducción de cada excepción de negocio a su código HTTP
CODIGOS_HTTP = {
    # Regla de negocio incumplida -> 400 Bad Request
    ReglaNegocioError: 400,
    # Sin token o token inválido -> 401 Unauthorized
    NoAutenticadoError: 401,
    # Rol sin permiso -> 403 Forbidden
    PermisoDenegadoError: 403,
    # No existe -> 404 Not Found
    NoEncontradoError: 404,
    # Valor repetido -> 409 Conflict
    ConflictoError: 409,
}

# Mensajes en español para los errores de validación más comunes de Pydantic
# La llave es el "tipo" de error de Pydantic; {min_length}, {ge}, etc. se reemplazan por el valor real
MENSAJES_VALIDACION = {
    # Falta un campo obligatorio
    "missing": "El campo es obligatorio.",
    # Se envió un campo que el esquema no tiene
    "extra_forbidden": "Este campo no está permitido.",
    # Se esperaba un texto
    "string_type": "Debe ser un texto.",
    # Texto más corto que el mínimo
    "string_too_short": "Debe tener mínimo {min_length} caracteres.",
    # Texto más largo que el máximo
    "string_too_long": "Debe tener máximo {max_length} caracteres.",
    # El texto no cumple la expresión regular (pattern)
    "string_pattern_mismatch": "No tiene el formato requerido.",
    # No se pudo convertir a número entero
    "int_parsing": "Debe ser un número entero.",
    # Se esperaba un número entero
    "int_type": "Debe ser un número entero.",
    # Se envió un decimal donde se espera un entero
    "int_from_float": "Debe ser un número entero.",
    # No se pudo convertir a número decimal
    "decimal_parsing": "Debe ser un número.",
    # Se esperaba un número decimal
    "decimal_type": "Debe ser un número.",
    # Demasiados decimales
    "decimal_max_places": "Debe tener máximo {decimal_places} decimales.",
    # Demasiados dígitos en total
    "decimal_max_digits": "Debe tener máximo {max_digits} dígitos.",
    # Demasiados dígitos antes del punto decimal
    "decimal_whole_digits": "Tiene demasiados dígitos enteros.",
    # Debe ser mayor que (gt = greater than)
    "greater_than": "Debe ser mayor que {gt}.",
    # Debe ser mayor o igual que (ge = greater or equal)
    "greater_than_equal": "Debe ser mayor o igual que {ge}.",
    # Debe ser menor que (lt = less than)
    "less_than": "Debe ser menor que {lt}.",
    # Debe ser menor o igual que (le = less or equal)
    "less_than_equal": "Debe ser menor o igual que {le}.",
    # No se pudo convertir a verdadero/falso
    "bool_parsing": "Debe ser verdadero o falso.",
    # Se esperaba verdadero/falso
    "bool_type": "Debe ser verdadero o falso.",
    # Fecha con formato inválido
    "date_parsing": "Debe ser una fecha válida con formato AAAA-MM-DD.",
    # Se envió fecha con hora inválida
    "date_from_datetime_parsing": "Debe ser una fecha válida con formato AAAA-MM-DD.",
    # Se esperaba una fecha
    "date_type": "Debe ser una fecha válida con formato AAAA-MM-DD.",
    # Valor fuera de la lista permitida (Enum)
    "enum": "Debe ser uno de estos valores: {expected}.",
    # Valor fuera de la lista permitida (Literal)
    "literal_error": "Debe ser uno de estos valores: {expected}.",
    # Se esperaba una lista
    "list_type": "Debe ser una lista.",
    # Lista con menos elementos de los permitidos
    "too_short": "Debe tener mínimo {min_length} elemento(s).",
    # Lista con más elementos de los permitidos
    "too_long": "Debe tener máximo {max_length} elemento(s).",
    # El cuerpo de la petición no es JSON
    "json_invalid": "El cuerpo de la petición no es un JSON válido.",
    # Se esperaba un objeto
    "model_attributes_type": "Debe ser un objeto JSON.",
    # Se esperaba un diccionario
    "dict_type": "Debe ser un objeto JSON.",
}

# Descripción de cada código de error para la documentación de Swagger
DESCRIPCIONES = {
    # 400
    400: "Regla de negocio no cumplida",
    # 401
    401: "Token ausente, inválido o vencido",
    # 403
    403: "El rol no tiene permiso para esta operación",
    # 404
    404: "Registro no encontrado",
    # 409
    409: "Ya existe un registro con ese valor único",
    # 422
    422: "Datos de entrada inválidos",
}


# Recibe los códigos de error de un endpoint (por ejemplo 401, 403) para documentarlos en Swagger
def respuestas_error(*codigos: int) -> dict:
    """Documenta en Swagger las respuestas de error que puede dar un endpoint."""
    # Arma {401: {"model": ErrorRespuesta, "description": "..."}, ...} para cada código
    return {codigo: {"model": ErrorRespuesta, "description": DESCRIPCIONES[codigo]} for codigo in codigos}


# Función interna que construye la respuesta JSON de error con la estructura única
def _respuesta(estado: int, mensaje: str, detalles: list[dict] | None = None, headers: dict | None = None) -> JSONResponse:
    # Crea el objeto ErrorRespuesta y lo convierte en diccionario
    contenido = ErrorRespuesta(estado=estado, mensaje=mensaje, detalles=detalles).model_dump()
    # Devuelve la respuesta HTTP con ese código, el JSON y los encabezados opcionales
    return JSONResponse(status_code=estado, content=contenido, headers=headers)


# Convierte un error de Pydantic en {"campo": ..., "mensaje": ...} en español
def _traducir_error(error: dict) -> dict:
    """Convierte un error de Pydantic en {campo, mensaje} con el mensaje en español."""
    # "loc" es la ubicación del error, por ejemplo ("body", "correo"); se quitan "body", "query" y "path"
    campo = ".".join(str(parte) for parte in error["loc"] if parte not in ("body", "query", "path"))
    # "ctx" trae datos extra del error (por ejemplo min_length=3); si no hay, usa un diccionario vacío
    contexto = error.get("ctx") or {}
    # value_error = error lanzado por nuestros validadores (ValueError) o por el validador de correos
    if error["type"] == "value_error":
        # Mensajes de nuestros validadores (ValueError) o del validador de correos
        # Si el contexto trae el mensaje de nuestro validador, se usa; si no, es un correo inválido
        mensaje = str(contexto["error"]) if "error" in contexto else "No es un correo electrónico válido."
    # Para los demás tipos de error se busca la plantilla en español
    else:
        # Busca la plantilla del tipo de error (None si no está en la tabla)
        plantilla = MENSAJES_VALIDACION.get(error["type"])
        # Intenta rellenar la plantilla con los datos del contexto
        try:
            # Si hay plantilla la rellena (format); si no, deja el mensaje original de Pydantic
            mensaje = plantilla.format(**contexto) if plantilla else error["msg"]
        # Si a la plantilla le falta algún dato del contexto...
        except (KeyError, IndexError):
            # ...usa el mensaje original de Pydantic
            mensaje = error["msg"]
    # Si no se pudo identificar el campo, se reporta como "cuerpo"
    return {"campo": campo or "cuerpo", "mensaje": mensaje}


# Manejador de nuestras excepciones (ReglaNegocioError, NoEncontradoError, etc.)
async def _manejar_error_aplicacion(request: Request, exc: ErrorAplicacion) -> JSONResponse:
    # Busca el código HTTP según el tipo de excepción; si no la encuentra, usa 400
    estado = next((codigo for tipo, codigo in CODIGOS_HTTP.items() if isinstance(exc, tipo)), 400)
    # El estándar HTTP pide el encabezado WWW-Authenticate en las respuestas 401
    headers = {"WWW-Authenticate": "Bearer"} if estado == 401 else None
    # Devuelve la respuesta con el mensaje de la excepción
    return _respuesta(estado, exc.mensaje, headers=headers)


# Manejador de los errores de validación de datos (422)
async def _manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Traduce cada error de Pydantic al formato {campo, mensaje} en español
    detalles = [_traducir_error(error) for error in exc.errors()]
    # Responde 422 con la lista de campos inválidos
    return _respuesta(422, "Los datos enviados no son válidos.", detalles)


# Manejador de los errores HTTP de FastAPI/Starlette (ruta inexistente, método no permitido)
async def _manejar_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Mensajes en español para los dos casos más comunes
    mensajes = {404: "La ruta solicitada no existe.", 405: "Método HTTP no permitido para esta ruta."}
    # Usa el mensaje en español si existe; si no, el detalle original del error
    return _respuesta(exc.status_code, mensajes.get(exc.status_code, str(exc.detail)))


# Manejador de los errores de integridad de PostgreSQL
async def _manejar_integridad(request: Request, exc: IntegrityError) -> JSONResponse:
    # Última defensa: la base de datos rechazó el cambio (único, llave foránea o CHECK)
    # Escribe el detalle técnico en el log del servidor (no se lo muestra al usuario)
    logger.warning("Error de integridad en %s: %s", request.url.path, exc.orig)
    # Responde 409 con un mensaje general
    return _respuesta(409, "La operación viola una restricción de la base de datos.")


# Manejador de cualquier error no previsto (error de programación, base de datos caída, etc.)
async def _manejar_error_inesperado(request: Request, exc: Exception) -> JSONResponse:
    # El detalle técnico va al log del servidor (RNF34), nunca al usuario
    # logger.exception escribe el error con toda la traza en el log
    logger.exception("Error inesperado en %s %s", request.method, request.url.path)
    # Responde 500 sin detalles técnicos
    return _respuesta(500, "Ocurrió un error interno. Intente más tarde.")


# Registra todos los manejadores en la aplicación (se llama desde main.py)
def registrar_manejadores(app: FastAPI) -> None:
    # Nuestras excepciones -> 400, 401, 403, 404 o 409
    app.add_exception_handler(ErrorAplicacion, _manejar_error_aplicacion)
    # Datos inválidos -> 422
    app.add_exception_handler(RequestValidationError, _manejar_validacion)
    # Ruta inexistente o método no permitido -> 404 o 405
    app.add_exception_handler(StarletteHTTPException, _manejar_http)
    # Restricción de la base de datos -> 409
    app.add_exception_handler(IntegrityError, _manejar_integridad)
    # Cualquier otro error -> 500
    app.add_exception_handler(Exception, _manejar_error_inesperado)
