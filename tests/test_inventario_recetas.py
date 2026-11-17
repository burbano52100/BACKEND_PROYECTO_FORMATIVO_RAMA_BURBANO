# Pruebas del inventario y las recetas

# Traigo las ayudas de las pruebas
from tests.ayudas import client, API, ENCARGADO, numero_al_azar


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
    respuesta = client.post(API + "/inventario/materiales", json=datos, headers=ENCARGADO)
    # Devuelvo el material
    return respuesta.json()


# Prueba: al crear un material con stock se guarda una entrada en el kardex
def test_crear_material_hace_entrada_en_kardex():
    # Creo un material con 10 de stock
    material = crear_material_prueba(10)
    # Tiene que tener 10 de stock
    assert material["stock"] == 10
    # Pido el kardex de ese material
    respuesta = client.get(API + "/inventario/kardex?material_id=" + str(material["id"]), headers=ENCARGADO)
    # Saco la lista de movimientos
    movimientos = respuesta.json()
    # Tiene que haber un solo movimiento
    assert len(movimientos) == 1
    # Tiene que ser una entrada
    assert movimientos[0]["tipo"] == "ENTRADA"
    # De 10
    assert movimientos[0]["entrada"] == 10


# Prueba: no se puede sacar más de lo que hay
def test_salida_mayor_que_el_stock():
    # Creo un material con 5 de stock
    material = crear_material_prueba(5)
    # Intento sacar 8
    respuesta = client.post(API + "/inventario/movimientos", json={"material_id": material["id"], "tipo": "SALIDA", "cantidad": 8, "concepto": "Prueba de salida"}, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: una merma baja el stock
def test_merma_baja_el_stock():
    # Creo un material con 10 de stock
    material = crear_material_prueba(10)
    # Hago una merma de 2.5
    respuesta = client.post(API + "/inventario/movimientos", json={"material_id": material["id"], "tipo": "MERMA", "cantidad": 2.5, "concepto": "Se dañó"}, headers=ENCARGADO)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Tiene que quedar 7.5
    assert respuesta.json()["saldo"] == 7.5
    # Consulto el material
    material_despues = client.get(API + "/inventario/materiales/" + str(material["id"]), headers=ENCARGADO).json()
    # El stock tiene que ser 7.5
    assert material_despues["stock"] == 7.5


# Prueba: el estado del stock se calcula bien con los datos de prueba
def test_estado_del_stock():
    # El arroz (id 1) está bien
    assert client.get(API + "/inventario/materiales/1", headers=ENCARGADO).json()["estado_stock"] == "BUENO"
    # El fríjol (id 2) está bajo
    assert client.get(API + "/inventario/materiales/2", headers=ENCARGADO).json()["estado_stock"] == "BAJO"
    # El pollo (id 3) se está venciendo
    assert client.get(API + "/inventario/materiales/3", headers=ENCARGADO).json()["estado_stock"] == "VENCIENDO"
    # El tomate (id 6) está crítico
    assert client.get(API + "/inventario/materiales/6", headers=ENCARGADO).json()["estado_stock"] == "CRITICO"


# Prueba: no se puede eliminar un material que usa una receta activa
def test_no_se_borra_material_de_receta_activa():
    # Intento eliminar el arroz (lo usan varias recetas)
    respuesta = client.delete(API + "/inventario/materiales/1", headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: el costo de la receta se calcula bien
def test_costo_de_la_receta():
    # Pido el bistec a caballo (id 7), que cuesta más de lo que se vende
    receta = client.get(API + "/recetas/7", headers=ENCARGADO).json()
    # Cuesta 5720 hacerlo
    assert receta["costo_produccion"] == 5720
    # Se pierden 720
    assert receta["margen"] == -720
    # Tiene que salir la alerta
    assert receta["alerta_margen_negativo"] == True


# Prueba: un material no se puede repetir en la misma receta
def test_receta_con_material_repetido():
    # Armo una receta con el arroz dos veces
    datos = {"nombre": "Receta repetida " + numero_al_azar(), "precio_venta": 5000, "ingredientes": [{"material_id": 1, "cantidad": 0.1}, {"material_id": 1, "cantidad": 0.2}]}
    # Intento crearla
    respuesta = client.post(API + "/recetas", json=datos, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: crear, actualizar y eliminar una receta
def test_crear_actualizar_y_eliminar_receta():
    # Armo la receta con arroz (4200 el kilo) y papa (2500 el kilo)
    datos = {"nombre": "Receta de prueba " + numero_al_azar(), "precio_venta": 5000, "ingredientes": [{"material_id": 1, "cantidad": 0.5}, {"material_id": 5, "cantidad": 0.2}]}
    # Creo la receta
    respuesta = client.post(API + "/recetas", json=datos, headers=ENCARGADO)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Saco la receta
    receta = respuesta.json()
    # El costo es 0.5 x 4200 + 0.2 x 2500 = 2600
    assert receta["costo_produccion"] == 2600
    # Le cambio los ingredientes por solo arroz
    respuesta = client.put(API + "/recetas/" + str(receta["id"]), json={"ingredientes": [{"material_id": 1, "cantidad": 1}]}, headers=ENCARGADO)
    # El costo ahora es 4200
    assert respuesta.json()["costo_produccion"] == 4200
    # Elimino la receta
    respuesta = client.delete(API + "/recetas/" + str(receta["id"]), headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Si la busco ya no existe
    respuesta = client.get(API + "/recetas/" + str(receta["id"]), headers=ENCARGADO)
    # Tiene que responder 404
    assert respuesta.status_code == 404
