# En este archivo hago la conexión con la base de datos PostgreSQL
# y están las funciones para guardar y borrar que usan todos los módulos

# datetime sirve para saber la fecha y hora de ahora (para la auditoría)
from datetime import datetime

# create_engine sirve para crear la conexión e inspect sirve para mirar qué columnas tiene una tabla
from sqlalchemy import create_engine, inspect
# sessionmaker crea las sesiones
from sqlalchemy.orm import sessionmaker

# quote_plus escapa caracteres especiales en la contraseña de la base de datos
from urllib.parse import quote_plus

# Traigo los datos de conexión que están en config.py
from app.core.config import bd_servidor, bd_puerto, bd_nombre, bd_usuario, bd_contrasena

# Armo la dirección de la base de datos así: postgresql+psycopg://usuario:clave@servidor:puerto/nombre
url_base_datos = f"postgresql+psycopg://{bd_usuario}:{quote_plus(bd_contrasena)}@{bd_servidor}:{bd_puerto}/{bd_nombre}"

# Creo el motor que se conecta a PostgreSQL
# Con options=-csearch_path=gastrosena le digo que busque las tablas en el esquema gastrosena
motor = create_engine(url_base_datos, connect_args={"options": "-csearch_path=gastrosena"})

# Creo la fábrica de sesiones (una sesión es como una conversación con la base de datos)
sesion_local = sessionmaker(autocommit=False, autoflush=False, bind=motor)


# Esta función abre una sesión en cada petición y la cierra cuando termina
def obtener_bd():
    # Abro una sesión nueva
    bd = sesion_local()
    # Uso try y finally para que la sesión siempre se cierre aunque haya un error
    try:
        # Le entrego la sesión a la ruta que la pidió
        yield bd
    # Esto se ejecuta siempre al final
    finally:
        # Cierro la sesión
        bd.close()


# Busca un registro de cualquier tabla por su id (modelo es la tabla, por ejemplo modelo_usuario)
def buscar_por_id(bd, modelo, registro_id):
    # Hago la consulta y traigo el primero (o None si no existe)
    return bd.query(modelo).filter(modelo.id == registro_id).first()


# Auditoría: llena quién creó o modificó los registros que se van a guardar
# El id del usuario lo guarda permisos.py en bd.info cuando revisa el token de la petición
def poner_auditoria(bd):
    # Saco el id del usuario que está haciendo la petición
    usuario_id = bd.info.get("usuario_id")
    # Si no hay usuario (por ejemplo al iniciar sesión) no hago nada
    if usuario_id is None:
        # Me salgo de la función
        return
    # Recorro los registros nuevos que hay en la sesión
    for registro in bd.new:
        # Si la tabla tiene la columna creado_por y todavía está vacía
        if hasattr(registro, "creado_por") and registro.creado_por is None:
            # Guardo quién lo creó
            registro.creado_por = usuario_id
    # Recorro los registros que ya existían y que cambiaron
    for registro in bd.dirty:
        # Si la tabla tiene la columna modificado_por y de verdad cambió algún dato
        if hasattr(registro, "modificado_por") and bd.is_modified(registro):
            # Guardo quién lo modificó
            registro.modificado_por = usuario_id
            # Guardo cuándo lo modificó
            registro.fecha_modificacion = datetime.now()


# Guarda un registro nuevo (y también los cambios que haya pendientes en la sesión)
def guardar(bd, registro):
    # Lo agrego a la sesión
    bd.add(registro)
    # Lleno la auditoría (quién lo creó)
    poner_auditoria(bd)
    # Guardo y, si falla, dejo la sesión limpia para no guardar a medias
    try:
        bd.commit()
    except Exception:
        bd.rollback()
        raise
    # Lo vuelvo a leer para tener el id y los datos que pone PostgreSQL
    bd.refresh(registro)
    # Devuelvo el registro
    return registro


# Agrega un registro a la sesión sin guardarlo todavía (se guarda con guardar_cambios)
def agregar(bd, registro):
    # Lo agrego a la sesión
    bd.add(registro)


# Guarda los cambios de un registro que ya existe
def guardar_cambios(bd, registro):
    # Lleno la auditoría (quién lo modificó y cuándo)
    poner_auditoria(bd)
    # Guardo y, si falla, dejo la sesión limpia para no guardar a medias
    try:
        bd.commit()
    except Exception:
        bd.rollback()
        raise
    # Vuelvo a leer el registro
    bd.refresh(registro)
    # Devuelvo el registro
    return registro


# Borra un registro de la base de datos
def eliminar(bd, registro):
    # Lo borro
    bd.delete(registro)
    # Guardo y, si falla, dejo la sesión limpia
    try:
        bd.commit()
    except Exception:
        bd.rollback()
        raise


# Revisa que la base de datos tenga las columnas que usan los modelos actuales
# Si la base se creó antes de la auditoría hay que ejecutar database/04_auditoria.sql
# y database/05_compatibilidad.sql
def columnas_faltantes():
    inspector = inspect(motor)
    requeridas = {
        "usuarios": {"contrasena", "creado_por", "fecha_creacion", "modificado_por", "fecha_modificacion"},
        "fichas": {"creado_por", "fecha_creacion", "modificado_por", "fecha_modificacion"},
        "menus": {"creado_por", "fecha_creacion", "modificado_por", "fecha_modificacion"},
        "reservas": {"creado_por", "fecha_creacion", "modificado_por", "fecha_modificacion"},
        "pagos_instructor": {"creado_por", "fecha_pago", "modificado_por", "fecha_modificacion"},
        "materiales": {"creado_por", "fecha_creacion", "modificado_por", "fecha_modificacion"},
        "recetas": {"creado_por", "fecha_creacion", "modificado_por", "fecha_modificacion"},
        "sugerencias": {"creado_por", "fecha_creacion", "modificado_por", "fecha_respuesta", "fecha_modificacion"},
        "movimientos_inventario": {"material_id", "usuario_id", "fecha"},
    }
    faltantes = []
    for tabla, columnas in requeridas.items():
        try:
            actuales = {columna["name"] for columna in inspector.get_columns(tabla, schema="gastrosena")}
        except Exception:
            faltantes.append(tabla + " (tabla inexistente)")
            continue
        for columna in sorted(columnas - actuales):
            faltantes.append(tabla + "." + columna)
    return faltantes


# Compatibilidad con el nombre que usaba main.py
def falta_auditoria():
    return bool(columnas_faltantes())
