"""Excepciones de la aplicación.

Los servicios lanzan estas excepciones cuando se incumple una regla. No conocen
HTTP: core/errores.py traduce cada una al código de estado que corresponde.
"""


# Clase padre de todos los errores controlados; hereda de Exception (error normal de Python)
class ErrorAplicacion(Exception):
    """Base de todos los errores controlados de la API."""

    # Constructor: recibe el mensaje en español que verá el usuario
    def __init__(self, mensaje: str) -> None:
        # Llama al constructor de Exception para que el error funcione como cualquier excepción
        super().__init__(mensaje)
        # Guarda el mensaje para que core/errores.py lo ponga en la respuesta JSON
        self.mensaje = mensaje


# Hereda de ErrorAplicacion; se usa cuando no se cumple una regla del negocio
class ReglaNegocioError(ErrorAplicacion):
    """Se incumple una regla de negocio (400)."""


# Se usa cuando no se sabe quién es el usuario (sin token, token falso o vencido)
class NoAutenticadoError(ErrorAplicacion):
    """Credenciales incorrectas o token ausente, inválido o vencido (401)."""


# Se usa cuando se sabe quién es el usuario, pero su rol no puede hacer la operación
class PermisoDenegadoError(ErrorAplicacion):
    """El usuario se identificó, pero no puede hacer la operación (403)."""


# Se usa cuando se busca un registro que no existe
class NoEncontradoError(ErrorAplicacion):
    """El registro buscado o relacionado no existe (404)."""


# Se usa cuando se intenta guardar un valor que ya existe y debe ser único
class ConflictoError(ErrorAplicacion):
    """Ya existe un registro con un valor que debe ser único (409)."""
