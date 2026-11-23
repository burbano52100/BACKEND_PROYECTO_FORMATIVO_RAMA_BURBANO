# Pruebas de la auditoría (quién crea o modifica cada registro) y de los errores 409 y 500

# TestClient deja hacer peticiones a la API sin prenderla
from fastapi.testclient import TestClient

# Traigo la aplicación para hacer un cliente que no lance los errores del servidor
from app.main import aplicacion
# Traigo la función que da la sesión de la base de datos (la voy a dañar a propósito)
from app.database.conexion import obtener_bd
# Traigo las ayudas de las pruebas
from tests.ayudas import cliente, api, cabecera_encargado, crear_menu_prueba, crear_material_prueba


# Función para saber el id de la encargada
def id_encargada():
    # Pido el perfil de la encargada
    perfil = cliente.get(api + "/autenticacion/perfil", headers=cabecera_encargado).json()
    # Devuelvo su id
    return perfil["id"]


# Prueba: al crear un menú queda guardado quién lo creó
def prueba_menu_guarda_quien_lo_creo():
    # Creo un menú con la encargada
    menu = crear_menu_prueba()
    # Tiene que decir que lo creó la encargada
    assert menu["creado_por"] == id_encargada()
    # Todavía nadie lo ha modificado
    assert menu["modificado_por"] is None


# Prueba: al actualizar un menú queda guardado quién lo modificó y cuándo
def prueba_menu_guarda_quien_lo_modifico():
    # Creo un menú
    menu = crear_menu_prueba()
    # Le cambio el nombre
    respuesta = cliente.put(api + "/menus/" + str(menu["id"]), json={"nombre": "Nombre cambiado"}, headers=cabecera_encargado)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Saco los datos
    datos = respuesta.json()
    # Tiene que decir que lo modificó la encargada
    assert datos["modificado_por"] == id_encargada()
    # Tiene que tener la fecha de la modificación
    assert datos["fecha_modificacion"] is not None


# Prueba: un código de barras repetido responde 409
def prueba_material_repetido_responde_409():
    # Creo un material
    material = crear_material_prueba()
    # Armo otro material con el mismo código de barras
    datos = {"codigo_barras": material["codigo_barras"], "nombre": "Otro material", "categoria": "GRANO", "unidad_medida": "KG", "costo_unitario": 1000, "stock_inicial": 1, "stock_minimo": 1}
    # Intento crearlo
    respuesta = cliente.post(api + "/inventario/materiales", json=datos, headers=cabecera_encargado)
    # Tiene que responder 409
    assert respuesta.status_code == 409
    # El error tiene la misma forma que todos: {"detalle": ...}
    assert respuesta.json()["detalle"] == "Ya existe un material con ese código de barras"


# Prueba: si algo falla dentro del servidor responde 500 sin mostrar detalles técnicos
def prueba_error_interno_no_muestra_detalles():
    # Función dañada que hace fallar la conexión a la base de datos
    def bd_danada():
        # Lanzo un error técnico
        raise RuntimeError("detalle técnico secreto de la conexión")
    # Le digo a la API que use la función dañada en vez de la de verdad
    aplicacion.dependency_overrides[obtener_bd] = bd_danada
    # Uso try y finally para que la API siempre vuelva a quedar bien
    try:
        # Cliente que devuelve la respuesta 500 en vez de lanzar el error
        cliente_500 = TestClient(aplicacion, raise_server_exceptions=False)
        # Pido una ruta privada
        respuesta = cliente_500.get(api + "/menus/hoy", headers=cabecera_encargado)
    # Esto se ejecuta siempre
    finally:
        # Quito la función dañada
        aplicacion.dependency_overrides.clear()
    # Tiene que responder 500
    assert respuesta.status_code == 500
    # El mensaje es general
    assert respuesta.json()["detalle"] == "Ocurrió un error interno, intente más tarde"
    # Y no muestra el detalle técnico
    assert "secreto" not in respuesta.text


# Prueba: cada ruta está documentada en Swagger con descripción y el rol que se necesita
def prueba_rutas_documentadas():
    # Pido la documentación de la API
    documentacion = cliente.get("/openapi.json").json()
    # Recorro cada ruta
    for ruta, metodos in documentacion["paths"].items():
        # Recorro cada método de la ruta (get, post, put...)
        for metodo, detalle in metodos.items():
            # Tiene que tener un resumen
            assert detalle.get("summary"), metodo + " " + ruta + " no tiene resumen"
            # La descripción tiene que decir qué rol se necesita
            assert "Rol requerido" in detalle.get("description", ""), metodo + " " + ruta + " no dice el rol"
