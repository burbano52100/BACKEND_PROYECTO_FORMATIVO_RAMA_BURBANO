# Pruebas de la cartera, las sugerencias y los reportes

# Traigo las ayudas de las pruebas
from tests.ayudas import client, API, ENCARGADO, INSTRUCTOR, APRENDIZ, crear_usuario_prueba, crear_menu_prueba


# Prueba: la cartera muestra a Carlos (id 2) con la deuda vencida
def test_cartera_con_deuda_vencida():
    # Pido la cartera
    respuesta = client.get(API + "/cartera", headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Saco la lista de deudores
    deudores = respuesta.json()["deudores"]
    # Aquí guardo la deuda de Carlos
    deuda_carlos = None
    # Busco a Carlos en la lista
    for deuda in deudores:
        # Si es Carlos
        if deuda["instructor_id"] == 2:
            # La guardo
            deuda_carlos = deuda
    # Carlos tiene que estar en la lista
    assert deuda_carlos is not None
    # Debe 10000
    assert deuda_carlos["saldo"] == 10000
    # Su deuda está vencida
    assert deuda_carlos["estado"] == "VENCIDA"


# Prueba: un aprendiz no puede ver la cartera
def test_aprendiz_no_ve_la_cartera():
    # Pido la cartera como aprendiz
    respuesta = client.get(API + "/cartera", headers=APRENDIZ)
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: un pago no puede ser mayor que la deuda
def test_pago_mayor_que_la_deuda():
    # Intento registrar un pago muy grande para Carlos
    respuesta = client.post(API + "/cartera/2/pagos", json={"valor": 999999, "metodo": "EFECTIVO"}, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: si el instructor paga todo queda al día y sus consumos quedan pagados
def test_pago_completo_deja_al_dia():
    # Creo un menú
    menu = crear_menu_prueba()
    # Creo un instructor
    instructor = crear_usuario_prueba(2)
    # El instructor reserva
    reserva = client.post(API + "/reservas", json={"menu_id": menu["id"]}, headers=instructor["headers"]).json()
    # La encargada registra el pago completo
    respuesta = client.post(API + "/cartera/" + str(instructor["id"]) + "/pagos", json={"valor": 5000, "metodo": "NOMINA"}, headers=ENCARGADO)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Ya no debe nada
    assert respuesta.json()["saldo_actual"] == 0
    # Consulto la cuenta del instructor
    cuenta = client.get(API + "/cartera/" + str(instructor["id"]), headers=ENCARGADO).json()
    # Tiene que estar al día
    assert cuenta["estado"] == "AL_DIA"
    # Consulto la reserva
    reserva_despues = client.get(API + "/reservas/" + str(reserva["id"]), headers=ENCARGADO).json()
    # Tiene que estar pagada
    assert reserva_despues["estado"] == "PAGADO"


# Prueba: el instructor ve su propia cuenta
def test_mi_cuenta_instructor():
    # Carlos pide su cuenta
    respuesta = client.get(API + "/cartera/mi-cuenta", headers=INSTRUCTOR)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Debe 10000
    assert respuesta.json()["saldo"] == 10000
    # Una aprendiz no tiene cuenta
    respuesta = client.get(API + "/cartera/mi-cuenta", headers=APRENDIZ)
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: mandar una sugerencia y que la encargada la atienda
def test_enviar_y_atender_sugerencia():
    # La aprendiz manda una sugerencia
    respuesta = client.post(API + "/sugerencias", json={"asunto": "Prueba", "mensaje": "Esta es una sugerencia de prueba"}, headers=APRENDIZ)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Saco la sugerencia
    sugerencia = respuesta.json()
    # Tiene que quedar pendiente
    assert sugerencia["estado"] == "PENDIENTE"
    # La encargada la atiende
    respuesta = client.patch(API + "/sugerencias/" + str(sugerencia["id"]) + "/atender", json={"respuesta": "Gracias"}, headers=ENCARGADO)
    # Tiene que quedar atendida
    assert respuesta.json()["estado"] == "ATENDIDA"
    # Si la intento atender otra vez responde 400
    respuesta = client.patch(API + "/sugerencias/" + str(sugerencia["id"]) + "/atender", json={"respuesta": "Otra vez"}, headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400
    # La aprendiz ve sus sugerencias
    mias = client.get(API + "/sugerencias/mias", headers=APRENDIZ).json()
    # La sugerencia tiene que estar en la lista
    assert mias[0]["id"] == sugerencia["id"]


# Prueba: el buzón trae los contadores
def test_buzon_con_contadores():
    # Pido el buzón
    respuesta = client.get(API + "/sugerencias", headers=ENCARGADO)
    # Saco los contadores
    contadores = respuesta.json()["contadores"]
    # El total tiene que ser pendientes más atendidas
    assert contadores["total"] == contadores["pendientes"] + contadores["atendidas"]


# Prueba: el reporte de ventas
def test_reporte_de_ventas():
    # Pido las ventas del mes
    respuesta = client.get(API + "/reportes/ventas?periodo=mes", headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Tiene que haber ventas (por lo menos las de hoy)
    assert respuesta.json()["total_almuerzos"] > 0
    # Un periodo que no existe responde 400
    respuesta = client.get(API + "/reportes/ventas?periodo=siglo", headers=ENCARGADO)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: los indicadores del encargado
def test_indicadores():
    # Pido los indicadores
    respuesta = client.get(API + "/reportes/indicadores", headers=ENCARGADO)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Hoy se vendieron almuerzos
    assert respuesta.json()["ventas_hoy"] > 0
