"""Pruebas de autenticación, seguridad y permisos por rol."""

# Duración (para crear un token ya vencido)
from datetime import timedelta

# Función que crea tokens de acceso
from app.core.seguridad import crear_access_token
# Constantes y funciones de apoyo de conftest.py
from tests.conftest import API, ENCARGADO, INACTIVO, ROL_INVITADO, crear_usuario


# Prueba: un login correcto devuelve los tokens y el rol
def test_login_exitoso_devuelve_tokens_y_rol(cliente):
    # Inicia sesión como encargado
    respuesta = cliente.post(f"{API}/auth/login", json=ENCARGADO)
    # Debe responder 200
    assert respuesta.status_code == 200
    # Cuerpo de la respuesta como diccionario
    cuerpo = respuesta.json()
    # Deben venir los dos tokens (no vacíos)
    assert cuerpo["access_token"] and cuerpo["refresh_token"]
    # El rol debe ser encargado
    assert cuerpo["rol"] == "encargado"


# Prueba: credenciales incorrectas responden 401 con un mensaje genérico
def test_login_incorrecto_responde_401_con_mensaje_generico(cliente):
    # Intenta iniciar sesión con un correo que no existe
    respuesta = cliente.post(f"{API}/auth/login", json={"correo": "nadie@gastrosena.com", "password": "Xx123456"})
    # Debe responder 401
    assert respuesta.status_code == 401
    # Debe tener la estructura de error única con el mensaje genérico
    assert respuesta.json() == {"estado": 401, "mensaje": "Correo o contraseña incorrectos.", "detalles": None}


# Prueba: una cuenta inactiva no puede iniciar sesión
def test_cuenta_inactiva_no_inicia_sesion(cliente):
    # Inicia sesión con la cuenta inactiva
    respuesta = cliente.post(f"{API}/auth/login", json=INACTIVO)
    # Debe responder 403
    assert respuesta.status_code == 403
    # El mensaje debe mencionar que está inactiva
    assert "inactiva" in respuesta.json()["mensaje"]


# Prueba: sin token responde 401
def test_peticion_sin_token_responde_401(cliente):
    # Pide el menú de hoy sin encabezado Authorization
    respuesta = cliente.get(f"{API}/menus/hoy")
    # Debe responder 401
    assert respuesta.status_code == 401
    # Debe incluir el encabezado WWW-Authenticate
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


# Prueba: un token falso responde 401
def test_token_invalido_responde_401(cliente):
    # Envía un texto que no es un JWT
    respuesta = cliente.get(f"{API}/menus/hoy", headers={"Authorization": "Bearer token-falso"})
    # Debe responder 401
    assert respuesta.status_code == 401
    # Con este mensaje
    assert respuesta.json()["mensaje"] == "El token no es válido."


# Prueba: un token vencido responde 401
def test_token_vencido_responde_401(cliente):
    # Crea un token que venció hace 1 segundo (duración negativa)
    token = crear_access_token(1, duracion=timedelta(seconds=-1))
    # Lo usa en una petición
    respuesta = cliente.get(f"{API}/menus/hoy", headers={"Authorization": f"Bearer {token}"})
    # Debe responder 401
    assert respuesta.status_code == 401
    # El mensaje debe decir que expiró
    assert "expirado" in respuesta.json()["mensaje"]


