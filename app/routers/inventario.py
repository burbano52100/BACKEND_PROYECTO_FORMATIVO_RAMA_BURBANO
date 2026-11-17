# Rutas del inventario: materiales, movimientos (entradas, salidas y mermas) y kardex

# date es una fecha
from datetime import date
# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas, Depends es para dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database import get_db
# Modelos que uso
from app.models import Material, MovimientoInventario, Receta, RecetaIngrediente, Usuario
# Esquemas que uso
from app.schemas import MaterialCrear, MaterialActualizar, MovimientoCrear
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol

# Creo el router, todas las rutas empiezan con /inventario
router = APIRouter(prefix="/inventario", tags=["Inventario"])

# Categorías que se pueden usar
CATEGORIAS = ["PROTEINA", "GRANO", "VERDURA", "FRUTA", "LACTEO", "ABARROTE", "DESECHABLE"]
# Unidades de medida que se pueden usar
UNIDADES = ["KG", "G", "L", "ML", "UND"]
# Tipos de movimiento que se pueden hacer
TIPOS_MOVIMIENTO = ["ENTRADA", "SALIDA", "MERMA"]
# Si al material le faltan estos días o menos para vencerse sale como VENCIENDO
DIAS_ALERTA_VENCIMIENTO = 7


# Función que dice cómo está el stock de un material
def calcular_estado_stock(material):
    # Si el material tiene fecha de vencimiento
    if material.fecha_vencimiento is not None:
        # Cuento cuántos días le faltan para vencerse
        dias_para_vencer = (material.fecha_vencimiento - date.today()).days
        # Si le faltan 7 días o menos
        if dias_para_vencer <= DIAS_ALERTA_VENCIMIENTO:
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


