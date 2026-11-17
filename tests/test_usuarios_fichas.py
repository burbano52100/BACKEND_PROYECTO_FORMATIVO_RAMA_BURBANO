# Pruebas de usuarios, beneficiarios y fichas

# Traigo las ayudas de las pruebas
from tests.ayudas import client, API, ENCARGADO, APRENDIZ, crear_usuario_prueba, numero_al_azar


# Prueba: la encargada puede ver la lista de usuarios
def test_encargado_ve_los_usuarios():
    # Pido la lista de usuarios
    respuesta = client.get(API + "/usuarios", headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Tienen que venir por lo menos los 12 usuarios de prueba
    assert len(respuesta.json()) >= 12


# Prueba: un aprendiz no puede ver los usuarios
def test_aprendiz_no_ve_los_usuarios():
    # Pido la lista con el token de la aprendiz
    respuesta = client.get(API + "/usuarios", headers=APRENDIZ)
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: crear un usuario
def test_crear_usuario():
    # Creo un invitado de prueba
    usuario = crear_usuario_prueba(4)
    # Tiene que tener id
    assert usuario["id"] > 0
    # El rol tiene que ser invitado
    assert usuario["rol"]["nombre"] == "invitado"


# Prueba: no se puede repetir el correo
def test_no_se_repite_el_correo():
    # Creo un invitado de prueba
    usuario = crear_usuario_prueba(4)
    # Intento crear otro con el mismo correo
    datos = {"documento": numero_al_azar(), "nombre": "Otro usuario", "correo": usuario["correo"], "password": "Prueba12345", "rol_id": 4}
    # Mando la petición
    respuesta = client.post(API + "/usuarios", json=datos, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: un aprendiz tiene que tener ficha
def test_aprendiz_sin_ficha():
    # Saco un número al azar
    numero = numero_al_azar()
    # Armo los datos
    datos = {"documento": numero, "nombre": "Aprendiz sin ficha", "correo": "sinficha" + numero + "@gastrosena.com", "password": "Prueba12345", "rol_id": 3}
    # Mando la petición
    respuesta = client.post(API + "/usuarios", json=datos, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: la contraseña tiene que ser segura
def test_contrasena_debil():
    # Saco un número al azar
    numero = numero_al_azar()
    # Armo los datos
    datos = {"documento": numero, "nombre": "Usuario debil", "correo": "debil" + numero + "@gastrosena.com", "password": "abcdefgh", "rol_id": 4}
    # Mando la petición
    respuesta = client.post(API + "/usuarios", json=datos, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: el documento solo puede tener números
def test_documento_con_letras():
    # Armo los datos con letras en el documento
    datos = {"documento": "12345abc", "nombre": "Usuario raro", "correo": "raro" + numero_al_azar() + "@gastrosena.com", "password": "Prueba12345", "rol_id": 4}
    # Mando la petición
    respuesta = client.post(API + "/usuarios", json=datos, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: un correo mal escrito responde 422 (lo revisa pydantic)
def test_correo_mal_escrito():
    # Armo los datos con un correo sin @
    datos = {"documento": numero_al_azar(), "nombre": "Usuario raro", "correo": "esto-no-es-correo", "password": "Prueba12345", "rol_id": 4}
    # Mando la petición
    respuesta = client.post(API + "/usuarios", json=datos, headers=ENCARGADO)
    # Tiene que responder 422
    assert respuesta.status_code == 422


# Prueba: nadie puede cambiar su propio rol
def test_no_puede_cambiar_su_propio_rol():
    # La encargada (id 1) intenta ponerse rol de instructor
    respuesta = client.put(API + "/usuarios/1", json={"rol_id": 2}, headers=ENCARGADO)
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: un usuario desactivado ya no puede entrar
def test_desactivar_usuario():
    # Creo un invitado de prueba
    usuario = crear_usuario_prueba(4)
    # Lo desactivo
    respuesta = client.delete(API + "/usuarios/" + str(usuario["id"]), headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Intento entrar con ese usuario
    respuesta = client.post(API + "/auth/login", json={"correo": usuario["correo"], "password": usuario["password"]})
    # Tiene que responder 403
    assert respuesta.status_code == 403
    # Su token viejo tampoco sirve
    respuesta = client.get(API + "/auth/perfil", headers=usuario["headers"])
    # Tiene que responder 401
    assert respuesta.status_code == 401


# Prueba: poner y quitar a un aprendiz como beneficiario
def test_beneficiario():
    # Creo un aprendiz de la ficha 1
    aprendiz = crear_usuario_prueba(3, 1)
    # Lo pongo como beneficiario
    respuesta = client.patch(API + "/usuarios/" + str(aprendiz["id"]) + "/beneficiario", json={"es_beneficiario": True}, headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Ahora tiene que ser beneficiario
    assert respuesta.json()["es_beneficiario"] == True
    # Si lo intento otra vez responde 400
    respuesta = client.patch(API + "/usuarios/" + str(aprendiz["id"]) + "/beneficiario", json={"es_beneficiario": True}, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400
    # Un instructor no puede ser beneficiario
    respuesta = client.patch(API + "/usuarios/2/beneficiario", json={"es_beneficiario": True}, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: crear una ficha y que no se repita el código
def test_crear_ficha():
    # Saco un código al azar de 8 números
    codigo = numero_al_azar()[:8]
    # Armo los datos de la ficha
    datos = {"codigo": codigo, "programa": "Programa de prueba", "jornada": "DIURNA", "cantidad_estudiantes": 20}
    # Creo la ficha
    respuesta = client.post(API + "/fichas", json=datos, headers=ENCARGADO)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Intento crearla otra vez con el mismo código
    respuesta = client.post(API + "/fichas", json=datos, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: una ficha con aprendices solo se desactiva y una sin aprendices se borra
def test_eliminar_fichas():
    # Creo una ficha
    ficha = client.post(API + "/fichas", json={"codigo": numero_al_azar()[:8], "programa": "Ficha con aprendiz", "jornada": "MIXTA"}, headers=ENCARGADO).json()
    # Le creo un aprendiz
    crear_usuario_prueba(3, ficha["id"])
    # Elimino la ficha
    respuesta = client.delete(API + "/fichas/" + str(ficha["id"]), headers=ENCARGADO)
    # Tiene que decir que solo se desactivó
    assert "desactivó" in respuesta.json()["mensaje"]
    # Creo otra ficha sin aprendices
    ficha2 = client.post(API + "/fichas", json={"codigo": numero_al_azar()[:8], "programa": "Ficha sin aprendices", "jornada": "NOCTURNA"}, headers=ENCARGADO).json()
    # La elimino
    respuesta = client.delete(API + "/fichas/" + str(ficha2["id"]), headers=ENCARGADO)
    # Tiene que decir que se eliminó
    assert respuesta.json()["mensaje"] == "La ficha se eliminó"
    # Si la busco ya no existe
    respuesta = client.get(API + "/fichas/" + str(ficha2["id"]), headers=ENCARGADO)
    # Tiene que responder 404
    assert respuesta.status_code == 404


# Prueba: las estadísticas de los grupos
def test_estadisticas_de_grupos():
    # Pido las estadísticas
    respuesta = client.get(API + "/fichas/estadisticas", headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Tiene que haber grupos
    assert respuesta.json()["total_grupos"] >= 1
