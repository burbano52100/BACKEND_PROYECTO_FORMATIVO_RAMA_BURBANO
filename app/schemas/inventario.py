# Esquemas del inventario
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# date es una fecha
from datetime import date
# Optional quiere decir que el campo puede venir vacío (None)
from typing import Optional

# BaseModel es la clase base y Field sirve para poner reglas
from pydantic import BaseModel, Field


# Datos para crear un material
class material_crear(BaseModel):
    # Código de barras de 8 a 14 números
    codigo_barras: str = Field(min_length=8, max_length=14)
    # Nombre del material
    nombre: str = Field(min_length=2, max_length=100)
    # Categoría: PROTEINA, GRANO, VERDURA, FRUTA, LACTEO, ABARROTE o DESECHABLE
    categoria: str
    # Unidad: KG, G, L, ML o UND
    unidad_medida: str
    # Costo de una unidad (más de 0)
    costo_unitario: float = Field(gt=0)
    # Con cuánto empieza el inventario
    stock_inicial: float = Field(default=0, ge=0)
    # Cantidad mínima que debería haber
    stock_minimo: float = Field(default=0, ge=0)
    # Fecha de vencimiento (opcional)
    fecha_vencimiento: Optional[date] = None


# Datos para actualizar un material (el stock no se cambia aquí, solo con movimientos)
class material_actualizar(BaseModel):
    # Nombre nuevo
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    # Categoría nueva
    categoria: Optional[str] = None
    # Costo nuevo
    costo_unitario: Optional[float] = Field(default=None, gt=0)
    # Stock mínimo nuevo
    stock_minimo: Optional[float] = Field(default=None, ge=0)
    # Fecha de vencimiento nueva
    fecha_vencimiento: Optional[date] = None


# Datos para hacer una entrada, salida o merma
class movimiento_crear(BaseModel):
    # Id del material
    material_id: int
    # ENTRADA, SALIDA o MERMA
    tipo: str
    # Cantidad (más de 0)
    cantidad: float = Field(gt=0)
    # Por qué se hace el movimiento
    concepto: str = Field(min_length=3, max_length=255)
