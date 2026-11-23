# Pruebas de la cartera de los instructores

# Traigo las ayudas de las pruebas
from tests.ayudas import cliente, api, cabecera_encargado, cabecera_instructor, cabecera_aprendiz, crear_usuario_prueba, crear_menu_prueba


# Prueba: la cartera muestra a Carlos (id 2) con la deuda vencida
def prueba_cartera_con_deuda_vencida():
    # Pido la cartera
    respuesta = cliente.get(api + "/cartera", headers=cabecera_encargado)
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
def prueba_aprendiz_no_ve_la_cartera():
    # Pido la cartera como aprendiz
    respuesta = cliente.get(api + "/cartera", headers=cabecera_aprendiz)
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: un pago no puede ser mayor que la deuda
def prueba_pago_mayor_que_la_deuda():
    # Intento registrar un pago muy grande para Carlos
    respuesta = cliente.post(api + "/cartera/2/pagos", json={"valor": 999999, "metodo": "EFECTIVO"}, headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: si el instructor paga todo queda al día y sus consumos quedan pagados
def prueba_pago_completo_deja_al_dia():
    # Creo un menú
    menu = crear_menu_prueba()
    # Creo un instructor
    instructor = crear_usuario_prueba(2)
    # El instructor reserva
    reserva = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=instructor["cabeceras"]).json()
    # La encargada registra el pago completo
    respuesta = cliente.post(api + "/cartera/" + str(instructor["id"]) + "/pagos", json={"valor": 5000, "metodo": "NOMINA"}, headers=cabecera_encargado)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Ya no debe nada
    assert respuesta.json()["saldo_actual"] == 0
    # Consulto la cuenta del instructor
    cuenta = cliente.get(api + "/cartera/" + str(instructor["id"]), headers=cabecera_encargado).json()
    # Tiene que estar al día
    assert cuenta["estado"] == "AL_DIA"
    # Consulto la reserva
    reserva_despues = cliente.get(api + "/reservas/" + str(reserva["id"]), headers=cabecera_encargado).json()
    # Tiene que estar pagada
    assert reserva_despues["estado"] == "PAGADO"


# Prueba: el instructor ve su propia cuenta
def prueba_mi_cuenta_instructor():
    # Carlos pide su cuenta
    respuesta = cliente.get(api + "/cartera/mi-cuenta", headers=cabecera_instructor)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Debe 10000
    assert respuesta.json()["saldo"] == 10000
    # Una aprendiz no tiene cuenta
    respuesta = cliente.get(api + "/cartera/mi-cuenta", headers=cabecera_aprendiz)
    # Tiene que responder 403
    assert respuesta.status_code == 403
