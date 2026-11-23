# Funciones que consultan y guardan las fichas en la base de datos

# Modelo de ficha
from app.models.ficha import modelo_ficha
# Función para paginar
from app.repositories.paginacion import paginar



# Busca una ficha por su código
def buscar_por_codigo(bd, codigo):
    # Hago la consulta y traigo la primera (o None si no existe)
    return bd.query(modelo_ficha).filter(modelo_ficha.codigo == codigo).first()


# Trae la lista de fichas con los filtros
def listar(bd, buscar, jornada, activo, saltar, limite):
    # Traigo las fichas activas o inactivas según el filtro
    consulta = bd.query(modelo_ficha).filter(modelo_ficha.activo == activo)
    # Si mandaron algo para buscar
    if buscar:
        # Busco en el código o en el programa
        consulta = consulta.filter((modelo_ficha.codigo.ilike(f"%{buscar}%")) | (modelo_ficha.programa.ilike(f"%{buscar}%")))
    # Si mandaron jornada
    if jornada:
        # Filtro por jornada
        consulta = consulta.filter(modelo_ficha.jornada == jornada)
    # Ordeno por código
    consulta = consulta.order_by(modelo_ficha.codigo)
    # Pagino y devuelvo la lista
    return paginar(consulta, saltar, limite)


# Trae todas las fichas activas
def listar_activas(bd):
    # Hago la consulta
    return bd.query(modelo_ficha).filter(modelo_ficha.activo == True).all()
