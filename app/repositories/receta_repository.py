# Funciones que consultan y guardan las recetas y sus ingredientes

# Modelos de recetas e ingredientes
from app.models.receta import modelo_receta, modelo_receta_ingrediente
# Función para paginar
from app.repositories.paginacion import paginar



# Busca una receta por su nombre (ilike no tiene en cuenta mayúsculas)
def buscar_por_nombre(bd, nombre):
    # Hago la consulta y traigo la primera (o None si no existe)
    return bd.query(modelo_receta).filter(modelo_receta.nombre.ilike(nombre)).first()


# Busca otra receta (diferente a receta_id) que tenga ese nombre
def buscar_otra_con_nombre(bd, nombre, receta_id):
    # Hago la consulta y traigo la primera (o None si no existe)
    return bd.query(modelo_receta).filter(modelo_receta.nombre.ilike(nombre), modelo_receta.id != receta_id).first()


# Trae la lista de recetas con los filtros
def listar(bd, buscar, activo, saltar, limite):
    # Traigo las recetas activas o inactivas según el filtro
    consulta = bd.query(modelo_receta).filter(modelo_receta.activo == activo)
    # Si mandaron algo para buscar
    if buscar:
        # Busco por nombre
        consulta = consulta.filter(modelo_receta.nombre.ilike(f"%{buscar}%"))
    # Ordeno por nombre
    consulta = consulta.order_by(modelo_receta.nombre)
    # Pagino y devuelvo la lista
    return paginar(consulta, saltar, limite)


# Trae los ingredientes de una receta
def listar_ingredientes(bd, receta_id):
    # Hago la consulta
    return bd.query(modelo_receta_ingrediente).filter(modelo_receta_ingrediente.receta_id == receta_id).order_by(modelo_receta_ingrediente.id).all()


# Trae los ingredientes de todas las recetas que usan un material
def listar_ingredientes_con_material(bd, material_id):
    # Hago la consulta
    return bd.query(modelo_receta_ingrediente).filter(modelo_receta_ingrediente.material_id == material_id).all()




# Borra los ingredientes de una receta (se guarda después con guardar_cambios)
def borrar_ingredientes(bd, receta_id):
    # Borro todos los ingredientes de esa receta
    bd.query(modelo_receta_ingrediente).filter(modelo_receta_ingrediente.receta_id == receta_id).delete()
