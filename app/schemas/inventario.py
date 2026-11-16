"""Esquemas del inventario: materiales y kardex."""

# Tipos fecha y fecha-hora
from datetime import date, datetime
# Decimal = número decimal exacto
from decimal import Decimal
# Lista cerrada de valores de texto
from enum import StrEnum

# Herramientas de Pydantic
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

# Tipos reutilizables
from app.schemas.comunes import (
    # Cantidad mayor que 0 con hasta 3 decimales
    Cantidad,
    # Dinero de salida (número en el JSON)
    Dinero,
    # Esquema base de entrada
    EsquemaEntrada,
    # Fecha de hoy en adelante
    FechaNoPasada,
    # Cantidad de salida (número en el JSON)
    Medida,
    # Paginación
    PaginacionBase,
    # Valor monetario mayor que 0
    Valor,
)
# Resumen del usuario (responsable de cada movimiento)
from app.schemas.usuario import UsuarioResumen


# Categorías de material
class Categoria(StrEnum):
    # Carnes, pollo, huevo...
    PROTEINA = "PROTEINA"
    # Arroz, fríjol, lenteja...
    GRANO = "GRANO"
    # Papa, tomate, cebolla...
    VERDURA = "VERDURA"
    # Plátano...
    FRUTA = "FRUTA"
    # Leche...
    LACTEO = "LACTEO"
    # Aceite, sal...
    ABARROTE = "ABARROTE"
    # Bandejas, cubiertos...
    DESECHABLE = "DESECHABLE"


# Unidades de medida
class UnidadMedida(StrEnum):
    # Kilogramo
    KG = "KG"
    # Gramo
    G = "G"
    # Litro
    L = "L"
    # Mililitro
    ML = "ML"
    # Unidad
    UND = "UND"


# Estados del stock (los calcula PostgreSQL)
class EstadoStock(StrEnum):
    # Stock por encima del mínimo
    BUENO = "BUENO"
    # Stock menor o igual al mínimo
    BAJO = "BAJO"
    # Stock menor o igual al 50 % del mínimo
    CRITICO = "CRITICO"
    # Vence en 7 días o menos
    VENCIENDO = "VENCIENDO"


# Tipos de movimiento del kardex
class TipoMovimiento(StrEnum):
    # Suma al stock
    ENTRADA = "ENTRADA"
    # Resta del stock (uso en cocina)
    SALIDA = "SALIDA"
    # Resta del stock (pérdida: dañado o vencido)
    MERMA = "MERMA"


# Datos para crear un material (POST /inventario/materiales)
class MaterialCrear(EsquemaEntrada):
    # Código de barras de 8 a 14 dígitos
    codigo_barras: str = Field(pattern=r"^[0-9]{8,14}$", description="Código de barras de 8 a 14 dígitos")
    # Nombre: 2 a 100 caracteres
    nombre: str = Field(min_length=2, max_length=100)
    # Una de las categorías
    categoria: Categoria
    # Una de las unidades
    unidad_medida: UnidadMedida
    # Costo mayor que 0
    costo_unitario: Valor = Field(description="Costo por unidad de medida")
    # Stock inicial (0 por defecto); si es mayor que 0 genera una ENTRADA en el kardex
    stock_inicial: Decimal = Field(Decimal(0), ge=0, le=99999, max_digits=12, decimal_places=3,
                                   description="Genera una ENTRADA en el kardex (RF29)")  # Texto de ayuda en Swagger
    # Stock mínimo (0 por defecto)
    stock_minimo: Decimal = Field(Decimal(0), ge=0, le=99999, max_digits=12, decimal_places=3)
    # Fecha de vencimiento opcional (no puede ser pasada)
    fecha_vencimiento: FechaNoPasada | None = None


# Datos para editar un material (todos opcionales)
class MaterialActualizar(EsquemaEntrada):
    """El stock no se edita aquí: solo cambia con movimientos del kardex (RF30)."""

    # Nuevo nombre
    nombre: str | None = Field(None, min_length=2, max_length=100)
    # Nueva categoría
    categoria: Categoria | None = None
    # Nuevo costo
    costo_unitario: Valor | None = None
    # Nuevo mínimo
    stock_minimo: Decimal | None = Field(None, ge=0, le=99999, max_digits=12, decimal_places=3)
    # Nueva fecha de vencimiento
    fecha_vencimiento: FechaNoPasada | None = None


