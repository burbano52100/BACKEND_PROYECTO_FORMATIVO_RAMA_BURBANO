# Lógica de los usuarios: revisar las reglas antes de crear, actualizar o desactivar

# Modelo de usuario para crear usuarios nuevos
from app.models.usuario import modelo_usuario, modelo_rol
# Funciones para responder los errores
from app.core.excepciones import error_regla, error_sin_permiso, error_no_encontrado, error_duplicado
# Funciones de seguridad para las contraseñas
from app.core.seguridad import encriptar_contrasena, contrasena_es_segura
# Funciones para buscar y guardar en la base de datos
from app.database.conexion import guardar, guardar_cambios, buscar_por_id
# Repositorio de usuarios
from app.repositories import usuario_repository
# Servicio de fichas para buscar la ficha del aprendiz
from app.services import ficha_service


# Función que busca un usuario y si no existe responde 404
def buscar_usuario_existente(bd, usuario_id):
    # Busco el usuario
    usuario = buscar_por_id(bd, modelo_usuario, usuario_id)
    # Si no existe
    if usuario is None:
        # Respondo 404
        error_no_encontrado("El usuario no existe")
    # Devuelvo el usuario
    return usuario


# Función que revisa que la ficha exista y esté activa
def revisar_ficha_activa(bd, ficha_id):
    # Busco la ficha (si no existe responde 404)
    ficha = ficha_service.buscar_ficha_existente(bd, ficha_id)
    # Si la ficha está inactiva
    if ficha.activo == False:
        # Respondo 400
        error_regla("La ficha está inactiva")


# Función que revisa que el teléfono solo tenga números
def revisar_telefono(telefono):
    # Si mandaron teléfono y no son solo números
    if telefono is not None and not telefono.isdigit():
        # Respondo 400
        error_regla("El teléfono solo puede tener números")


# Función para traer los roles
def listar_roles(bd):
    # Le pido los roles al repositorio
    return usuario_repository.listar_roles(bd)


# Función para traer la lista de usuarios
def listar_usuarios(bd, buscar, rol_id, activo, saltar, limite):
    # Le pido la lista al repositorio
    return usuario_repository.listar(bd, buscar, rol_id, activo, saltar, limite)


# Función para crear un usuario
def crear_usuario(bd, datos):
    # El documento solo puede tener números
    if not datos.documento.isdigit():
        # Respondo 400
        error_regla("El documento solo puede tener números")
    # Reviso el teléfono
    revisar_telefono(datos.telefono)
    # Reviso que la contraseña sea segura
    if not contrasena_es_segura(datos.contrasena):
        # Respondo 400
        error_regla("La contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula y un número")
    # Paso el correo a minúsculas
    correo = datos.correo.lower()
    # Si ya hay un usuario con ese correo
    if usuario_repository.buscar_por_correo(bd, correo) is not None:
        # Respondo 409 porque ese valor no se puede repetir
        error_duplicado("Ya existe un usuario con ese correo")
    # Si ya hay un usuario con ese documento
    if usuario_repository.buscar_por_documento(bd, datos.documento) is not None:
        # Respondo 409 porque ese valor no se puede repetir
        error_duplicado("Ya existe un usuario con ese documento")
    # Busco el rol
    rol = buscar_por_id(bd, modelo_rol, datos.rol_id)
    # Si el rol no existe
    if rol is None:
        # Respondo 404
        error_no_encontrado("El rol no existe")
    # Si es aprendiz tiene que tener una ficha
    if rol.nombre == "aprendiz":
        # Si no mandaron ficha
        if datos.ficha_id is None:
            # Respondo 400
            error_regla("Los aprendices tienen que tener una ficha")
        # Reviso que la ficha exista y esté activa
        revisar_ficha_activa(bd, datos.ficha_id)
    # Si no es aprendiz
    else:
        # No puede tener ficha
        if datos.ficha_id is not None:
            # Respondo 400
            error_regla("Solo los aprendices pueden tener ficha")
        # Ni puede ser beneficiario
        if datos.es_beneficiario == True:
            # Respondo 400
            error_regla("Solo los aprendices pueden ser beneficiarios")
    # Creo el usuario nuevo
    nuevo_usuario = modelo_usuario(
        documento=datos.documento,  # Documento
        nombre=datos.nombre,  # Nombre
        correo=correo,  # Correo en minúsculas
        telefono=datos.telefono,  # Teléfono
        contrasena=encriptar_contrasena(datos.contrasena),  # Contraseña encriptada
        rol_id=datos.rol_id,  # Rol
        ficha_id=datos.ficha_id,  # Ficha
        es_beneficiario=datos.es_beneficiario,  # Si es beneficiario
    )
    # Lo guardo en la base de datos y lo devuelvo
    return guardar(bd, nuevo_usuario)


