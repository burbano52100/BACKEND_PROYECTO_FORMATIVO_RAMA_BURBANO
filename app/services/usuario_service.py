"""Reglas de negocio de la gestión de usuarios y beneficiarios (solo el Encargado)."""

# Sesión de base de datos
from sqlalchemy.orm import Session

# Errores 409, 404, 403 y 400
from app.core.excepciones import ConflictoError, NoEncontradoError, PermisoDenegadoError, ReglaNegocioError
# Nombres de los roles
from app.core.roles import Roles
# Función que cifra contraseñas con bcrypt
from app.core.seguridad import cifrar_password
# Modelos de las tablas roles y usuarios
from app.models import Rol, Usuario
# Consultas de fichas
from app.repositories.ficha_repository import FichaRepository
# Consultas de usuarios
from app.repositories.usuario_repository import UsuarioRepository
# Arma la respuesta paginada
from app.schemas.comunes import armar_pagina
# Datos de entrada de usuarios
from app.schemas.usuario import BeneficiarioEntrada, FiltrosUsuario, UsuarioActualizar, UsuarioCrear


# Clase con las reglas de usuarios
class UsuarioService:
    # Constructor: recibe la sesión y crea los repositorios
    def __init__(self, db: Session) -> None:
        # Repositorio de usuarios
        self.usuarios = UsuarioRepository(db)
        # Repositorio de fichas (para validar la ficha de los aprendices)
        self.fichas = FichaRepository(db)

    # Lista usuarios con filtros
    def listar(self, filtros: FiltrosUsuario) -> dict:
        # Consulta (usuarios, total)
        items, total = self.usuarios.listar(filtros)
        # Devuelve la respuesta paginada
        return armar_pagina(items, total, filtros)

    # Busca un usuario o responde 404
    def obtener(self, usuario_id: int) -> Usuario:
        # Busca por id
        usuario = self.usuarios.obtener_por_id(usuario_id)
        # Si no existe...
        if usuario is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un usuario con id {usuario_id}.")
        # Devuelve el usuario
        return usuario

    # Registra un usuario nuevo
    def crear(self, datos: UsuarioCrear, actor: Usuario) -> Usuario:
        # Validaciones que dependen de la base de datos: únicos (409) y relacionados (404)
        # Si el correo ya está registrado...
        if self.usuarios.existe_correo(datos.correo):
            # ...responde 409
            raise ConflictoError("Ya existe un usuario con ese correo.")
        # Si el documento ya está registrado...
        if self.usuarios.existe_documento(datos.documento):
            # ...responde 409
            raise ConflictoError("Ya existe un usuario con ese documento.")
        # Verifica que el rol exista (404 si no)
        rol = self._obtener_rol(datos.rol_id)
        # Valida la ficha y la condición de beneficiario según el rol
        ficha_id, beneficiario = self._validar_ficha(rol, datos.ficha_id, datos.es_beneficiario)

        # Crea el objeto Usuario
        usuario = Usuario(
            # Copia los campos del esquema excepto la contraseña, la ficha y el beneficiario
            **datos.model_dump(exclude={"password", "ficha_id", "es_beneficiario"}),
            # Guarda la contraseña cifrada (nunca la contraseña real)
            password_hash=cifrar_password(datos.password),
            # Ficha ya validada
            ficha_id=ficha_id,
            # Beneficiario ya validado
            es_beneficiario=beneficiario,
            # Auditoría: el encargado que lo creó
            creado_por=actor.id,
        )
        # Guarda en la base de datos y lo devuelve
        return self.usuarios.guardar(usuario)

    # Actualiza un usuario
    def actualizar(self, usuario_id: int, datos: UsuarioActualizar, actor: Usuario) -> Usuario:
        # Busca el usuario (404 si no existe)
        usuario = self.obtener(usuario_id)
        # Diccionario solo con los campos que se enviaron (exclude_none quita los no enviados)
        cambios = datos.model_dump(exclude_none=True)

        # Un usuario no puede cambiar su propio rol ni desactivar su propia cuenta
        # Si el encargado se está editando a sí mismo...
        if usuario.id == actor.id:
            # ...y el rol enviado es distinto del actual...
            if cambios.get("rol_id", usuario.rol_id) != usuario.rol_id:
                # ...responde 403
                raise PermisoDenegadoError("No puede cambiar su propio rol.")
            # ...o intenta desactivarse...
            if cambios.get("activo") is False:
                # ...responde 403
                raise PermisoDenegadoError("No puede desactivar su propia cuenta.")

        # Rol final: el enviado o el actual (pop lo saca del diccionario de cambios)
        rol = self._obtener_rol(cambios.pop("rol_id", usuario.rol_id))
        # Si cambia el rol o se envió una ficha, hay que revalidar ficha y beneficiario
        if rol.id != usuario.rol_id or "ficha_id" in cambios:
            # Si sigue siendo aprendiz conserva su ficha; si no, se le quita
            ficha_por_defecto = usuario.ficha_id if rol.nombre == Roles.APRENDIZ else None
            # Solo conserva el beneficio si sigue siendo aprendiz
            beneficiario = usuario.es_beneficiario and rol.nombre == Roles.APRENDIZ
            # Valida y asigna la ficha y el beneficiario
            usuario.ficha_id, usuario.es_beneficiario = self._validar_ficha(
                # Rol nuevo, ficha enviada (o la de por defecto) y beneficio calculado
                rol, cambios.pop("ficha_id", ficha_por_defecto), beneficiario
            )
        # Asigna el rol
        usuario.rol_id = rol.id

        # Copia los demás cambios (nombre, teléfono, activo) al usuario
        for campo, valor in cambios.items():
            # setattr(objeto, "campo", valor) equivale a usuario.campo = valor
            setattr(usuario, campo, valor)
        # Si se está reactivando la cuenta...
        if cambios.get("activo") is True:
            # Reactivar una cuenta también la desbloquea
            # Reinicia los intentos fallidos
            usuario.intentos_fallidos = 0
            # Quita el bloqueo
            usuario.bloqueado_hasta = None
        # Auditoría: quién hizo el cambio
        usuario.actualizado_por = actor.id
        # Guarda y devuelve el usuario
        return self.usuarios.guardar(usuario)

    # Desactiva un usuario (borrado lógico)
    def desactivar(self, usuario_id: int, actor: Usuario) -> str:
        """Borrado lógico: los usuarios nunca se borran porque quedan en la auditoría."""
        # Busca el usuario (404 si no existe)
        usuario = self.obtener(usuario_id)
        # Si intenta desactivarse a sí mismo...
        if usuario.id == actor.id:
            # ...responde 403
            raise PermisoDenegadoError("No puede desactivar su propia cuenta.")
        # Si ya estaba inactivo...
        if not usuario.activo:
            # ...responde 400
            raise ReglaNegocioError("El usuario ya está inactivo.")
        # Marca la cuenta como inactiva
        usuario.activo = False
        # Auditoría
        usuario.actualizado_por = actor.id
        # Guarda el cambio
        self.usuarios.guardar(usuario)
        # Devuelve el mensaje de confirmación
        return f"El usuario {usuario.nombre} se desactivó (borrado lógico)."

    # Agrega o quita la condición de beneficiario
    def cambiar_beneficiario(self, usuario_id: int, datos: BeneficiarioEntrada, actor: Usuario) -> Usuario:
        """Agregar (RF45) o quitar (RF46) la condición de beneficiario de un aprendiz."""
        # Busca el usuario (404 si no existe)
        usuario = self.obtener(usuario_id)
        # Si no es aprendiz...
        if usuario.rol.nombre != Roles.APRENDIZ:
            # ...responde 400
            raise ReglaNegocioError("Solo los aprendices pueden ser beneficiarios.")
        # Si está inactivo...
        if not usuario.activo:
            # ...responde 400
            raise ReglaNegocioError("El aprendiz está inactivo.")
        # Si se quiere agregar y ya es beneficiario...
        if datos.es_beneficiario and usuario.es_beneficiario:
            # ...responde 409
            raise ConflictoError("El aprendiz ya es beneficiario.")
        # Si se quiere quitar y no es beneficiario...
        if not datos.es_beneficiario and not usuario.es_beneficiario:
            # ...responde 400
            raise ReglaNegocioError("El aprendiz no es beneficiario.")
        # Cambia la condición
        usuario.es_beneficiario = datos.es_beneficiario
        # Auditoría
        usuario.actualizado_por = actor.id
        # Guarda y devuelve el usuario
        return self.usuarios.guardar(usuario)

    # Lista los roles
    def listar_roles(self) -> list[Rol]:
        # Consulta todos los roles
        return self.usuarios.listar_roles()

    # ----- Métodos internos -----

    # Busca un rol o responde 404
    def _obtener_rol(self, rol_id: int) -> Rol:
        # Busca el rol por id
        rol = self.usuarios.obtener_rol(rol_id)
        # Si no existe...
        if rol is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe un rol con id {rol_id}.")
        # Devuelve el rol
        return rol

    # Valida la ficha y el beneficio según el rol
    def _validar_ficha(self, rol: Rol, ficha_id: int | None, es_beneficiario: bool) -> tuple[int | None, bool]:
        """Los aprendices deben pertenecer a una ficha activa; los demás roles, a ninguna."""
        # Si el rol NO es aprendiz...
        if rol.nombre != Roles.APRENDIZ:
            # ...no puede tener ficha
            if ficha_id is not None:
                # 400
                raise ReglaNegocioError("Solo los aprendices pertenecen a una ficha.")
            # ...ni ser beneficiario
            if es_beneficiario:
                # 400
                raise ReglaNegocioError("Solo los aprendices pueden ser beneficiarios.")
            # Sin ficha y sin beneficio
            return None, False
        # Si es aprendiz y no se envió ficha...
        if ficha_id is None:
            # ...responde 400
            raise ReglaNegocioError("Los aprendices deben pertenecer a una ficha.")
        # Busca la ficha
        ficha = self.fichas.obtener_por_id(ficha_id)
        # Si no existe...
        if ficha is None:
            # ...responde 404
            raise NoEncontradoError(f"No existe una ficha con id {ficha_id}.")
        # Si está inactiva...
        if not ficha.activo:
            # ...responde 400
            raise ReglaNegocioError(f"La ficha {ficha.codigo} está inactiva.")
        # Ficha válida y beneficio solicitado
        return ficha_id, es_beneficiario
