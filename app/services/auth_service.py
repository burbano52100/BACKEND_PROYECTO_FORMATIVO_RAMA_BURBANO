"""Reglas de autenticación: inicio de sesión, bloqueo, tokens y cambio de contraseña."""

# Tipos fecha-hora, duración y zona horaria UTC
from datetime import datetime, timedelta, timezone
# ceil redondea hacia arriba (para los minutos de bloqueo que faltan)
from math import ceil

# Sesión de base de datos
from sqlalchemy.orm import Session

# Configuración (intentos máximos, minutos de bloqueo, duración del token)
from app.core.config import settings
# Errores 401, 403 y 400
from app.core.excepciones import NoAutenticadoError, PermisoDenegadoError, ReglaNegocioError
# Funciones de seguridad
from app.core.seguridad import (
    # Constante "access"
    TOKEN_ACCESO,
    # Constante "refresh"
    TOKEN_ACTUALIZACION,
    # Cifra una contraseña con bcrypt
    cifrar_password,
    # Crea el token de acceso
    crear_access_token,
    # Crea el token de actualización
    crear_refresh_token,
    # Lee y valida un token
    decodificar_token,
    # Compara una contraseña con su hash
    verificar_password,
)
# Modelo de la tabla usuarios
from app.models import Usuario
# Consultas de usuarios
from app.repositories.usuario_repository import UsuarioRepository
# Datos de entrada del cambio de contraseña y del login
from app.schemas.auth import CambioPasswordEntrada, LoginEntrada

# Mismo mensaje si el correo no existe o si la contraseña está mal (RF02):
# así no se revela qué correos están registrados.
CREDENCIALES_INVALIDAS = "Correo o contraseña incorrectos."