# Datos mínimos de un material (se usan dentro del kardex y de las recetas)
class MaterialResumen(BaseModel):
    # Permite crear el esquema desde el modelo Material
    model_config = ConfigDict(from_attributes=True)

    # Id
    id: int
    # Código de barras
    codigo_barras: str
    # Nombre
    nombre: str
    # Unidad de medida
    unidad_medida: str


# Respuesta completa de un material
class MaterialSalida(BaseModel):
    # Permite crear el esquema desde el modelo Material
    model_config = ConfigDict(from_attributes=True)

    # Id
    id: int
    # Código de barras
    codigo_barras: str
    # Nombre
    nombre: str
    # Categoría
    categoria: str
    # Unidad
    unidad_medida: str
    # Costo unitario
    costo_unitario: Dinero
    # Stock actual
    stock: Medida
    # Stock mínimo
    stock_minimo: Medida
    # Vencimiento
    fecha_vencimiento: date | None
    # Estado calculado (BUENO, BAJO, CRITICO o VENCIENDO); lo agrega el servicio
    estado_stock: EstadoStock | None = None
    # Si está activo
    activo: bool
    # Cuándo se creó
    creado_en: datetime
    # Cuándo se modificó
    actualizado_en: datetime | None


# Filtros de GET /inventario/materiales (más pagina y tamano heredados)
class FiltrosMaterial(PaginacionBase):
    # Busca por nombre o código de barras
    buscar: str | None = Field(None, description="Nombre o código de barras (RF28)")
    # Filtra por categoría
    categoria: Categoria | None = None
    # Filtra por estado del stock
    estado: EstadoStock | None = None
    # Por defecto solo los activos
    activo: bool = True


# Datos para registrar un movimiento (POST /inventario/movimientos)
class MovimientoCrear(EsquemaEntrada):
    # Id del material (mayor que 0)
    material_id: int = Field(gt=0)
    # ENTRADA, SALIDA o MERMA
    tipo: TipoMovimiento
    # Cantidad mayor que 0
    cantidad: Cantidad
    # Motivo obligatorio: 3 a 255 caracteres
    concepto: str = Field(min_length=3, max_length=255, description="Motivo; en una MERMA es la razón detallada")


# Cómo se muestra una fila del kardex
class MovimientoSalida(BaseModel):
    # Permite crear el esquema desde el modelo MovimientoInventario
    model_config = ConfigDict(from_attributes=True)

    # Id del movimiento
    id: int
    # Material resumido
    material: MaterialResumen
    # Tipo de movimiento
    tipo: str
    # Cantidad
    cantidad: Medida
    # Saldo después del movimiento
    saldo: Medida
    # Motivo
    concepto: str
    # Usuario que lo registró
    responsable: UsuarioResumen
    # Fecha y hora
    creado_en: datetime

    # Campo calculado: columna "entrada" del kardex
    @computed_field
    # Se usa como atributo
    @property
    # Cantidad que entró
    def entrada(self) -> float:
        # Si es ENTRADA muestra la cantidad; si no, 0
        return float(self.cantidad) if self.tipo == TipoMovimiento.ENTRADA else 0.0

    # Campo calculado: columna "salida" del kardex
    @computed_field
    # Se usa como atributo
    @property
    # Cantidad que salió
    def salida(self) -> float:
        # Si es ENTRADA muestra 0; si es SALIDA o MERMA, la cantidad
        return 0.0 if self.tipo == TipoMovimiento.ENTRADA else float(self.cantidad)


# Filtros de GET /inventario/kardex (más pagina y tamano heredados)
class FiltrosKardex(PaginacionBase):
    # Filtra por material
    material_id: int | None = None
    # Filtra por tipo (MERMA = historial de mermas)
    tipo: TipoMovimiento | None = None
    # Desde esta fecha
    desde: date | None = None
    # Hasta esta fecha
    hasta: date | None = None

    # Validación que revisa varios campos juntos
    @model_validator(mode="after")
    # Revisa que el rango de fechas tenga sentido
    def validar_rango(self) -> "FiltrosKardex":
        # Si "desde" es posterior a "hasta"...
        if self.desde and self.hasta and self.desde > self.hasta:
            # ...error 422
            raise ValueError("La fecha 'desde' no puede ser posterior a la fecha 'hasta'.")
        # Rango válido
        return self