# Prueba: el refresh renueva tokens, pero no sirve como token de acceso
def test_refresh_entrega_tokens_y_no_sirve_como_access(cliente):
    # Inicia sesión y guarda los tokens
    tokens = cliente.post(f"{API}/auth/login", json=ENCARGADO).json()
    # Pide tokens nuevos con el refresh token
    renovado = cliente.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    # Debe responder 200
    assert renovado.status_code == 200
    # Intenta usar el refresh token como si fuera de acceso
    con_refresh = cliente.get(f"{API}/auth/perfil", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    # Debe responder 401
    assert con_refresh.status_code == 401


# Prueba: el perfil nunca devuelve la contraseña
def test_perfil_no_expone_la_contrasena(cliente, encargado):
    # Consulta el perfil del encargado
    cuerpo = cliente.get(f"{API}/auth/perfil", headers=encargado).json()
    # Debe ser el correo del encargado
    assert cuerpo["correo"] == ENCARGADO["correo"]
    # No deben aparecer los campos de contraseña
    assert "password" not in cuerpo and "password_hash" not in cuerpo


# Prueba: después de 5 intentos fallidos la cuenta se bloquea
def test_bloqueo_tras_cinco_intentos_fallidos(cliente, encargado):
    # Crea un usuario nuevo (para no bloquear a los usuarios de prueba)
    usuario = crear_usuario(cliente, encargado, ROL_INVITADO)
    # Credenciales con contraseña incorrecta
    malas = {"correo": usuario["correo"], "password": "Incorrecta123"}
    # Repite 4 veces...
    for _ in range(4):
        # ...cada intento fallido responde 401
        assert cliente.post(f"{API}/auth/login", json=malas).status_code == 401
    # Quinto intento fallido
    quinto = cliente.post(f"{API}/auth/login", json=malas)
    # Debe responder 403 (bloqueada)
    assert quinto.status_code == 403
    # El mensaje debe decir que está bloqueada
    assert "bloqueada" in quinto.json()["mensaje"]
    # Aun con la contraseña correcta sigue bloqueada
    # Credenciales correctas
    buenas = {"correo": usuario["correo"], "password": usuario["password"]}
    # Sigue respondiendo 403
    assert cliente.post(f"{API}/auth/login", json=buenas).status_code == 403


# Prueba: cambiar la propia contraseña
def test_cambiar_mi_contrasena(cliente, encargado):
    # Crea un usuario nuevo
    usuario = crear_usuario(cliente, encargado, ROL_INVITADO)
    # Intenta poner una contraseña débil (solo minúsculas)
    debil = cliente.put(f"{API}/auth/password", headers=usuario["headers"],
                        json={"password_actual": usuario["password"], "password_nueva": "solominusculas"})  # Cuerpo
    # Debe responder 422
    assert debil.status_code == 422
    # Intenta con una contraseña actual equivocada
    erronea = cliente.put(f"{API}/auth/password", headers=usuario["headers"],
                          json={"password_actual": "NoEsLaActual1", "password_nueva": "NuevaClave2026"})  # Cuerpo
    # Debe responder 400
    assert erronea.status_code == 400
    # Cambio correcto
    respuesta = cliente.put(f"{API}/auth/password", headers=usuario["headers"],
                            json={"password_actual": usuario["password"], "password_nueva": "NuevaClave2026"})  # Cuerpo
    # Debe responder 200
    assert respuesta.status_code == 200
    # Inicia sesión con la contraseña nueva
    nuevo = cliente.post(f"{API}/auth/login", json={"correo": usuario["correo"], "password": "NuevaClave2026"})
    # Debe funcionar
    assert nuevo.status_code == 200


# Prueba: los roles sin permiso reciben 403
def test_roles_sin_permiso_reciben_403(cliente, aprendiz, invitado, instructor, encargado):
    # Un aprendiz no puede listar usuarios
    assert cliente.get(f"{API}/usuarios", headers=aprendiz).status_code == 403
    # Un invitado no puede ver el inventario
    assert cliente.get(f"{API}/inventario/materiales", headers=invitado).status_code == 403
    # Un instructor no puede ver los indicadores
    assert cliente.get(f"{API}/reportes/indicadores", headers=instructor).status_code == 403
    # Un aprendiz no tiene cuenta mensual
    assert cliente.get(f"{API}/cartera/mi-cuenta", headers=aprendiz).status_code == 403
    # El encargado no puede reservar
    assert cliente.post(f"{API}/reservas", json={"menu_id": 1}, headers=encargado).status_code == 403


# Prueba: una ruta que no existe responde con el formato de error de la API
def test_ruta_inexistente_usa_el_formato_de_error(cliente, encargado):
    # Pide una ruta inexistente
    respuesta = cliente.get(f"{API}/no-existe", headers=encargado)
    # Debe responder 404
    assert respuesta.status_code == 404
    # Con la estructura {"estado": 404, ...}
    assert respuesta.json()["estado"] == 404
