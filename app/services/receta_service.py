# Lógica de las recetas: ingredientes, costo de producción y margen

# Modelo que uso para buscar por id
from app.models.inventario import modelo_material
# Modelos de recetas e ingredientes para crear registros nuevos
from app.models.receta import modelo_receta, modelo_receta_ingrediente
# Funciones para responder los errores
from app.core.excepciones import error_regla, error_no_encontrado, error_duplicado
# Funciones para buscar, guardar y borrar en la base de datos
from app.database.conexion import guardar, agregar, guardar_cambios, eliminar, buscar_por_id
# Repositorio de recetas
from app.repositories import receta_repository


# Función que arma la receta con sus ingredientes y calcula el costo y la ganancia
def armar_receta(bd, receta):
    # Traigo los ingredientes de la receta
    ingredientes = receta_repository.listar_ingredientes(bd, receta.id)
    # Aquí voy a guardar los ingredientes con su costo
    lista_ingredientes = []
    # Aquí voy a sumar lo que cuesta hacer el plato
    costo_produccion = 0
    # Recorro los ingredientes
    for ingrediente in ingredientes:
        # El costo del ingrediente es la cantidad por el costo de una unidad
        costo = round(ingrediente.cantidad * ingrediente.material.costo_unitario, 2)
        # Lo sumo al costo del plato
        costo_produccion = costo_produccion + costo
        # Agrego el ingrediente a la lista
        lista_ingredientes.append({
            "material_id": ingrediente.material_id,  # Id del material
            "nombre_material": ingrediente.material.nombre,  # Nombre del material
            "unidad_medida": ingrediente.material.unidad_medida,  # Unidad
            "cantidad": ingrediente.cantidad,  # Cuánto se usa
            "costo_unitario": ingrediente.material.costo_unitario,  # Costo de una unidad
            "costo": costo,  # Costo del ingrediente en el plato
        })
    # Redondeo el costo del plato
    costo_produccion = round(costo_produccion, 2)
    # La ganancia (margen) es el precio de venta menos el costo
    margen = round(receta.precio_venta - costo_produccion, 2)
    # El margen en porcentaje
    margen_porcentaje = round(margen / receta.precio_venta * 100, 2)
    # Devuelvo la receta completa
    return {
        "id": receta.id,  # Id de la receta
        "nombre": receta.nombre,  # Nombre
        "descripcion": receta.descripcion,  # Descripción
        "precio_venta": receta.precio_venta,  # Precio de venta
        "activo": receta.activo,  # Si está activa
        "ingredientes": lista_ingredientes,  # Ingredientes
        "costo_produccion": costo_produccion,  # Lo que cuesta hacer el plato
        "margen": margen,  # La ganancia
        "margen_porcentaje": margen_porcentaje,  # La ganancia en porcentaje
        "alerta_margen_negativo": margen < 0,  # True si se pierde plata
    }


# Función que revisa que los ingredientes estén bien
def revisar_ingredientes(bd, ingredientes):
    # La receta tiene que tener al menos un ingrediente
    if len(ingredientes) == 0:
        # Respondo 400
        error_regla("La receta tiene que tener al menos un ingrediente")
    # Aquí voy guardando los materiales que ya revisé
    materiales_usados = []
    # Recorro los ingredientes
    for ingrediente in ingredientes:
        # Si el material ya estaba en la lista
        if ingrediente.material_id in materiales_usados:
            # Respondo 400 porque no se puede repetir
            error_regla("Un material no se puede repetir en la misma receta")
        # Lo agrego a la lista de usados
        materiales_usados.append(ingrediente.material_id)
        # Busco el material
        material = buscar_por_id(bd, modelo_material, ingrediente.material_id)
        # Si no existe
        if material is None:
            # Respondo 404
            error_no_encontrado("No existe el material con id " + str(ingrediente.material_id))
        # Si está inactivo
        if material.activo == False:
            # Respondo 400
            error_regla("El material " + material.nombre + " está inactivo")


