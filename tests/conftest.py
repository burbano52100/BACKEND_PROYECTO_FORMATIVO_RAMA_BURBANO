"""Configuración compartida de las pruebas.

Requisitos: la base de datos creada con los scripts de database/ y el archivo .env
apuntando a ella. Use una base de datos de PRUEBAS: las pruebas crean registros.
Ejecutar desde la carpeta del proyecto:  pytest -v
"""

# os permite modificar las variables de entorno
import os
# random genera números aleatorios (para datos únicos)
import random
# timedelta = duración (para sumar días a una fecha)
from datetime import timedelta

# Las pruebas deben poder correr a cualquier hora: se amplía el horario de reservas.
# (Se define antes de importar la app, porque la configuración se lee al importarla.)
# Horario de inicio: medianoche
os.environ["HORA_INICIO_RESERVAS"] = "00:00"
# Horario de fin: 23:59:59
os.environ["HORA_FIN_RESERVAS"] = "23:59:59"

# pytest = herramienta de pruebas ("noqa: E402" le dice al revisor de estilo que el import tardío es intencional)
import pytest  # noqa: E402
# TestClient permite hacer peticiones a la API sin levantar el servidor
from fastapi.testclient import TestClient  # noqa: E402

# Fecha de hoy en Colombia
from app.core import tiempo  # noqa: E402
# La aplicación FastAPI
from app.main import app  # noqa: E402

# Prefijo de todas las rutas
API = "/api/v1"

# Credenciales de los usuarios de prueba (están en 02_dml.sql)
# Encargado
ENCARGADO = {"correo": "encargado@gastrosena.com", "password": "Encargado123"}
# Instructor
INSTRUCTOR = {"correo": "instructor@gastrosena.com", "password": "Instructor123"}
# Aprendiz
APRENDIZ = {"correo": "aprendiz@gastrosena.com", "password": "Aprendiz123"}
# Aprendiz beneficiario
BENEFICIARIO = {"correo": "beneficiario@gastrosena.com", "password": "Aprendiz123"}
# Invitado
INVITADO = {"correo": "invitado@gastrosena.com", "password": "Invitado123"}
# Cuenta inactiva
INACTIVO = {"correo": "inactivo@gastrosena.com", "password": "Aprendiz123"}

# Ids que generan los scripts sobre una base de datos nueva
# Ids de los roles instructor, aprendiz e invitado
ROL_INSTRUCTOR, ROL_APRENDIZ, ROL_INVITADO = 2, 3, 4
# Id de la ficha 2847251 (ADSO)
FICHA_ADSO = 1


# Fixture = dato que pytest prepara y entrega a las pruebas; scope="session" = se crea una sola vez
@pytest.fixture(scope="session")
# Crea el cliente de pruebas
def cliente():
    # "with" arranca la aplicación y la cierra al terminar
    with TestClient(app) as cliente:
        # Entrega el cliente a las pruebas
        yield cliente


# Inicia sesión y devuelve el encabezado con el token
def encabezado_de(cliente: TestClient, credenciales: dict) -> dict:
    """Inicia sesión y devuelve el header Authorization listo para usar."""
    # POST /auth/login con las credenciales
    respuesta = cliente.post(f"{API}/auth/login", json=credenciales)
    # Verifica que el login funcionó (si no, muestra el texto de la respuesta)
    assert respuesta.status_code == 200, respuesta.text
    # Devuelve {"Authorization": "Bearer <token>"}
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


# Fixture con el encabezado del encargado
@pytest.fixture(scope="session")
# Una prueba que pida "encargado" recibe este encabezado
def encargado(cliente):
    # Inicia sesión como encargado
    return encabezado_de(cliente, ENCARGADO)


# Fixture con el encabezado del instructor
@pytest.fixture(scope="session")
# Una prueba que pida "instructor" recibe este encabezado
def instructor(cliente):
    # Inicia sesión como instructor
    return encabezado_de(cliente, INSTRUCTOR)


