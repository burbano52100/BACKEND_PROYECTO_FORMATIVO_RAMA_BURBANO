# En este archivo está la clase base de todos los modelos y las columnas de auditoría

# Column es una columna, Integer un número entero y DateTime una fecha con hora
from sqlalchemy import Column, Integer, DateTime
# declarative_base sirve para hacer los modelos (tablas)
from sqlalchemy.orm import declarative_base

# Esta es la clase base de la que heredan todos los modelos
base = declarative_base()


# Columnas de auditoría: quién creó el registro, quién lo modificó y cuándo
# Las tablas que las necesitan heredan de esta clase, por ejemplo: class modelo_menu(base, auditoria)
# La fecha de creación ya está en cada tabla (fecha_creacion o fecha_pago)
# Los valores los pone sola la función poner_auditoria de database/conexion.py
class auditoria:
    # Id del usuario que creó el registro
    creado_por = Column(Integer)
    # Id del usuario que lo modificó por última vez
    modificado_por = Column(Integer)
    # Fecha y hora de la última modificación
    fecha_modificacion = Column(DateTime)
