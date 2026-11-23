# En este archivo están las funciones que arreglan los errores para que salgan en español
# y todos con la misma forma: {"detalle": "mensaje"}
# En main.py se le dice a la API que use estas funciones

# logging sirve para escribir los errores en la consola del servidor (no se le muestran al usuario)
import logging
# Union quiere decir que un campo puede ser de un tipo o de otro
from typing import Union

# JSONResponse sirve para devolver una respuesta en JSON armada por mí
from fastapi.responses import JSONResponse
# BaseModel sirve para hacer el esquema de la respuesta de error (sale en /docs)
from pydantic import BaseModel

# Creo el "registro" donde se escriben los errores del servidor
registro = logging.getLogger("gastrosena")


# Esta es la forma de todas las respuestas de error (así sale en /docs)
class error_respuesta(BaseModel):
    # El mensaje del error (o la lista de mensajes cuando son datos malos)
    detalle: Union[str, list[str]]


# Qué quiere decir cada código de error (se muestra en /docs)
descripciones_error = {
    400: "No se cumple una regla del negocio",  # Regla de negocio
    401: "Falta el token, no es válido o ya se venció",  # Sin sesión
    403: "El rol no tiene permiso para hacer esto",  # Sin permiso
    404: "El registro no existe",  # No existe
    409: "Ya existe un registro con ese valor (no se puede repetir)",  # Duplicado
    422: "Los datos enviados no son válidos",  # Datos malos
    500: "Error interno del servidor",  # Error del servidor
}


# Función que arma las respuestas de error que salen en /docs para cada ruta
# Por ejemplo respuestas_error(401, 403, 404) documenta esos tres códigos
def respuestas_error(*codigos):
    # Aquí voy a guardar las respuestas
    respuestas = {}
    # Recorro cada código que me pidieron
    for codigo in codigos:
        # Le pongo el esquema del error y su descripción
        respuestas[codigo] = {"model": error_respuesta, "description": descripciones_error[codigo]}
    # Todas las rutas pueden dar error 500 si algo falla en el servidor
    respuestas[500] = {"model": error_respuesta, "description": descripciones_error[500]}
    # Devuelvo las respuestas
    return respuestas


# Esta función arregla los errores normales (400, 401, 403, 404, 409...)
def manejar_errores(peticion, error):
    # Saco el mensaje del error
    mensaje = error.detail
    # Si la ruta no existe FastAPI pone "Not Found"
    if mensaje == "Not Found":
        # Lo cambio a español
        mensaje = "La ruta no existe"
    # Si el método no se puede usar FastAPI pone "Method Not Allowed"
    if mensaje == "Method Not Allowed":
        # Lo cambio a español
        mensaje = "Ese método no se puede usar en esta ruta"
    # Devuelvo el error con el mismo código
    return JSONResponse(status_code=error.status_code, content={"detalle": mensaje})


# Esta función arregla los errores de datos malos (422) para que salgan en español
def manejar_datos_malos(peticion, error):
    # Aquí voy a guardar los mensajes
    errores = []
    # Recorro cada error que encontró FastAPI
    for problema in error.errors():
        # El último dato de "loc" es el nombre del campo que está malo
        campo = str(problema["loc"][-1])
        # Si el campo no lo mandaron
        if problema["type"] == "missing":
            # Agrego el mensaje de que falta
            errores.append("Falta el campo " + campo)
        # Si lo mandaron pero está malo
        else:
            # Agrego el mensaje de que no es válido
            errores.append("El campo " + campo + " no es válido")
    # Devuelvo el error 422 con la lista de mensajes
    return JSONResponse(status_code=422, content={"detalle": errores})


# Esta función atrapa cuando PostgreSQL rechaza un cambio (un valor repetido, una llave foránea o un CHECK)
# Casi nunca pasa porque los servicios revisan antes, pero es la última defensa
def manejar_error_integridad(peticion, error):
    # Escribo el detalle técnico en la consola del servidor
    registro.warning("PostgreSQL rechazó el cambio en %s: %s", peticion.url.path, error.orig)
    # Al usuario le respondo 409 con un mensaje claro y sin detalles técnicos
    return JSONResponse(status_code=409, content={"detalle": "No se pudo guardar porque choca con datos que ya existen"})


# Esta función atrapa cualquier error que no esperábamos (error 500)
# El detalle técnico se escribe en la consola del servidor y NUNCA se le muestra al usuario
def manejar_error_interno(peticion, error):
    # Escribo el error completo en la consola del servidor
    registro.exception("Error interno en %s %s", peticion.method, peticion.url.path)
    # Al usuario solo le digo que algo falló
    return JSONResponse(status_code=500, content={"detalle": "Ocurrió un error interno, intente más tarde"})
