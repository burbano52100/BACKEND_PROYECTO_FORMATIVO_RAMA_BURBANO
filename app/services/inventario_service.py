"""Reglas de negocio del inventario: materiales, stock, kardex y mermas (RF28 a RF38)."""

# Tipos fecha y duración
from datetime import date, timedelta
# Decimal = número decimal exacto
from decimal import Decimal

# Sesión de base de datos
from sqlalchemy.orm import Session

# Fecha de hoy en Colombia
from app.core import tiempo
# Configuración (días de alerta y porcentaje crítico)
from app.core.config import settings
# Errores 409, 404 y 400
from app.core.excepciones import ConflictoError, NoEncontradoError, ReglaNegocioError
# Modelos de las tablas usadas
from app.models import Material, MovimientoInventario, Usuario
# Consultas del inventario
from app.repositories.inventario_repository import InventarioRepository
# Arma la respuesta paginada
from app.schemas.comunes import armar_pagina
# Esquemas del inventario
from app.schemas.inventario import (
    # Estados del stock
    EstadoStock,
    # Filtros del kardex
    FiltrosKardex,
    # Filtros de materiales
    FiltrosMaterial,
    # Entrada para editar
    MaterialActualizar,
    # Entrada para crear
    MaterialCrear,
    # Salida de un material
    MaterialSalida,
    # Entrada de un movimiento
    MovimientoCrear,
    # Tipos de movimiento
    TipoMovimiento,
)


# Da formato legible a una cantidad
def cantidad_legible(valor: Decimal) -> str:
    """0.500 -> 0.5 ; 9.000 -> 9"""
    # normalize quita los ceros sobrantes; "f" evita la notación científica (9E+0)
    return format(valor.normalize(), "f")


