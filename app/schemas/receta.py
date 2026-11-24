# Esquemas de las recetas
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# Optional quiere decir que el campo puede venir vacío (None)
from typing import Optional

# BaseModel es la clase base y Field sirve para poner reglas
from pydantic import BaseModel, Field


# Un ingrediente de la receta
class ingrediente_datos(BaseModel):
    # Id del material que se usa
    material_id: int = Field(gt=0)
    # Cuánto se usa en un plato (más de 0)
    cantidad: float = Field(gt=0)


# Datos para crear una receta
class receta_crear(BaseModel):
    # Nombre del plato
    nombre: str = Field(min_length=3, max_length=100)
    # Descripción (opcional)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    # Precio de venta (más de 0)
    precio_venta: float = Field(gt=0)
    # Lista de ingredientes (una receta necesita por lo menos uno)
    ingredientes: list[ingrediente_datos] = Field(min_length=1)


# Datos para actualizar una receta (todo opcional)
class receta_actualizar(BaseModel):
    # Nombre nuevo
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    # Descripción nueva
    descripcion: Optional[str] = Field(default=None, max_length=500)
    # Precio nuevo
    precio_venta: Optional[float] = Field(default=None, gt=0)
    # Activar o desactivar
    activo: Optional[bool] = None
    # Si se mandan ingredientes, se cambian todos los anteriores por estos
    ingredientes: Optional[list[ingrediente_datos]] = Field(default=None, min_length=1)
