# En este archivo están las funciones para responder los errores
# Cada función lanza un HTTPException con su código para no repetirlo en todos lados

# HTTPException sirve para responder un error con su código
from fastapi import HTTPException


# Error 400: no se cumple una regla del negocio o los datos están malos
def error_regla(mensaje):
    # Lanzo el error con el código 400
    raise HTTPException(status_code=400, detail=mensaje)


# Error 401: no inició sesión o el token está malo
def error_no_autenticado(mensaje):
    # Lanzo el error con el código 401
    raise HTTPException(status_code=401, detail=mensaje)


# Error 403: inició sesión pero no tiene permiso para hacer eso
def error_sin_permiso(mensaje):
    # Lanzo el error con el código 403
    raise HTTPException(status_code=403, detail=mensaje)


# Error 404: lo que busca no existe
def error_no_encontrado(mensaje):
    # Lanzo el error con el código 404
    raise HTTPException(status_code=404, detail=mensaje)


# Error 409: ya existe un registro con un valor que no se puede repetir (correo, documento, código...)
def error_duplicado(mensaje):
    # Lanzo el error con el código 409 (conflicto)
    raise HTTPException(status_code=409, detail=mensaje)
