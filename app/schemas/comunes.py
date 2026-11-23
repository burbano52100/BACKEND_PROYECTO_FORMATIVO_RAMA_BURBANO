# Esquemas que se usan en varios módulos

# BaseModel es la clase base de los esquemas
from pydantic import BaseModel


# Lo que se responde cuando solo hay que mandar un mensaje (por ejemplo al eliminar algo)
class mensaje_respuesta(BaseModel):
    # El mensaje para el usuario
    mensaje: str
