"""Modelos ORM: cada clase representa una tabla del esquema gastrosena."""

# Clase base de todos los modelos
from app.models.base import Base
# Tabla fichas
from app.models.ficha import Ficha
# Tablas materiales y movimientos_inventario (kardex)
from app.models.inventario import Material, MovimientoInventario
# Tabla menus
from app.models.menu import Menu
# Tablas recetas y receta_ingredientes
from app.models.receta import Receta, RecetaIngrediente
# Tablas pagos_instructor y reservas
from app.models.reserva import PagoInstructor, Reserva
# Tabla sugerencias
from app.models.sugerencia import Sugerencia
# Tablas roles y usuarios
from app.models.usuario import Rol, Usuario

# __all__ lista lo que se exporta al escribir "from app.models import ..."
__all__ = [
    # Base y modelos de la A a la M
    "Base", "Ficha", "Material", "Menu", "MovimientoInventario", "PagoInstructor",
    # Modelos de la R a la U
    "Receta", "RecetaIngrediente", "Reserva", "Rol", "Sugerencia", "Usuario",
]