# Función que agrega los ingredientes a una receta (se guardan después con guardar_cambios)
def agregar_ingredientes(bd, receta_id, ingredientes):
    # Recorro los ingredientes que mandaron
    for ingrediente in ingredientes:
        # Creo cada ingrediente
        nuevo_ingrediente = modelo_receta_ingrediente(
            receta_id=receta_id,  # Receta
            material_id=ingrediente.material_id,  # Material
            cantidad=ingrediente.cantidad,  # Cantidad
        )
        # Lo agrego a la sesión
        agregar(bd, nuevo_ingrediente)


# Función que busca una receta y si no existe responde 404
def buscar_receta_existente(bd, receta_id):
    # Busco la receta
    receta = buscar_por_id(bd, modelo_receta, receta_id)
    # Si no existe
    if receta is None:
        # Respondo 404
        error_no_encontrado("La receta no existe")
    # Devuelvo la receta
    return receta


# Función para ver las recetas con su costo
def listar_recetas(bd, buscar, activo, saltar, limite):
    # Traigo las recetas
    recetas = receta_repository.listar(bd, buscar, activo, saltar, limite)
    # Aquí voy a guardar las recetas armadas
    lista = []
    # Recorro las recetas
    for receta in recetas:
        # Agrego cada receta con su costo
        lista.append(armar_receta(bd, receta))
    # Devuelvo la lista
    return lista


# Función para ver una receta con su costo
def ver_receta(bd, receta_id):
    # Busco la receta
    receta = buscar_receta_existente(bd, receta_id)
    # Devuelvo la receta con su costo
    return armar_receta(bd, receta)


# Función para crear una receta
def crear_receta(bd, datos):
    # Si ya hay una receta con ese nombre
    if receta_repository.buscar_por_nombre(bd, datos.nombre) is not None:
        # Respondo 409 porque ese valor no se puede repetir
        error_duplicado("Ya existe una receta con ese nombre")
    # Reviso los ingredientes
    revisar_ingredientes(bd, datos.ingredientes)
    # Creo la receta
    nueva_receta = modelo_receta(
        nombre=datos.nombre,  # Nombre
        descripcion=datos.descripcion,  # Descripción
        precio_venta=datos.precio_venta,  # Precio
    )
    # La guardo para tener el id
    guardar(bd, nueva_receta)
    # Le agrego los ingredientes
    agregar_ingredientes(bd, nueva_receta.id, datos.ingredientes)
    # Guardo los ingredientes
    guardar_cambios(bd, nueva_receta)
    # Devuelvo la receta con su costo
    return armar_receta(bd, nueva_receta)


# Función para actualizar una receta
def actualizar_receta(bd, receta_id, datos):
    # Busco la receta
    receta = buscar_receta_existente(bd, receta_id)
    # Si mandaron nombre
    if datos.nombre is not None:
        # Si otra receta ya tiene ese nombre
        if receta_repository.buscar_otra_con_nombre(bd, datos.nombre, receta_id) is not None:
            # Respondo 409 porque ese valor no se puede repetir
            error_duplicado("Ya existe una receta con ese nombre")
        # Cambio el nombre
        receta.nombre = datos.nombre
    # Si mandaron descripción
    if datos.descripcion is not None:
        # Cambio la descripción
        receta.descripcion = datos.descripcion
    # Si mandaron precio
    if datos.precio_venta is not None:
        # Cambio el precio
        receta.precio_venta = datos.precio_venta
    # Si mandaron activo
    if datos.activo is not None:
        # Cambio el estado
        receta.activo = datos.activo
    # Si mandaron ingredientes
    if datos.ingredientes is not None:
        # Reviso los ingredientes nuevos
        revisar_ingredientes(bd, datos.ingredientes)
        # Borro los ingredientes que tenía antes
        receta_repository.borrar_ingredientes(bd, receta_id)
        # Le agrego los ingredientes nuevos
        agregar_ingredientes(bd, receta_id, datos.ingredientes)
    # Guardo todos los cambios
    guardar_cambios(bd, receta)
    # Devuelvo la receta con su costo
    return armar_receta(bd, receta)


# Función para eliminar una receta
def eliminar_receta(bd, receta_id):
    # Busco la receta
    receta = buscar_receta_existente(bd, receta_id)
    # Primero borro los ingredientes de la receta
    receta_repository.borrar_ingredientes(bd, receta_id)
    # Después borro la receta
    eliminar(bd, receta)
    # Devuelvo un mensaje
    return {"mensaje": "La receta se eliminó"}
