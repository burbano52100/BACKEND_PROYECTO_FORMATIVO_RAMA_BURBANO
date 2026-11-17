# Rutas para manejar los usuarios y los roles (solo las puede usar el encargado)

# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas, Depends es para dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database import get_db
# Modelos que uso
from app.models import Usuario, Rol, Ficha
# Esquemas que uso
from app.schemas import UsuarioCrear, UsuarioActualizar, UsuarioRespuesta, BeneficiarioDatos, RolRespuesta
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol, encriptar_password, password_es_segura

# Creo el router (aquí no pongo prefix porque hay rutas /usuarios y /roles)
router = APIRouter(tags=["Usuarios"])


# Ruta para ver la lista de roles
@router.get("/roles", response_model=list[RolRespuesta])
def listar_roles(db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Traigo todos los roles ordenados por id
    roles = db.query(Rol).order_by(Rol.id).all()
    # Devuelvo los roles
    return roles


# Ruta para ver la lista de usuarios (con filtros y paginación)
@router.get("/usuarios", response_model=list[UsuarioRespuesta])
def listar_usuarios(
    buscar: Optional[str] = None,  # Buscar por nombre
    rol_id: Optional[int] = None,  # Filtrar por rol
    activo: Optional[bool] = None,  # Filtrar activos o inactivos
    skip: int = 0,  # Cuántos registros me salto (para paginar)
    limit: int = 100,  # Cuántos registros traigo como máximo
    db: Session = Depends(get_db),  # Sesión de la base de datos
    usuario_actual: Usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Empiezo la consulta con todos los usuarios
    consulta = db.query(Usuario)
    # Si mandaron algo para buscar
    if buscar:
        # Busco los que tengan ese texto en el nombre (ilike no tiene en cuenta mayúsculas)
        consulta = consulta.filter(Usuario.nombre.ilike(f"%{buscar}%"))
    # Si mandaron el rol
    if rol_id is not None:
        # Filtro por rol
        consulta = consulta.filter(Usuario.rol_id == rol_id)
    # Si mandaron activo
    if activo is not None:
        # Filtro por activo
        consulta = consulta.filter(Usuario.activo == activo)
    # Ordeno por nombre, me salto "skip" registros y traigo máximo "limit"
    usuarios = consulta.order_by(Usuario.nombre).offset(skip).limit(limit).all()
    # Devuelvo la lista
    return usuarios


# Ruta para ver un usuario por su id
@router.get("/usuarios/{usuario_id}", response_model=UsuarioRespuesta)
def ver_usuario(usuario_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    # Si no existe
    if usuario is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El usuario no existe")
    # Devuelvo el usuario
    return usuario


# Ruta para crear un usuario
@router.post("/usuarios", response_model=UsuarioRespuesta, status_code=201)
def crear_usuario(datos: UsuarioCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede crear usuarios
    verificar_rol(usuario_actual, ["encargado"])
    # El documento solo puede tener números
    if not datos.documento.isdigit():
        # Respondo 400
        raise HTTPException(status_code=400, detail="El documento solo puede tener números")
    # Si mandaron teléfono y no son solo números
    if datos.telefono is not None and not datos.telefono.isdigit():
        # Respondo 400
        raise HTTPException(status_code=400, detail="El teléfono solo puede tener números")
    # Reviso que la contraseña sea segura
    if not password_es_segura(datos.password):
        # Respondo 400
        raise HTTPException(status_code=400, detail="La contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula y un número")
    # Paso el correo a minúsculas
    correo = datos.correo.lower()
    # Busco si ya hay un usuario con ese correo
    existe_correo = db.query(Usuario).filter(Usuario.correo == correo).first()
    # Si ya existe
    if existe_correo is not None:
        # Respondo 400
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese correo")
    # Busco si ya hay un usuario con ese documento
    existe_documento = db.query(Usuario).filter(Usuario.documento == datos.documento).first()
    # Si ya existe
    if existe_documento is not None:
        # Respondo 400
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese documento")
    # Busco el rol
    rol = db.query(Rol).filter(Rol.id == datos.rol_id).first()
    # Si el rol no existe
    if rol is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El rol no existe")
    # Si es aprendiz tiene que tener una ficha
    if rol.nombre == "aprendiz":
        # Si no mandaron ficha
        if datos.ficha_id is None:
            # Respondo 400
            raise HTTPException(status_code=400, detail="Los aprendices tienen que tener una ficha")
        # Busco la ficha
        ficha = db.query(Ficha).filter(Ficha.id == datos.ficha_id).first()
        # Si la ficha no existe
        if ficha is None:
            # Respondo 404
            raise HTTPException(status_code=404, detail="La ficha no existe")
        # Si la ficha está inactiva
        if ficha.activo == False:
            # Respondo 400
            raise HTTPException(status_code=400, detail="La ficha está inactiva")
    # Si no es aprendiz
    else:
        # No puede tener ficha
        if datos.ficha_id is not None:
            # Respondo 400
            raise HTTPException(status_code=400, detail="Solo los aprendices pueden tener ficha")
        # Ni puede ser beneficiario
        if datos.es_beneficiario == True:
            # Respondo 400
            raise HTTPException(status_code=400, detail="Solo los aprendices pueden ser beneficiarios")
    # Creo el usuario nuevo
    nuevo_usuario = Usuario(
        documento=datos.documento,  # Documento
        nombre=datos.nombre,  # Nombre
        correo=correo,  # Correo en minúsculas
        telefono=datos.telefono,  # Teléfono
        password=encriptar_password(datos.password),  # Contraseña encriptada
        rol_id=datos.rol_id,  # Rol
        ficha_id=datos.ficha_id,  # Ficha
        es_beneficiario=datos.es_beneficiario,  # Si es beneficiario
    )
    # Lo agrego a la sesión
    db.add(nuevo_usuario)
    # Lo guardo en la base de datos
    db.commit()
    # Lo vuelvo a leer para tener el id y los datos nuevos
    db.refresh(nuevo_usuario)
    # Devuelvo el usuario creado
    return nuevo_usuario


# Ruta para actualizar un usuario
@router.put("/usuarios/{usuario_id}", response_model=UsuarioRespuesta)
def actualizar_usuario(usuario_id: int, datos: UsuarioActualizar, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede actualizar usuarios
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    # Si no existe
    if usuario is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El usuario no existe")
    # Nadie puede cambiar su propio rol
    if usuario.id == usuario_actual.id and datos.rol_id is not None and datos.rol_id != usuario.rol_id:
        # Respondo 403
        raise HTTPException(status_code=403, detail="No puede cambiar su propio rol")
    # Nadie puede desactivar su propia cuenta
    if usuario.id == usuario_actual.id and datos.activo == False:
        # Respondo 403
        raise HTTPException(status_code=403, detail="No puede desactivar su propia cuenta")
    # Si mandaron nombre
    if datos.nombre is not None:
        # Cambio el nombre
        usuario.nombre = datos.nombre
    # Si mandaron teléfono
    if datos.telefono is not None:
        # Reviso que sean solo números
        if not datos.telefono.isdigit():
            # Respondo 400
            raise HTTPException(status_code=400, detail="El teléfono solo puede tener números")
        # Cambio el teléfono
        usuario.telefono = datos.telefono
    # Si mandaron rol
    if datos.rol_id is not None:
        # Busco el rol
        rol = db.query(Rol).filter(Rol.id == datos.rol_id).first()
        # Si no existe
        if rol is None:
            # Respondo 404
            raise HTTPException(status_code=404, detail="El rol no existe")
        # Cambio el rol
        usuario.rol_id = datos.rol_id
    # Si mandaron ficha
    if datos.ficha_id is not None:
        # Busco la ficha
        ficha = db.query(Ficha).filter(Ficha.id == datos.ficha_id).first()
        # Si no existe
        if ficha is None:
            # Respondo 404
            raise HTTPException(status_code=404, detail="La ficha no existe")
        # Si está inactiva
        if ficha.activo == False:
            # Respondo 400
            raise HTTPException(status_code=400, detail="La ficha está inactiva")
        # Cambio la ficha
        usuario.ficha_id = datos.ficha_id
    # Si mandaron activo
    if datos.activo is not None:
        # Cambio el estado
        usuario.activo = datos.activo
        # Si lo están activando otra vez
        if datos.activo == True:
            # Le borro los intentos fallidos
            usuario.intentos_fallidos = 0
            # Y le quito el bloqueo
            usuario.bloqueado_hasta = None
    # Busco el rol que quedó para revisar la ficha
    rol_final = db.query(Rol).filter(Rol.id == usuario.rol_id).first()
    # Si quedó como aprendiz
    if rol_final.nombre == "aprendiz":
        # Tiene que tener ficha
        if usuario.ficha_id is None:
            # Respondo 400
            raise HTTPException(status_code=400, detail="Los aprendices tienen que tener una ficha")
    # Si no quedó como aprendiz
    else:
        # Si mandaron una ficha
        if datos.ficha_id is not None:
            # Respondo 400
            raise HTTPException(status_code=400, detail="Solo los aprendices pueden tener ficha")
        # Le quito la ficha
        usuario.ficha_id = None
        # Y le quito lo de beneficiario
        usuario.es_beneficiario = False
    # Guardo los cambios
    db.commit()
    # Vuelvo a leer el usuario
    db.refresh(usuario)
    # Devuelvo el usuario actualizado
    return usuario


# Ruta para desactivar un usuario (no se borra, solo se pone inactivo)
@router.delete("/usuarios/{usuario_id}")
def desactivar_usuario(usuario_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede desactivar usuarios
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    # Si no existe
    if usuario is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El usuario no existe")
    # No se puede desactivar a sí mismo
    if usuario.id == usuario_actual.id:
        # Respondo 403
        raise HTTPException(status_code=403, detail="No puede desactivar su propia cuenta")
    # Si ya está inactivo
    if usuario.activo == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El usuario ya está inactivo")
    # Lo pongo inactivo (borrado lógico)
    usuario.activo = False
    # Guardo los cambios
    db.commit()
    # Respondo con un mensaje
    return {"mensaje": "El usuario " + usuario.nombre + " se desactivó"}


# Ruta para poner o quitar a un aprendiz como beneficiario (almuerzo gratis)
@router.patch("/usuarios/{usuario_id}/beneficiario", response_model=UsuarioRespuesta)
def cambiar_beneficiario(usuario_id: int, datos: BeneficiarioDatos, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede hacer esto
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    # Si no existe
    if usuario is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El usuario no existe")
    # Solo los aprendices pueden ser beneficiarios
    if usuario.rol.nombre != "aprendiz":
        # Respondo 400
        raise HTTPException(status_code=400, detail="Solo los aprendices pueden ser beneficiarios")
    # Si el aprendiz está inactivo
    if usuario.activo == False:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El aprendiz está inactivo")
    # Si ya tiene ese mismo estado
    if usuario.es_beneficiario == datos.es_beneficiario:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El aprendiz ya tiene ese estado de beneficiario")
    # Cambio el estado
    usuario.es_beneficiario = datos.es_beneficiario
    # Guardo los cambios
    db.commit()
    # Vuelvo a leer el usuario
    db.refresh(usuario)
    # Devuelvo el usuario
    return usuario
