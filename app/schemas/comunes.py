"""Tipos y esquemas reutilizables: validadores de formato, paginación y errores."""

# re = expresiones regulares (para revisar formatos de texto)
import re
# Tipo fecha
from datetime import date
# Decimal = número decimal exacto
from decimal import Decimal
# ceil redondea hacia arriba (para calcular el número de páginas)
from math import ceil
# Annotated agrega reglas a un tipo; Any = cualquier tipo; Generic y TypeVar crean clases "genéricas"
from typing import Annotated, Any, Generic, TypeVar

# Herramientas de Pydantic para definir y validar esquemas
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, PlainSerializer

# Módulo de fecha y hora de Colombia (para saber cuál es "hoy")
from app.core import tiempo

# T representa "cualquier tipo de elemento" en la paginación (usuarios, menús, reservas...)
T = TypeVar("T")


# ---------------------------------------------------------------------------
# Validadores de formato con mensajes en español
# ---------------------------------------------------------------------------

# Revisa que la contraseña cumpla la política de seguridad
def _validar_password(valor: str) -> str:
    # Debe tener al menos una mayúscula, una minúscula y un número
    if not (re.search(r"[A-Z]", valor) and re.search(r"[a-z]", valor) and re.search(r"[0-9]", valor)):
        # Pydantic convierte este ValueError en un error 422 con este mensaje
        raise ValueError("La contraseña debe tener al menos una mayúscula, una minúscula y un número.")
    # bcrypt solo usa los primeros 72 bytes; se rechazan las más largas (las tildes ocupan 2 bytes)
    if len(valor.encode("utf-8")) > 72:
        # Error 422
        raise ValueError("La contraseña es demasiado larga (bcrypt admite máximo 72 bytes).")
    # Si todo está bien, devuelve la contraseña sin cambios
    return valor


# Revisa el formato del número de documento
def _validar_documento(valor: str) -> str:
    # fullmatch exige que TODO el texto sean entre 6 y 10 dígitos
    if not re.fullmatch(r"[0-9]{6,10}", valor):
        # Error 422
        raise ValueError("El documento debe tener entre 6 y 10 dígitos, sin puntos ni espacios.")
    # Documento válido
    return valor


# Revisa el formato del teléfono colombiano
def _validar_telefono(valor: str) -> str:
    # Celular: 3 seguido de 9 dígitos; fijo: 60 seguido de 8 dígitos
    if not re.fullmatch(r"3[0-9]{9}|60[0-9]{8}", valor):
        # Error 422
        raise ValueError("El teléfono debe tener 10 dígitos: celular (3XX...) o fijo (60X...).")
    # Teléfono válido
    return valor


# Revisa que una fecha no sea anterior a hoy
def _validar_fecha_no_pasada(valor: date) -> date:
    # Compara con la fecha de hoy en Colombia
    if valor < tiempo.hoy():
        # Error 422
        raise ValueError("La fecha no puede ser anterior a hoy.")
    # Fecha válida
    return valor


# Tipo contraseña: texto de 8 a 64 caracteres que además pasa por _validar_password
Password = Annotated[str, Field(min_length=8, max_length=64), AfterValidator(_validar_password)]
# Tipo documento: texto que pasa por _validar_documento
Documento = Annotated[str, AfterValidator(_validar_documento)]
# Tipo teléfono: texto que pasa por _validar_telefono
Telefono = Annotated[str, AfterValidator(_validar_telefono)]
# Tipo correo: EmailStr valida el formato y str.lower lo convierte a minúsculas
Correo = Annotated[EmailStr, AfterValidator(str.lower)]
# Tipo fecha que no puede ser anterior a hoy
FechaNoPasada = Annotated[date, AfterValidator(_validar_fecha_no_pasada)]

# Valores monetarios de entrada (Decimal, sin errores de redondeo)
# Valor mayor que 0, hasta 12 dígitos con 2 decimales (pagos, costos, precios de venta)
Valor = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
# Precio del menú: puede ser 0 (ge=0 = mayor o igual que 0), hasta 10 dígitos con 2 decimales
PrecioMenu = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
# Cantidades de inventario: hasta 3 decimales (por ejemplo 0.150 KG)
# Cantidad mayor que 0 y hasta 99999
Cantidad = Annotated[Decimal, Field(gt=0, le=99999, max_digits=12, decimal_places=3)]

# En las respuestas JSON los Decimal se envían como número y no como texto
# Dinero de salida: al convertirse a JSON se envía como número (float)
Dinero = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
# Cantidad de salida (stock, saldo): igual, como número
Medida = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


# Clase padre de todos los esquemas que reciben datos del cliente
class EsquemaEntrada(BaseModel):
    """Base de los esquemas que reciben datos del cliente.

    - str_strip_whitespace: quita espacios al inicio y al final de los textos.
    - extra="forbid": rechaza campos que no existen en el esquema (por ejemplo,
      enviar "valor" o "estado" al reservar para saltarse las reglas).
    """

    # Configuración que heredan todos los esquemas de entrada
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


# ---------------------------------------------------------------------------
# Paginación
# ---------------------------------------------------------------------------

# Parámetros de paginación que heredan todos los filtros de los listados
class PaginacionBase(BaseModel):
    """Parámetros de consulta comunes a todos los listados."""

    # Número de página: 1 por defecto, mínimo 1 (ge=1)
    pagina: int = Field(1, ge=1, description="Número de página, empieza en 1")
    # Registros por página: 10 por defecto, entre 1 y 100
    tamano: int = Field(10, ge=1, le=100, description="Registros por página (máximo 100)")


# Respuesta paginada; Generic[T] permite usarla como Pagina[UsuarioSalida], Pagina[MenuSalida], etc.
class Pagina(BaseModel, Generic[T]):
    """Respuesta de los listados paginados."""

    # Registros de la página actual
    items: list[T]
    # Total de registros (de todas las páginas)
    total: int
    # Página actual
    pagina: int
    # Registros por página
    tamano: int
    # Cantidad total de páginas
    paginas: int


# Arma el diccionario de una respuesta paginada
def armar_pagina(items: list[Any], total: int, filtros: PaginacionBase) -> dict:
    # Devuelve los registros junto con los datos de la paginación
    return {
        # Registros de esta página
        "items": items,
        # Total de registros
        "total": total,
        # Página pedida
        "pagina": filtros.pagina,
        # Tamaño de página pedido
        "tamano": filtros.tamano,
        # Páginas = total / tamaño, redondeado hacia arriba (ej.: 21 registros / 10 = 3 páginas)
        "paginas": ceil(total / filtros.tamano),
    }


# ---------------------------------------------------------------------------
# Respuestas genéricas
# ---------------------------------------------------------------------------

# Respuesta simple con un mensaje, por ejemplo al eliminar
class Mensaje(BaseModel):
    # Texto del mensaje
    mensaje: str


# Detalle de un campo inválido dentro de un error 422
class DetalleError(BaseModel):
    # Nombre del campo con error
    campo: str
    # Explicación del error en español
    mensaje: str


# Forma única de todas las respuestas de error
class ErrorRespuesta(BaseModel):
    """Estructura única de todas las respuestas de error de la API."""

    # Código HTTP (400, 401, 403, 404, 409, 422 o 500)
    estado: int = Field(description="Código de estado HTTP")
    # Mensaje claro en español
    mensaje: str
    # Lista de campos inválidos (solo en el error 422; en los demás es null)
    detalles: list[DetalleError] | None = None
