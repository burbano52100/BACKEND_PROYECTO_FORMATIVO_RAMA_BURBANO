# En este archivo están todas las tablas de la base de datos hechas como clases de Python
# Cada clase es una tabla y cada atributo es una columna

# Importo los tipos de columnas que voy a usar
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Float, ForeignKey
# relationship sirve para unir una tabla con otra (por ejemplo la reserva con su menú)
from sqlalchemy.orm import relationship
# func.now() sirve para poner la fecha y hora actual
from sqlalchemy.sql import func

# Base es la clase de la que tienen que heredar todos los modelos
from app.database import Base


# Tabla de roles (encargado, instructor, aprendiz e invitado)
class Rol(Base):
    # Nombre de la tabla en PostgreSQL
    __tablename__ = "roles"

    # Id del rol (llave primaria)
    id = Column(Integer, primary_key=True, index=True)
    # Nombre del rol, no se puede repetir
    nombre = Column(String(20), unique=True, nullable=False)
    # Descripción del rol
    descripcion = Column(String(150))


# Tabla de fichas (los grupos de los aprendices)
class Ficha(Base):
    # Nombre de la tabla
    __tablename__ = "fichas"

    # Id de la ficha
    id = Column(Integer, primary_key=True, index=True)
    # Número de la ficha, no se puede repetir
    codigo = Column(String(10), unique=True, nullable=False)
    # Nombre del programa de formación
    programa = Column(String(120), nullable=False)
    # Jornada: DIURNA, NOCTURNA, MIXTA o FIN_DE_SEMANA
    jornada = Column(String(15), nullable=False)
    # Nombre del vocero del grupo (puede estar vacío)
    vocero = Column(String(100))
    # Cuántos estudiantes tiene la ficha
    cantidad_estudiantes = Column(Integer, default=0)
    # Si la ficha está activa o no
    activo = Column(Boolean, default=True)
    # Fecha en que se creó (la pone PostgreSQL sola)
    fecha_creacion = Column(DateTime, server_default=func.now())


# Tabla de usuarios
class Usuario(Base):
    # Nombre de la tabla
    __tablename__ = "usuarios"

    # Id del usuario
    id = Column(Integer, primary_key=True, index=True)
    # Número de documento, no se puede repetir
    documento = Column(String(10), unique=True, nullable=False)
    # Nombre completo
    nombre = Column(String(100), nullable=False)
    # Correo con el que inicia sesión, no se puede repetir
    correo = Column(String(120), unique=True, nullable=False)
    # Teléfono (puede estar vacío)
    telefono = Column(String(10))
    # Contraseña encriptada con bcrypt (nunca se guarda la contraseña normal)
    password = Column(String(100), nullable=False)
    # Id del rol del usuario (llave foránea a la tabla roles)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    # Id de la ficha (solo los aprendices tienen ficha)
    ficha_id = Column(Integer, ForeignKey("fichas.id"))
    # Si es beneficiario el almuerzo le sale gratis
    es_beneficiario = Column(Boolean, default=False)
    # Si está activo puede iniciar sesión
    activo = Column(Boolean, default=True)
    # Cuántas veces seguidas se equivocó en la contraseña
    intentos_fallidos = Column(Integer, default=0)
    # Hasta qué hora está bloqueada la cuenta (vacío si no está bloqueada)
    bloqueado_hasta = Column(DateTime)
    # Fecha en que se creó
    fecha_creacion = Column(DateTime, server_default=func.now())

    # Con esto puedo escribir usuario.rol.nombre
    rol = relationship("Rol")
    # Con esto puedo escribir usuario.ficha.codigo
    ficha = relationship("Ficha")


# Tabla de menús (el menú de cada día)
class Menu(Base):
    # Nombre de la tabla
    __tablename__ = "menus"

    # Id del menú
    id = Column(Integer, primary_key=True, index=True)
    # Fecha del menú, solo puede haber un menú por día
    fecha = Column(Date, unique=True, nullable=False)
    # Nombre del plato
    nombre = Column(String(100), nullable=False)
    # Lo que trae el almuerzo
    descripcion = Column(String(500), nullable=False)
    # Precio para aprendices e instructores
    precio_aprendiz = Column(Float, nullable=False)
    # Precio para invitados
    precio_invitado = Column(Float, nullable=False)
    # Cuántos almuerzos se van a hacer en total
    cantidad_total = Column(Integer, nullable=False)
    # Cuántos almuerzos quedan
    cantidad_disponible = Column(Integer, nullable=False)
    # Si el menú está activo o no
    activo = Column(Boolean, default=True)
    # Fecha en que se creó
    fecha_creacion = Column(DateTime, server_default=func.now())


# Tabla de reservas (también guarda las compras de los invitados y los consumos de los instructores)
class Reserva(Base):
    # Nombre de la tabla
    __tablename__ = "reservas"

    # Id de la reserva
    id = Column(Integer, primary_key=True, index=True)
    # Id del menú que se reservó
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    # Id del usuario que reservó
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # Tipo: APRENDIZ, BENEFICIARIO, INSTRUCTOR o INVITADO
    tipo = Column(String(15), nullable=False)
    # Lo que tiene que pagar
    valor = Column(Float, nullable=False)
    # Estado: RESERVADO, PENDIENTE, PAGADO, NO_PAGADO o CANCELADA
    estado = Column(String(15), nullable=False)
    # Fecha en que se hizo la reserva
    fecha_creacion = Column(DateTime, server_default=func.now())

    # Con esto puedo escribir reserva.menu.fecha
    menu = relationship("Menu")
    # Con esto puedo escribir reserva.usuario.nombre
    usuario = relationship("Usuario")