# Función para actualizar un usuario
def actualizar_usuario(bd, usuario_id, datos, usuario_actual):
    # Busco el usuario
    usuario = buscar_usuario_existente(bd, usuario_id)
    # Nadie puede cambiar su propio rol
    if usuario.id == usuario_actual.id and datos.rol_id is not None and datos.rol_id != usuario.rol_id:
        # Respondo 403
        error_sin_permiso("No puede cambiar su propio rol")
    # Nadie puede desactivar su propia cuenta
    if usuario.id == usuario_actual.id and datos.activo == False:
        # Respondo 403
        error_sin_permiso("No puede desactivar su propia cuenta")
    # Si mandaron nombre
    if datos.nombre is not None:
        # Cambio el nombre
        usuario.nombre = datos.nombre
    # Si mandaron teléfono
    if datos.telefono is not None:
        # Reviso que sean solo números
        revisar_telefono(datos.telefono)
        # Cambio el teléfono
        usuario.telefono = datos.telefono
    # Si mandaron rol
    if datos.rol_id is not None:
        # Si el rol no existe
        if buscar_por_id(bd, modelo_rol, datos.rol_id) is None:
            # Respondo 404
            error_no_encontrado("El rol no existe")
        # Cambio el rol
        usuario.rol_id = datos.rol_id
    # Si mandaron ficha
    if datos.ficha_id is not None:
        # Reviso que la ficha exista y esté activa
        revisar_ficha_activa(bd, datos.ficha_id)
        # Cambio la ficha
        usuario.ficha_id = datos.ficha_id
    # Si mandaron activo
    if datos.activo is not None:
        # Cambio el estado
        usuario.activo = datos.activo
        # Si lo están activando otra vez
        if datos.activo == True:
            # Le borro los intentos fallidos
            usuario.intentos_fallidos = 0
            # Y le quito el bloqueo
            usuario.bloqueado_hasta = None
    # Busco el rol que quedó para revisar la ficha
    rol_final = buscar_por_id(bd, modelo_rol, usuario.rol_id)
    # Si quedó como aprendiz
    if rol_final.nombre == "aprendiz":
        # Tiene que tener ficha
        if usuario.ficha_id is None:
            # Respondo 400
            error_regla("Los aprendices tienen que tener una ficha")
    # Si no quedó como aprendiz
    else:
        # Si mandaron una ficha
        if datos.ficha_id is not None:
            # Respondo 400
            error_regla("Solo los aprendices pueden tener ficha")
        # Le quito la ficha
        usuario.ficha_id = None
        # Y le quito lo de beneficiario
        usuario.es_beneficiario = False
    # Guardo los cambios y devuelvo el usuario
    return guardar_cambios(bd, usuario)


# Función para desactivar un usuario (no se borra, solo se pone inactivo)
def desactivar_usuario(bd, usuario_id, usuario_actual):
    # Busco el usuario
    usuario = buscar_usuario_existente(bd, usuario_id)
    # No se puede desactivar a sí mismo
    if usuario.id == usuario_actual.id:
        # Respondo 403
        error_sin_permiso("No puede desactivar su propia cuenta")
    # Si ya está inactivo
    if usuario.activo == False:
        # Respondo 400
        error_regla("El usuario ya está inactivo")
    # Lo pongo inactivo (borrado lógico)
    usuario.activo = False
    # Guardo los cambios
    guardar_cambios(bd, usuario)
    # Devuelvo un mensaje
    return {"mensaje": "El usuario " + usuario.nombre + " se desactivó"}


# Función para poner o quitar a un aprendiz como beneficiario (almuerzo gratis)
def cambiar_beneficiario(bd, usuario_id, datos):
    # Busco el usuario
    usuario = buscar_usuario_existente(bd, usuario_id)
    # Solo los aprendices pueden ser beneficiarios
    if usuario.rol.nombre != "aprendiz":
        # Respondo 400
        error_regla("Solo los aprendices pueden ser beneficiarios")
    # Si el aprendiz está inactivo
    if usuario.activo == False:
        # Respondo 400
        error_regla("El aprendiz está inactivo")
    # Si ya tiene ese mismo estado
    if usuario.es_beneficiario == datos.es_beneficiario:
        # Respondo 400
        error_regla("El aprendiz ya tiene ese estado de beneficiario")
    # Cambio el estado
    usuario.es_beneficiario = datos.es_beneficiario
    # Guardo los cambios y devuelvo el usuario
    return guardar_cambios(bd, usuario)
