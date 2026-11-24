# Función para paginar las consultas (traer solo una parte de los registros)

# Función que responde 422 para los parámetros de paginación
from app.core.excepciones import error_parametros


# Revisa que saltar y limite estén en un rango seguro
def validar_paginacion(saltar, limite):
    if saltar < 0:
        error_parametros("saltar no puede ser negativo")
    if limite < 1 or limite > 100:
        error_parametros("limite debe estar entre 1 y 100")


# Función que aplica saltar y limite a una consulta y trae los registros
def paginar(consulta, saltar, limite):
    validar_paginacion(saltar, limite)
    # Me salto los registros que dice saltar y traigo máximo los que dice limite
    registros = consulta.offset(saltar).limit(limite).all()
    # Devuelvo los registros
    return registros
