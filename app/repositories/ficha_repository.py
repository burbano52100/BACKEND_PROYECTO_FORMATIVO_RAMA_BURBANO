"""Acceso a datos de fichas (grupos de formación)."""

# Funciones para armar consultas SQL
from sqlalchemy import exists, func, or_, select
# Sesión de base de datos
from sqlalchemy.orm import Session

# Modelos de las tablas fichas y usuarios
from app.models import Ficha, Usuario
# Función para paginar
from app.repositories.paginacion import paginar
# Filtros del listado de fichas
from app.schemas.ficha import FiltrosFicha


# Clase con todas las consultas de fichas
class FichaRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión
        self.db = db

    # Busca una ficha por su id
    def obtener_por_id(self, ficha_id: int) -> Ficha | None:
        # SELECT por llave primaria; None si no existe
        return self.db.get(Ficha, ficha_id)

    # Indica si ya existe una ficha con ese código
    def existe_codigo(self, codigo: str) -> bool:
        # SELECT EXISTS (... WHERE codigo = :codigo)
        return self.db.scalar(select(exists().where(Ficha.codigo == codigo)))

    # Lista fichas con filtros y paginación
    def listar(self, filtros: FiltrosFicha) -> tuple[list[Ficha], int]:
        # Consulta base: fichas con el estado pedido (activas por defecto), ordenadas por código
        consulta = select(Ficha).where(Ficha.activo == filtros.activo).order_by(Ficha.codigo)
        # Si se envió texto para buscar...
        if filtros.buscar:
            # Patrón para coincidencia parcial
            patron = f"%{filtros.buscar}%"
            # Busca en el código O en el programa, sin importar mayúsculas
            consulta = consulta.where(or_(Ficha.codigo.ilike(patron), Ficha.programa.ilike(patron)))
        # Si se filtró por jornada...
        if filtros.jornada is not None:
            # ...agrega WHERE jornada = :jornada
            consulta = consulta.where(Ficha.jornada == filtros.jornada)
        # Ejecuta la consulta paginada
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)

    # Indica si la ficha tiene usuarios (aprendices) asignados
    def tiene_usuarios(self, ficha_id: int) -> bool:
        # SELECT EXISTS (SELECT ... FROM usuarios WHERE ficha_id = :id)
        return self.db.scalar(select(exists().where(Usuario.ficha_id == ficha_id)))

    # Cuenta las fichas activas y suma sus estudiantes
    def totales_activas(self) -> tuple[int, int]:
        """Cantidad de fichas activas y suma de sus estudiantes."""
        # SELECT count(id), coalesce(sum(cantidad_estudiantes), 0) FROM fichas WHERE activo
        fila = self.db.execute(
            # coalesce(..., 0) devuelve 0 en lugar de NULL si no hay fichas
            select(func.count(Ficha.id), func.coalesce(func.sum(Ficha.cantidad_estudiantes), 0)).where(Ficha.activo)
        ).one()  # .one(): exige exactamente una fila de resultado
        # Devuelve (cantidad de fichas, total de estudiantes)
        return fila[0], fila[1]

    # Guarda una ficha nueva o modificada
    def guardar(self, ficha: Ficha) -> Ficha:
        # INSERT o UPDATE
        self.db.add(ficha)
        # Confirma en PostgreSQL
        self.db.commit()
        # Vuelve a leer la fila (id y fechas)
        self.db.refresh(ficha)
        # Devuelve la ficha guardada
        return ficha

    # Borra una ficha definitivamente (borrado físico)
    def eliminar(self, ficha: Ficha) -> None:
        # Marca la fila para DELETE
        self.db.delete(ficha)
        # Confirma el borrado
        self.db.commit()