# Clase con las reglas de autenticación
class AuthService:
    # Constructor: recibe la sesión y crea el repositorio de usuarios
    def __init__(self, db: Session) -> None:
        # Repositorio para consultar y guardar usuarios
        self.usuarios = UsuarioRepository(db)

    # Proceso de inicio de sesión
    def iniciar_sesion(self, datos: LoginEntrada) -> dict:
        # Busca al usuario por su correo
        usuario = self.usuarios.obtener_por_correo(datos.correo)
        # Si el correo no existe...
        if usuario is None:
            # ...responde 401 con el mensaje genérico
            raise NoAutenticadoError(CREDENCIALES_INVALIDAS)

        # Hora actual en UTC (la base de datos guarda bloqueado_hasta con zona horaria)
        ahora = datetime.now(timezone.utc)
        # Si la cuenta tiene un bloqueo que todavía no termina...
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
            # ...responde 403 indicando cuántos minutos faltan
            raise PermisoDenegadoError(self._mensaje_bloqueo(usuario.bloqueado_hasta, ahora))

        # Si la contraseña no coincide con el hash guardado...
        if not verificar_password(datos.password, usuario.password_hash):
            # ...suma un intento fallido (este método siempre lanza un error 401 o 403)
            self._registrar_intento_fallido(usuario, ahora)

        # Si la cuenta está desactivada...
        if not usuario.activo:
            # ...responde 403
            raise PermisoDenegadoError("La cuenta está inactiva. Comuníquese con el Encargado.")

        # Inicio de sesión correcto: se reinicia el contador de intentos
        # Solo guarda si había intentos o un bloqueo vencido (evita escribir sin necesidad)
        if usuario.intentos_fallidos or usuario.bloqueado_hasta:
            # Reinicia los intentos
            usuario.intentos_fallidos = 0
            # Quita el bloqueo
            usuario.bloqueado_hasta = None
            # Guarda los cambios
            self.usuarios.guardar(usuario)
        # Devuelve los tokens y el rol
        return self._emitir_tokens(usuario)

    # Entrega tokens nuevos a partir de un refresh token
    def renovar_tokens(self, refresh_token: str) -> dict:
        # Valida que sea un token de tipo "refresh" y obtiene el id del usuario
        usuario_id = decodificar_token(refresh_token, TOKEN_ACTUALIZACION)
        # Verifica que el usuario siga activo y emite tokens nuevos
        return self._emitir_tokens(self._usuario_activo(usuario_id))

    # Obtiene el usuario a partir del token de acceso (lo usa core/permisos.py)
    def obtener_usuario_desde_token(self, access_token: str) -> Usuario:
        # Valida que sea un token de tipo "access" y obtiene el id del usuario
        usuario_id = decodificar_token(access_token, TOKEN_ACCESO)
        # Devuelve el usuario si sigue activo
        return self._usuario_activo(usuario_id)

    # Cambia la contraseña del propio usuario
    def cambiar_password(self, usuario: Usuario, datos: CambioPasswordEntrada) -> None:
        # Si la contraseña actual escrita no es la correcta...
        if not verificar_password(datos.password_actual, usuario.password_hash):
            # ...responde 400
            raise ReglaNegocioError("La contraseña actual no es correcta.")
        # Si la nueva es igual a la actual...
        if datos.password_actual == datos.password_nueva:
            # ...responde 400
            raise ReglaNegocioError("La nueva contraseña debe ser diferente de la actual.")
        # Cifra y guarda la nueva contraseña
        usuario.password_hash = cifrar_password(datos.password_nueva)
        # Auditoría: el propio usuario hizo el cambio
        usuario.actualizado_por = usuario.id
        # Guarda en la base de datos
        self.usuarios.guardar(usuario)

    # ----- Métodos internos -----

    # Suma un intento fallido y, al llegar al máximo, bloquea la cuenta
    def _registrar_intento_fallido(self, usuario: Usuario, ahora: datetime) -> None:
        """Suma un intento fallido; al llegar al máximo bloquea la cuenta temporalmente."""
        # Suma 1 al contador
        usuario.intentos_fallidos += 1
        # Si llegó al máximo (5 por defecto)...
        if usuario.intentos_fallidos >= settings.MAX_LOGIN_ATTEMPTS:
            # Reinicia el contador para después del bloqueo
            usuario.intentos_fallidos = 0
            # Bloquea la cuenta durante LOCKOUT_MINUTES (15 por defecto)
            usuario.bloqueado_hasta = ahora + timedelta(minutes=settings.LOCKOUT_MINUTES)
            # Guarda el bloqueo
            self.usuarios.guardar(usuario)
            # Responde 403 con los minutos de bloqueo
            raise PermisoDenegadoError(self._mensaje_bloqueo(usuario.bloqueado_hasta, ahora))
        # Si aún no llega al máximo, guarda el contador
        self.usuarios.guardar(usuario)
        # Responde 401 con el mensaje genérico
        raise NoAutenticadoError(CREDENCIALES_INVALIDAS)

    # Método estático: no usa "self" (no necesita datos del objeto)
    @staticmethod
    # Arma el mensaje de cuenta bloqueada
    def _mensaje_bloqueo(bloqueado_hasta: datetime, ahora: datetime) -> str:
        # Minutos que faltan para el desbloqueo, redondeados hacia arriba
        minutos = ceil((bloqueado_hasta - ahora).total_seconds() / 60)
        # Devuelve el mensaje con los minutos
        return f"Cuenta bloqueada por intentos fallidos. Intente de nuevo en {minutos} minuto(s)."

    # Busca al usuario y verifica que siga activo
    def _usuario_activo(self, usuario_id: int) -> Usuario:
        """Un token deja de servir si la cuenta fue desactivada después de emitirlo."""
        # Busca al usuario por su id
        usuario = self.usuarios.obtener_por_id(usuario_id)
        # Si no existe o está inactivo...
        if usuario is None or not usuario.activo:
            # ...responde 401
            raise NoAutenticadoError("El token no es válido o la cuenta está inactiva.")
        # Devuelve el usuario
        return usuario

    # Método estático
    @staticmethod
    # Crea la respuesta con los tokens
    def _emitir_tokens(usuario: Usuario) -> dict:
        # Diccionario con la forma de TokenRespuesta
        return {
            # Token de acceso
            "access_token": crear_access_token(usuario.id),
            # Token de actualización
            "refresh_token": crear_refresh_token(usuario.id),
            # Tipo de token
            "token_type": "bearer",
            # Duración del access token en segundos (minutos x 60)
            "expira_en": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            # Nombre del rol para que el frontend abra el panel correcto
            "rol": usuario.rol.nombre,
        }
