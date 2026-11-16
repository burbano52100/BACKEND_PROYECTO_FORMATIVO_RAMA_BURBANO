"""Acceso a datos de usuarios y roles."""

# exists = SQL EXISTS; func = funciones SQL; or_ = condición OR; select = SELECT
from sqlalchemy import exists, func, or_, select
# Sesión de base de datos
from sqlalchemy.orm import Session

# Nombres de los roles
from app.core.roles import Roles
# Modelos de las tablas roles y usuarios
from app.models import Rol, Usuario
# Función para paginar
from app.repositories.paginacion import paginar
# Filtros del listado de usuarios
from app.schemas.usuario import FiltrosUsuario


# Clase con todas las consultas de usuarios y roles
class UsuarioRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión para usarla en los métodos
        self.db = db

    # Busca un usuario por su id
    def obtener_por_id(self, usuario_id: int) -> Usuario | None:
        # SELECT por llave primaria; devuelve None si no existe
        return self.db.get(Usuario, usuario_id)

    # Busca un usuario por su correo
    def obtener_por_correo(self, correo: str) -> Usuario | None:
        # SELECT * FROM usuarios WHERE correo = :correo
        return self.db.scalar(select(Usuario).where(Usuario.correo == correo))

    # Indica si ya existe un usuario con ese correo
    def existe_correo(self, correo: str) -> bool:
        # SELECT EXISTS (... WHERE correo = :correo) -> True o False
        return self.db.scalar(select(exists().where(Usuario.correo == correo)))

    # Indica si ya existe un usuario con ese documento
    def existe_documento(self, documento: str) -> bool:
        # SELECT EXISTS (... WHERE documento = :documento)
        return self.db.scalar(select(exists().where(Usuario.documento == documento)))

    # Lista usuarios con filtros y paginación
    def listar(self, filtros: FiltrosUsuario) -> tuple[list[Usuario], int]:
        # Consulta base: todos los usuarios ordenados por nombre
        consulta = select(Usuario).order_by(Usuario.nombre)
        # Si se envió texto para buscar...
        if filtros.buscar:
            # Los valores van como parámetros: SQLAlchemy evita la inyección SQL
            # % = cualquier texto antes y después (coincidencia parcial)
            patron = f"%{filtros.buscar}%"
            # ilike = LIKE sin importar mayúsculas; busca en el nombre O en el documento
            consulta = consulta.where(or_(Usuario.nombre.ilike(patron), Usuario.documento.ilike(patron)))
        # Si se filtró por rol...
        if filtros.rol_id is not None:
            # ...agrega WHERE rol_id = :rol_id
            consulta = consulta.where(Usuario.rol_id == filtros.rol_id)
        # Si se filtró por ficha...
        if filtros.ficha_id is not None:
            # ...agrega WHERE ficha_id = :ficha_id
            consulta = consulta.where(Usuario.ficha_id == filtros.ficha_id)
        # Si se filtró por estado...
        if filtros.activo is not None:
            # ...agrega WHERE activo = :activo
            consulta = consulta.where(Usuario.activo == filtros.activo)
        # Si se filtró por beneficiario...
        if filtros.es_beneficiario is not None:
            # ...agrega WHERE es_beneficiario = :valor
            consulta = consulta.where(Usuario.es_beneficiario == filtros.es_beneficiario)
        # Ejecuta la consulta paginada y devuelve (usuarios, total)
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)

    # Cuenta los aprendices activos
    def contar_aprendices_activos(self) -> int:
        # SELECT count(usuarios.id)
        consulta = (
            # Cuenta ids de usuarios
            select(func.count(Usuario.id))
            # Une con la tabla roles para conocer el nombre del rol
            .join(Rol, Rol.id == Usuario.rol_id)
            # Solo aprendices activos
            .where(Rol.nombre == Roles.APRENDIZ, Usuario.activo)
        )
        # Ejecuta y devuelve el número
        return self.db.scalar(consulta)

    # Bloquea la fila del usuario mientras dura la transacción
    def bloquear(self, usuario_id: int) -> None:
        """SELECT ... FOR UPDATE sobre la fila del usuario hasta el commit."""
        # Otra petición que intente bloquear la misma fila esperará hasta el commit
        self.db.execute(select(Usuario.id).where(Usuario.id == usuario_id).with_for_update())

    # Guarda un usuario nuevo o modificado
    def guardar(self, usuario: Usuario) -> Usuario:
        """Inserta o actualiza el usuario y confirma la transacción."""
        # add: INSERT si es nuevo; si ya existe, registra los cambios para hacer UPDATE
        self.db.add(usuario)
        # commit: confirma los cambios en PostgreSQL
        self.db.commit()
        # refresh: vuelve a leer la fila (trae el id y las fechas que puso la base de datos)
        self.db.refresh(usuario)
        # Devuelve el usuario actualizado
        return usuario

    # Busca un rol por su id
    def obtener_rol(self, rol_id: int) -> Rol | None:
        # SELECT por llave primaria; None si no existe
        return self.db.get(Rol, rol_id)

    # Lista todos los roles
    def listar_roles(self) -> list[Rol]:
        # SELECT * FROM roles ORDER BY id
        return list(self.db.scalars(select(Rol).order_by(Rol.id)))
