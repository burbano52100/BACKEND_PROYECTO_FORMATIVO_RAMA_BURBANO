"""Endpoints de usuarios, beneficiarios y roles (solo el Encargado)."""

# Annotated asocia dependencias o fuentes de datos a un tipo
from typing import Annotated

# APIRouter agrupa endpoints; Depends inyecta dependencias; Query lee parámetros de la URL; status trae los códigos HTTP
from fastapi import APIRouter, Depends, Query, status

# Documenta en Swagger los errores de cada endpoint
from app.core.errores import respuestas_error
# Solo deja pasar al encargado
from app.core.permisos import Encargado
# Sesión de base de datos por petición
from app.database.conexion import SesionDB
# Respuesta con mensaje y respuesta paginada
from app.schemas.comunes import Mensaje, Pagina
# Esquemas de usuarios
from app.schemas.usuario import (
    # Entrada para agregar o quitar beneficiario
    BeneficiarioEntrada,
    # Filtros del listado
    FiltrosUsuario,
    # Salida de un rol
    RolSalida,
    # Entrada para actualizar
    UsuarioActualizar,
    # Entrada para crear
    UsuarioCrear,
    # Salida de un usuario (sin contraseña)
    UsuarioSalida,
)
# Servicio con las reglas de usuarios
from app.services.usuario_service import UsuarioService

# Router sin prefijo (tiene rutas /usuarios y /roles); tag para agrupar en Swagger
router = APIRouter(tags=["Usuarios y beneficiarios"])


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> UsuarioService:
    # Devuelve un UsuarioService nuevo
    return UsuarioService(db)


# Atajo para recibir el servicio en los endpoints
Servicio = Annotated[UsuarioService, Depends(obtener_servicio)]


# Endpoint GET /api/v1/usuarios
@router.get(
    "/usuarios",  # Ruta
    response_model=Pagina[UsuarioSalida],  # Respuesta: página de usuarios
    summary="Listar usuarios (RF44)",  # Título en Swagger
    description="Filtros por nombre o documento, rol, ficha, estado y beneficiario.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Query() indica que los filtros vienen en la URL (?buscar=...&rol_id=...); "_" = encargado (no se usa, solo exige el rol)
def listar_usuarios(filtros: Annotated[FiltrosUsuario, Query()], servicio: Servicio, _: Encargado):
    # Devuelve la página de usuarios
    return servicio.listar(filtros)


# Endpoint GET /api/v1/usuarios/{usuario_id}
@router.get(
    "/usuarios/{usuario_id}",  # {usuario_id} es un valor que va en la ruta
    response_model=UsuarioSalida,  # Respuesta: un usuario
    summary="Consultar un usuario",  # Título
    description="**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 404),  # Errores posibles
)
# usuario_id se toma de la ruta y se convierte a entero
def obtener_usuario(usuario_id: int, servicio: Servicio, _: Encargado):
    # Devuelve el usuario (o 404)
    return servicio.obtener(usuario_id)


# Endpoint POST /api/v1/usuarios
@router.post(
    "/usuarios",  # Ruta
    response_model=UsuarioSalida,  # Respuesta: el usuario creado
    status_code=status.HTTP_201_CREATED,  # Código 201 = creado
    summary="Registrar un usuario (RF01)",  # Título
    description=(  # Explicación
        "El Encargado crea la cuenta y asigna el rol. Correo y documento únicos (409). Los aprendices deben "
        "tener una ficha activa. La contraseña se guarda con bcrypt y nunca se devuelve.\n\n"
        "**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores posibles
)
# Recibe el cuerpo validado, el servicio y el encargado (para la auditoría)
def crear_usuario(datos: UsuarioCrear, servicio: Servicio, encargado: Encargado):
    # Crea y devuelve el usuario
    return servicio.crear(datos, encargado)


# Endpoint PATCH /api/v1/usuarios/{usuario_id}
@router.patch(
    "/usuarios/{usuario_id}",  # Ruta
    response_model=UsuarioSalida,  # Respuesta: el usuario actualizado
    summary="Actualizar un usuario",  # Título
    description=(  # Explicación
        "Cambia nombre, teléfono, rol, ficha o estado. Nadie puede cambiar su propio rol ni desactivar su "
        "propia cuenta.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores posibles
)
# Recibe el id, los cambios, el servicio y el encargado
def actualizar_usuario(usuario_id: int, datos: UsuarioActualizar, servicio: Servicio, encargado: Encargado):
    # Actualiza y devuelve el usuario
    return servicio.actualizar(usuario_id, datos, encargado)


# Endpoint DELETE /api/v1/usuarios/{usuario_id}
@router.delete(
    "/usuarios/{usuario_id}",  # Ruta
    response_model=Mensaje,  # Respuesta: un mensaje
    summary="Desactivar un usuario",  # Título
    description="Borrado lógico: la cuenta queda inactiva y no puede iniciar sesión.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(400, 401, 403, 404),  # Errores posibles
)
# Recibe el id, el servicio y el encargado
def desactivar_usuario(usuario_id: int, servicio: Servicio, encargado: Encargado):
    # Desactiva y devuelve el mensaje
    return {"mensaje": servicio.desactivar(usuario_id, encargado)}


# Endpoint PATCH /api/v1/usuarios/{usuario_id}/beneficiario
@router.patch(
    "/usuarios/{usuario_id}/beneficiario",  # Ruta
    response_model=UsuarioSalida,  # Respuesta: el usuario actualizado
    summary="Agregar o quitar beneficiario (RF45, RF46)",  # Título
    description=(  # Explicación
        "Solo aprendices activos. El beneficiario reserva el almuerzo a $0; las reservas ya hechas conservan su "
        "valor.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores posibles
)
# Recibe el id, {"es_beneficiario": true/false}, el servicio y el encargado
def cambiar_beneficiario(usuario_id: int, datos: BeneficiarioEntrada, servicio: Servicio, encargado: Encargado):
    # Cambia la condición y devuelve el usuario
    return servicio.cambiar_beneficiario(usuario_id, datos, encargado)


# Endpoint GET /api/v1/roles
@router.get(
    "/roles",  # Ruta
    response_model=list[RolSalida],  # Respuesta: lista de roles
    summary="Listar roles",  # Título
    description="Roles disponibles para asignar a los usuarios.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403),  # Errores posibles
)
# Solo exige ser encargado
def listar_roles(servicio: Servicio, _: Encargado):
    # Devuelve los 4 roles
    return servicio.listar_roles()
