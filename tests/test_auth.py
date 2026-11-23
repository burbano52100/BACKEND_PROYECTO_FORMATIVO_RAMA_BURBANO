# Pruebas del inicio de sesión, los tokens y la contraseña

# Para crear un token vencido a mano
from datetime import datetime, timedelta, timezone

# jwt sirve para crear el token vencido
import jwt

# Traigo la clave secreta para firmar el token vencido
from app.core.config import clave_secreta
# Traigo las ayudas de las pruebas
from tests.ayudas import cliente, api, cabecera_encargado, crear_usuario_prueba


# Prueba: iniciar sesión con datos correctos devuelve los tokens y el rol
def prueba_ingreso_correcto():
    # Inicio sesión con la encargada
    respuesta = cliente.post(api + "/autenticacion/ingresar", json={"correo": "encargado@gastrosena.com", "contrasena": "Encargado123"})
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Saco los datos
    datos = respuesta.json()
    # Tiene que traer el token de acceso
    assert datos["token_acceso"] != ""
    # Tiene que traer el token para renovar
    assert datos["token_renovar"] != ""
    # El rol tiene que ser encargado
    assert datos["rol"] == "encargado"


# Prueba: con la contraseña mala responde 401
def prueba_ingreso_con_contrasena_mala():
    # Inicio sesión con una contraseña que no es
    respuesta = cliente.post(api + "/autenticacion/ingresar", json={"correo": "encargado@gastrosena.com", "contrasena": "NoEsLaClave1"})
    # Tiene que responder 401
    assert respuesta.status_code == 401
    # Tiene que decir el mensaje de error
    assert respuesta.json()["detalle"] == "Correo o contraseña incorrectos"


# Prueba: una cuenta inactiva no puede entrar
def prueba_ingreso_cuenta_inactiva():
    # Inicio sesión con la cuenta inactiva
    respuesta = cliente.post(api + "/autenticacion/ingresar", json={"correo": "inactivo@gastrosena.com", "contrasena": "Aprendiz123"})
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: sin token no se puede entrar a las rutas privadas
def prueba_peticion_sin_token():
    # Pido el menú de hoy sin token
    respuesta = cliente.get(api + "/menus/hoy")
    # Tiene que responder 401
    assert respuesta.status_code == 401


# Prueba: con un token falso responde 401
def prueba_token_falso():
    # Pido el menú de hoy con un token inventado
    respuesta = cliente.get(api + "/menus/hoy", headers={"Authorization": "Bearer token-falso"})
    # Tiene que responder 401
    assert respuesta.status_code == 401


# Prueba: con un token vencido responde 401
def prueba_token_vencido():
    # Armo un token que se venció hace un minuto
    datos = {"usuario_id": "1", "tipo": "acceso", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
    # Lo firmo con la clave secreta
    token = jwt.encode(datos, clave_secreta, algorithm="HS256")
    # Pido el menú de hoy con ese token
    respuesta = cliente.get(api + "/menus/hoy", headers={"Authorization": "Bearer " + token})
    # Tiene que responder 401
    assert respuesta.status_code == 401
    # El mensaje tiene que decir que se venció
    assert "venció" in respuesta.json()["detalle"]


# Prueba: el token para renovar da tokens nuevos pero no sirve como token de acceso
def prueba_renovar_token():
    # Inicio sesión
    tokens = cliente.post(api + "/autenticacion/ingresar", json={"correo": "encargado@gastrosena.com", "contrasena": "Encargado123"}).json()
    # Pido tokens nuevos con el token para renovar
    respuesta = cliente.post(api + "/autenticacion/renovar", json={"token_renovar": tokens["token_renovar"]})
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Intento usar el token para renovar como si fuera el token de acceso
    respuesta2 = cliente.get(api + "/autenticacion/perfil", headers={"Authorization": "Bearer " + tokens["token_renovar"]})
    # Tiene que responder 401
    assert respuesta2.status_code == 401


# Prueba: el perfil no muestra la contraseña
def prueba_perfil_no_muestra_la_contrasena():
    # Pido el perfil de la encargada
    respuesta = cliente.get(api + "/autenticacion/perfil", headers=cabecera_encargado)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # El correo tiene que ser el de la encargada
    assert respuesta.json()["correo"] == "encargado@gastrosena.com"
    # No puede venir la contraseña
    assert "contrasena" not in respuesta.json()


# Prueba: después de 5 intentos fallidos la cuenta se bloquea
def prueba_bloqueo_despues_de_5_intentos():
    # Creo un invitado de prueba
    usuario = crear_usuario_prueba(4)
    # Datos con la contraseña mala
    datos_malos = {"correo": usuario["correo"], "contrasena": "Equivocada123"}
    # Me equivoco 4 veces
    for intento in range(4):
        # Intento iniciar sesión con datos malos
        respuesta = cliente.post(api + "/autenticacion/ingresar", json=datos_malos)
        # Tiene que responder 401
        assert respuesta.status_code == 401
    # Me equivoco la quinta vez
    respuesta = cliente.post(api + "/autenticacion/ingresar", json=datos_malos)
    # Ahora tiene que responder 403 porque se bloqueó
    assert respuesta.status_code == 403
    # Aunque ponga la contraseña buena sigue bloqueada
    respuesta = cliente.post(api + "/autenticacion/ingresar", json={"correo": usuario["correo"], "contrasena": usuario["contrasena"]})
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: cambiar la contraseña propia
def prueba_cambiar_contrasena():
    # Creo un invitado de prueba
    usuario = crear_usuario_prueba(4)
    # Intento poner una contraseña sin mayúsculas ni números
    respuesta = cliente.put(api + "/autenticacion/contrasena", headers=usuario["cabeceras"], json={"contrasena_actual": usuario["contrasena"], "contrasena_nueva": "solominusculas"})
    # Tiene que responder 400
    assert respuesta.status_code == 400
    # Intento con la contraseña actual mala
    respuesta = cliente.put(api + "/autenticacion/contrasena", headers=usuario["cabeceras"], json={"contrasena_actual": "NoEsLaActual1", "contrasena_nueva": "NuevaClave2026"})
    # Tiene que responder 400
    assert respuesta.status_code == 400
    # Ahora lo hago bien
    respuesta = cliente.put(api + "/autenticacion/contrasena", headers=usuario["cabeceras"], json={"contrasena_actual": usuario["contrasena"], "contrasena_nueva": "NuevaClave2026"})
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Pruebo entrar con la contraseña nueva
    respuesta = cliente.post(api + "/autenticacion/ingresar", json={"correo": usuario["correo"], "contrasena": "NuevaClave2026"})
    # Tiene que responder 200
    assert respuesta.status_code == 200
