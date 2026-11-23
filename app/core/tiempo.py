# En este archivo están las funciones que tienen que ver con la hora

# datetime es la fecha y hora actual
from datetime import datetime

# Traigo el horario en el que se puede reservar
from app.core.config import hora_apertura, hora_cierre


# Función que dice si ahora se puede reservar o cancelar
def esta_en_horario():
    # Saco la hora de ahora (solo la hora, de 0 a 23)
    hora_actual = datetime.now().hour
    # Si la hora está entre la apertura y el cierre
    if hora_apertura <= hora_actual < hora_cierre:
        # Sí se puede
        return True
    # Si no, no se puede
    return False
