# Funciones que consultan y guardan los usuarios y los roles en la base de datos

# Modelos de roles y usuarios
from app.models.usuario import modelo_rol, modelo_usuario
# Función para paginar
from app.repositories.paginacion import paginar



# Busca un usuario por su correo
def buscar_por_correo(bd, correo):
    # Hago la consulta y traigo el primero (o None si no existe)
    return bd.query(modelo_usuario).filter(modelo_usuario.correo == correo).first()


# Busca un usuario por su documento
def buscar_por_documento(bd, documento):
    # Hago la consulta y traigo el primero (o None si no existe)
    return bd.query(modelo_usuario).filter(modelo_usuario.documento == documento).first()


# Trae la lista de usuarios con los filtros
def listar(bd, buscar, rol_id, activo, saltar, limite):
    # Empiezo la consulta con todos los usuarios
    consulta = bd.query(modelo_usuario)
    # Si mandaron algo para buscar
    if buscar:
        # Busco los que tengan ese texto en el nombre (ilike no tiene en cuenta mayúsculas)
        consulta = consulta.filter(modelo_usuario.nombre.ilike(f"%{buscar}%"))
    # Si mandaron el rol
    if rol_id is not None:
        # Filtro por rol
        consulta = consulta.filter(modelo_usuario.rol_id == rol_id)
    # Si mandaron activo
    if activo is not None:
        # Filtro por activo
        consulta = consulta.filter(modelo_usuario.activo == activo)
    # Ordeno por nombre
    consulta = consulta.order_by(modelo_usuario.nombre)
    # Pagino y devuelvo la lista
    return paginar(consulta, saltar, limite)


# Trae todos los roles ordenados por id
def listar_roles(bd):
    # Hago la consulta
    return bd.query(modelo_rol).order_by(modelo_rol.id).all()



# Busca un rol por su nombre
def buscar_rol_por_nombre(bd, nombre):
    # Hago la consulta y traigo el primero (o None si no existe)
    return bd.query(modelo_rol).filter(modelo_rol.nombre == nombre).first()


# Trae todos los usuarios que tienen un rol
def listar_por_rol(bd, rol_id):
    # Hago la consulta
    return bd.query(modelo_usuario).filter(modelo_usuario.rol_id == rol_id).all()


# Cuenta los usuarios activos que tienen un rol
def contar_activos_por_rol(bd, rol_id):
    # Hago la consulta y cuento
    return bd.query(modelo_usuario).filter(modelo_usuario.rol_id == rol_id, modelo_usuario.activo == True).count()


# Cuenta los usuarios que son de una ficha
def contar_por_ficha(bd, ficha_id):
    # Hago la consulta y cuento
    return bd.query(modelo_usuario).filter(modelo_usuario.ficha_id == ficha_id).count()
