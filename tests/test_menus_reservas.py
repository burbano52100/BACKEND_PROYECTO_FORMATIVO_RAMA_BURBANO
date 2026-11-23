# Pruebas del menú del día y de las reservas

# date y timedelta sirven para sacar la fecha de ayer
from datetime import date, timedelta

# Traigo las ayudas de las pruebas
from tests.ayudas import cliente, api, cabecera_encargado, cabecera_aprendiz, cabecera_beneficiario, cabecera_invitado, crear_usuario_prueba, crear_menu_prueba


# Prueba: el menú de hoy muestra el precio según el rol de quien pregunta
def prueba_menu_de_hoy_con_precio_segun_rol():
    # Pido el menú de hoy como aprendiz
    respuesta = cliente.get(api + "/menus/hoy", headers=cabecera_aprendiz)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Al aprendiz le cuesta 5000
    assert respuesta.json()["precio_para_mi"] == 5000
    # Pido el menú de hoy como beneficiario
    respuesta = cliente.get(api + "/menus/hoy", headers=cabecera_beneficiario)
    # Al beneficiario le cuesta 0
    assert respuesta.json()["precio_para_mi"] == 0
    # Pido el menú de hoy como invitado
    respuesta = cliente.get(api + "/menus/hoy", headers=cabecera_invitado)
    # Al invitado le cuesta 8000
    assert respuesta.json()["precio_para_mi"] == 8000


# Prueba: no se puede crear un menú para un día que ya pasó
def prueba_menu_en_fecha_pasada():
    # Saco la fecha de ayer
    ayer = date.today() - timedelta(days=1)
    # Armo los datos del menú
    datos = {"fecha": str(ayer), "nombre": "Menú viejo", "descripcion": "No se debe crear", "precio_aprendiz": 5000, "precio_invitado": 8000, "cantidad_total": 10}
    # Intento crearlo
    respuesta = cliente.post(api + "/menus", json=datos, headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: solo puede haber un menú por día
def prueba_un_menu_por_dia():
    # Creo un menú de prueba
    menu = crear_menu_prueba()
    # Intento crear otro en la misma fecha
    datos = {"fecha": menu["fecha"], "nombre": "Otro menú", "descripcion": "Mismo día", "precio_aprendiz": 5000, "precio_invitado": 8000, "cantidad_total": 10}
    # Mando la petición
    respuesta = cliente.post(api + "/menus", json=datos, headers=cabecera_encargado)
    # Tiene que responder 409 porque ya hay un menú en esa fecha
    assert respuesta.status_code == 409


# Prueba: al reservar se descuenta un almuerzo del menú
def prueba_reservar_descuenta_el_cupo():
    # Creo un menú con 10 almuerzos
    menu = crear_menu_prueba(10)
    # Creo un aprendiz de la ficha 1
    aprendiz = crear_usuario_prueba(3, 1)
    # Reservo
    respuesta = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=aprendiz["cabeceras"])
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Al aprendiz le cobran 5000
    assert respuesta.json()["valor"] == 5000
    # Queda reservado
    assert respuesta.json()["estado"] == "RESERVADO"
    # Consulto el menú otra vez
    menu_despues = cliente.get(api + "/menus/" + str(menu["id"]), headers=cabecera_encargado).json()
    # Ahora quedan 9
    assert menu_despues["cantidad_disponible"] == 9


# Prueba: no se puede reservar dos veces el mismo menú
def prueba_no_se_reserva_dos_veces():
    # Creo un menú
    menu = crear_menu_prueba()
    # Creo un invitado
    invitado = crear_usuario_prueba(4)
    # Reservo la primera vez
    cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado["cabeceras"])
    # Reservo otra vez
    respuesta = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado["cabeceras"])
    # Tiene que responder 409 porque ya tiene una reserva para ese menú
    assert respuesta.status_code == 409


# Prueba: si el menú se agota ya no se puede reservar
def prueba_menu_agotado():
    # Creo un menú con un solo almuerzo
    menu = crear_menu_prueba(1)
    # Creo dos invitados
    invitado1 = crear_usuario_prueba(4)
    # El segundo invitado
    invitado2 = crear_usuario_prueba(4)
    # El primero reserva
    respuesta = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado1["cabeceras"])
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # El segundo intenta reservar
    respuesta = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado2["cabeceras"])
    # Tiene que responder 400
    assert respuesta.status_code == 400
    # El mensaje dice que está agotado
    assert "agotado" in respuesta.json()["detalle"]


