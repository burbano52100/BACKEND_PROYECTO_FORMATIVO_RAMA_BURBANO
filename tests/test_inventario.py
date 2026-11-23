# Pruebas del inventario y el kardex

# Traigo las ayudas de las pruebas
from tests.ayudas import cliente, api, cabecera_encargado, crear_material_prueba


# Prueba: al crear un material con stock se guarda una entrada en el kardex
def prueba_crear_material_hace_entrada_en_kardex():
    # Creo un material con 10 de stock
    material = crear_material_prueba(10)
    # Tiene que tener 10 de stock
    assert material["stock"] == 10
    # Pido el kardex de ese material
    respuesta = cliente.get(api + "/inventario/kardex?material_id=" + str(material["id"]), headers=cabecera_encargado)
    # Saco la lista de movimientos
    movimientos = respuesta.json()
    # Tiene que haber un solo movimiento
    assert len(movimientos) == 1
    # Tiene que ser una entrada
    assert movimientos[0]["tipo"] == "ENTRADA"
    # De 10
    assert movimientos[0]["entrada"] == 10


# Prueba: no se puede sacar más de lo que hay
def prueba_salida_mayor_que_el_stock():
    # Creo un material con 5 de stock
    material = crear_material_prueba(5)
    # Intento sacar 8
    respuesta = cliente.post(api + "/inventario/movimientos", json={"material_id": material["id"], "tipo": "SALIDA", "cantidad": 8, "concepto": "Prueba de salida"}, headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: una merma baja el stock
def prueba_merma_baja_el_stock():
    # Creo un material con 10 de stock
    material = crear_material_prueba(10)
    # Hago una merma de 2.5
    respuesta = cliente.post(api + "/inventario/movimientos", json={"material_id": material["id"], "tipo": "MERMA", "cantidad": 2.5, "concepto": "Se dañó"}, headers=cabecera_encargado)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Tiene que quedar 7.5
    assert respuesta.json()["saldo"] == 7.5
    # Consulto el material
    material_despues = cliente.get(api + "/inventario/materiales/" + str(material["id"]), headers=cabecera_encargado).json()
    # El stock tiene que ser 7.5
    assert material_despues["stock"] == 7.5


# Prueba: el estado del stock se calcula bien con los datos de prueba
def prueba_estado_del_stock():
    # El arroz (id 1) está bien
    assert cliente.get(api + "/inventario/materiales/1", headers=cabecera_encargado).json()["estado_stock"] == "BUENO"
    # El fríjol (id 2) está bajo
    assert cliente.get(api + "/inventario/materiales/2", headers=cabecera_encargado).json()["estado_stock"] == "BAJO"
    # El pollo (id 3) se está venciendo
    assert cliente.get(api + "/inventario/materiales/3", headers=cabecera_encargado).json()["estado_stock"] == "VENCIENDO"
    # El tomate (id 6) está crítico
    assert cliente.get(api + "/inventario/materiales/6", headers=cabecera_encargado).json()["estado_stock"] == "CRITICO"


# Prueba: no se puede eliminar un material que usa una receta activa
def prueba_no_se_borra_material_de_receta_activa():
    # Intento eliminar el arroz (lo usan varias recetas)
    respuesta = cliente.delete(api + "/inventario/materiales/1", headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400
