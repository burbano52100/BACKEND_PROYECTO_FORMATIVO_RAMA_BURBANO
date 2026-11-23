# Esquemas de las reservas
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# BaseModel es la clase base
from pydantic import BaseModel


# Datos para reservar (el precio lo calcula la API, no se manda)
class reserva_crear(BaseModel):
    # Id del menú que se quiere reservar
    menu_id: int


# Datos para marcar el pago de una reserva
class pago_reserva_datos(BaseModel):
    # PAGADO o NO_PAGADO
    estado: str
