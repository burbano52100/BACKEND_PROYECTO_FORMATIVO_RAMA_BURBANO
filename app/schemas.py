# En este archivo están los esquemas de Pydantic
# Sirven para revisar los datos que llegan a la API y para decir qué datos se responden

# date es una fecha y datetime es una fecha con hora
from datetime import date, datetime
# Optional quiere decir que el campo puede venir vacío (None)
from typing import Optional

# BaseModel es la clase base, Field sirve para poner reglas y EmailStr revisa que sea un correo
from pydantic import BaseModel, Field, EmailStr


# ---------------------------------- LOGIN ----------------------------------

# Datos que se mandan para iniciar sesión
class LoginDatos(BaseModel):
    # Correo del usuario
    correo: EmailStr
    # Contraseña del usuario
    password: str = Field(min_length=1, max_length=50)


# Lo que responde el login
class TokenRespuesta(BaseModel):
    # Token para hacer las peticiones
    access_token: str
    # Token para pedir un token nuevo cuando se venza
    refresh_token: str
    # Tipo de token (siempre es bearer)
    token_type: str
    # Rol del usuario para saber qué pantalla mostrar
    rol: str


# Datos para pedir un token nuevo
class RefreshDatos(BaseModel):
    # El refresh token que dio el login
    refresh_token: str


# Datos para cambiar la contraseña
class CambiarPasswordDatos(BaseModel):
    # La contraseña que tiene ahora
    password_actual: str = Field(min_length=1, max_length=50)
    # La contraseña nueva
    password_nueva: str = Field(min_length=8, max_length=50)


# ---------------------------------- USUARIOS ----------------------------------

# Lo que se responde de un rol
class RolRespuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id del rol
    id: int
    # Nombre del rol
    nombre: str
    # Descripción del rol
    descripcion: Optional[str] = None


# Datos para crear un usuario
class UsuarioCrear(BaseModel):
    # Documento de 6 a 10 números
    documento: str = Field(min_length=6, max_length=10)
    # Nombre completo
    nombre: str = Field(min_length=3, max_length=100)
    # Correo
    correo: EmailStr
    # Teléfono de 10 números (es opcional)
    telefono: Optional[str] = Field(default=None, min_length=10, max_length=10)
    # Contraseña de mínimo 8 caracteres
    password: str = Field(min_length=8, max_length=50)
    # Id del rol
    rol_id: int
    # Id de la ficha (solo para aprendices)
    ficha_id: Optional[int] = None
    # Si es beneficiario (solo para aprendices)
    es_beneficiario: bool = False


# Datos para actualizar un usuario (todo es opcional, solo se cambia lo que se manda)
class UsuarioActualizar(BaseModel):
    # Nombre nuevo
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    # Teléfono nuevo
    telefono: Optional[str] = Field(default=None, min_length=10, max_length=10)
    # Rol nuevo
    rol_id: Optional[int] = None
    # Ficha nueva
    ficha_id: Optional[int] = None
    # Activar o desactivar
    activo: Optional[bool] = None


# Datos para poner o quitar a un aprendiz como beneficiario
class BeneficiarioDatos(BaseModel):
    # True para ponerlo y False para quitarlo
    es_beneficiario: bool


# Lo que se responde de un usuario (no lleva la contraseña)
class UsuarioRespuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id del usuario
    id: int
    # Documento
    documento: str
    # Nombre
    nombre: str
    # Correo
    correo: str
    # Teléfono
    telefono: Optional[str] = None
    # Id del rol
    rol_id: int
    # Id de la ficha
    ficha_id: Optional[int] = None
    # Si es beneficiario
    es_beneficiario: bool
    # Si está activo
    activo: bool
    # Datos del rol
    rol: RolRespuesta


# ---------------------------------- FICHAS ----------------------------------