# Clase con las reglas del inventario
class InventarioService:
    # Constructor: recibe la sesión y crea el repositorio
    def __init__(self, db: Session) -> None:
        # Repositorio del inventario
        self.inventario = InventarioRepository(db)

    # ----- Materiales -----

    # Lista materiales con su estado
    def listar_materiales(self, filtros: FiltrosMaterial) -> dict:
        # Consulta (lista de (material, estado), total); * pasa los 2 parámetros de estado
        filas, total = self.inventario.listar_materiales(filtros, *self._parametros_estado())
        # Convierte cada fila en MaterialSalida y arma la página
        return armar_pagina([self._salida(material, estado) for material, estado in filas], total, filtros)

    # Consulta un material con su estado
    def obtener_material(self, material_id: int) -> MaterialSalida:
        # Busca el material y su estado
        fila = self.inventario.obtener_con_estado(material_id, *self._parametros_estado())
        # Si no existe...
        if fila is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un material con id {material_id}.")
        # Convierte (material, estado) en MaterialSalida
        return self._salida(*fila)

    # Crea un material
    def crear_material(self, datos: MaterialCrear, actor: Usuario) -> MaterialSalida:
        """El código de barras es único y el stock inicial genera una ENTRADA en el kardex (RF29)."""
        # Si el código de barras ya existe...
        if self.inventario.existe_codigo(datos.codigo_barras):
            # ...responde 409
            raise ConflictoError(f"Ya existe un material con el código de barras {datos.codigo_barras}.")
        # Crea el material: stock = stock inicial (el campo stock_inicial no existe en la tabla)
        material = Material(**datos.model_dump(exclude={"stock_inicial"}), stock=datos.stock_inicial, creado_por=actor.id)
        # Por defecto no hay movimiento
        movimiento = None
        # Si trae stock inicial...
        if datos.stock_inicial > 0:
            # ...crea la primera ENTRADA del kardex
            movimiento = MovimientoInventario(
                # Tipo ENTRADA
                tipo=TipoMovimiento.ENTRADA,
                # Cantidad = stock inicial
                cantidad=datos.stock_inicial,
                # Saldo = stock inicial
                saldo=datos.stock_inicial,
                # Motivo
                concepto="Stock inicial",
                # Responsable
                creado_por=actor.id,
            )
        # Guarda el material y su movimiento en una sola transacción
        material = self.inventario.crear_material(material, movimiento)
        # Devuelve el material con su estado calculado
        return self.obtener_material(material.id)

    # Edita un material
    def actualizar_material(self, material_id: int, datos: MaterialActualizar, actor: Usuario) -> MaterialSalida:
        # Busca el material activo (404 o 400)
        material = self._material_activo(material_id)
        # Recorre los campos enviados
        for campo, valor in datos.model_dump(exclude_none=True).items():
            # Asigna el nuevo valor
            setattr(material, campo, valor)
        # Auditoría
        material.actualizado_por = actor.id
        # Guarda
        self.inventario.guardar(material)
        # Devuelve el material con su estado
        return self.obtener_material(material.id)

    # Elimina un material (lógico o físico)
    def eliminar_material(self, material_id: int, actor: Usuario) -> str:
        """No se elimina si una receta activa lo usa (RF31). Con historial en el kardex o
        en recetas se desactiva (borrado lógico); si no, se borra definitivamente."""
        # Busca el material activo
        material = self._material_activo(material_id)
        # Nombres de las recetas activas que lo usan
        recetas = self.inventario.recetas_activas_que_usan(material.id)
        # Si alguna receta activa lo usa...
        if recetas:
            # ...responde 400 con hasta 3 nombres de ejemplo
            raise ReglaNegocioError(
                # Primera parte del mensaje
                f"No se puede eliminar {material.nombre}: se usa en {len(recetas)} receta(s) activa(s), "
                # Segunda parte: los primeros 3 nombres separados por coma
                f"por ejemplo {', '.join(recetas[:3])}."
            )
        # Guarda el nombre para el mensaje
        nombre = material.nombre
        # Si tiene movimientos o aparece en recetas (aunque estén inactivas)...
        if self.inventario.tiene_movimientos(material.id) or self.inventario.usado_en_recetas(material.id):
            # ...solo se desactiva
            material.activo = False
            # Auditoría
            material.actualizado_por = actor.id
            # Guarda
            self.inventario.guardar(material)
            # Mensaje de borrado lógico
            return f"{nombre} tiene historial en el kardex: se desactivó (borrado lógico)."
        # Si no tiene historial, se borra definitivamente
        self.inventario.eliminar(material)
        # Mensaje de borrado físico
        return f"{nombre} se eliminó definitivamente."

    # ----- Kardex -----

    # Registra una entrada, salida o merma
    def registrar_movimiento(self, datos: MovimientoCrear, actor: Usuario) -> MovimientoInventario:
        """Proceso de negocio: entrada, salida o merma (RF36, RF37).

        - Una salida o merma no puede dejar el stock en negativo.
        - El movimiento y el nuevo stock se guardan en una sola transacción.
        """
        # Lee el material bloqueando su fila (evita que dos salidas a la vez dejen el stock negativo)
        material = self.inventario.obtener_para_actualizar(datos.material_id)
        # Si no existe...
        if material is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un material con id {datos.material_id}.")
        # Si está inactivo...
        if not material.activo:
            # ...responde 400
            raise ReglaNegocioError(f"{material.nombre} está inactivo.")

        # Si es una ENTRADA...
        if datos.tipo == TipoMovimiento.ENTRADA:
            # ...suma al stock
            nuevo_stock = material.stock + datos.cantidad
        # Si es SALIDA o MERMA...
        else:
            # ...y la cantidad es mayor que el stock...
            if datos.cantidad > material.stock:
                # ...responde 400
                raise ReglaNegocioError(
                    # Mensaje con lo disponible...
                    f"Stock insuficiente de {material.nombre}: disponible {cantidad_legible(material.stock)} "
                    # ...y lo solicitado
                    f"{material.unidad_medida}, solicitado {cantidad_legible(datos.cantidad)}."
                )
            # Resta del stock
            nuevo_stock = material.stock - datos.cantidad

        # Actualiza el stock del material
        material.stock = nuevo_stock
        # Auditoría
        material.actualizado_por = actor.id
        # Crea la fila del kardex
        movimiento = MovimientoInventario(
            # Material
            material_id=material.id,
            # Tipo
            tipo=datos.tipo,
            # Cantidad
            cantidad=datos.cantidad,
            # Saldo después del movimiento
            saldo=nuevo_stock,
            # Motivo
            concepto=datos.concepto,
            # Responsable
            creado_por=actor.id,
        )
        # Guarda el movimiento y el nuevo stock juntos
        return self.inventario.registrar_movimiento(movimiento)

    # Lista el kardex
    def kardex(self, filtros: FiltrosKardex) -> dict:
        # Consulta (movimientos, total)
        items, total = self.inventario.listar_kardex(filtros)
        # Respuesta paginada
        return armar_pagina(items, total, filtros)

    # ----- Métodos internos -----

    # Busca un material y verifica que esté activo
    def _material_activo(self, material_id: int) -> Material:
        # Busca por id
        material = self.inventario.obtener_material(material_id)
        # Si no existe...
        if material is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un material con id {material_id}.")
        # Si está inactivo...
        if not material.activo:
            # ...responde 400
            raise ReglaNegocioError(f"{material.nombre} está inactivo.")
        # Devuelve el material
        return material

    # Método estático: no usa datos del objeto
    @staticmethod
    # Calcula los dos parámetros que necesita el CASE del estado del stock
    def _parametros_estado() -> tuple[date, Decimal]:
        """Umbrales de la configuración (RF39): días de alerta y porcentaje crítico."""
        # Fecha límite: hoy + días de alerta (7 por defecto)
        limite_vencimiento = tiempo.hoy() + timedelta(days=settings.DIAS_ALERTA_VENCIMIENTO)
        # Factor crítico: 50 % -> 0.5
        factor_critico = Decimal(settings.PORCENTAJE_STOCK_CRITICO) / 100
        # Devuelve los dos valores
        return limite_vencimiento, factor_critico

    # Método estático
    @staticmethod
    # Convierte (material, estado) en MaterialSalida
    def _salida(material: Material, estado: str) -> MaterialSalida:
        # Crea el esquema desde el modelo y le agrega el estado calculado
        return MaterialSalida.model_validate(material).model_copy(update={"estado_stock": EstadoStock(estado)})