# Prueba: el encargado no puede reservar
def prueba_encargado_no_reserva():
    # Creo un menú
    menu = crear_menu_prueba()
    # La encargada intenta reservar
    respuesta = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=cabecera_encargado)
    # Tiene que responder 403
    assert respuesta.status_code == 403


# Prueba: el consumo de un instructor queda pendiente para su cuenta del mes
def prueba_instructor_queda_pendiente():
    # Creo un menú
    menu = crear_menu_prueba()
    # Creo un instructor
    instructor = crear_usuario_prueba(2)
    # El instructor reserva
    respuesta = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=instructor["cabeceras"])
    # Tiene que quedar pendiente
    assert respuesta.json()["estado"] == "PENDIENTE"
    # Y le cobran 5000
    assert respuesta.json()["valor"] == 5000


# Prueba: al cancelar se devuelve el almuerzo al menú
def prueba_cancelar_devuelve_el_cupo():
    # Creo un menú con 5 almuerzos
    menu = crear_menu_prueba(5)
    # Creo un invitado
    invitado = crear_usuario_prueba(4)
    # Reservo
    reserva = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado["cabeceras"]).json()
    # Cancelo la reserva
    respuesta = cliente.patch(api + "/reservas/" + str(reserva["id"]) + "/cancelar", headers=invitado["cabeceras"])
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Tiene que quedar cancelada
    assert respuesta.json()["estado"] == "CANCELADA"
    # Consulto el menú otra vez
    menu_despues = cliente.get(api + "/menus/" + str(menu["id"]), headers=cabecera_encargado).json()
    # Tienen que volver a quedar 5
    assert menu_despues["cantidad_disponible"] == 5


# Prueba: nadie puede ver la reserva de otra persona (menos el encargado)
def prueba_no_ve_la_reserva_de_otro():
    # Creo un menú
    menu = crear_menu_prueba()
    # Creo un invitado que reserva
    invitado = crear_usuario_prueba(4)
    # Reservo
    reserva = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado["cabeceras"]).json()
    # La aprendiz intenta ver la reserva del invitado
    respuesta = cliente.get(api + "/reservas/" + str(reserva["id"]), headers=cabecera_aprendiz)
    # Tiene que responder 403
    assert respuesta.status_code == 403
    # La encargada sí la puede ver
    respuesta = cliente.get(api + "/reservas/" + str(reserva["id"]), headers=cabecera_encargado)
    # Tiene que responder 200
    assert respuesta.status_code == 200


# Prueba: la encargada marca el pago de una reserva
def prueba_marcar_pago():
    # Creo un menú
    menu = crear_menu_prueba()
    # Creo un invitado
    invitado = crear_usuario_prueba(4)
    # Reservo
    reserva = cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado["cabeceras"]).json()
    # La encargada marca que pagó
    respuesta = cliente.patch(api + "/reservas/" + str(reserva["id"]) + "/pago", json={"estado": "PAGADO"}, headers=cabecera_encargado)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Tiene que quedar pagado
    assert respuesta.json()["estado"] == "PAGADO"
    # Un estado que no existe responde 400
    respuesta = cliente.patch(api + "/reservas/" + str(reserva["id"]) + "/pago", json={"estado": "REGALADO"}, headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: la cantidad del menú no puede quedar menor que lo vendido
def prueba_cupo_no_menor_que_lo_vendido():
    # Creo un menú con 5 almuerzos
    menu = crear_menu_prueba(5)
    # Creo dos invitados que reservan
    for i in range(2):
        # Creo el invitado
        invitado = crear_usuario_prueba(4)
        # Reservo
        cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado["cabeceras"])
    # Intento dejar el menú con 1 almuerzo
    respuesta = cliente.put(api + "/menus/" + str(menu["id"]), json={"cantidad_total": 1}, headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: un menú con reservas solo se desactiva al eliminarlo
def prueba_eliminar_menu_con_reservas():
    # Creo un menú
    menu = crear_menu_prueba()
    # Creo un invitado que reserva
    invitado = crear_usuario_prueba(4)
    # Reservo
    cliente.post(api + "/reservas", json={"menu_id": menu["id"]}, headers=invitado["cabeceras"])
    # Elimino el menú
    respuesta = cliente.delete(api + "/menus/" + str(menu["id"]), headers=cabecera_encargado)
    # Tiene que decir que se desactivó
    assert "desactivó" in respuesta.json()["mensaje"]
