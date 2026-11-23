# Rutas para iniciar sesión, pedir un token nuevo, ver el perfil y cambiar la contraseña

# APIRouter sirve para agrupar rutas y Depends para las dependencias
from fastapi import APIRouter, Depends
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database.conexion import obtener_bd
# Modelo de usuario
from app.models.usuario import modelo_usuario
# Función para saber quién hace la petición
from app.core.permisos import obtener_usuario_actual
# Esquemas que uso en estas rutas
from app.schemas.auth import ingreso_datos, token_respuesta, renovar_datos, cambiar_contrasena_datos
# Esquema para responder el usuario
from app.schemas.usuario import usuario_respuesta
# Esquema para responder un mensaje
from app.schemas.comunes import mensaje_respuesta
# Servicio con la lógica de la autenticación
from app.services import auth_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /autenticacion
enrutador = APIRouter(prefix="/autenticacion", tags=["Autenticación"])


# Ruta para iniciar sesión (es la única que no necesita token)
@enrutador.post(
    "/ingresar", response_model=token_respuesta,
    summary="Iniciar sesión",  # Título corto que sale en /docs
    description="Revisa el correo y la contraseña y devuelve el token de acceso, el token para renovar y el rol. Después de 5 intentos fallidos la cuenta se bloquea 15 minutos y una cuenta inactiva no puede entrar. **Rol requerido:** ninguno (es la única ruta pública).",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def ingresar(datos: ingreso_datos, bd: Session = Depends(obtener_bd)):
    # Le pido al servicio que revise el correo y la contraseña
    tokens = auth_service.ingresar(bd, datos)
    # Devuelvo los tokens
    return tokens


# Ruta para pedir tokens nuevos con el token para renovar
@enrutador.post(
    "/renovar", response_model=token_respuesta,
    summary="Renovar los tokens",  # Título corto que sale en /docs
    description="Recibe el token para renovar y entrega tokens nuevos sin pedir la contraseña. **Rol requerido:** ninguno, pero el token para renovar tiene que ser válido.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 422),  # Errores que puede responder
)
def renovar_token(datos: renovar_datos, bd: Session = Depends(obtener_bd)):
    # Le pido al servicio los tokens nuevos
    tokens = auth_service.renovar_token(bd, datos)
    # Devuelvo los tokens
    return tokens


# Ruta para ver los datos de quien inició sesión
@enrutador.get(
    "/perfil", response_model=usuario_respuesta,
    summary="Ver mi perfil",  # Título corto que sale en /docs
    description="Devuelve los datos de quien inició sesión (nunca la contraseña). **Rol requerido:** cualquiera con sesión iniciada.",  # Explicación y rol que se necesita
    responses=respuestas_error(401),  # Errores que puede responder
)
def ver_perfil(usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Devuelvo el usuario (el esquema usuario_respuesta no muestra la contraseña)
    return usuario_actual


# Ruta para cambiar la contraseña propia
@enrutador.put(
    "/contrasena", response_model=mensaje_respuesta,
    summary="Cambiar mi contraseña",  # Título corto que sale en /docs
    description="La contraseña nueva debe tener mínimo 8 caracteres, una mayúscula, una minúscula y un número, y ser diferente a la actual. **Rol requerido:** cualquiera con sesión iniciada.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 422),  # Errores que puede responder
)
def cambiar_contrasena(datos: cambiar_contrasena_datos, usuario_actual: modelo_usuario = Depends(obtener_usuario_actual), bd: Session = Depends(obtener_bd)):
    # Le pido al servicio que cambie la contraseña
    respuesta = auth_service.cambiar_contrasena(bd, usuario_actual, datos)
    # Devuelvo el mensaje
    return respuesta
