# Funciones que consultan y guardan las sugerencias en la base de datos

# Modelo de sugerencia
from app.models.sugerencia import modelo_sugerencia
# Función para paginar
from app.repositories.paginacion import paginar



# Trae las sugerencias de una persona de la más nueva a la más vieja
def listar_de_usuario(bd, usuario_id):
    # Hago la consulta
    return bd.query(modelo_sugerencia).filter(modelo_sugerencia.usuario_id == usuario_id).order_by(modelo_sugerencia.id.desc()).all()


# Trae todas las sugerencias con el filtro de estado
def listar(bd, estado, saltar, limite):
    # Empiezo con todas las sugerencias
    consulta = bd.query(modelo_sugerencia)
    # Si mandaron estado
    if estado is not None:
        # Filtro por estado
        consulta = consulta.filter(modelo_sugerencia.estado == estado)
    # Ordeno de la más nueva a la más vieja
    consulta = consulta.order_by(modelo_sugerencia.id.desc())
    # Pagino y devuelvo la lista
    return paginar(consulta, saltar, limite)


# Cuenta todas las sugerencias
def contar_todas(bd):
    # Hago la consulta y cuento
    return bd.query(modelo_sugerencia).count()


# Cuenta las sugerencias que tienen un estado
def contar_por_estado(bd, estado):
    # Hago la consulta y cuento
    return bd.query(modelo_sugerencia).filter(modelo_sugerencia.estado == estado).count()