# Datos para crear una ficha
class FichaCrear(BaseModel):
    # Número de la ficha
    codigo: str = Field(min_length=6, max_length=10)
    # Programa de formación
    programa: str = Field(min_length=3, max_length=120)
    # Jornada: DIURNA, NOCTURNA, MIXTA o FIN_DE_SEMANA
    jornada: str
    # Vocero del grupo (opcional)
    vocero: Optional[str] = Field(default=None, max_length=100)
    # Cantidad de estudiantes (de 0 a 60)
    cantidad_estudiantes: int = Field(default=0, ge=0, le=60)


# Datos para actualizar una ficha (todo opcional)
class FichaActualizar(BaseModel):
    # Programa nuevo
    programa: Optional[str] = Field(default=None, min_length=3, max_length=120)
    # Jornada nueva
    jornada: Optional[str] = None
    # Vocero nuevo
    vocero: Optional[str] = Field(default=None, max_length=100)
    # Cantidad de estudiantes nueva
    cantidad_estudiantes: Optional[int] = Field(default=None, ge=0, le=60)


# Lo que se responde de una ficha
class FichaRespuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id de la ficha
    id: int
    # Número de la ficha
    codigo: str
    # Programa
    programa: str
    # Jornada
    jornada: str
    # Vocero
    vocero: Optional[str] = None
    # Cantidad de estudiantes
    cantidad_estudiantes: int
    # Si está activa
    activo: bool


# ---------------------------------- MENÚS ----------------------------------

# Datos para crear un menú
class MenuCrear(BaseModel):
    # Fecha del menú (año-mes-día)
    fecha: date
    # Nombre del plato
    nombre: str = Field(min_length=3, max_length=100)
    # Lo que trae el almuerzo
    descripcion: str = Field(min_length=3, max_length=500)
    # Precio para aprendices (no puede ser negativo)
    precio_aprendiz: float = Field(ge=0)
    # Precio para invitados (no puede ser negativo)
    precio_invitado: float = Field(ge=0)
    # Cuántos almuerzos hay (más de 0)
    cantidad_total: int = Field(gt=0, le=1000)


# Datos para actualizar un menú (todo opcional, la fecha no se cambia)
class MenuActualizar(BaseModel):
    # Nombre nuevo
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    # Descripción nueva
    descripcion: Optional[str] = Field(default=None, min_length=3, max_length=500)
    # Precio de aprendiz nuevo
    precio_aprendiz: Optional[float] = Field(default=None, ge=0)
    # Precio de invitado nuevo
    precio_invitado: Optional[float] = Field(default=None, ge=0)
    # Cantidad total nueva
    cantidad_total: Optional[int] = Field(default=None, gt=0, le=1000)


# Lo que se responde de un menú
class MenuRespuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id del menú
    id: int
    # Fecha
    fecha: date
    # Nombre
    nombre: str
    # Descripción
    descripcion: str
    # Precio de aprendiz
    precio_aprendiz: float
    # Precio de invitado
    precio_invitado: float
    # Cantidad total
    cantidad_total: int
    # Cantidad que queda
    cantidad_disponible: int
    # Si está activo
    activo: bool


# ---------------------------------- RESERVAS ----------------------------------

# Datos para reservar (el precio lo calcula la API, no se manda)
class ReservaCrear(BaseModel):
    # Id del menú que se quiere reservar
    menu_id: int


# Datos para marcar el pago de una reserva
class PagoReservaDatos(BaseModel):
    # PAGADO o NO_PAGADO
    estado: str


# ---------------------------------- CARTERA ----------------------------------

# Datos para registrar un pago de un instructor
class PagoCrear(BaseModel):
    # Cuánto paga (más de 0)
    valor: float = Field(gt=0)
    # Cómo paga: EFECTIVO, TRANSFERENCIA o NOMINA
    metodo: str
    # Una nota (opcional)
    observacion: Optional[str] = Field(default=None, max_length=255)


# ---------------------------------- INVENTARIO ----------------------------------