# Tabla de pagos que hacen los instructores a su cuenta
class PagoInstructor(Base):
    # Nombre de la tabla
    __tablename__ = "pagos_instructor"

    # Id del pago
    id = Column(Integer, primary_key=True, index=True)
    # Id del instructor que pagó
    instructor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # Cuánto pagó
    valor = Column(Float, nullable=False)
    # Cómo pagó: EFECTIVO, TRANSFERENCIA o NOMINA
    metodo = Column(String(15), nullable=False)
    # Una nota del pago (puede estar vacía)
    observacion = Column(String(255))
    # Fecha del pago
    fecha_pago = Column(DateTime, server_default=func.now())


# Tabla de materiales del inventario de la cocina
class Material(Base):
    # Nombre de la tabla
    __tablename__ = "materiales"

    # Id del material
    id = Column(Integer, primary_key=True, index=True)
    # Código de barras, no se puede repetir
    codigo_barras = Column(String(14), unique=True, nullable=False)
    # Nombre del material
    nombre = Column(String(100), nullable=False)
    # Categoría: PROTEINA, GRANO, VERDURA, FRUTA, LACTEO, ABARROTE o DESECHABLE
    categoria = Column(String(15), nullable=False)
    # Unidad de medida: KG, G, L, ML o UND
    unidad_medida = Column(String(5), nullable=False)
    # Lo que cuesta una unidad
    costo_unitario = Column(Float, nullable=False)
    # Cantidad que hay
    stock = Column(Float, default=0)
    # Cantidad mínima que debería haber
    stock_minimo = Column(Float, default=0)
    # Fecha de vencimiento (puede estar vacía)
    fecha_vencimiento = Column(Date)
    # Si el material está activo o no
    activo = Column(Boolean, default=True)
    # Fecha en que se creó
    fecha_creacion = Column(DateTime, server_default=func.now())


# Tabla de movimientos del inventario (el kardex)
class MovimientoInventario(Base):
    # Nombre de la tabla
    __tablename__ = "movimientos_inventario"

    # Id del movimiento
    id = Column(Integer, primary_key=True, index=True)
    # Id del material que se movió
    material_id = Column(Integer, ForeignKey("materiales.id"), nullable=False)
    # Id del usuario que hizo el movimiento
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # Tipo: ENTRADA, SALIDA o MERMA
    tipo = Column(String(10), nullable=False)
    # Cantidad que entró o salió
    cantidad = Column(Float, nullable=False)
    # Lo que quedó de stock después del movimiento
    saldo = Column(Float, nullable=False)
    # Por qué se hizo el movimiento
    concepto = Column(String(255), nullable=False)
    # Fecha del movimiento
    fecha = Column(DateTime, server_default=func.now())

    # Con esto puedo escribir movimiento.material.nombre
    material = relationship("Material")
    # Con esto puedo escribir movimiento.usuario.nombre
    usuario = relationship("Usuario")


# Tabla de recetas (los platos)
class Receta(Base):
    # Nombre de la tabla
    __tablename__ = "recetas"

    # Id de la receta
    id = Column(Integer, primary_key=True, index=True)
    # Nombre del plato, no se puede repetir
    nombre = Column(String(100), unique=True, nullable=False)
    # Descripción del plato (puede estar vacía)
    descripcion = Column(String(500))
    # Precio al que se vende el plato
    precio_venta = Column(Float, nullable=False)
    # Si la receta está activa o no
    activo = Column(Boolean, default=True)
    # Fecha en que se creó
    fecha_creacion = Column(DateTime, server_default=func.now())


# Tabla de ingredientes de cada receta
class RecetaIngrediente(Base):
    # Nombre de la tabla
    __tablename__ = "receta_ingredientes"

    # Id del ingrediente
    id = Column(Integer, primary_key=True, index=True)
    # Id de la receta a la que pertenece
    receta_id = Column(Integer, ForeignKey("recetas.id"), nullable=False)
    # Id del material que se usa
    material_id = Column(Integer, ForeignKey("materiales.id"), nullable=False)
    # Cuánto se usa del material en un plato
    cantidad = Column(Float, nullable=False)

    # Con esto puedo escribir ingrediente.material.costo_unitario
    material = relationship("Material")


# Tabla de sugerencias (el buzón)
class Sugerencia(Base):
    # Nombre de la tabla
    __tablename__ = "sugerencias"

    # Id de la sugerencia
    id = Column(Integer, primary_key=True, index=True)
    # Id del usuario que la mandó
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # Tema de la sugerencia
    asunto = Column(String(100), nullable=False)
    # Lo que escribió el usuario
    mensaje = Column(String(500), nullable=False)
    # Estado: PENDIENTE o ATENDIDA
    estado = Column(String(10), default="PENDIENTE")
    # Respuesta del encargado (puede estar vacía)
    respuesta = Column(String(500))
    # Fecha en que se mandó
    fecha_creacion = Column(DateTime, server_default=func.now())
    # Fecha en que el encargado la atendió
    fecha_respuesta = Column(DateTime)

    # Con esto puedo escribir sugerencia.usuario.nombre
    usuario = relationship("Usuario")
