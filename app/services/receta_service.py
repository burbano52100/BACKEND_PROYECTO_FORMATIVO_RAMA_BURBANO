"""Reglas de negocio de recetas: fórmula, costo de producción y margen (RF33, RF34)."""

# Decimal = número decimal exacto
from decimal import Decimal

# Sesión de base de datos
from sqlalchemy.orm import Session

# Errores 409, 404 y 400
from app.core.excepciones import ConflictoError, NoEncontradoError, ReglaNegocioError
# Modelos de las tablas usadas
from app.models import Receta, RecetaIngrediente, Usuario
# Consultas del inventario (para validar los ingredientes)
from app.repositories.inventario_repository import InventarioRepository
# Consultas de recetas
from app.repositories.receta_repository import RecetaRepository
# Arma la respuesta paginada
from app.schemas.comunes import armar_pagina
# Esquemas de recetas
from app.schemas.receta import FiltrosReceta, IngredienteEntrada, RecetaActualizar, RecetaCrear

# Precisión de 2 decimales (centavos) para redondear el dinero
CENTAVOS = Decimal("0.01")


# Clase con las reglas de recetas
class RecetaService:
    # Constructor: recibe la sesión y crea los repositorios
    def __init__(self, db: Session) -> None:
        # Repositorio de recetas
        self.recetas = RecetaRepository(db)
        # Repositorio del inventario
        self.inventario = InventarioRepository(db)

    # Lista recetas con su costo
    def listar(self, filtros: FiltrosReceta) -> dict:
        # Consulta (recetas, total)
        items, total = self.recetas.listar(filtros)
        # Calcula los costos de cada receta y arma la página
        return armar_pagina([self._con_costos(receta) for receta in items], total, filtros)

    # Consulta una receta con su costo
    def obtener(self, receta_id: int) -> dict:
        # Busca la receta (404 si no existe) y calcula sus costos
        return self._con_costos(self._obtener(receta_id))

    # Crea una receta
    def crear(self, datos: RecetaCrear, actor: Usuario) -> dict:
        # Si ya existe una receta con ese nombre...
        if self.recetas.existe_nombre(datos.nombre):
            # ...responde 409
            raise ConflictoError(f"Ya existe una receta llamada '{datos.nombre}'.")
        # Crea la receta
        receta = Receta(
            # Nombre, descripción y precio
            **datos.model_dump(exclude={"ingredientes"}),
            # Ingredientes validados contra el inventario
            ingredientes=self._armar_ingredientes(datos.ingredientes),
            # Auditoría
            creado_por=actor.id,
        )
        # Guarda y devuelve la receta con sus costos
        return self._con_costos(self.recetas.guardar(receta))

    # Actualiza una receta
    def actualizar(self, receta_id: int, datos: RecetaActualizar, actor: Usuario) -> dict:
        # Busca la receta (404 si no existe)
        receta = self._obtener(receta_id)
        # Campos enviados, sin los ingredientes (se tratan aparte)
        cambios = datos.model_dump(exclude_none=True, exclude={"ingredientes"})
        # Si cambia el nombre y otro registro ya lo usa...
        if "nombre" in cambios and self.recetas.existe_nombre(cambios["nombre"], excluir_id=receta.id):
            # ...responde 409
            raise ConflictoError(f"Ya existe una receta llamada '{cambios['nombre']}'.")
        # Si se enviaron ingredientes...
        if datos.ingredientes is not None:
            # ...reemplaza toda la fórmula
            self.recetas.reemplazar_ingredientes(receta, self._armar_ingredientes(datos.ingredientes))
        # Copia los demás cambios
        for campo, valor in cambios.items():
            # Asigna el valor
            setattr(receta, campo, valor)
        # Auditoría
        receta.actualizado_por = actor.id
        # Guarda y devuelve la receta con sus costos
        return self._con_costos(self.recetas.guardar(receta))

    # Elimina una receta
    def eliminar(self, receta_id: int) -> str:
        """Las recetas no tienen movimientos asociados: se borran con su fórmula."""
        # Busca la receta (404 si no existe)
        receta = self._obtener(receta_id)
        # Guarda el nombre para el mensaje
        nombre = receta.nombre
        # Borra la receta (y sus ingredientes en cascada)
        self.recetas.eliminar(receta)
        # Mensaje de confirmación
        return f"La receta '{nombre}' se eliminó definitivamente."

    # ----- Métodos internos -----

    # Busca una receta o responde 404
    def _obtener(self, receta_id: int) -> Receta:
        # Busca por id
        receta = self.recetas.obtener_por_id(receta_id)
        # Si no existe...
        if receta is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe una receta con id {receta_id}.")
        # Devuelve la receta
        return receta

    # Convierte los ingredientes enviados en objetos RecetaIngrediente
    def _armar_ingredientes(self, ingredientes: list[IngredienteEntrada]) -> list[RecetaIngrediente]:
        """Los ingredientes se eligen del inventario: deben existir (404) y estar activos (400)."""
        # Lista donde se acumulan los ingredientes válidos
        resultado = []
        # Recorre cada ingrediente enviado
        for ingrediente in ingredientes:
            # Busca el material en el inventario
            material = self.inventario.obtener_material(ingrediente.material_id)
            # Si no existe...
            if material is None:
                # ...responde 404
                raise NoEncontradoError(f"No existe un material con id {ingrediente.material_id}.")
            # Si está inactivo...
            if not material.activo:
                # ...responde 400
                raise ReglaNegocioError(f"El material {material.nombre} está inactivo.")
            # Agrega el ingrediente con su material y cantidad
            resultado.append(RecetaIngrediente(material=material, cantidad=ingrediente.cantidad))
        # Devuelve la lista
        return resultado

    # Método estático: no usa datos del objeto
    @staticmethod
    # Calcula el costo de producción y el margen de una receta
    def _con_costos(receta: Receta) -> dict:
        """Cálculo de negocio (RF34):
        costo de cada ingrediente = cantidad x costo unitario
        costo de producción = suma de los ingredientes
        margen = precio de venta - costo (también en porcentaje)."""
        # Lista de ingredientes con su costo
        ingredientes = []
        # Acumulador del costo total (empieza en 0)
        costo_produccion = Decimal(0)
        # Recorre los ingredientes de la receta
        for ingrediente in receta.ingredientes:
            # Costo = cantidad x costo unitario, redondeado a centavos
            costo = (ingrediente.cantidad * ingrediente.material.costo_unitario).quantize(CENTAVOS)
            # Suma al costo total
            costo_produccion += costo
            # Agrega el ingrediente con su desglose
            ingredientes.append({
                # Material
                "material": ingrediente.material,
                # Cantidad por plato
                "cantidad": ingrediente.cantidad,
                # Costo unitario del material
                "costo_unitario": ingrediente.material.costo_unitario,
                # Costo de este ingrediente
                "costo": costo,
            })
        # Margen = precio de venta - costo de producción
        margen = receta.precio_venta - costo_produccion
        # Devuelve la receta con los cálculos (forma de RecetaSalida)
        return {
            # Id
            "id": receta.id,
            # Nombre
            "nombre": receta.nombre,
            # Descripción
            "descripcion": receta.descripcion,
            # Precio de venta
            "precio_venta": receta.precio_venta,
            # Si está activa
            "activo": receta.activo,
            # Ingredientes con costo
            "ingredientes": ingredientes,
            # Costo total
            "costo_produccion": costo_produccion,
            # Margen en pesos
            "margen": margen,
            # Margen en porcentaje con 2 decimales
            "margen_porcentaje": float((margen / receta.precio_venta * 100).quantize(CENTAVOS)),
            # True si el margen es negativo
            "alerta_margen_negativo": margen < 0,
        }
