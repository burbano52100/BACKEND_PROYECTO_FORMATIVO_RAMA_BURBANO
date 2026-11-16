"""Configuración centralizada: lee las variables de entorno y el archivo .env."""

# Importa el tipo "time" (una hora del día, sin fecha) para el horario de reservas
from datetime import time

# Field permite ponerle restricciones a un valor (mínimo, máximo, longitud...)
from pydantic import Field
# BaseSettings llena la clase con variables de entorno; SettingsConfigDict configura cómo leerlas
from pydantic_settings import BaseSettings, SettingsConfigDict


# Clase con toda la configuración de la API; al heredar de BaseSettings lee el .env automáticamente
class Settings(BaseSettings):
    """Cada atributo se llena con la variable de entorno del mismo nombre.

    Si falta una variable obligatoria, la API no arranca y muestra cuál falta.
    """

    # Lee el archivo ".env" en UTF-8 e ignora las variables que no estén declaradas en esta clase
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de datos
    # Servidor donde está PostgreSQL (por defecto, el mismo computador)
    DB_HOST: str = "localhost"
    # Puerto de PostgreSQL (5432 es el puerto por defecto)
    DB_PORT: int = 5432
    # Nombre de la base de datos (obligatorio: no tiene valor por defecto)
    DB_NAME: str
    # Esquema del proyecto dentro de la base de datos (gastrosena)
    DB_SCHEMA: str
    # Usuario con el que la API se conecta a PostgreSQL (api_gastrosena)
    DB_USER: str
    # Contraseña de ese usuario
    DB_PASSWORD: str

    # JWT
    # Clave secreta para firmar los tokens; debe tener mínimo 32 caracteres o la API no arranca
    JWT_SECRET_KEY: str = Field(min_length=32)
    # Algoritmo de firma de los tokens (HS256 = HMAC con SHA-256)
    JWT_ALGORITHM: str = "HS256"
    # Minutos que dura el token de acceso
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Días que dura el token de actualización (refresh)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Seguridad
    # Intentos fallidos de inicio de sesión antes de bloquear la cuenta
    MAX_LOGIN_ATTEMPTS: int = 5
    # Minutos que dura el bloqueo de la cuenta
    LOCKOUT_MINUTES: int = 15

    # CORS: texto con los orígenes separados por coma
    # Páginas web autorizadas para llamar la API, por ejemplo "http://localhost:5173,https://..."
    CORS_ORIGINS: str = ""

    # Reglas del negocio (valores propuestos en la especificación de requisitos)
    # Hora desde la que se puede reservar o cancelar (7:00 a. m.)
    HORA_INICIO_RESERVAS: time = time(7, 0)
    # Hora hasta la que se puede reservar o cancelar (9:00 p. m.)
    HORA_FIN_RESERVAS: time = time(21, 0)
    # Un material está "VENCIENDO" si vence dentro de estos días; ge=0 exige que no sea negativo
    DIAS_ALERTA_VENCIMIENTO: int = Field(7, ge=0)
    # Stock "CRÍTICO" si es menor o igual a este porcentaje del stock mínimo (entre 0 y 100)
    PORCENTAJE_STOCK_CRITICO: int = Field(50, ge=0, le=100)
    # Días que tiene un instructor para pagar después del corte mensual
    DIAS_PLAZO_PAGO: int = Field(5, ge=0)

    # @property permite usar este método como si fuera un atributo: settings.cors_origins
    @property
    # Convierte el texto CORS_ORIGINS en una lista de orígenes
    def cors_origins(self) -> list[str]:
        # Separa el texto por comas, quita espacios a cada origen y descarta los vacíos
        return [origen.strip() for origen in self.CORS_ORIGINS.split(",") if origen.strip()]


# Crea UNA sola instancia de la configuración; el resto del proyecto importa "settings"
settings = Settings()
