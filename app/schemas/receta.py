"""Esquemas de recetas y su costo de producción."""

# Annotated agrega reglas a un tipo
from typing import Annotated

# Herramientas de Pydantic
from pydantic import AfterValidator, BaseModel, Field

# Tipos reutilizables
from app.schemas.comunes import Cantidad, Dinero, EsquemaEntrada, Medida, PaginacionBase, Valor
# Resumen del material (para mostrarlo en cada ingrediente)
from app.schemas.inventario import MaterialResumen


# Un ingrediente de la receta, tal como lo envía el cliente
class IngredienteEntrada(EsquemaEntrada):
    # Id del material del inventario
    material_id: int = Field(gt=0)
    # Cantidad por plato (mayor que 0)
    cantidad: Cantidad = Field(description="Cantidad por plato, en la unidad del material")


# Revisa que no se repita el mismo material en la lista de ingredientes
def _sin_repetidos(ingredientes: list[IngredienteEntrada]) -> list[IngredienteEntrada]:
    # Saca la lista de ids de material
    ids = [ingrediente.material_id for ingrediente in ingredientes]
    # set() quita los repetidos; si cambia el tamaño, había repetidos
    if len(ids) != len(set(ids)):
        # Error 422
        raise ValueError("Un material no puede repetirse en la misma receta.")
    # Lista válida
    return ingredientes


# Tipo lista de ingredientes: entre 1 y 30, sin repetidos
Ingredientes = Annotated[list[IngredienteEntrada], Field(min_length=1, max_length=30), AfterValidator(_sin_repetidos)]


# Datos para crear una receta (POST /recetas)
class RecetaCrear(EsquemaEntrada):
    # Nombre: 3 a 100 caracteres
    nombre: str = Field(min_length=3, max_length=100)
    # Descripción opcional
    descripcion: str | None = Field(None, max_length=500)
    # Precio de venta mayor que 0
    precio_venta: Valor
    # Fórmula del plato
    ingredientes: Ingredientes


# Datos para actualizar una receta (todos opcionales)
class RecetaActualizar(EsquemaEntrada):
    """Si se envían ingredientes, reemplazan la fórmula completa."""

    # Nuevo nombre
    nombre: str | None = Field(None, min_length=3, max_length=100)
    # Nueva descripción
    descripcion: str | None = Field(None, max_length=500)
    # Nuevo precio
    precio_venta: Valor | None = None
    # Nueva fórmula completa
    ingredientes: Ingredientes | None = None
    # Activar o desactivar la receta
    activo: bool | None = None


# Cómo se muestra cada ingrediente, con su costo
class IngredienteSalida(BaseModel):
    # Material resumido
    material: MaterialResumen
    # Cantidad por plato
    cantidad: Medida
    # Costo de una unidad del material
    costo_unitario: Dinero
    # cantidad x costo_unitario
    costo: Dinero


# Cómo se muestra una receta con el cálculo de costos
class RecetaSalida(BaseModel):
    # Id
    id: int
    # Nombre
    nombre: str
    # Descripción
    descripcion: str | None
    # Precio de venta
    precio_venta: Dinero
    # Si está activa
    activo: bool
    # Ingredientes con su costo
    ingredientes: list[IngredienteSalida]
    # Suma de los costos de los ingredientes
    costo_produccion: Dinero
    # precio_venta - costo_produccion
    margen: Dinero
    # margen / precio_venta x 100
    margen_porcentaje: float
    # True si el plato cuesta más de lo que se vende
    alerta_margen_negativo: bool


# Filtros de GET /recetas (más pagina y tamano heredados)
class FiltrosReceta(PaginacionBase):
    # Busca por nombre
    buscar: str | None = None
    # Por defecto solo las activas
    activo: bool = True
