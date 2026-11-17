# Rutas para iniciar sesión, pedir un token nuevo, ver el perfil y cambiar la contraseña

# datetime es la fecha y hora actual y timedelta sirve para sumar minutos
from datetime import datetime, timedelta

# APIRouter sirve para agrupar rutas, Depends para las dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database import get_db
# Modelo de usuario
from app.models import Usuario
# Esquemas que uso en estas rutas
from app.schemas import LoginDatos, TokenRespuesta, RefreshDatos, CambiarPasswordDatos, UsuarioRespuesta
# Funciones de seguridad
from app.seguridad import verificar_password, encriptar_password, password_es_segura, crear_token, leer_token, obtener_usuario_actual

# Creo el router, todas las rutas empiezan con /auth
router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Cuántas veces se puede equivocar antes de bloquear la cuenta
MAXIMO_INTENTOS = 5
# Cuántos minutos se bloquea la cuenta
MINUTOS_BLOQUEO = 15


# Ruta para iniciar sesión (es la única que no necesita token)
@router.post("/login", response_model=TokenRespuesta)
def login(datos: LoginDatos, db: Session = Depends(get_db)):
    # Busco el usuario por el correo (en minúsculas)
    usuario = db.query(Usuario).filter(Usuario.correo == datos.correo.lower()).first()
    # Si no existe el usuario
    if usuario is None:
        # No digo si el error es el correo o la contraseña por seguridad
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    # Si la cuenta está bloqueada y todavía no ha pasado el tiempo
    if usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > datetime.now():
        # Respondo 403
        raise HTTPException(status_code=403, detail="La cuenta está bloqueada por muchos intentos fallidos, intente más tarde")
    # Si la contraseña está mal
    if not verificar_password(datos.password, usuario.password):
        # Le sumo un intento fallido
        usuario.intentos_fallidos = usuario.intentos_fallidos + 1
        # Si ya llegó al máximo de intentos
        if usuario.intentos_fallidos >= MAXIMO_INTENTOS:
            # Bloqueo la cuenta por 15 minutos
            usuario.bloqueado_hasta = datetime.now() + timedelta(minutes=MINUTOS_BLOQUEO)
            # Vuelvo a poner los intentos en 0
            usuario.intentos_fallidos = 0
            # Guardo los cambios
            db.commit()
            # Respondo 403
            raise HTTPException(status_code=403, detail="La cuenta se bloqueó 15 minutos por muchos intentos fallidos")
        # Guardo el intento fallido
        db.commit()
        # Respondo 401
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    # Si la cuenta está desactivada no puede entrar
    if usuario.activo == False:
        # Respondo 403
        raise HTTPException(status_code=403, detail="La cuenta está inactiva, hable con el encargado")
    # Como entró bien, borro los intentos fallidos
    usuario.intentos_fallidos = 0
    # Y le quito el bloqueo
    usuario.bloqueado_hasta = None
    # Guardo los cambios
    db.commit()
    # Devuelvo los tokens y el rol
    return {
        "access_token": crear_token(usuario.id, "access"),  # Token para las peticiones
        "refresh_token": crear_token(usuario.id, "refresh"),  # Token para renovar
        "token_type": "bearer",  # Tipo de token
        "rol": usuario.rol.nombre,  # Rol del usuario
    }


# Ruta para pedir tokens nuevos con el refresh token
@router.post("/refresh", response_model=TokenRespuesta)
def renovar_token(datos: RefreshDatos, db: Session = Depends(get_db)):
    # Leo el refresh token y saco el id del usuario
    usuario_id = leer_token(datos.refresh_token, "refresh")
    # Busco el usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    # Si no existe o está desactivado
    if usuario is None or usuario.activo == False:
        # Respondo 401
        raise HTTPException(status_code=401, detail="El usuario no existe o está inactivo")
    # Devuelvo tokens nuevos
    return {
        "access_token": crear_token(usuario.id, "access"),  # Token nuevo para las peticiones
        "refresh_token": crear_token(usuario.id, "refresh"),  # Refresh token nuevo
        "token_type": "bearer",  # Tipo de token
        "rol": usuario.rol.nombre,  # Rol del usuario
    }


# Ruta para ver los datos de quien inició sesión
@router.get("/perfil", response_model=UsuarioRespuesta)
def ver_perfil(usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Devuelvo el usuario (el esquema UsuarioRespuesta no muestra la contraseña)
    return usuario_actual


# Ruta para cambiar la contraseña propia
@router.put("/password")
def cambiar_password(datos: CambiarPasswordDatos, usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    # Reviso que la contraseña actual sea la correcta
    if not verificar_password(datos.password_actual, usuario_actual.password):
        # Respondo 400
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    # Reviso que la nueva sea segura
    if not password_es_segura(datos.password_nueva):
        # Respondo 400
        raise HTTPException(status_code=400, detail="La contraseña nueva debe tener mínimo 8 caracteres, una mayúscula, una minúscula y un número")
    # La nueva no puede ser igual a la anterior
    if datos.password_actual == datos.password_nueva:
        # Respondo 400
        raise HTTPException(status_code=400, detail="La contraseña nueva tiene que ser diferente a la actual")
    # Encripto la contraseña nueva y la guardo
    usuario_actual.password = encriptar_password(datos.password_nueva)
    # Guardo los cambios
    db.commit()
    # Respondo con un mensaje
    return {"mensaje": "La contraseña se cambió correctamente"}
