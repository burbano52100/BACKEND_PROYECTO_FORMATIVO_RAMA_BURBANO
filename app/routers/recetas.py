# Rutas de las recetas: los platos, sus ingredientes y lo que cuesta hacerlos

# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas, Depends es para dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database import get_db
# Modelos que uso
from app.models import Receta, RecetaIngrediente, Material, Usuario
# Esquemas que uso
from app.schemas import RecetaCrear, RecetaActualizar
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol

# Creo el router, todas las rutas empiezan con /recetas
router = APIRouter(prefix="/recetas", tags=["Recetas"])


# Función que arma la receta con sus ingredientes y calcula el costo y la ganancia
def armar_receta(receta, db):
    # Traigo los ingredientes de la receta
    ingredientes = db.query(RecetaIngrediente).filter(RecetaIngrediente.receta_id == receta.id).order_by(RecetaIngrediente.id).all()
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
def revisar_ingredientes(ingredientes, db):
    # La receta tiene que tener al menos un ingrediente
    if len(ingredientes) == 0:
        # Respondo 400
        raise HTTPException(status_code=400, detail="La receta tiene que tener al menos un ingrediente")
    # Aquí voy guardando los materiales que ya revisé
    materiales_usados = []
    # Recorro los ingredientes
    for ingrediente in ingredientes:
        # Si el material ya estaba en la lista
        if ingrediente.material_id in materiales_usados:
            # Respondo 400 porque no se puede repetir
            raise HTTPException(status_code=400, detail="Un material no se puede repetir en la misma receta")
        # Lo agrego a la lista de usados
        materiales_usados.append(ingrediente.material_id)
        # Busco el material
        material = db.query(Material).filter(Material.id == ingrediente.material_id).first()
        # Si no existe
        if material is None:
            # Respondo 404
            raise HTTPException(status_code=404, detail="No existe el material con id " + str(ingrediente.material_id))
        # Si está inactivo
        if material.activo == False:
            # Respondo 400
            raise HTTPException(status_code=400, detail="El material " + material.nombre + " está inactivo")


# Ruta para ver las recetas (solo el encargado)
@router.get("")
def listar_recetas(
    buscar: Optional[str] = None,  # Buscar por nombre
    activo: bool = True,  # Por defecto muestro las activas
    skip: int = 0,  # Cuántos registros me salto
    limit: int = 100,  # Cuántos registros traigo como máximo
    db: Session = Depends(get_db),  # Sesión de la base de datos
    usuario_actual: Usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Traigo las recetas activas o inactivas según el filtro
    consulta = db.query(Receta).filter(Receta.activo == activo)
    # Si mandaron algo para buscar
    if buscar:
        # Busco por nombre
        consulta = consulta.filter(Receta.nombre.ilike(f"%{buscar}%"))
    # Ordeno por nombre y pagino
    recetas = consulta.order_by(Receta.nombre).offset(skip).limit(limit).all()
    # Aquí voy a guardar las recetas armadas
    lista = []
    # Recorro las recetas
    for receta in recetas:
        # Agrego cada receta con su costo
        lista.append(armar_receta(receta, db))
    # Devuelvo la lista
    return lista


# Ruta para ver una receta por su id (solo el encargado)
@router.get("/{receta_id}")
def ver_receta(receta_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Busco la receta
    receta = db.query(Receta).filter(Receta.id == receta_id).first()
    # Si no existe
    if receta is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La receta no existe")
    # Devuelvo la receta con su costo
    return armar_receta(receta, db)


# Ruta para crear una receta (solo el encargado)
@router.post("", status_code=201)
def crear_receta(datos: RecetaCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear recetas
    verificar_rol(usuario_actual, ["encargado"])
    # Busco si ya hay una receta con ese nombre (ilike no tiene en cuenta mayúsculas)
    existe = db.query(Receta).filter(Receta.nombre.ilike(datos.nombre)).first()
    # Si ya existe
    if existe is not None:
        # Respondo 400
        raise HTTPException(status_code=400, detail="Ya existe una receta con ese nombre")
    # Reviso los ingredientes
    revisar_ingredientes(datos.ingredientes, db)
    # Creo la receta
    nueva_receta = Receta(
        nombre=datos.nombre,  # Nombre
        descripcion=datos.descripcion,  # Descripción
        precio_venta=datos.precio_venta,  # Precio
    )
    # La agrego a la sesión
    db.add(nueva_receta)
    # La guardo
    db.commit()
    # La vuelvo a leer para tener el id
    db.refresh(nueva_receta)
    # Recorro los ingredientes que mandaron
    for ingrediente in datos.ingredientes:
        # Creo cada ingrediente
        nuevo_ingrediente = RecetaIngrediente(
            receta_id=nueva_receta.id,  # Receta
            material_id=ingrediente.material_id,  # Material
            cantidad=ingrediente.cantidad,  # Cantidad
        )
        # Lo agrego a la sesión
        db.add(nuevo_ingrediente)
    # Guardo los ingredientes
    db.commit()
    # Devuelvo la receta con su costo
    return armar_receta(nueva_receta, db)


# Ruta para actualizar una receta (solo el encargado)
@router.put("/{receta_id}")
def actualizar_receta(receta_id: int, datos: RecetaActualizar, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar recetas
    verificar_rol(usuario_actual, ["encargado"])
    # Busco la receta
    receta = db.query(Receta).filter(Receta.id == receta_id).first()
    # Si no existe
    if receta is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La receta no existe")
    # Si mandaron nombre
    if datos.nombre is not None:
        # Busco si otra receta ya tiene ese nombre
        existe = db.query(Receta).filter(Receta.nombre.ilike(datos.nombre), Receta.id != receta_id).first()
        # Si ya existe
        if existe is not None:
            # Respondo 400
            raise HTTPException(status_code=400, detail="Ya existe una receta con ese nombre")
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
        revisar_ingredientes(datos.ingredientes, db)
        # Borro los ingredientes que tenía antes
        db.query(RecetaIngrediente).filter(RecetaIngrediente.receta_id == receta_id).delete()
        # Recorro los ingredientes nuevos
        for ingrediente in datos.ingredientes:
            # Creo cada ingrediente
            nuevo_ingrediente = RecetaIngrediente(
                receta_id=receta_id,  # Receta
                material_id=ingrediente.material_id,  # Material
                cantidad=ingrediente.cantidad,  # Cantidad
            )
            # Lo agrego a la sesión
            db.add(nuevo_ingrediente)
    # Guardo todos los cambios
    db.commit()
    # Vuelvo a leer la receta
    db.refresh(receta)
    # Devuelvo la receta con su costo
    return armar_receta(receta, db)


# Ruta para eliminar una receta (solo el encargado)
@router.delete("/{receta_id}")
def eliminar_receta(receta_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede eliminar recetas
    verificar_rol(usuario_actual, ["encargado"])
    # Busco la receta
    receta = db.query(Receta).filter(Receta.id == receta_id).first()
    # Si no existe
    if receta is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="La receta no existe")
    # Primero borro los ingredientes de la receta
    db.query(RecetaIngrediente).filter(RecetaIngrediente.receta_id == receta_id).delete()
    # Después borro la receta
    db.delete(receta)
    # Guardo los cambios
    db.commit()
    # Respondo con un mensaje
    return {"mensaje": "La receta se eliminó"}
