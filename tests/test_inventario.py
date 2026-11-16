"""Pruebas del inventario: materiales, estado del stock, kardex y mermas."""

# Constantes y funciones de apoyo de conftest.py
from tests.conftest import API, aleatorio

POLLO, TOMATE, ARROZ = 3, 6, 1  # ids de los datos de prueba


# Crea un material de prueba con stock inicial y mínimo
def crear_material(cliente, encargado, stock_inicial=20, stock_minimo=5):
    # Datos del material (código de barras aleatorio de 13 dígitos)
    datos = {"codigo_barras": aleatorio(13), "nombre": "Material de prueba", "categoria": "ABARROTE",
             "unidad_medida": "KG", "costo_unitario": 3000, "stock_inicial": stock_inicial, "stock_minimo": stock_minimo}  # Unidad, costo y stock
    # POST /inventario/materiales
    respuesta = cliente.post(f"{API}/inventario/materiales", json=datos, headers=encargado)
    # Debe responder 201
    assert respuesta.status_code == 201, respuesta.text
    # Devuelve el material creado
    return respuesta.json()


# Registra un movimiento y devuelve la respuesta
def movimiento(cliente, encargado, material_id, tipo, cantidad, concepto="Prueba"):
    # POST /inventario/movimientos
    return cliente.post(f"{API}/inventario/movimientos", headers=encargado,
                        json={"material_id": material_id, "tipo": tipo, "cantidad": cantidad, "concepto": concepto})  # Cuerpo


# Prueba: el estado del stock se calcula bien
def test_estado_del_stock(cliente, encargado):
    # El pollo vence en 4 días: VENCIENDO
    assert cliente.get(f"{API}/inventario/materiales/{POLLO}", headers=encargado).json()["estado_stock"] == "VENCIENDO"
    # El tomate tiene 3 de mínimo 8 (menos del 50 %): CRITICO
    assert cliente.get(f"{API}/inventario/materiales/{TOMATE}", headers=encargado).json()["estado_stock"] == "CRITICO"
    # Filtra los materiales en estado CRITICO
    criticos = cliente.get(f"{API}/inventario/materiales", params={"estado": "CRITICO", "tamano": 100}, headers=encargado)
    # Todos los devueltos deben estar en CRITICO
    assert all(m["estado_stock"] == "CRITICO" for m in criticos.json()["items"])


# Prueba: buscar por código de barras
def test_buscar_por_codigo_de_barras(cliente, encargado):
    # Busca el código del arroz
    items = cliente.get(f"{API}/inventario/materiales", params={"buscar": "7702001000011"}, headers=encargado).json()["items"]
    # Solo debe aparecer el arroz
    assert [m["nombre"] for m in items] == ["Arroz blanco"]


# Prueba: el stock inicial genera una ENTRADA en el kardex
def test_stock_inicial_genera_entrada_en_el_kardex(cliente, encargado):
    # Crea un material con 12.5 de stock inicial
    material = crear_material(cliente, encargado, stock_inicial=12.5)
    # Consulta el kardex de ese material
    kardex = cliente.get(f"{API}/inventario/kardex", params={"material_id": material["id"]}, headers=encargado).json()
    # Primera fila del kardex
    fila = kardex["items"][0]
    # Debe ser una ENTRADA de 12.5 con saldo 12.5
    assert (fila["tipo"], fila["entrada"], fila["saldo"]) == ("ENTRADA", 12.5, 12.5)
    # El responsable es la encargada
    assert fila["responsable"]["nombre"] == "Marta Lucía Rojas"


# Prueba: código de barras duplicado o con formato inválido
def test_codigo_duplicado_e_invalido(cliente, encargado):
    # Crea un material
    material = crear_material(cliente, encargado)
    # Datos de otro material con el mismo código
    datos = {"codigo_barras": material["codigo_barras"], "nombre": "Otro", "categoria": "GRANO",
             "unidad_medida": "KG", "costo_unitario": 1000}  # Unidad y costo
    # Responde 409
    assert cliente.post(f"{API}/inventario/materiales", json=datos, headers=encargado).status_code == 409
    # Cambia el código por uno con letras
    datos["codigo_barras"] = "ABC"
    # Responde 422
    assert cliente.post(f"{API}/inventario/materiales", json=datos, headers=encargado).status_code == 422


