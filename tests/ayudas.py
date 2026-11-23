# Funciones y datos que uso en todas las pruebas
# OJO: las pruebas crean registros, es mejor correrlas en una base de datos de prueba

# random sirve para sacar números al azar
import random
# date es una fecha y timedelta sirve para sumar días
from datetime import date, timedelta

# TestClient deja hacer peticiones a la API sin tener que prenderla con uvicorn
from fastapi.testclient import TestClient

# Traigo la aplicación
from app.main import aplicacion

# Creo el cliente para hacer las peticiones
cliente = TestClient(aplicacion)
# Todas las rutas empiezan con esto
api = "/api/v1"


# Función para iniciar sesión y devolver el encabezado con el token
def iniciar_sesion(correo, contrasena):
    # Inicio sesión
    respuesta = cliente.post(api + "/autenticacion/ingresar", json={"correo": correo, "contrasena": contrasena})
    # Saco el token de la respuesta
    token = respuesta.json()["token_acceso"]
    # Devuelvo el encabezado listo para usar
    return {"Authorization": "Bearer " + token}


# Inicio sesión una sola vez con la encargada
cabecera_encargado = iniciar_sesion("encargado@gastrosena.com", "Encargado123")
# Inicio sesión con el instructor (Carlos, que tiene deuda vencida)
cabecera_instructor = iniciar_sesion("instructor@gastrosena.com", "Instructor123")
# Inicio sesión con la aprendiz
cabecera_aprendiz = iniciar_sesion("aprendiz@gastrosena.com", "Aprendiz123")
# Inicio sesión con el aprendiz beneficiario
cabecera_beneficiario = iniciar_sesion("beneficiario@gastrosena.com", "Aprendiz123")
# Inicio sesión con el invitado
cabecera_invitado = iniciar_sesion("invitado@gastrosena.com", "Invitado123")


# Función que da un número al azar de 10 cifras (para que los datos no se repitan)
def numero_al_azar():
    # Saco un número entre 1000000000 y 9999999999 y lo vuelvo texto
    return str(random.randint(1000000000, 9999999999))


# Función para crear un usuario de prueba (rol_id: 2 instructor, 3 aprendiz, 4 invitado)
def crear_usuario_prueba(rol_id, ficha_id=None):
    # Saco un número al azar
    numero = numero_al_azar()
    # Armo los datos del usuario
    datos = {
        "documento": numero,  # Documento al azar
        "nombre": "Usuario de prueba",  # Nombre
        "correo": "prueba" + numero + "@gastrosena.com",  # Correo al azar
        "contrasena": "Prueba12345",  # Contraseña segura
        "rol_id": rol_id,  # Rol
        "ficha_id": ficha_id,  # Ficha
    }
    # Creo el usuario con la encargada
    respuesta = cliente.post(api + "/usuarios", json=datos, headers=cabecera_encargado)
    # Saco los datos del usuario creado
    usuario = respuesta.json()
    # Le agrego la contraseña para usarla en las pruebas
    usuario["contrasena"] = datos["contrasena"]
    # Le agrego el encabezado con su token
    usuario["cabeceras"] = iniciar_sesion(datos["correo"], datos["contrasena"])
    # Devuelvo el usuario
    return usuario


# Función para crear un menú de prueba en una fecha lejana (solo puede haber un menú por día)
def crear_menu_prueba(cantidad=50):
    # Lo intento varias veces por si la fecha ya estaba ocupada
    for intento in range(20):
        # Saco una fecha al azar en el futuro
        fecha = date.today() + timedelta(days=random.randint(400, 40000))
        # Armo los datos del menú
        datos = {
            "fecha": str(fecha),  # Fecha en texto (año-mes-día)
            "nombre": "Menú de prueba",  # Nombre
            "descripcion": "Arroz, proteína, ensalada y jugo",  # Descripción
            "precio_aprendiz": 5000,  # Precio de aprendiz
            "precio_invitado": 8000,  # Precio de invitado
            "cantidad_total": cantidad,  # Cantidad
        }
        # Creo el menú con la encargada
        respuesta = cliente.post(api + "/menus", json=datos, headers=cabecera_encargado)
        # Si se creó bien
        if respuesta.status_code == 201:
            # Devuelvo el menú
            return respuesta.json()
    # Si nunca se pudo crear hago fallar la prueba
    raise Exception("No se pudo crear el menú de prueba")


# Función para crear un material de prueba
def crear_material_prueba(stock=10):
    # Armo los datos del material
    datos = {
        "codigo_barras": "77" + numero_al_azar(),  # Código de barras al azar de 12 números
        "nombre": "Material de prueba",  # Nombre
        "categoria": "GRANO",  # Categoría
        "unidad_medida": "KG",  # Unidad
        "costo_unitario": 1000,  # Costo
        "stock_inicial": stock,  # Stock inicial
        "stock_minimo": 2,  # Stock mínimo
    }
    # Creo el material
    respuesta = cliente.post(api + "/inventario/materiales", json=datos, headers=cabecera_encargado)
    # Devuelvo el material
    return respuesta.json()
