"""Pruebas de la cartera de deudas y la cuenta mensual de instructores."""

# Constantes y funciones de apoyo de conftest.py
from tests.conftest import API, ROL_INSTRUCTOR, crear_menu, crear_usuario, reservar


# Prueba: el resumen de la cartera cuadra con la lista de deudores
def test_resumen_de_cartera_es_coherente(cliente, encargado):
    # GET /cartera
    cuerpo = cliente.get(f"{API}/cartera", headers=encargado).json()
    # Lista de saldos de los deudores
    saldos = [deudor["saldo"] for deudor in cuerpo["deudores"]]
    # Resumen
    resumen = cuerpo["resumen"]
    # Total de deudores = cantidad de saldos
    assert resumen["total_deudores"] == len(saldos)
    # Deuda total = suma de saldos
    assert resumen["deuda_total"] == sum(saldos)
    # Mayor deuda = saldo máximo
    assert resumen["mayor_deuda"] == max(saldos)
    # La lista viene ordenada de mayor a menor
    assert saldos == sorted(saldos, reverse=True)


# Prueba: el filtro de deudas vencidas
def test_filtro_de_deudas_vencidas(cliente, encargado):
    # GET /cartera?solo_vencidas=true
    vencidas = cliente.get(f"{API}/cartera", params={"solo_vencidas": True}, headers=encargado).json()["deudores"]
    # Debe haber al menos una y todas deben estar VENCIDA con días vencidos
    assert vencidas and all(d["estado"] == "VENCIDA" and d["dias_vencidos"] > 0 for d in vencidas)


# Prueba: flujo completo de pago parcial y total
def test_flujo_de_pago_parcial_y_total(cliente, encargado):
    # Crea un instructor nuevo
    nuevo = crear_usuario(cliente, encargado, ROL_INSTRUCTOR)
    # Crea un menú
    menu = crear_menu(cliente, encargado)
    # El instructor consume
    consumo = reservar(cliente, nuevo["headers"], menu["id"]).json()
    # El consumo queda PENDIENTE
    assert consumo["estado"] == "PENDIENTE"

    # Consulta el detalle de su cuenta
    detalle = cliente.get(f"{API}/cartera/{nuevo['id']}", headers=encargado).json()
    # Debe $5.000 y la deuda está ACTIVA
    assert detalle["saldo"] == 5000 and detalle["estado"] == "ACTIVA"

    # Ruta para registrar pagos
    ruta = f"{API}/cartera/{nuevo['id']}/pagos"
    # Intenta pagar más de lo que debe
    excedido = cliente.post(ruta, json={"valor": 9000, "metodo": "EFECTIVO"}, headers=encargado)
    # Debe responder 400 con el mensaje
    assert excedido.status_code == 400 and "no puede ser mayor" in excedido.json()["mensaje"]

    # Pago parcial de $2.000
    parcial = cliente.post(ruta, json={"valor": 2000, "metodo": "EFECTIVO"}, headers=encargado).json()
    # Pasa de 5.000 a 3.000
    assert (parcial["saldo_anterior"], parcial["saldo_actual"]) == (5000, 3000)

    # Pago del saldo restante
    total = cliente.post(ruta, json={"valor": 3000, "metodo": "TRANSFERENCIA"}, headers=encargado).json()
    # Queda en 0 y AL_DIA
    assert total["saldo_actual"] == 0 and total["estado"] == "AL_DIA"
    # Al saldar la deuda, los consumos quedan pagados y se ve en la cuenta del instructor
    # Consulta los consumos del instructor
    mias = cliente.get(f"{API}/reservas/mias", headers=nuevo["headers"]).json()["items"]
    # Su consumo pasó a PAGADO
    assert mias[0]["estado"] == "PAGADO"
    # Consulta su cuenta mensual
    cuenta = cliente.get(f"{API}/cartera/mi-cuenta", headers=nuevo["headers"]).json()
    # Saldo 0 y último método TRANSFERENCIA
    assert cuenta["saldo"] == 0 and cuenta["ultimo_metodo_pago"] == "TRANSFERENCIA"

    # Intenta pagar sin deuda
    sin_deuda = cliente.post(ruta, json={"valor": 1000, "metodo": "EFECTIVO"}, headers=encargado)
    # Debe responder 400
    assert sin_deuda.status_code == 400


# Prueba: pagos a quien no es instructor o no existe
def test_pago_a_quien_no_es_instructor_o_no_existe(cliente, encargado):
    # El usuario 5 es aprendiz: responde 400
    assert cliente.post(f"{API}/cartera/5/pagos", json={"valor": 1000, "metodo": "EFECTIVO"}, headers=encargado).status_code == 400
    # El usuario 99999 no existe: responde 404
    assert cliente.post(f"{API}/cartera/99999/pagos", json={"valor": 1000, "metodo": "EFECTIVO"}, headers=encargado).status_code == 404


# Prueba: pago con datos inválidos
def test_pago_con_datos_invalidos(cliente, encargado):
    # Valor negativo y método que no existe
    respuesta = cliente.post(f"{API}/cartera/2/pagos", json={"valor": -5, "metodo": "CHEQUE"}, headers=encargado)
    # Debe responder 422
    assert respuesta.status_code == 422
    # Los campos con error deben ser valor y metodo
    assert {d["campo"] for d in respuesta.json()["detalles"]} == {"valor", "metodo"}


# Prueba: la cuenta mensual del instructor cuadra
def test_mi_cuenta_del_instructor(cliente, instructor):
    # GET /cartera/mi-cuenta como instructor
    cuenta = cliente.get(f"{API}/cartera/mi-cuenta", headers=instructor).json()
    # Saldo = consumido - pagado
    assert cuenta["saldo"] == cuenta["total_consumido"] - cuenta["total_pagado"]
    # La frecuencia de pago es mensual
    assert cuenta["frecuencia_pago"] == "MENSUAL"
