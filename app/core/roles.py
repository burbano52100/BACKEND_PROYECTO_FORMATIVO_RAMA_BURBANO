"""Nombres de los roles tal como están guardados en la tabla roles."""

# StrEnum crea una enumeración cuyos valores también se comportan como texto (str)
from enum import StrEnum


# Lista cerrada de los 4 roles del sistema; evita escribir los nombres a mano (y equivocarse)
class Roles(StrEnum):
    # Responsable del servicio y administrador del sistema
    ENCARGADO = "encargado"
    # Docente que consume almuerzos y paga con una cuenta mensual
    INSTRUCTOR = "instructor"
    # Estudiante que reserva su almuerzo
    APRENDIZ = "aprendiz"
    # Visitante externo que compra el almuerzo
    INVITADO = "invitado"
