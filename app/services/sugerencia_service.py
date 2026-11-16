"""Reglas de negocio del buzón de sugerencias (RF47 a RF49)."""

# Sesión de base de datos
from sqlalchemy.orm import Session

# Fecha y hora de Colombia
from app.core import tiempo
# Errores 404 y 400
from app.core.excepciones import NoEncontradoError, ReglaNegocioError
# Modelos de las tablas sugerencias y usuarios
from app.models import Sugerencia, Usuario
# Consultas de sugerencias
from app.repositories.sugerencia_repository import SugerenciaRepository
# Paginación base y armado de la página
from app.schemas.comunes import PaginacionBase, armar_pagina
# Esquemas de sugerencias
from app.schemas.sugerencia import AtenderEntrada, EstadoSugerencia, FiltrosSugerencia, SugerenciaCrear


# Clase con las reglas del buzón
class SugerenciaService:
    # Constructor: recibe la sesión y crea el repositorio
    def __init__(self, db: Session) -> None:
        # Repositorio de sugerencias
        self.sugerencias = SugerenciaRepository(db)

    # Envía una sugerencia
    def crear(self, datos: SugerenciaCrear, actor: Usuario) -> Sugerencia:
        """La sugerencia queda asociada a quien la envía."""
        # Crea la sugerencia con el id de quien la envía (sale del token) y la guarda
        return self.sugerencias.guardar(Sugerencia(usuario_id=actor.id, **datos.model_dump()))

    # Buzón completo con contadores
    def listar(self, filtros: FiltrosSugerencia) -> dict:
        # Consulta (sugerencias, total)
        items, total = self.sugerencias.listar(filtros)
        # Página más los contadores del buzón
        return {**armar_pagina(items, total, filtros), "contadores": self.sugerencias.contadores()}

    # Sugerencias propias
    def listar_mias(self, actor: Usuario, filtros: PaginacionBase) -> dict:
        # Consulta las sugerencias de la persona
        items, total = self.sugerencias.listar_de_usuario(actor.id, filtros)
        # Respuesta paginada
        return armar_pagina(items, total, filtros)

    # Atiende una sugerencia
    def atender(self, sugerencia_id: int, datos: AtenderEntrada, actor: Usuario) -> Sugerencia:
        """Cambio de estado: PENDIENTE -> ATENDIDA, con respuesta opcional."""
        # Busca la sugerencia
        sugerencia = self.sugerencias.obtener_por_id(sugerencia_id)
        # Si no existe...
        if sugerencia is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe una sugerencia con id {sugerencia_id}.")
        # Si ya fue atendida...
        if sugerencia.estado == EstadoSugerencia.ATENDIDA:
            # ...responde 400
            raise ReglaNegocioError("La sugerencia ya fue atendida.")
        # Cambia el estado
        sugerencia.estado = EstadoSugerencia.ATENDIDA
        # Guarda la respuesta (puede ser None)
        sugerencia.respuesta = datos.respuesta
        # Encargado que la atendió
        sugerencia.atendida_por = actor.id
        # Fecha y hora de atención
        sugerencia.atendida_en = tiempo.ahora()
        # Guarda y devuelve la sugerencia
        return self.sugerencias.guardar(sugerencia)