# Prueba: salidas y mermas actualizan el stock y el saldo
def test_salida_y_merma_actualizan_stock_y_saldo(cliente, encargado):
    # Material con 10 de stock y 4 de mínimo
    material = crear_material(cliente, encargado, stock_inicial=10, stock_minimo=4)
    # Salida de 3
    salida = movimiento(cliente, encargado, material["id"], "SALIDA", 3).json()
    # Queda en 7
    assert salida["saldo"] == 7
    # Merma de 2.5
    merma = movimiento(cliente, encargado, material["id"], "MERMA", 2.5, "Empaque roto").json()
    # Queda en 4.5 y la columna salida muestra 2.5
    assert merma["saldo"] == 4.5 and merma["salida"] == 2.5
    # Consulta el material
    actual = cliente.get(f"{API}/inventario/materiales/{material['id']}", headers=encargado).json()
    # Su stock es 4.5
    assert actual["stock"] == 4.5


# Prueba: una salida mayor al stock responde 400
def test_salida_mayor_al_stock_responde_400(cliente, encargado):
    # Material con 2 de stock
    material = crear_material(cliente, encargado, stock_inicial=2)
    # Intenta sacar 5
    respuesta = movimiento(cliente, encargado, material["id"], "SALIDA", 5)
    # Debe responder 400
    assert respuesta.status_code == 400
    # Con el mensaje de stock insuficiente
    assert respuesta.json()["mensaje"].startswith("Stock insuficiente")


# Prueba: una merma sin razón (concepto) responde 422
def test_merma_sin_razon_responde_422(cliente, encargado):
    # Movimiento sin el campo concepto
    respuesta = cliente.post(f"{API}/inventario/movimientos", headers=encargado,
                             json={"material_id": ARROZ, "tipo": "MERMA", "cantidad": 1})  # Cuerpo sin concepto
    # Debe responder 422
    assert respuesta.status_code == 422
    # El campo con error es concepto
    assert respuesta.json()["detalles"][0]["campo"] == "concepto"


# Prueba: el stock no se puede editar directamente
def test_el_stock_no_se_edita_directamente(cliente, encargado):
    # Intenta cambiar el stock con PATCH
    respuesta = cliente.patch(f"{API}/inventario/materiales/{ARROZ}", json={"stock": 999}, headers=encargado)
    # Debe responder 422 (campo no permitido)
    assert respuesta.status_code == 422


# Prueba: reglas para eliminar materiales
def test_eliminar_material(cliente, encargado):
    # Usado en recetas activas: no se puede
    # El arroz está en recetas activas: responde 400
    assert cliente.delete(f"{API}/inventario/materiales/{ARROZ}", headers=encargado).status_code == 400
    # Sin movimientos: borrado físico
    # Material sin stock inicial (sin movimientos)
    sin_movimientos = crear_material(cliente, encargado, stock_inicial=0)
    # Lo elimina
    respuesta = cliente.delete(f"{API}/inventario/materiales/{sin_movimientos['id']}", headers=encargado)
    # Se borra definitivamente
    assert "definitivamente" in respuesta.json()["mensaje"]
    # Con movimientos: borrado lógico
    # Material con stock inicial (tiene una ENTRADA)
    con_movimientos = crear_material(cliente, encargado, stock_inicial=5)
    # Lo elimina
    respuesta = cliente.delete(f"{API}/inventario/materiales/{con_movimientos['id']}", headers=encargado)
    # Se desactiva (borrado lógico)
    assert "borrado lógico" in respuesta.json()["mensaje"]


# Prueba: el kardex filtrado por mermas
def test_kardex_filtrado_por_mermas(cliente, encargado):
    # GET /inventario/kardex?tipo=MERMA
    mermas = cliente.get(f"{API}/inventario/kardex", params={"tipo": "MERMA", "tamano": 100}, headers=encargado).json()
    # Debe haber mermas y todas deben ser tipo MERMA
    assert mermas["items"] and all(m["tipo"] == "MERMA" for m in mermas["items"])
