# Lógica del inventario: materiales, entradas, salidas, mermas y kardex

# date es una fecha
from datetime import date

# Modelo que uso para buscar por id
from app.models.receta import modelo_receta
# Modelos de materiales y movimientos para crear registros nuevos
from app.models.inventario import modelo_material, modelo_movimiento_inventario
# Funciones para responder los errores
from app.core.excepciones import error_regla, error_no_encontrado, error_duplicado
# Funciones para buscar, guardar y borrar en la base de datos
from app.database.conexion import guardar, guardar_cambios, eliminar, buscar_por_id
# Repositorios que uso
from app.repositories import inventario_repository, receta_repository

# Categorías que se pueden usar
categorias = ["PROTEINA", "GRANO", "VERDURA", "FRUTA", "LACTEO", "ABARROTE", "DESECHABLE"]
# Unidades de medida que se pueden usar
unidades = ["KG", "G", "L", "ML", "UND"]
# Tipos de movimiento que se pueden hacer
tipos_movimiento = ["ENTRADA", "SALIDA", "MERMA"]
# Si al material le faltan estos días o menos para vencerse sale como VENCIENDO
dias_alerta_vencimiento = 7


# Función que dice cómo está el stock de un material
def calcular_estado_stock(material):
    # Si el material tiene fecha de vencimiento
    if material.fecha_vencimiento is not None:
        # Cuento cuántos días le faltan para vencerse
        dias_para_vencer = (material.fecha_vencimiento - date.today()).days
        # Si le faltan 7 días o menos
        if dias_para_vencer <= dias_alerta_vencimiento:
            # Se está venciendo
            return "VENCIENDO"
    # Si tiene la mitad o menos del mínimo
    if material.stock <= material.stock_minimo * 0.5:
        # Está crítico
        return "CRITICO"
    # Si tiene el mínimo o menos
    if material.stock <= material.stock_minimo:
        # Está bajo
        return "BAJO"
    # Si no, está bien
    return "BUENO"


# Función que convierte un material en un diccionario para responder
def convertir_material(material):
    # Armo el diccionario con los datos del material
    return {
        "id": material.id,  # Id del material
        "codigo_barras": material.codigo_barras,  # Código de barras
        "nombre": material.nombre,  # Nombre
        "categoria": material.categoria,  # Categoría
        "unidad_medida": material.unidad_medida,  # Unidad
        "costo_unitario": material.costo_unitario,  # Costo de una unidad
        "stock": material.stock,  # Cantidad que hay
        "stock_minimo": material.stock_minimo,  # Cantidad mínima
        "fecha_vencimiento": material.fecha_vencimiento,  # Fecha de vencimiento
        "estado_stock": calcular_estado_stock(material),  # BUENO, BAJO, CRITICO o VENCIENDO
        "activo": material.activo,  # Si está activo
    }


# Función que convierte un movimiento en un diccionario para responder
def convertir_movimiento(movimiento):
    # Al principio la entrada y la salida están en 0
    entrada = 0
    # La salida también empieza en 0
    salida = 0
    # Si el movimiento es una entrada
    if movimiento.tipo == "ENTRADA":
        # La cantidad va en la entrada
        entrada = movimiento.cantidad
    # Si es salida o merma
    else:
        # La cantidad va en la salida
        salida = movimiento.cantidad
    # Armo el diccionario con los datos del movimiento
    return {
        "id": movimiento.id,  # Id del movimiento
        "material_id": movimiento.material_id,  # Id del material
        "nombre_material": movimiento.material.nombre,  # Nombre del material
        "tipo": movimiento.tipo,  # ENTRADA, SALIDA o MERMA
        "entrada": entrada,  # Lo que entró
        "salida": salida,  # Lo que salió
        "saldo": movimiento.saldo,  # Lo que quedó
        "concepto": movimiento.concepto,  # Por qué se hizo
        "responsable": movimiento.usuario.nombre,  # Quién lo hizo
        "fecha": movimiento.fecha,  # Cuándo se hizo
    }


# Función que revisa que la categoría esté en la lista
def revisar_categoria(categoria):
    # Si la categoría no está en la lista
    if categoria not in categorias:
        # Respondo 400
        error_regla("La categoría no es válida")


# Función que revisa que la fecha de vencimiento no sea de un día que ya pasó
def revisar_fecha_vencimiento(fecha_vencimiento):
    # Si mandaron fecha y ya pasó
    if fecha_vencimiento is not None and fecha_vencimiento < date.today():
        # Respondo 400
        error_regla("La fecha de vencimiento no puede ser de un día que ya pasó")