# Ruta para ver los materiales (solo el encargado)
@router.get("/materiales")
def listar_materiales(
    buscar: Optional[str] = None,  # Buscar por nombre o código de barras
    categoria: Optional[str] = None,  # Filtrar por categoría
    estado: Optional[str] = None,  # Filtrar por estado del stock
    activo: bool = True,  # Por defecto muestro los activos
    skip: int = 0,  # Cuántos registros me salto
    limit: int = 100,  # Cuántos registros traigo como máximo
    db: Session = Depends(get_db),  # Sesión de la base de datos
    usuario_actual: Usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Traigo los materiales activos o inactivos según el filtro
    consulta = db.query(Material).filter(Material.activo == activo)
    # Si mandaron algo para buscar
    if buscar:
        # Busco en el nombre o en el código de barras
        consulta = consulta.filter((Material.nombre.ilike(f"%{buscar}%")) | (Material.codigo_barras.ilike(f"%{buscar}%")))
    # Si mandaron categoría
    if categoria:
        # Filtro por categoría
        consulta = consulta.filter(Material.categoria == categoria)
    # Traigo todos los materiales ordenados por nombre
    materiales = consulta.order_by(Material.nombre).all()
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
    # Devuelvo solo la página que pidieron
    return lista[skip:skip + limit]


# Ruta para ver un material por su id (solo el encargado)
@router.get("/materiales/{material_id}")
def ver_material(material_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el material
    material = db.query(Material).filter(Material.id == material_id).first()
    # Si no existe
    if material is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El material no existe")
    # Devuelvo el material
    return convertir_material(material)


# Ruta para crear un material (solo el encargado)
@router.post("/materiales", status_code=201)
def crear_material(datos: MaterialCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear materiales
    verificar_rol(usuario_actual, ["encargado"])
    # El código de barras solo puede tener números
    if not datos.codigo_barras.isdigit():
        # Respondo 400
        raise HTTPException(status_code=400, detail="El código de barras solo puede tener números")
    # La categoría tiene que estar en la lista
    if datos.categoria not in CATEGORIAS:
        # Respondo 400
        raise HTTPException(status_code=400, detail="La categoría no es válida")
    # La unidad tiene que estar en la lista
    if datos.unidad_medida not in UNIDADES:
        # Respondo 400
        raise HTTPException(status_code=400, detail="La unidad de medida debe ser KG, G, L, ML o UND")
    # Si mandaron fecha de vencimiento y ya pasó
    if datos.fecha_vencimiento is not None and datos.fecha_vencimiento < date.today():
        # Respondo 400
        raise HTTPException(status_code=400, detail="La fecha de vencimiento no puede ser de un día que ya pasó")
    # Busco si ya hay un material con ese código
    existe = db.query(Material).filter(Material.codigo_barras == datos.codigo_barras).first()
    # Si ya existe
    if existe is not None:
        # Respondo 400
        raise HTTPException(status_code=400, detail="Ya existe un material con ese código de barras")
    # Creo el material
    nuevo_material = Material(
        codigo_barras=datos.codigo_barras,  # Código de barras
        nombre=datos.nombre,  # Nombre
        categoria=datos.categoria,  # Categoría
        unidad_medida=datos.unidad_medida,  # Unidad
        costo_unitario=datos.costo_unitario,  # Costo
        stock=datos.stock_inicial,  # Empieza con el stock inicial
        stock_minimo=datos.stock_minimo,  # Stock mínimo
        fecha_vencimiento=datos.fecha_vencimiento,  # Vencimiento
    )
    # Lo agrego a la sesión
    db.add(nuevo_material)
    # Lo guardo en la base de datos
    db.commit()
    # Lo vuelvo a leer para tener el id
    db.refresh(nuevo_material)
    # Si empezó con stock, guardo una entrada en el kardex
    if datos.stock_inicial > 0:
        # Creo el movimiento de entrada
        movimiento = MovimientoInventario(
            material_id=nuevo_material.id,  # Material
            usuario_id=usuario_actual.id,  # Quién lo hizo
            tipo="ENTRADA",  # Es una entrada
            cantidad=datos.stock_inicial,  # Lo que entró
            saldo=datos.stock_inicial,  # Lo que quedó
            concepto="Stock inicial",  # Por qué
        )
        # Lo agrego a la sesión
        db.add(movimiento)
        # Lo guardo
        db.commit()
    # Devuelvo el material
    return convertir_material(nuevo_material)


# Ruta para actualizar un material (el stock no se cambia aquí)
@router.put("/materiales/{material_id}")
def actualizar_material(material_id: int, datos: MaterialActualizar, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar materiales
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el material
    material = db.query(Material).filter(Material.id == material_id).first()
    # Si no existe
    if material is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El material no existe")
    # Si está inactivo
    if material.activo == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El material está inactivo")
    # Si mandaron nombre
    if datos.nombre is not None:
        # Cambio el nombre
        material.nombre = datos.nombre
    # Si mandaron categoría
    if datos.categoria is not None:
        # Reviso que la categoría esté en la lista
        if datos.categoria not in CATEGORIAS:
            # Respondo 400
            raise HTTPException(status_code=400, detail="La categoría no es válida")
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
        if datos.fecha_vencimiento < date.today():
            # Respondo 400
            raise HTTPException(status_code=400, detail="La fecha de vencimiento no puede ser de un día que ya pasó")
        # Cambio la fecha
        material.fecha_vencimiento = datos.fecha_vencimiento
    # Guardo los cambios
    db.commit()
    # Vuelvo a leer el material
    db.refresh(material)
    # Devuelvo el material
    return convertir_material(material)


# Ruta para eliminar un material (solo el encargado)
@router.delete("/materiales/{material_id}")
def eliminar_material(material_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede eliminar materiales
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el material
    material = db.query(Material).filter(Material.id == material_id).first()
    # Si no existe
    if material is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El material no existe")
    # Si ya está inactivo
    if material.activo == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El material ya está inactivo")
    # Busco en qué recetas se usa el material
    ingredientes = db.query(RecetaIngrediente).filter(RecetaIngrediente.material_id == material_id).all()
    # Recorro esos ingredientes
    for ingrediente in ingredientes:
        # Busco la receta del ingrediente
        receta = db.query(Receta).filter(Receta.id == ingrediente.receta_id).first()
        # Si la receta está activa no se puede eliminar el material
        if receta.activo == True:
            # Respondo 400
            raise HTTPException(status_code=400, detail="No se puede eliminar porque lo usa la receta " + receta.nombre)
    # Cuento los movimientos del material
    cantidad_movimientos = db.query(MovimientoInventario).filter(MovimientoInventario.material_id == material_id).count()
    # Si tiene movimientos o está en alguna receta no lo puedo borrar
    if cantidad_movimientos > 0 or len(ingredientes) > 0:
        # Solo lo desactivo (borrado lógico)
        material.activo = False
        # Guardo los cambios
        db.commit()
        # Respondo con un mensaje
        return {"mensaje": "El material tiene historial, por eso solo se desactivó"}
    # Si no tiene historial lo borro de verdad
    db.delete(material)
    # Guardo los cambios
    db.commit()
    # Respondo con un mensaje
    return {"mensaje": "El material se eliminó"}


# Ruta para hacer una entrada, salida o merma (solo el encargado)
@router.post("/movimientos", status_code=201)
def registrar_movimiento(datos: MovimientoCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede hacer movimientos
    verificar_rol(usuario_actual, ["encargado"])
    # Reviso que el tipo sea válido
    if datos.tipo not in TIPOS_MOVIMIENTO:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El tipo debe ser ENTRADA, SALIDA o MERMA")
    # Busco el material
    material = db.query(Material).filter(Material.id == datos.material_id).first()
    # Si no existe
    if material is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El material no existe")
    # Si está inactivo
    if material.activo == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El material está inactivo")
    # Si es una entrada
    if datos.tipo == "ENTRADA":
        # Sumo la cantidad al stock
        nuevo_stock = material.stock + datos.cantidad
    # Si es salida o merma
    else:
        # No puede sacar más de lo que hay
        if datos.cantidad > material.stock:
            # Respondo 400
            raise HTTPException(status_code=400, detail="No hay suficiente stock de " + material.nombre + ", solo hay " + str(material.stock))
        # Resto la cantidad del stock
        nuevo_stock = material.stock - datos.cantidad
    # Redondeo a 3 decimales para que no salgan números raros
    nuevo_stock = round(nuevo_stock, 3)
    # Cambio el stock del material
    material.stock = nuevo_stock
    # Creo el movimiento para el kardex
    movimiento = MovimientoInventario(
        material_id=material.id,  # Material
        usuario_id=usuario_actual.id,  # Quién lo hizo
        tipo=datos.tipo,  # Tipo
        cantidad=datos.cantidad,  # Cantidad
        saldo=nuevo_stock,  # Lo que quedó
        concepto=datos.concepto,  # Por qué
    )
    # Lo agrego a la sesión
    db.add(movimiento)
    # Guardo el movimiento y el stock nuevo al mismo tiempo
    db.commit()
    # Vuelvo a leer el movimiento
    db.refresh(movimiento)
    # Devuelvo el movimiento
    return convertir_movimiento(movimiento)


# Ruta para ver el kardex (historial de movimientos)
@router.get("/kardex")
def ver_kardex(
    material_id: Optional[int] = None,  # Filtrar por material
    tipo: Optional[str] = None,  # Filtrar por tipo (por ejemplo MERMA)
    skip: int = 0,  # Cuántos registros me salto
    limit: int = 100,  # Cuántos registros traigo como máximo
    db: Session = Depends(get_db),  # Sesión de la base de datos
    usuario_actual: Usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Empiezo con todos los movimientos
    consulta = db.query(MovimientoInventario)
    # Si mandaron material
    if material_id is not None:
        # Filtro por material
        consulta = consulta.filter(MovimientoInventario.material_id == material_id)
    # Si mandaron tipo
    if tipo is not None:
        # Filtro por tipo
        consulta = consulta.filter(MovimientoInventario.tipo == tipo)
    # Ordeno del más nuevo al más viejo y pagino
    movimientos = consulta.order_by(MovimientoInventario.fecha.desc(), MovimientoInventario.id.desc()).offset(skip).limit(limit).all()
    # Aquí voy a guardar los movimientos convertidos
    lista = []
    # Recorro los movimientos
    for movimiento in movimientos:
        # Agrego cada movimiento convertido
        lista.append(convertir_movimiento(movimiento))
    # Devuelvo la lista
    return lista
