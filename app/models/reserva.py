# Tablas de reservas y de pagos de los instructores

# Importo los tipos de columnas que voy a usar
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
# relationship sirve para unir una tabla con otra
from sqlalchemy.orm import relationship
# func.now() sirve para poner la fecha y hora actual
from sqlalchemy.sql import func

# base es la clase de la que heredan todos los modelos y auditoria trae las columnas de quién creó o modificó
from app.models.base import base, auditoria


# Tabla de reservas (también guarda las compras de los invitados y los consumos de los instructores)
class modelo_reserva(base, auditoria):
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
    menu = relationship("modelo_menu")
    # Con esto puedo escribir reserva.usuario.nombre
    usuario = relationship("modelo_usuario")


# Tabla de pagos que hacen los instructores a su cuenta
class modelo_pago_instructor(base, auditoria):
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