# Función que busca un material y si no existe responde 404
def buscar_material_existente(bd, material_id):
    # Busco el material
    material = buscar_por_id(bd, modelo_material, material_id)
    # Si no existe
    if material is None:
        # Respondo 404
        error_no_encontrado("El material no existe")
    # Devuelvo el material
    return material


# Función que busca un material y revisa que esté activo
def buscar_material_activo(bd, material_id):
    # Busco el material (si no existe responde 404)
    material = buscar_material_existente(bd, material_id)
    # Si está inactivo
    if material.activo == False:
        # Respondo 400
        error_regla("El material está inactivo")
    # Devuelvo el material
    return material


# Función para ver los materiales
def listar_materiales(bd, buscar, categoria, estado, activo, saltar, limite):
    # Traigo los materiales con los filtros
    materiales = inventario_repository.listar_materiales(bd, buscar, categoria, activo)
    # Aquí voy a guardar los materiales convertidos
    lista = []
    # Recorro los materiales
    for material in materiales:
        # Convierto el material
        material_convertido = convertir_material(material)
        # Si no mandaron estado, o si el estado es el que pidieron
        if estado is None or material_convertido["estado_stock"] == estado:
            # Lo agrego a la lista
            lista.append(material_convertido)
    # Devuelvo solo la página que pidieron (aquí pagino en Python porque el estado se calcula)
    return lista[saltar:saltar + limite]


# Función para ver un material
def ver_material(bd, material_id):
    # Busco el material
    material = buscar_material_existente(bd, material_id)
    # Devuelvo el material convertido
    return convertir_material(material)


# Función para crear un material
def crear_material(bd, datos, usuario):
    # El código de barras solo puede tener números
    if not datos.codigo_barras.isdigit():
        # Respondo 400
        error_regla("El código de barras solo puede tener números")
    # La categoría tiene que estar en la lista
    revisar_categoria(datos.categoria)
    # La unidad tiene que estar en la lista
    if datos.unidad_medida not in unidades:
        # Respondo 400
        error_regla("La unidad de medida debe ser KG, G, L, ML o UND")
    # La fecha de vencimiento no puede haber pasado
    revisar_fecha_vencimiento(datos.fecha_vencimiento)
    # Si ya hay un material con ese código
    if inventario_repository.buscar_material_por_codigo(bd, datos.codigo_barras) is not None:
        # Respondo 409 porque ese valor no se puede repetir
        error_duplicado("Ya existe un material con ese código de barras")
    # Creo el material
    nuevo_material = modelo_material(
        codigo_barras=datos.codigo_barras,  # Código de barras
        nombre=datos.nombre,  # Nombre
        categoria=datos.categoria,  # Categoría
        unidad_medida=datos.unidad_medida,  # Unidad
        costo_unitario=datos.costo_unitario,  # Costo
        stock=datos.stock_inicial,  # Empieza con el stock inicial
        stock_minimo=datos.stock_minimo,  # Stock mínimo
        fecha_vencimiento=datos.fecha_vencimiento,  # Vencimiento
    )
    # Lo guardo en la base de datos
    guardar(bd, nuevo_material)
    # Si empezó con stock, guardo una entrada en el kardex
    if datos.stock_inicial > 0:
        # Creo el movimiento de entrada
        movimiento = modelo_movimiento_inventario(
            material_id=nuevo_material.id,  # Material
            usuario_id=usuario.id,  # Quién lo hizo
            tipo="ENTRADA",  # Es una entrada
            cantidad=datos.stock_inicial,  # Lo que entró
            saldo=datos.stock_inicial,  # Lo que quedó
            concepto="Stock inicial",  # Por qué
        )
        # Lo guardo
        guardar(bd, movimiento)
    # Devuelvo el material
    return convertir_material(nuevo_material)


