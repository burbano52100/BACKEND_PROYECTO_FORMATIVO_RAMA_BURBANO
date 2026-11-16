"""Reglas de negocio de fichas y del módulo de Grupos (RF40 a RF42)."""

# Tipo fecha
from datetime import date

# Sesión de base de datos
from sqlalchemy.orm import Session

# Fecha de hoy en Colombia
from app.core import tiempo
# Errores 409, 404 y 400
from app.core.excepciones import ConflictoError, NoEncontradoError, ReglaNegocioError
# Modelos de las tablas fichas y usuarios
from app.models import Ficha, Usuario
# Consultas de fichas
from app.repositories.ficha_repository import FichaRepository
# Consultas de reservas (para las estadísticas)
from app.repositories.reserva_repository import ReservaRepository
# Consultas de usuarios (para contar aprendices)
from app.repositories.usuario_repository import UsuarioRepository
# Arma la respuesta paginada
from app.schemas.comunes import armar_pagina
# Datos de entrada de fichas
from app.schemas.ficha import FichaActualizar, FichaCrear, FiltrosFicha


# Clase con las reglas de fichas y grupos
class FichaService:
    # Constructor: recibe la sesión y crea los repositorios
    def __init__(self, db: Session) -> None:
        # Repositorio de fichas
        self.fichas = FichaRepository(db)
        # Repositorio de reservas
        self.reservas = ReservaRepository(db)
        # Repositorio de usuarios
        self.usuarios = UsuarioRepository(db)

    # Lista fichas con filtros
    def listar(self, filtros: FiltrosFicha) -> dict:
        # Consulta (fichas, total)
        items, total = self.fichas.listar(filtros)
        # Respuesta paginada
        return armar_pagina(items, total, filtros)

    # Busca una ficha o responde 404
    def obtener(self, ficha_id: int) -> Ficha:
        # Busca por id
        ficha = self.fichas.obtener_por_id(ficha_id)
        # Si no existe...
        if ficha is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe una ficha con id {ficha_id}.")
        # Devuelve la ficha
        return ficha

    # Crea una ficha
    def crear(self, datos: FichaCrear, actor: Usuario) -> Ficha:
        # Si el código ya existe...
        if self.fichas.existe_codigo(datos.codigo):
            # ...responde 409
            raise ConflictoError(f"Ya existe la ficha {datos.codigo}.")
        # Crea la ficha con los datos enviados y la auditoría, la guarda y la devuelve
        return self.fichas.guardar(Ficha(**datos.model_dump(), creado_por=actor.id))

    # Actualiza una ficha
    def actualizar(self, ficha_id: int, datos: FichaActualizar, actor: Usuario) -> Ficha:
        # Busca la ficha (404 si no existe)
        ficha = self.obtener(ficha_id)
        # Recorre solo los campos que se enviaron
        for campo, valor in datos.model_dump(exclude_none=True).items():
            # Asigna el nuevo valor
            setattr(ficha, campo, valor)
        # Auditoría
        ficha.actualizado_por = actor.id
        # Guarda y devuelve la ficha
        return self.fichas.guardar(ficha)

    # Elimina una ficha (lógico o físico)
    def eliminar(self, ficha_id: int, actor: Usuario) -> str:
        """Borrado lógico si la ficha tiene aprendices; físico si no tiene."""
        # Busca la ficha (404 si no existe)
        ficha = self.obtener(ficha_id)
        # Si ya está inactiva...
        if not ficha.activo:
            # ...responde 400
            raise ReglaNegocioError(f"La ficha {ficha.codigo} ya está inactiva.")
        # Guarda el código para el mensaje (después de borrar ya no se podría leer)
        codigo = ficha.codigo
        # Si tiene aprendices asignados...
        if self.fichas.tiene_usuarios(ficha.id):
            # ...solo se desactiva (borrado lógico)
            ficha.activo = False
            # Auditoría
            ficha.actualizado_por = actor.id
            # Guarda el cambio
            self.fichas.guardar(ficha)
            # Mensaje de borrado lógico
            return f"La ficha {codigo} tiene aprendices: se desactivó (borrado lógico)."
        # Si no tiene aprendices, se borra definitivamente
        self.fichas.eliminar(ficha)
        # Mensaje de borrado físico
        return f"La ficha {codigo} se eliminó definitivamente."

    # Estadísticas de los grupos en una fecha
    def estadisticas(self, fecha: date | None) -> dict:
        """Totales de grupos y promedio de almuerzos por grupo en la fecha (RF40)."""
        # Si no se envió fecha, usa hoy
        fecha = fecha or tiempo.hoy()
        # Cantidad de fichas activas y suma de sus estudiantes
        total_grupos, total_estudiantes = self.fichas.totales_activas()
        # Reservas de aprendices en la fecha
        reservados = self.reservas.contar_aprendices_del_dia(fecha)
        # Devuelve las estadísticas
        return {
            # Fecha consultada
            "fecha": fecha,
            # Fichas activas
            "total_grupos": total_grupos,
            # Estudiantes de las fichas activas
            "total_estudiantes": total_estudiantes,
            # Aprendices activos con cuenta
            "aprendices_con_cuenta": self.usuarios.contar_aprendices_activos(),
            # Almuerzos reservados por aprendices
            "almuerzos_reservados": reservados,
            # Promedio con 2 decimales; si no hay grupos, 0 (evita dividir entre cero)
            "promedio_por_grupo": round(reservados / total_grupos, 2) if total_grupos else 0.0,
        }

    # Aprendices de una ficha que reservaron en una fecha
    def reservas_del_dia(self, ficha_id: int, fecha: date | None) -> list[dict]:
        """Aprendices de la ficha que reservaron, con su estado de pago (RF41)."""
        # Verifica que la ficha exista (404 si no)
        self.obtener(ficha_id)
        # Consulta las reservas de los aprendices de la ficha en la fecha (hoy por defecto)
        reservas = self.reservas.listar_aprendices_de_ficha(ficha_id, fecha or tiempo.hoy())
        # Convierte cada reserva en un diccionario con los datos del aprendiz
        return [
            # Un diccionario por reserva
            {
                # Id de la reserva
                "reserva_id": reserva.id,
                # Id del aprendiz
                "aprendiz_id": reserva.usuario.id,
                # Nombre del aprendiz
                "nombre": reserva.usuario.nombre,
                # Documento del aprendiz
                "documento": reserva.usuario.documento,
                # APRENDIZ o BENEFICIARIO
                "tipo": reserva.tipo,
                # Valor
                "valor": reserva.valor,
                # Estado de pago
                "estado": reserva.estado,
            }
            # Recorre todas las reservas encontradas
            for reserva in reservas
        ]
