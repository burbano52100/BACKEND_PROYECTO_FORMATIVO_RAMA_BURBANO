"""Acceso a datos del buzón de sugerencias."""

# case = CASE WHEN; func = funciones SQL; select = SELECT
from sqlalchemy import case, func, select
# Sesión de base de datos
from sqlalchemy.orm import Session

# Modelo de la tabla sugerencias
from app.models import Sugerencia
# Función para paginar
from app.repositories.paginacion import paginar
# Paginación base
from app.schemas.comunes import PaginacionBase
# Estados y filtros de sugerencias
from app.schemas.sugerencia import EstadoSugerencia, FiltrosSugerencia


# Clase con todas las consultas de sugerencias
class SugerenciaRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión
        self.db = db

    # Busca una sugerencia por su id
    def obtener_por_id(self, sugerencia_id: int) -> Sugerencia | None:
        # SELECT por llave primaria
        return self.db.get(Sugerencia, sugerencia_id)

    # Lista todas las sugerencias (buzón del encargado)
    def listar(self, filtros: FiltrosSugerencia) -> tuple[list[Sugerencia], int]:
        # Las pendientes aparecen primero (RF48)
        # CASE WHEN estado = 'PENDIENTE' THEN 0 ELSE 1: las pendientes ordenan primero
        primero_pendientes = case((Sugerencia.estado == EstadoSugerencia.PENDIENTE, 0), else_=1)
        # Ordena: pendientes primero, luego las más recientes
        consulta = select(Sugerencia).order_by(primero_pendientes, Sugerencia.creado_en.desc(), Sugerencia.id.desc())
        # Si se filtró por estado...
        if filtros.estado:
            # ...WHERE estado = :estado
            consulta = consulta.where(Sugerencia.estado == filtros.estado)
        # Ejecuta la consulta paginada
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)

    # Lista las sugerencias de una persona
    def listar_de_usuario(self, usuario_id: int, filtros: PaginacionBase) -> tuple[list[Sugerencia], int]:
        # Arma la consulta
        consulta = (
            # SELECT * FROM sugerencias
            select(Sugerencia)
            # De la persona indicada
            .where(Sugerencia.usuario_id == usuario_id)
            # Más recientes primero
            .order_by(Sugerencia.creado_en.desc(), Sugerencia.id.desc())
        )
        # Ejecuta la consulta paginada
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)

    # Cuenta las sugerencias totales, atendidas y pendientes
    def contadores(self) -> dict:
        # Ejecuta la consulta y toma la única fila
        fila = self.db.execute(
            # Tres conteos en una sola consulta
            select(
                # Total
                func.count(Sugerencia.id),
                # Solo las ATENDIDA (count con FILTER)
                func.count(Sugerencia.id).filter(Sugerencia.estado == EstadoSugerencia.ATENDIDA),
                # Solo las PENDIENTE
                func.count(Sugerencia.id).filter(Sugerencia.estado == EstadoSugerencia.PENDIENTE),
            )
        ).one()  # .one(): exige exactamente una fila de resultado
        # Devuelve los tres números en un diccionario
        return {"total": fila[0], "atendidas": fila[1], "pendientes": fila[2]}

    # Guarda una sugerencia nueva o modificada
    def guardar(self, sugerencia: Sugerencia) -> Sugerencia:
        # INSERT o UPDATE
        self.db.add(sugerencia)
        # Confirma
        self.db.commit()
        # Vuelve a leer la fila
        self.db.refresh(sugerencia)
        # Devuelve la sugerencia
        return sugerencia
