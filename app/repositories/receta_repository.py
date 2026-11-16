"""Acceso a datos de recetas."""

# Funciones para armar consultas SQL
from sqlalchemy import exists, func, select
# Sesión de base de datos
from sqlalchemy.orm import Session

# Modelos de las tablas recetas y receta_ingredientes
from app.models import Receta, RecetaIngrediente
# Función para paginar
from app.repositories.paginacion import paginar
# Filtros del listado de recetas
from app.schemas.receta import FiltrosReceta


# Clase con todas las consultas de recetas
class RecetaRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión
        self.db = db

    # Busca una receta por su id
    def obtener_por_id(self, receta_id: int) -> Receta | None:
        # SELECT por llave primaria
        return self.db.get(Receta, receta_id)

    # Indica si ya existe una receta con ese nombre (opcionalmente sin contar una receta)
    def existe_nombre(self, nombre: str, excluir_id: int | None = None) -> bool:
        """Compara sin importar mayúsculas: "Ajiaco" y "AJIACO" son la misma receta."""
        # lower(nombre) = lower(:nombre)
        condicion = func.lower(Receta.nombre) == nombre.lower()
        # Al actualizar, no se compara la receta consigo misma...
        if excluir_id is not None:
            # ...AND id <> :excluir_id
            condicion = condicion & (Receta.id != excluir_id)
        # SELECT EXISTS (... WHERE condición)
        return self.db.scalar(select(exists().where(condicion)))

    # Lista recetas con filtros y paginación
    def listar(self, filtros: FiltrosReceta) -> tuple[list[Receta], int]:
        # Consulta base: recetas con el estado pedido, ordenadas por nombre
        consulta = select(Receta).where(Receta.activo == filtros.activo).order_by(Receta.nombre)
        # Si se envió texto para buscar...
        if filtros.buscar:
            # ...busca en el nombre sin importar mayúsculas
            consulta = consulta.where(Receta.nombre.ilike(f"%{filtros.buscar}%"))
        # Ejecuta la consulta paginada
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)

    # Cambia la fórmula completa de una receta
    def reemplazar_ingredientes(self, receta: Receta, nuevos: list[RecetaIngrediente]) -> None:
        """Borra la fórmula anterior antes de agregar la nueva (evita choques con
        la restricción UNIQUE receta_id + material_id)."""
        # Vacía la lista: por delete-orphan, los ingredientes viejos se marcan para DELETE
        receta.ingredientes.clear()
        # flush envía los DELETE a la base de datos ahora (sin confirmar todavía)
        self.db.flush()
        # Agrega los ingredientes nuevos (se insertan en el commit)
        receta.ingredientes.extend(nuevos)

    # Guarda una receta nueva o modificada
    def guardar(self, receta: Receta) -> Receta:
        # INSERT o UPDATE (junto con sus ingredientes)
        self.db.add(receta)
        # Confirma
        self.db.commit()
        # Vuelve a leer la fila
        self.db.refresh(receta)
        # Devuelve la receta
        return receta

    # Borra una receta definitivamente
    def eliminar(self, receta: Receta) -> None:
        """Los ingredientes se borran en cascada (ON DELETE CASCADE)."""
        # Marca la receta para DELETE
        self.db.delete(receta)
        # Confirma el borrado
        self.db.commit()