# Datos para crear un material
class MaterialCrear(BaseModel):
    # Código de barras de 8 a 14 números
    codigo_barras: str = Field(min_length=8, max_length=14)
    # Nombre del material
    nombre: str = Field(min_length=2, max_length=100)
    # Categoría: PROTEINA, GRANO, VERDURA, FRUTA, LACTEO, ABARROTE o DESECHABLE
    categoria: str
    # Unidad: KG, G, L, ML o UND
    unidad_medida: str
    # Costo de una unidad (más de 0)
    costo_unitario: float = Field(gt=0)
    # Con cuánto empieza el inventario
    stock_inicial: float = Field(default=0, ge=0)
    # Cantidad mínima que debería haber
    stock_minimo: float = Field(default=0, ge=0)
    # Fecha de vencimiento (opcional)
    fecha_vencimiento: Optional[date] = None


# Datos para actualizar un material (el stock no se cambia aquí, solo con movimientos)
class MaterialActualizar(BaseModel):
    # Nombre nuevo
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    # Categoría nueva
    categoria: Optional[str] = None
    # Costo nuevo
    costo_unitario: Optional[float] = Field(default=None, gt=0)
    # Stock mínimo nuevo
    stock_minimo: Optional[float] = Field(default=None, ge=0)
    # Fecha de vencimiento nueva
    fecha_vencimiento: Optional[date] = None


# Datos para hacer una entrada, salida o merma
class MovimientoCrear(BaseModel):
    # Id del material
    material_id: int
    # ENTRADA, SALIDA o MERMA
    tipo: str
    # Cantidad (más de 0)
    cantidad: float = Field(gt=0)
    # Por qué se hace el movimiento
    concepto: str = Field(min_length=3, max_length=255)


# ---------------------------------- RECETAS ----------------------------------

# Un ingrediente de la receta
class IngredienteDatos(BaseModel):
    # Id del material que se usa
    material_id: int
    # Cuánto se usa en un plato (más de 0)
    cantidad: float = Field(gt=0)


# Datos para crear una receta
class RecetaCrear(BaseModel):
    # Nombre del plato
    nombre: str = Field(min_length=3, max_length=100)
    # Descripción (opcional)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    # Precio de venta (más de 0)
    precio_venta: float = Field(gt=0)
    # Lista de ingredientes
    ingredientes: list[IngredienteDatos]


# Datos para actualizar una receta (todo opcional)
class RecetaActualizar(BaseModel):
    # Nombre nuevo
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=100)
    # Descripción nueva
    descripcion: Optional[str] = Field(default=None, max_length=500)
    # Precio nuevo
    precio_venta: Optional[float] = Field(default=None, gt=0)
    # Activar o desactivar
    activo: Optional[bool] = None
    # Si se mandan ingredientes, se cambian todos los anteriores por estos
    ingredientes: Optional[list[IngredienteDatos]] = None


# ---------------------------------- SUGERENCIAS ----------------------------------

# Datos para mandar una sugerencia
class SugerenciaCrear(BaseModel):
    # Tema de la sugerencia
    asunto: str = Field(min_length=3, max_length=100)
    # Lo que quiere decir (máximo 500 letras)
    mensaje: str = Field(min_length=3, max_length=500)


# Datos para atender una sugerencia
class AtenderDatos(BaseModel):
    # Respuesta del encargado (opcional)
    respuesta: Optional[str] = Field(default=None, max_length=500)


# Lo que se responde de una sugerencia
class SugerenciaRespuesta(BaseModel):
    # Esto deja convertir el objeto de la base de datos a este esquema
    model_config = {"from_attributes": True}

    # Id de la sugerencia
    id: int
    # Id del usuario que la mandó
    usuario_id: int
    # Asunto
    asunto: str
    # Mensaje
    mensaje: str
    # Estado
    estado: str
    # Respuesta del encargado
    respuesta: Optional[str] = None
    # Fecha en que se mandó
    fecha_creacion: datetime
    # Fecha en que se respondió
    fecha_respuesta: Optional[datetime] = None
