# Funciones que consultan los datos que se usan en los reportes

# Modelo de menú
from app.models.menu import modelo_menu


# Trae los menús que hay entre dos fechas ordenados por fecha
def listar_menus_entre_fechas(bd, desde, hasta):
    # Hago la consulta
    return bd.query(modelo_menu).filter(modelo_menu.fecha >= desde, modelo_menu.fecha <= hasta).order_by(modelo_menu.fecha).all()
