"""Pruebas de gestión de usuarios, beneficiarios y fichas."""

# Constantes y funciones de apoyo de conftest.py
from tests.conftest import (
    # Prefijo /api/v1
    API,
    # Credenciales del encargado
    ENCARGADO,
    # Id de la ficha ADSO
    FICHA_ADSO,
    # Id del rol aprendiz
    ROL_APRENDIZ,
    # Id del rol instructor
    ROL_INSTRUCTOR,
    # Número aleatorio
    aleatorio,
    # Crea un menú de prueba
    crear_menu,
    # Crea un usuario de prueba
    crear_usuario,
    # Hace una reserva
    reservar,
)


# Arma los datos de un aprendiz nuevo; **cambios permite reemplazar algunos campos
def datos_usuario(**cambios) -> dict:
    # Número aleatorio para documento y correo
    numero = aleatorio()
    # Datos válidos por defecto
    datos = {"documento": numero, "nombre": "Aprendiz Nuevo", "correo": f"nuevo{numero}@gastrosena.com",
             "telefono": "3001234567", "password": "Aprendiz2026", "rol_id": ROL_APRENDIZ, "ficha_id": FICHA_ADSO}  # Rol y ficha
    # Une los datos por defecto con los cambios (los cambios ganan)
    return {**datos, **cambios}


# Prueba: crear un aprendiz con ficha
def test_crear_aprendiz_con_ficha(cliente, encargado):
    # POST /usuarios con datos válidos
    respuesta = cliente.post(f"{API}/usuarios", json=datos_usuario(), headers=encargado)
    # Debe responder 201
    assert respuesta.status_code == 201
    # Cuerpo de la respuesta
    cuerpo = respuesta.json()
    # Debe ser aprendiz de la ficha 2847251
    assert cuerpo["rol"]["nombre"] == "aprendiz" and cuerpo["ficha"]["codigo"] == "2847251"


# Prueba: reglas de ficha según el rol
def test_reglas_de_ficha_segun_el_rol(cliente, encargado):
    # Aprendiz sin ficha
    sin_ficha = cliente.post(f"{API}/usuarios", json=datos_usuario(ficha_id=None), headers=encargado)
    # Debe responder 400
    assert sin_ficha.status_code == 400
    # Aprendiz con una ficha que no existe
    ficha_inexistente = cliente.post(f"{API}/usuarios", json=datos_usuario(ficha_id=99999), headers=encargado)
    # Debe responder 404
    assert ficha_inexistente.status_code == 404
    # Instructor con ficha
    instructor_con_ficha = cliente.post(f"{API}/usuarios", json=datos_usuario(rol_id=ROL_INSTRUCTOR), headers=encargado)
    # Debe responder 400
    assert instructor_con_ficha.status_code == 400


# Prueba: correo y documento repetidos responden 409
def test_correo_y_documento_duplicados_responden_409(cliente, encargado):
    # Usa el correo del encargado (ya existe)
    correo = cliente.post(f"{API}/usuarios", json=datos_usuario(correo=ENCARGADO["correo"]), headers=encargado)
    # Debe responder 409
    assert correo.status_code == 409
    # Usa el documento del encargado (ya existe)
    documento = cliente.post(f"{API}/usuarios", json=datos_usuario(documento="1083000001"), headers=encargado)
    # Debe responder 409
    assert documento.status_code == 409


# Prueba: datos inválidos responden 422 con mensajes en español
def test_datos_invalidos_responden_422_en_espanol(cliente, encargado):
    # 5 campos inválidos a la vez
    datos = datos_usuario(documento="12.345", nombre="Al", correo="no-es-correo", telefono="12345", password="corta")
    # POST /usuarios
    respuesta = cliente.post(f"{API}/usuarios", json=datos, headers=encargado)
    # Debe responder 422
    assert respuesta.status_code == 422
    # Convierte la lista de detalles en {campo: mensaje}
    campos = {detalle["campo"]: detalle["mensaje"] for detalle in respuesta.json()["detalles"]}
    # Deben venir exactamente esos 5 campos
    assert set(campos) == {"documento", "nombre", "correo", "telefono", "password"}
    # Mensaje en español del nombre
    assert campos["nombre"] == "Debe tener mínimo 3 caracteres."
    # Mensaje en español del correo
    assert campos["correo"] == "No es un correo electrónico válido."


# Prueba: el encargado no puede cambiar su rol ni desactivarse
def test_encargado_no_cambia_su_rol_ni_se_desactiva(cliente, encargado):
    # Id del encargado (sale de su perfil)
    mi_id = cliente.get(f"{API}/auth/perfil", headers=encargado).json()["id"]
    # Intentar cambiar su propio rol responde 403
    assert cliente.patch(f"{API}/usuarios/{mi_id}", json={"rol_id": ROL_INSTRUCTOR}, headers=encargado).status_code == 403
    # Intentar desactivarse con PATCH responde 403
    assert cliente.patch(f"{API}/usuarios/{mi_id}", json={"activo": False}, headers=encargado).status_code == 403
    # Intentar desactivarse con DELETE responde 403
    assert cliente.delete(f"{API}/usuarios/{mi_id}", headers=encargado).status_code == 403


# Prueba: un usuario desactivado ya no puede iniciar sesión
def test_desactivar_usuario_impide_iniciar_sesion(cliente, encargado):
    # Crea un aprendiz nuevo
    usuario = crear_usuario(cliente, encargado, ROL_APRENDIZ, FICHA_ADSO)
    # Lo desactiva
    respuesta = cliente.delete(f"{API}/usuarios/{usuario['id']}", headers=encargado)
    # Debe responder 200 con mensaje de borrado lógico
    assert respuesta.status_code == 200 and "borrado lógico" in respuesta.json()["mensaje"]
    # Intenta iniciar sesión
    login = cliente.post(f"{API}/auth/login", json={"correo": usuario["correo"], "password": usuario["password"]})
    # Debe responder 403
    assert login.status_code == 403
    # Su token anterior tampoco sirve
    # El token que tenía antes responde 401
    assert cliente.get(f"{API}/auth/perfil", headers=usuario["headers"]).status_code == 401


