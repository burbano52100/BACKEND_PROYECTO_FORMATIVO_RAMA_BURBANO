# Funciones que consultan y guardan los materiales y los movimientos del inventario

# Modelos de materiales y movimientos
from app.models.inventario import modelo_material, modelo_movimiento_inventario
# Función para paginar
from app.repositories.paginacion import paginar



# Busca un material por su código de barras
def buscar_material_por_codigo(bd, codigo_barras):
    # Hago la consulta y traigo el primero (o None si no existe)
    return bd.query(modelo_material).filter(modelo_material.codigo_barras == codigo_barras).first()


def buscar_material_para_movimiento(bd, material_id):
    return bd.query(modelo_material).filter(modelo_material.id == material_id).with_for_update().first()


# Trae los materiales con los filtros ordenados por nombre (sin paginar)
def listar_materiales(bd, buscar, categoria, activo):
    # Traigo los materiales activos o inactivos según el filtro
    consulta = bd.query(modelo_material).filter(modelo_material.activo == activo)
    # Si mandaron algo para buscar
    if buscar:
        # Busco en el nombre o en el código de barras
        consulta = consulta.filter((modelo_material.nombre.ilike(f"%{buscar}%")) | (modelo_material.codigo_barras.ilike(f"%{buscar}%")))
    # Si mandaron categoría
    if categoria:
        # Filtro por categoría
        consulta = consulta.filter(modelo_material.categoria == categoria)
    # Ordeno por nombre y devuelvo la lista
    return consulta.order_by(modelo_material.nombre).all()





# Cuenta los movimientos que tiene un material
def contar_movimientos(bd, material_id):
    # Hago la consulta y cuento
    return bd.query(modelo_movimiento_inventario).filter(modelo_movimiento_inventario.material_id == material_id).count()



# Trae el kardex (historial de movimientos) con los filtros
def listar_kardex(bd, material_id, tipo, saltar, limite):
    # Empiezo con todos los movimientos
    consulta = bd.query(modelo_movimiento_inventario)
    # Si mandaron material
    if material_id is not None:
        # Filtro por material
        consulta = consulta.filter(modelo_movimiento_inventario.material_id == material_id)
    # Si mandaron tipo
    if tipo is not None:
        # Filtro por tipo
        consulta = consulta.filter(modelo_movimiento_inventario.tipo == tipo)
    # Ordeno del más nuevo al más viejo
    consulta = consulta.order_by(modelo_movimiento_inventario.fecha.desc(), modelo_movimiento_inventario.id.desc())
    # Pagino y devuelvo la lista
    return paginar(consulta, saltar, limite)
