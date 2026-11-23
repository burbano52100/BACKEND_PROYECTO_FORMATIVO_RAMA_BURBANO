# Esquemas de la cartera de los instructores
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# Optional quiere decir que el campo puede venir vacío (None)
from typing import Optional

# BaseModel es la clase base y Field sirve para poner reglas
from pydantic import BaseModel, Field


# Datos para registrar un pago de un instructor
class pago_crear(BaseModel):
    # Cuánto paga (más de 0)
    valor: float = Field(gt=0)
    # Cómo paga: EFECTIVO, TRANSFERENCIA o NOMINA
    metodo: str
    # Una nota (opcional)
    observacion: Optional[str] = Field(default=None, max_length=255)