# Función para actualizar un material (el stock no se cambia aquí)
def actualizar_material(bd, material_id, datos):
    # Busco el material y reviso que esté activo
    material = buscar_material_activo(bd, material_id)
    # Si mandaron nombre
    if datos.nombre is not None:
        # Cambio el nombre
        material.nombre = datos.nombre
    # Si mandaron categoría
    if datos.categoria is not None:
        # Reviso que la categoría esté en la lista
        revisar_categoria(datos.categoria)
        # Cambio la categoría
        material.categoria = datos.categoria
    # Si mandaron costo
    if datos.costo_unitario is not None:
        # Cambio el costo
        material.costo_unitario = datos.costo_unitario
    # Si mandaron stock mínimo
    if datos.stock_minimo is not None:
        # Cambio el stock mínimo
        material.stock_minimo = datos.stock_minimo
    # Si mandaron fecha de vencimiento
    if datos.fecha_vencimiento is not None:
        # Reviso que no sea de un día que ya pasó
        revisar_fecha_vencimiento(datos.fecha_vencimiento)
        # Cambio la fecha
        material.fecha_vencimiento = datos.fecha_vencimiento
    # Guardo los cambios
    guardar_cambios(bd, material)
    # Devuelvo el material
    return convertir_material(material)


# Función para eliminar un material
def eliminar_material(bd, material_id):
    # Busco el material
    material = buscar_material_existente(bd, material_id)
    # Si ya está inactivo
    if material.activo == False:
        # Respondo 400
        error_regla("El material ya está inactivo")
    # Busco en qué recetas se usa el material
    ingredientes = receta_repository.listar_ingredientes_con_material(bd, material_id)
    # Recorro esos ingredientes
    for ingrediente in ingredientes:
        # Busco la receta del ingrediente
        receta = buscar_por_id(bd, modelo_receta, ingrediente.receta_id)
        # Si la receta está activa no se puede eliminar el material
        if receta.activo == True:
            # Respondo 400
            error_regla("No se puede eliminar porque lo usa la receta " + receta.nombre)
    # Cuento los movimientos del material
    cantidad_movimientos = inventario_repository.contar_movimientos(bd, material_id)
    # Si tiene movimientos o está en alguna receta no lo puedo borrar
    if cantidad_movimientos > 0 or len(ingredientes) > 0:
        # Solo lo desactivo (borrado lógico)
        material.activo = False
        # Guardo los cambios
        guardar_cambios(bd, material)
        # Devuelvo un mensaje
        return {"mensaje": "El material tiene historial, por eso solo se desactivó"}
    # Si no tiene historial lo borro de verdad
    eliminar(bd, material)
    # Devuelvo un mensaje
    return {"mensaje": "El material se eliminó"}


# Función para hacer una entrada, salida o merma
def registrar_movimiento(bd, datos, usuario):
    # Reviso que el tipo sea válido
    if datos.tipo not in tipos_movimiento:
        # Respondo 400
        error_regla("El tipo debe ser ENTRADA, SALIDA o MERMA")
    # Busco el material y reviso que esté activo
    material = buscar_material_activo(bd, datos.material_id)
    # Si es una entrada
    if datos.tipo == "ENTRADA":
        # Sumo la cantidad al stock
        nuevo_stock = material.stock + datos.cantidad
    # Si es salida o merma
    else:
        # No puede sacar más de lo que hay
        if datos.cantidad > material.stock:
            # Respondo 400
            error_regla("No hay suficiente stock de " + material.nombre + ", solo hay " + str(material.stock))
        # Resto la cantidad del stock
        nuevo_stock = material.stock - datos.cantidad
    # Redondeo a 3 decimales para que no salgan números raros
    nuevo_stock = round(nuevo_stock, 3)
    # Cambio el stock del material
    material.stock = nuevo_stock
    # Creo el movimiento para el kardex
    movimiento = modelo_movimiento_inventario(
        material_id=material.id,  # Material
        usuario_id=usuario.id,  # Quién lo hizo
        tipo=datos.tipo,  # Tipo
        cantidad=datos.cantidad,  # Cantidad
        saldo=nuevo_stock,  # Lo que quedó
        concepto=datos.concepto,  # Por qué
    )
    # Guardo el movimiento y el stock nuevo al mismo tiempo
    guardar(bd, movimiento)
    # Devuelvo el movimiento
    return convertir_movimiento(movimiento)


# Función para ver el kardex (historial de movimientos)
def ver_kardex(bd, material_id, tipo, saltar, limite):
    # Traigo los movimientos
    movimientos = inventario_repository.listar_kardex(bd, material_id, tipo, saltar, limite)
    # Aquí voy a guardar los movimientos convertidos
    lista = []
    # Recorro los movimientos
    for movimiento in movimientos:
        # Agrego cada movimiento convertido
        lista.append(convertir_movimiento(movimiento))
    # Devuelvo la lista
    return lista
