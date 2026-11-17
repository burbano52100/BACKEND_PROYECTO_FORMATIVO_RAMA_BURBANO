# Pruebas del login, los tokens y la contraseña

# Para crear un token vencido a mano
from datetime import datetime, timedelta, timezone

# jwt sirve para crear el token vencido
import jwt

# Traigo la clave secreta para firmar el token vencido
from app.config import SECRET_KEY
# Traigo las ayudas de las pruebas
from tests.ayudas import client, API, ENCARGADO, crear_usuario_prueba


# Prueba: el login con datos correctos devuelve los tokens y el rol
def test_login_correcto():
    # Hago el login con la encargada
    respuesta = client.post(API + "/auth/login", json={"correo": "encargado@gastrosena.com", "password": "Encargado123"})
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Saco los datos
    datos = respuesta.json()
    # Tiene que traer el access token
    assert datos["access_token"] != ""
    # Tiene que traer el refresh token
    assert datos["refresh_token"] != ""
    # El rol tiene que ser encargado
    assert datos["rol"] == "encargado"


# Prueba: con la contraseña mala responde 401
def test_login_con_contrasena_mala():
    # Hago el login con una contraseña que no es
    respuesta = client.post(API + "/auth/login", json={"correo": "encargado@gastrosena.com", "password": "NoEsLaClave1"})
    # Tiene que responder 401
    assert respuesta.status_code == 401
    # Tiene que decir el mensaje de error
    assert respuesta.json()["detail"] == "Correo o contraseña incorrectos"


# Prueba: una cuenta inactiva no puede entrar
def test_login_cuenta_inactiva():
    # Hago el login con la cuenta inactiva
    respuesta = client.post(API + "/auth/login", json={"correo": "inactivo@gastrosena.com", "password": "Aprendiz123"})
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: sin token no se puede entrar a las rutas privadas
def test_peticion_sin_token():
    # Pido el menú de hoy sin token
    respuesta = client.get(API + "/menus/hoy")
    # Tiene que responder 401
    assert respuesta.status_code == 401


# Prueba: con un token falso responde 401
def test_token_falso():
    # Pido el menú de hoy con un token inventado
    respuesta = client.get(API + "/menus/hoy", headers={"Authorization": "Bearer token-falso"})
    # Tiene que responder 401
    assert respuesta.status_code == 401


# Prueba: con un token vencido responde 401
def test_token_vencido():
    # Armo un token que se venció hace un minuto
    datos = {"sub": "1", "tipo": "access", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
    # Lo firmo con la clave secreta
    token = jwt.encode(datos, SECRET_KEY, algorithm="HS256")
    # Pido el menú de hoy con ese token
    respuesta = client.get(API + "/menus/hoy", headers={"Authorization": "Bearer " + token})
    # Tiene que responder 401
    assert respuesta.status_code == 401
    # El mensaje tiene que decir que se venció
    assert "venció" in respuesta.json()["detail"]


# Prueba: el refresh token da tokens nuevos pero no sirve como access token
def test_refresh_token():
    # Hago el login
    tokens = client.post(API + "/auth/login", json={"correo": "encargado@gastrosena.com", "password": "Encargado123"}).json()
    # Pido tokens nuevos con el refresh token
    respuesta = client.post(API + "/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Intento usar el refresh token como si fuera el access token
    respuesta2 = client.get(API + "/auth/perfil", headers={"Authorization": "Bearer " + tokens["refresh_token"]})
    # Tiene que responder 401
    assert respuesta2.status_code == 401


# Prueba: el perfil no muestra la contraseña
def test_perfil_no_muestra_la_contrasena():
    # Pido el perfil de la encargada
    respuesta = client.get(API + "/auth/perfil", headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # El correo tiene que ser el de la encargada
    assert respuesta.json()["correo"] == "encargado@gastrosena.com"
    # No puede venir la contraseña
    assert "password" not in respuesta.json()


# Prueba: después de 5 intentos fallidos la cuenta se bloquea
def test_bloqueo_despues_de_5_intentos():
    # Creo un invitado de prueba
    usuario = crear_usuario_prueba(4)
    # Datos con la contraseña mala
    datos_malos = {"correo": usuario["correo"], "password": "Equivocada123"}
    # Me equivoco 4 veces
    for intento in range(4):
        # Hago el login malo
        respuesta = client.post(API + "/auth/login", json=datos_malos)
        # Tiene que responder 401
        assert respuesta.status_code == 401
    # Me equivoco la quinta vez
    respuesta = client.post(API + "/auth/login", json=datos_malos)
    # Ahora tiene que responder 403 porque se bloqueó
    assert respuesta.status_code == 403
    # Aunque ponga la contraseña buena sigue bloqueada
    respuesta = client.post(API + "/auth/login", json={"correo": usuario["correo"], "password": usuario["password"]})
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: cambiar la contraseña propia
def test_cambiar_contrasena():
    # Creo un invitado de prueba
    usuario = crear_usuario_prueba(4)
    # Intento poner una contraseña sin mayúsculas ni números
    respuesta = client.put(API + "/auth/password", headers=usuario["headers"], json={"password_actual": usuario["password"], "password_nueva": "solominusculas"})
    # Tiene que responder 400
    assert respuesta.status_code == 400
    # Intento con la contraseña actual mala
    respuesta = client.put(API + "/auth/password", headers=usuario["headers"], json={"password_actual": "NoEsLaActual1", "password_nueva": "NuevaClave2026"})
    # Tiene que responder 400
    assert respuesta.status_code == 400
    # Ahora lo hago bien
    respuesta = client.put(API + "/auth/password", headers=usuario["headers"], json={"password_actual": usuario["password"], "password_nueva": "NuevaClave2026"})
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Pruebo entrar con la contraseña nueva
    respuesta = client.post(API + "/auth/login", json={"correo": usuario["correo"], "password": "NuevaClave2026"})
    # Tiene que responder 200
    assert respuesta.status_code == 200