# Prueba: un beneficiario reserva a $0
def test_beneficiario_reserva_a_cero_pesos(cliente, encargado):
    # Crea un aprendiz nuevo
    usuario = crear_usuario(cliente, encargado, ROL_APRENDIZ, FICHA_ADSO)
    # Ruta para cambiar la condición de beneficiario
    ruta = f"{API}/usuarios/{usuario['id']}/beneficiario"
    # Agregar beneficiario responde 200
    assert cliente.patch(ruta, json={"es_beneficiario": True}, headers=encargado).status_code == 200
    # Agregarlo otra vez responde 409
    assert cliente.patch(ruta, json={"es_beneficiario": True}, headers=encargado).status_code == 409

    # Crea un menú
    menu = crear_menu(cliente, encargado)
    # El beneficiario reserva
    reserva = reservar(cliente, usuario["headers"], menu["id"]).json()
    # La reserva debe ser tipo BENEFICIARIO y valor 0
    assert reserva["tipo"] == "BENEFICIARIO" and reserva["valor"] == 0

    # Al quitar la condición, la reserva hecha conserva su valor
    # Quita el beneficio
    assert cliente.patch(ruta, json={"es_beneficiario": False}, headers=encargado).status_code == 200
    # Consulta la reserva hecha antes
    consultada = cliente.get(f"{API}/reservas/{reserva['id']}", headers=encargado).json()
    # Sigue valiendo 0
    assert consultada["valor"] == 0


# Prueba: solo los aprendices pueden ser beneficiarios
def test_solo_aprendices_pueden_ser_beneficiarios(cliente, encargado):
    # Crea un instructor
    usuario = crear_usuario(cliente, encargado, ROL_INSTRUCTOR)
    # Intenta hacerlo beneficiario
    respuesta = cliente.patch(f"{API}/usuarios/{usuario['id']}/beneficiario", json={"es_beneficiario": True}, headers=encargado)
    # Debe responder 400
    assert respuesta.status_code == 400


# Prueba: listar usuarios filtrando por rol
def test_listar_usuarios_con_filtros(cliente, encargado):
    # GET /usuarios?rol_id=2&tamano=50
    respuesta = cliente.get(f"{API}/usuarios", params={"rol_id": ROL_INSTRUCTOR, "tamano": 50}, headers=encargado)
    # Debe responder 200
    assert respuesta.status_code == 200
    # Todos los usuarios devueltos deben ser instructores
    assert all(u["rol"]["nombre"] == "instructor" for u in respuesta.json()["items"])


# Prueba: CRUD completo de fichas
def test_crud_de_fichas(cliente, encargado):
    # Código aleatorio de 9 dígitos
    codigo = aleatorio(9)
    # Datos de la ficha
    datos = {"codigo": codigo, "programa": "Cocina Internacional", "jornada": "MIXTA", "cantidad_estudiantes": 15}
    # Crea la ficha
    creada = cliente.post(f"{API}/fichas", json=datos, headers=encargado)
    # Debe responder 201
    assert creada.status_code == 201
    # Crearla otra vez responde 409
    assert cliente.post(f"{API}/fichas", json=datos, headers=encargado).status_code == 409
    # Id de la ficha creada
    ficha_id = creada.json()["id"]
    # Actualiza el vocero
    actualizada = cliente.patch(f"{API}/fichas/{ficha_id}", json={"vocero": "Ana Pérez"}, headers=encargado)
    # El vocero debe haber cambiado
    assert actualizada.json()["vocero"] == "Ana Pérez"
    # Sin aprendices: borrado físico
    # El mensaje debe decir "definitivamente"
    assert "definitivamente" in cliente.delete(f"{API}/fichas/{ficha_id}", headers=encargado).json()["mensaje"]
    # Ya no existe: 404
    assert cliente.get(f"{API}/fichas/{ficha_id}", headers=encargado).status_code == 404


# Prueba: una ficha con aprendices se desactiva en lugar de borrarse
def test_ficha_con_aprendices_se_desactiva(cliente, encargado):
    # Crea una ficha nueva
    ficha = cliente.post(f"{API}/fichas", json={"codigo": aleatorio(9), "programa": "Panadería", "jornada": "DIURNA"},
                         headers=encargado).json()  # Encabezado y respuesta como diccionario
    # Crea un aprendiz en esa ficha
    crear_usuario(cliente, encargado, ROL_APRENDIZ, ficha["id"])
    # Intenta eliminar la ficha
    respuesta = cliente.delete(f"{API}/fichas/{ficha['id']}", headers=encargado)
    # Debe ser borrado lógico
    assert "borrado lógico" in respuesta.json()["mensaje"]


# Prueba: estadísticas de grupos y reservas de una ficha
def test_grupos_estadisticas_y_reservas_de_la_ficha(cliente, encargado):
    # Consulta las estadísticas
    estadisticas = cliente.get(f"{API}/fichas/estadisticas", headers=encargado).json()
    # Debe haber al menos las 10 fichas de prueba
    assert estadisticas["total_grupos"] >= 10
    # Consulta las reservas de la ficha ADSO
    reservas = cliente.get(f"{API}/fichas/{FICHA_ADSO}/reservas", headers=encargado).json()
    # Todas deben ser de aprendices o beneficiarios
    assert all(r["tipo"] in ("APRENDIZ", "BENEFICIARIO") for r in reservas)
