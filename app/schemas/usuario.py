"""Esquemas de usuarios y roles. La salida nunca incluye la contraseña."""

# Tipo fecha-hora
from datetime import datetime

# Herramientas de Pydantic
from pydantic import BaseModel, ConfigDict, Field

# Tipos reutilizables con sus validaciones de formato
from app.schemas.comunes import Correo, Documento, EsquemaEntrada, PaginacionBase, Password, Telefono
# Resumen de la ficha (para mostrarla dentro del usuario)
from app.schemas.ficha import FichaResumen


# Cómo se muestra un rol
class RolSalida(BaseModel):
    # Permite crear el esquema desde el modelo Rol
    model_config = ConfigDict(from_attributes=True)

    # Id del rol
    id: int
    # Nombre del rol
    nombre: str
    # Descripción del rol
    descripcion: str | None


# Datos mínimos de un usuario (se usan dentro de reservas, kardex y sugerencias)
class UsuarioResumen(BaseModel):
    # Permite crear el esquema desde el modelo Usuario
    model_config = ConfigDict(from_attributes=True)

    # Id del usuario
    id: int
    # Nombre
    nombre: str
    # Documento
    documento: str


# Datos para registrar un usuario (POST /usuarios)
class UsuarioCrear(EsquemaEntrada):
    # 6 a 10 dígitos
    documento: Documento
    # Entre 3 y 100 caracteres
    nombre: str = Field(min_length=3, max_length=100)
    # Correo válido (se guarda en minúsculas)
    correo: Correo
    # Teléfono opcional con formato colombiano
    telefono: Telefono | None = None
    # Contraseña que cumple la política
    password: Password
    # Id del rol (mayor que 0)
    rol_id: int = Field(gt=0)
    # Ficha (obligatoria para aprendices; la regla se revisa en el servicio)
    ficha_id: int | None = Field(None, gt=0, description="Obligatoria para los aprendices")
    # Beneficiario (solo para aprendices)
    es_beneficiario: bool = Field(False, description="Solo aplica a aprendices")


# Datos para actualizar un usuario (PATCH /usuarios/{id})
class UsuarioActualizar(EsquemaEntrada):
    """Todos los campos son opcionales: solo se cambian los que se envían."""

    # Nuevo nombre
    nombre: str | None = Field(None, min_length=3, max_length=100)
    # Nuevo teléfono
    telefono: Telefono | None = None
    # Nuevo rol
    rol_id: int | None = Field(None, gt=0)
    # Nueva ficha
    ficha_id: int | None = Field(None, gt=0)
    # Activar (true) o desactivar (false)
    activo: bool | None = None


# Datos de PATCH /usuarios/{id}/beneficiario
class BeneficiarioEntrada(EsquemaEntrada):
    # true = agregar beneficiario; false = quitarlo
    es_beneficiario: bool


# Cómo se muestra un usuario: NO tiene el campo de la contraseña
class UsuarioSalida(BaseModel):
    """from_attributes permite construir el esquema a partir del modelo ORM."""

    # Permite crear el esquema desde el modelo Usuario
    model_config = ConfigDict(from_attributes=True)

    # Id del usuario
    id: int
    # Documento
    documento: str
    # Nombre
    nombre: str
    # Correo
    correo: str
    # Teléfono
    telefono: str | None
    # Rol completo (id, nombre, descripción)
    rol: RolSalida
    # Ficha resumida (null si no tiene)
    ficha: FichaResumen | None
    # Si es beneficiario
    es_beneficiario: bool
    # Si la cuenta está activa
    activo: bool
    # Cuándo se creó
    creado_en: datetime


# Filtros de GET /usuarios (más pagina y tamano heredados)
class FiltrosUsuario(PaginacionBase):
    # Busca por nombre o documento
    buscar: str | None = Field(None, description="Nombre o documento (coincidencia parcial)")
    # Filtra por rol
    rol_id: int | None = None
    # Filtra por ficha
    ficha_id: int | None = None
    # Filtra por estado
    activo: bool | None = None
    # Filtra beneficiarios
    es_beneficiario: bool | None = None