# Fixture con el encabezado del aprendiz
@pytest.fixture(scope="session")
# Una prueba que pida "aprendiz" recibe este encabezado
def aprendiz(cliente):
    # Inicia sesión como aprendiz
    return encabezado_de(cliente, APRENDIZ)


# Fixture con el encabezado del beneficiario
@pytest.fixture(scope="session")
# Una prueba que pida "beneficiario" recibe este encabezado
def beneficiario(cliente):
    # Inicia sesión como beneficiario
    return encabezado_de(cliente, BENEFICIARIO)


# Fixture con el encabezado del invitado
@pytest.fixture(scope="session")
# Una prueba que pida "invitado" recibe este encabezado
def invitado(cliente):
    # Inicia sesión como invitado
    return encabezado_de(cliente, INVITADO)


# Genera un número aleatorio como texto
def aleatorio(digitos: int = 10) -> str:
    """Número aleatorio para crear datos únicos (documentos, códigos, correos)."""
    # Número entre 10^(digitos-1) y 10^digitos - 1 (siempre tiene "digitos" cifras)
    return str(random.randint(10 ** (digitos - 1), 10**digitos - 1))


# Crea un usuario nuevo con el rol indicado
def crear_usuario(cliente: TestClient, encargado: dict, rol_id: int, ficha_id: int | None = None) -> dict:
    """Crea una cuenta nueva y devuelve su id, credenciales y encabezado de sesión."""
    # Número aleatorio para documento y correo
    numero = aleatorio()
    # Datos del usuario nuevo
    datos = {
        # Documento único
        "documento": numero,
        # Nombre
        "nombre": "Usuario de prueba",
        # Correo único
        "correo": f"prueba{numero}@gastrosena.com",
        # Contraseña que cumple la política
        "password": "Prueba12345",
        # Rol
        "rol_id": rol_id,
        # Ficha (solo aprendices)
        "ficha_id": ficha_id,
    }
    # POST /usuarios como encargado
    respuesta = cliente.post(f"{API}/usuarios", json=datos, headers=encargado)
    # Verifica que se creó (201)
    assert respuesta.status_code == 201, respuesta.text
    # Credenciales del usuario nuevo
    credenciales = {"correo": datos["correo"], "password": datos["password"]}
    # Devuelve id, credenciales y encabezado de sesión
    return {"id": respuesta.json()["id"], **credenciales, "headers": encabezado_de(cliente, credenciales)}


# Crea un menú en una fecha futura libre
def crear_menu(cliente: TestClient, encargado: dict, cantidad: int = 50) -> dict:
    """Crea un menú en una fecha futura libre (solo puede haber un menú por fecha)."""
    # Intenta hasta 10 veces (por si la fecha aleatoria ya está ocupada)
    for _ in range(10):
        # Fecha aleatoria lejana en el futuro
        fecha = tiempo.hoy() + timedelta(days=random.randint(400, 40000))
        # Datos del menú
        datos = {
            # Fecha en formato AAAA-MM-DD
            "fecha": fecha.isoformat(),
            # Nombre
            "nombre": "Menú de prueba",
            # Descripción
            "descripcion": "Arroz, proteína, ensalada y jugo",
            # Precio de aprendiz
            "precio_aprendiz": 5000,
            # Precio de invitado
            "precio_invitado": 8000,
            # Cupo
            "cantidad_total": cantidad,
        }
        # POST /menus como encargado
        respuesta = cliente.post(f"{API}/menus", json=datos, headers=encargado)
        # Si se creó...
        if respuesta.status_code == 201:
            # ...devuelve el menú
            return respuesta.json()
    # Si en 10 intentos no se pudo, la prueba falla
    raise AssertionError("No se pudo crear un menú de prueba")


# Reserva un menú con el encabezado de una persona
def reservar(cliente: TestClient, headers: dict, menu_id: int):
    # POST /reservas y devuelve la respuesta completa
    return cliente.post(f"{API}/reservas", json={"menu_id": menu_id}, headers=headers)
