"""Función auxiliar para paginar cualquier consulta."""

# Select = tipo de una consulta SELECT; func = funciones SQL (count); select = crea un SELECT
from sqlalchemy import Select, func, select
# Sesión de base de datos
from sqlalchemy.orm import Session


# Cuenta cuántos registros devuelve una consulta
def contar(db: Session, consulta: Select) -> int:
    """Total de registros que devuelve la consulta (sin paginar)."""
    # SQL: SELECT count(*) FROM (consulta sin ORDER BY); se quita el orden porque no afecta el conteo
    return db.scalar(select(func.count()).select_from(consulta.order_by(None).subquery()))


# Devuelve una página de resultados y el total
def paginar(db: Session, consulta: Select, pagina: int, tamano: int) -> tuple[list, int]:
    """Devuelve los registros de la página pedida y el total de registros."""
    # OFFSET salta los registros de las páginas anteriores; LIMIT trae solo "tamano" registros
    # Ejemplo: página 3 de tamaño 10 -> salta 20 y trae 10
    items = db.scalars(consulta.offset((pagina - 1) * tamano).limit(tamano)).all()
    # Devuelve (lista de registros, total sin paginar)
    return list(items), contar(db, consulta)
