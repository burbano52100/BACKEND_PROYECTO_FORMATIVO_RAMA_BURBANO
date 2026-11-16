"""Esquemas del Menú del Día."""

# Tipo fecha
from datetime import date

# computed_field = campo calculado; model_validator = validación que revisa varios campos juntos
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

# Tipos reutilizables
from app.schemas.comunes import Dinero, EsquemaEntrada, FechaNoPasada, PaginacionBase, PrecioMenu


# Datos para crear un menú (POST /menus)
class MenuCrear(EsquemaEntrada):
    # Fecha de hoy en adelante
    fecha: FechaNoPasada
    # Nombre: 3 a 100 caracteres
    nombre: str = Field(min_length=3, max_length=100)
    # Descripción: 3 a 500 caracteres
    descripcion: str = Field(min_length=3, max_length=500)
    # Precio mayor o igual que 0
    precio_aprendiz: PrecioMenu = Field(description="Precio para aprendices e instructores (por ejemplo 5000)")
    # Precio mayor o igual que 0
    precio_invitado: PrecioMenu = Field(description="Precio para invitados (por ejemplo 8000)")
    # Cupo entre 1 y 1000
    cantidad_total: int = Field(gt=0, le=1000, description="Cupo de almuerzos disponibles")


# Datos para actualizar un menú (todos opcionales)
class MenuActualizar(EsquemaEntrada):
    """La fecha no se puede cambiar; los demás campos son opcionales."""

    # Nuevo nombre
    nombre: str | None = Field(None, min_length=3, max_length=100)
    # Nueva descripción
    descripcion: str | None = Field(None, min_length=3, max_length=500)
    # Nuevo precio de aprendiz
    precio_aprendiz: PrecioMenu | None = None
    # Nuevo precio de invitado
    precio_invitado: PrecioMenu | None = None
    # Nuevo cupo
    cantidad_total: int | None = Field(None, gt=0, le=1000)


# Datos mínimos de un menú (se usan dentro de la reserva)
class MenuResumen(BaseModel):
    # Permite crear el esquema desde el modelo Menu
    model_config = ConfigDict(from_attributes=True)

    # Id del menú
    id: int
    # Fecha del menú
    fecha: date
    # Nombre del plato
    nombre: str


# Respuesta completa de un menú
class MenuSalida(BaseModel):
    # Permite crear el esquema desde el modelo Menu
    model_config = ConfigDict(from_attributes=True)

    # Id
    id: int
    # Fecha
    fecha: date
    # Nombre
    nombre: str
    # Descripción
    descripcion: str
    # Precio de aprendiz
    precio_aprendiz: Dinero
    # Precio de invitado
    precio_invitado: Dinero
    # Cupo total
    cantidad_total: int
    # Cupo restante
    cantidad_disponible: int
    # Si está activo
    activo: bool

    # Campo calculado que aparece en el JSON aunque no exista en la tabla
    @computed_field
    # @property: se usa como atributo (menu.vendidos)
    @property
    # Calcula cuántos almuerzos se han vendido
    def vendidos(self) -> int:
        """Almuerzos reservados o comprados (RF15)."""
        # Vendidos = cupo total - cupo restante
        return self.cantidad_total - self.cantidad_disponible

    # Otro campo calculado
    @computed_field
    # Se usa como atributo (menu.agotado)
    @property
    # Indica si ya no hay cupo
    def agotado(self) -> bool:
        # True cuando no queda cupo
        return self.cantidad_disponible == 0


# Reserva propia que se muestra dentro del menú (para saber si ya reservé)
class MiReserva(BaseModel):
    # Permite crear el esquema desde el modelo Reserva
    model_config = ConfigDict(from_attributes=True)

    # Id de la reserva
    id: int
    # Estado de la reserva
    estado: str
    # Valor de la reserva
    valor: Dinero


# Menú para quien va a comer: hereda todo MenuSalida y agrega 2 campos
class MenuParaComensal(MenuSalida):
    """Menú con el precio que le corresponde a quien consulta (RF08)."""

    # Precio según el rol de quien consulta (null para el encargado)
    precio_para_mi: Dinero | None = None
    # Su reserva vigente para este menú (null si no ha reservado)
    mi_reserva: MiReserva | None = None


# Filtros de GET /menus (más pagina y tamano heredados)
class FiltrosMenu(PaginacionBase):
    # Desde esta fecha
    desde: date | None = None
    # Hasta esta fecha
    hasta: date | None = None
    # Filtra por estado
    activo: bool | None = None

    # Validación que se ejecuta después de validar cada campo por separado
    @model_validator(mode="after")
    # Revisa que el rango de fechas tenga sentido
    def validar_rango(self) -> "FiltrosMenu":
        # Si llegaron las dos fechas y "desde" es posterior a "hasta"...
        if self.desde and self.hasta and self.desde > self.hasta:
            # ...error 422
            raise ValueError("La fecha 'desde' no puede ser posterior a la fecha 'hasta'.")
        # Si está bien, devuelve el mismo objeto
        return self
