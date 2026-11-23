# Lógica para iniciar sesión, renovar el token y cambiar la contraseña

# datetime es la fecha y hora actual y timedelta sirve para sumar minutos
from datetime import datetime, timedelta

# Modelo que uso para buscar por id
from app.models.usuario import modelo_usuario
# Funciones para responder los errores
from app.core.excepciones import error_regla, error_no_autenticado, error_sin_permiso
# Funciones de seguridad
from app.core.seguridad import verificar_contrasena, encriptar_contrasena, contrasena_es_segura, crear_token, leer_token
# Funciones para buscar y guardar en la base de datos
from app.database.conexion import guardar_cambios, buscar_por_id
# Repositorio de usuarios
from app.repositories import usuario_repository

# Cuántas veces se puede equivocar antes de bloquear la cuenta
maximo_intentos = 5
# Cuántos minutos se bloquea la cuenta
minutos_bloqueo = 15


# Función que arma la respuesta con los dos tokens y el rol
def armar_tokens(usuario):
    # Devuelvo los tokens y el rol
    return {
        "token_acceso": crear_token(usuario.id, "acceso"),  # Token para las peticiones
        "token_renovar": crear_token(usuario.id, "renovar"),  # Token para renovar
        "tipo_token": "bearer",  # Tipo de token
        "rol": usuario.rol.nombre,  # Rol del usuario
    }


# Función para iniciar sesión
def ingresar(bd, datos):
    # Busco el usuario por el correo (en minúsculas)
    usuario = usuario_repository.buscar_por_correo(bd, datos.correo.lower())
    # Si no existe el usuario
    if usuario is None:
        # No digo si el error es el correo o la contraseña por seguridad
        error_no_autenticado("Correo o contraseña incorrectos")
    # Si la cuenta está bloqueada y todavía no ha pasado el tiempo
    if usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > datetime.now():
        # Respondo 403
        error_sin_permiso("La cuenta está bloqueada por muchos intentos fallidos, intente más tarde")
    # Si la contraseña está mal
    if not verificar_contrasena(datos.contrasena, usuario.contrasena):
        # Le sumo un intento fallido
        usuario.intentos_fallidos = usuario.intentos_fallidos + 1
        # Si ya llegó al máximo de intentos
        if usuario.intentos_fallidos >= maximo_intentos:
            # Bloqueo la cuenta por 15 minutos
            usuario.bloqueado_hasta = datetime.now() + timedelta(minutes=minutos_bloqueo)
            # Vuelvo a poner los intentos en 0
            usuario.intentos_fallidos = 0
            # Guardo los cambios
            guardar_cambios(bd, usuario)
            # Respondo 403
            error_sin_permiso("La cuenta se bloqueó 15 minutos por muchos intentos fallidos")
        # Guardo el intento fallido
        guardar_cambios(bd, usuario)
        # Respondo 401
        error_no_autenticado("Correo o contraseña incorrectos")
    # Si la cuenta está desactivada no puede entrar
    if usuario.activo == False:
        # Respondo 403
        error_sin_permiso("La cuenta está inactiva, hable con el encargado")
    # Como entró bien, borro los intentos fallidos
    usuario.intentos_fallidos = 0
    # Y le quito el bloqueo
    usuario.bloqueado_hasta = None
    # Guardo los cambios
    guardar_cambios(bd, usuario)
    # Devuelvo los tokens
    return armar_tokens(usuario)


# Función para pedir tokens nuevos con el token para renovar
def renovar_token(bd, datos):
    # Leo el token para renovar y saco el id del usuario
    usuario_id = leer_token(datos.token_renovar, "renovar")
    # Busco el usuario
    usuario = buscar_por_id(bd, modelo_usuario, usuario_id)
    # Si no existe o está desactivado
    if usuario is None or usuario.activo == False:
        # Respondo 401
        error_no_autenticado("El usuario no existe o está inactivo")
    # Devuelvo tokens nuevos
    return armar_tokens(usuario)


# Función para cambiar la contraseña propia
def cambiar_contrasena(bd, usuario, datos):
    # Reviso que la contraseña actual sea la correcta
    if not verificar_contrasena(datos.contrasena_actual, usuario.contrasena):
        # Respondo 400
        error_regla("La contraseña actual no es correcta")
    # Reviso que la nueva sea segura
    if not contrasena_es_segura(datos.contrasena_nueva):
        # Respondo 400
        error_regla("La contraseña nueva debe tener mínimo 8 caracteres, una mayúscula, una minúscula y un número")
    # La nueva no puede ser igual a la anterior
    if datos.contrasena_actual == datos.contrasena_nueva:
        # Respondo 400
        error_regla("La contraseña nueva tiene que ser diferente a la actual")
    # Encripto la contraseña nueva y la pongo en el usuario
    usuario.contrasena = encriptar_contrasena(datos.contrasena_nueva)
    # Guardo los cambios
    guardar_cambios(bd, usuario)
    # Devuelvo un mensaje
    return {"mensaje": "La contraseña se cambió correctamente"}
