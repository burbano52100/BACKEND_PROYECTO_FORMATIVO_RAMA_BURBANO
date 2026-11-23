# Función para paginar las consultas (traer solo una parte de los registros)


# Función que aplica saltar y limite a una consulta y trae los registros
def paginar(consulta, saltar, limite):
    # Me salto los registros que dice saltar y traigo máximo los que dice limite
    registros = consulta.offset(saltar).limit(limite).all()
    # Devuelvo los registros
    return registros
