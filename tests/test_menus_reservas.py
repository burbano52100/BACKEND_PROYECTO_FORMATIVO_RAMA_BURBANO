"""Pruebas del Menú del Día y de las reservas (procesos de negocio principales)."""

# Tipos fecha-hora, hora y duración
from datetime import datetime, time, timedelta

# Fecha y hora de Colombia
from app.core import tiempo
# Configuración (para cambiar el horario en una prueba)
from app.core.config import settings
# Constantes y funciones de apoyo de conftest.py
from tests.conftest import API, FICHA_ADSO, ROL_APRENDIZ, crear_menu, crear_usuario, reservar


# Prueba: un menú nuevo empieza con el cupo completo
def test_crear_menu_inicia_con_cupo_completo(cliente, encargado):
    # Crea un menú con cupo 30
    menu = crear_menu(cliente, encargado, cantidad=30)
    # Disponible 30, vendidos 0 y no agotado
    assert menu["cantidad_disponible"] == 30 and menu["vendidos"] == 0 and menu["agotado"] is False


# Prueba: solo un menú por fecha
def test_un_solo_menu_por_fecha(cliente, encargado):
    # Crea un menú
    menu = crear_menu(cliente, encargado)
    # Datos de otro menú en la misma fecha
    datos = {"fecha": menu["fecha"], "nombre": "Otro", "descripcion": "Otro menú", "precio_aprendiz": 5000,
             "precio_invitado": 8000, "cantidad_total": 10}  # Precio de invitado y cupo
    # Debe responder 409
    assert cliente.post(f"{API}/menus", json=datos, headers=encargado).status_code == 409


# Prueba: un menú con datos inválidos responde 422
def test_menu_con_datos_invalidos_responde_422(cliente, encargado):
    # Fecha de ayer en formato AAAA-MM-DD
    ayer = (tiempo.hoy() - timedelta(days=1)).isoformat()
    # 5 campos inválidos: fecha pasada, nombre vacío, descripción corta, precio negativo y cupo 0
    datos = {"fecha": ayer, "nombre": "", "descripcion": "x", "precio_aprendiz": -1, "precio_invitado": 8000,
             "cantidad_total": 0}  # Cupo inválido
    # POST /menus
    respuesta = cliente.post(f"{API}/menus", json=datos, headers=encargado)
    # Debe responder 422
    assert respuesta.status_code == 422
    # Conjunto de campos con error
    campos = {d["campo"] for d in respuesta.json()["detalles"]}
    # Deben ser exactamente esos 5
    assert campos == {"fecha", "nombre", "descripcion", "precio_aprendiz", "cantidad_total"}


# Prueba: el precio depende del tipo de cuenta
def test_precio_segun_el_tipo_de_cuenta(cliente, encargado, aprendiz, beneficiario, invitado, instructor):
    # Crea un menú
    menu = crear_menu(cliente, encargado)
    # Resultado esperado para cada tipo de cuenta: (encabezado, tipo, valor, estado)
    esperado = {
        # Aprendiz: $5.000 RESERVADO
        "aprendiz": (aprendiz, "APRENDIZ", 5000, "RESERVADO"),
        # Beneficiario: $0 PAGADO
        "beneficiario": (beneficiario, "BENEFICIARIO", 0, "PAGADO"),
        # Invitado: $8.000 RESERVADO
        "invitado": (invitado, "INVITADO", 8000, "RESERVADO"),
        # Instructor: $5.000 PENDIENTE
        "instructor": (instructor, "INSTRUCTOR", 5000, "PENDIENTE"),
    }
    # Recorre cada caso
    for headers, tipo, valor, estado in esperado.values():
        # Reserva con esa cuenta
        respuesta = reservar(cliente, headers, menu["id"])
        # Debe responder 201
        assert respuesta.status_code == 201, respuesta.text
        # Cuerpo de la respuesta
        cuerpo = respuesta.json()
        # Tipo, valor y estado deben ser los esperados
        assert (cuerpo["tipo"], cuerpo["valor"], cuerpo["estado"]) == (tipo, valor, estado)
    # Consulta el menú después de las 4 reservas
    actualizado = cliente.get(f"{API}/menus/{menu['id']}", headers=encargado).json()
    # Vendidos 4 y el disponible bajó en 4
    assert actualizado["vendidos"] == 4 and actualizado["cantidad_disponible"] == menu["cantidad_total"] - 4


# Prueba: una sola reserva por persona y por menú
def test_una_sola_reserva_por_persona_y_menu(cliente, encargado, aprendiz):
    # Crea un menú
    menu = crear_menu(cliente, encargado)
    # La primera reserva funciona
    assert reservar(cliente, aprendiz, menu["id"]).status_code == 201
    # Segunda reserva del mismo aprendiz
    segunda = reservar(cliente, aprendiz, menu["id"])
    # Debe responder 409
    assert segunda.status_code == 409


# Prueba: un menú agotado no recibe reservas
def test_menu_agotado_no_recibe_reservas(cliente, encargado, aprendiz, invitado):
    # Menú con cupo 1
    menu = crear_menu(cliente, encargado, cantidad=1)
    # El aprendiz toma el único cupo
    assert reservar(cliente, aprendiz, menu["id"]).status_code == 201
    # El invitado intenta reservar
    agotado = reservar(cliente, invitado, menu["id"])
    # Debe responder 400
    assert agotado.status_code == 400
    # Con este mensaje
    assert agotado.json()["mensaje"] == "El menú está agotado."


# Prueba: el cliente no puede enviar el precio
def test_no_se_puede_enviar_el_precio(cliente, encargado, aprendiz):
    # Crea un menú
    menu = crear_menu(cliente, encargado)
    # Intenta reservar enviando "valor": 0
    respuesta = cliente.post(f"{API}/reservas", json={"menu_id": menu["id"], "valor": 0}, headers=aprendiz)
    # Debe responder 422
    assert respuesta.status_code == 422
    # El error dice que el campo valor no está permitido
    assert respuesta.json()["detalles"][0] == {"campo": "valor", "mensaje": "Este campo no está permitido."}


# Prueba: reservar un menú inexistente responde 404
def test_menu_inexistente_responde_404(cliente, aprendiz):
    # Menú 99999 no existe
    assert reservar(cliente, aprendiz, 99999).status_code == 404


# Prueba: fuera del horario no se reserva (monkeypatch cambia valores solo durante esta prueba)
def test_fuera_del_horario_no_se_reserva(cliente, encargado, aprendiz, monkeypatch):
    # Crea un menú
    menu = crear_menu(cliente, encargado)
    # Ventana de reservas que no incluye la hora actual
    # Hora actual
    ahora = tiempo.ahora()
    # El horario empieza dentro de 1 hora...
    monkeypatch.setattr(settings, "HORA_INICIO_RESERVAS", (ahora + timedelta(hours=1)).time())
    # ...y termina dentro de 2 horas
    monkeypatch.setattr(settings, "HORA_FIN_RESERVAS", (ahora + timedelta(hours=2)).time())
    # Intenta reservar ahora
    respuesta = reservar(cliente, aprendiz, menu["id"])
    # Debe responder 400
    assert respuesta.status_code == 400
    # Con el mensaje del horario
    assert respuesta.json()["mensaje"].startswith("Solo se puede reservar entre")


# Prueba: el horario incluye las horas de inicio y de fin
def test_en_horario_incluye_los_extremos():
    # Horario de 7:00 a 21:00
    inicio, fin = time(7, 0), time(21, 0)
    # Un día cualquiera
    dia = datetime(2026, 11, 16)
    # 7:00 está dentro
    assert tiempo.en_horario(dia.replace(hour=7), inicio, fin)
    # 21:00 está dentro
    assert tiempo.en_horario(dia.replace(hour=21), inicio, fin)
    # 6:59 está fuera
    assert not tiempo.en_horario(dia.replace(hour=6, minute=59), inicio, fin)
    # 21:01 está fuera
    assert not tiempo.en_horario(dia.replace(hour=21, minute=1), inicio, fin)


# Prueba: cancelar devuelve el cupo y permite reservar de nuevo
def test_cancelar_devuelve_el_cupo_y_permite_reservar_de_nuevo(cliente, encargado, aprendiz, invitado):
    # Menú con cupo 5
    menu = crear_menu(cliente, encargado, cantidad=5)
    # El aprendiz reserva
    reserva = reservar(cliente, aprendiz, menu["id"]).json()
    # El invitado intenta cancelar la reserva del aprendiz
    ajena = cliente.patch(f"{API}/reservas/{reserva['id']}/cancelar", headers=invitado)
    # Debe responder 403
    assert ajena.status_code == 403
    # El aprendiz cancela su reserva
    cancelada = cliente.patch(f"{API}/reservas/{reserva['id']}/cancelar", headers=aprendiz)
    # Responde 200 y queda CANCELADA
    assert cancelada.status_code == 200 and cancelada.json()["estado"] == "CANCELADA"
    # El cupo vuelve a 5
    assert cliente.get(f"{API}/menus/{menu['id']}", headers=encargado).json()["cantidad_disponible"] == 5
    # Puede reservar de nuevo
    assert reservar(cliente, aprendiz, menu["id"]).status_code == 201


# Prueba: el encargado marca el pago de un aprendiz
def test_encargado_marca_pago_de_aprendiz(cliente, encargado, aprendiz, instructor):
    # Crea un menú
    menu = crear_menu(cliente, encargado)
    # El aprendiz reserva
    reserva = reservar(cliente, aprendiz, menu["id"]).json()
    # El encargado marca PAGADO
    pagada = cliente.patch(f"{API}/reservas/{reserva['id']}/pago", json={"estado": "PAGADO"}, headers=encargado)
    # Responde 200 y queda PAGADO
    assert pagada.status_code == 200 and pagada.json()["estado"] == "PAGADO"
    # Una reserva pagada ya no se puede cancelar
    # Cancelarla responde 400
    assert cliente.patch(f"{API}/reservas/{reserva['id']}/cancelar", headers=aprendiz).status_code == 400
    # Los consumos de instructores van por la cartera
    # El instructor consume
    consumo = reservar(cliente, instructor, menu["id"]).json()
    # El encargado intenta marcar el pago del instructor
    respuesta = cliente.patch(f"{API}/reservas/{consumo['id']}/pago", json={"estado": "PAGADO"}, headers=encargado)
    # Debe responder 400
    assert respuesta.status_code == 400
    # Solo el encargado marca pagos
    # Un aprendiz intentándolo responde 403
    assert cliente.patch(f"{API}/reservas/{reserva['id']}/pago", json={"estado": "PAGADO"}, headers=aprendiz).status_code == 403


# Prueba: una reserva aparece en el grupo y en los consumos
def test_reservas_reflejadas_en_grupos_y_consumos(cliente, encargado):
    # Crea un aprendiz en la ficha ADSO
    aprendiz_nuevo = crear_usuario(cliente, encargado, ROL_APRENDIZ, FICHA_ADSO)
    # Fecha de hoy en formato AAAA-MM-DD
    hoy = tiempo.hoy().isoformat()
    # Consulta el menú de hoy
    menu_hoy = cliente.get(f"{API}/menus/hoy", headers=aprendiz_nuevo["headers"])
    # Existe y todavía no tiene reserva propia
    assert menu_hoy.status_code == 200 and menu_hoy.json()["mi_reserva"] is None
    # Reserva el menú de hoy
    reserva = reservar(cliente, aprendiz_nuevo["headers"], menu_hoy.json()["id"])
    # Responde 201
    assert reserva.status_code == 201
    # Consulta las reservas de la ficha ADSO hoy
    grupo = cliente.get(f"{API}/fichas/{FICHA_ADSO}/reservas", params={"fecha": hoy}, headers=encargado).json()
    # El aprendiz nuevo aparece en la lista
    assert aprendiz_nuevo["id"] in {r["aprendiz_id"] for r in grupo}
    # Consulta sus consumos
    mias = cliente.get(f"{API}/reservas/mias", headers=aprendiz_nuevo["headers"]).json()
    # El primero es la reserva que acaba de hacer
    assert mias["items"][0]["id"] == reserva.json()["id"]


# Prueba: eliminar un menú (lógico o físico)
def test_eliminar_menu_logico_o_fisico(cliente, encargado, aprendiz):
    # Menú sin reservas
    sin_reservas = crear_menu(cliente, encargado)
    # Se borra definitivamente
    assert "definitivamente" in cliente.delete(f"{API}/menus/{sin_reservas['id']}", headers=encargado).json()["mensaje"]
    # Menú con reservas
    con_reservas = crear_menu(cliente, encargado)
    # El aprendiz reserva
    reservar(cliente, aprendiz, con_reservas["id"])
    # Se desactiva (borrado lógico)
    assert "borrado lógico" in cliente.delete(f"{API}/menus/{con_reservas['id']}", headers=encargado).json()["mensaje"]
    # Ya no recibe reservas (400 inactivo o 409 porque ya tenía reserva)
    assert reservar(cliente, aprendiz, con_reservas["id"]).status_code in (400, 409)


# Prueba: el cupo no puede quedar por debajo de lo vendido
def test_cupo_no_puede_quedar_por_debajo_de_lo_vendido(cliente, encargado, aprendiz, invitado):
    # Menú con cupo 10
    menu = crear_menu(cliente, encargado, cantidad=10)
    # Primera reserva
    reservar(cliente, aprendiz, menu["id"])
    # Segunda reserva (2 vendidos)
    reservar(cliente, invitado, menu["id"])
    # Bajar el cupo a 1 responde 400
    assert cliente.patch(f"{API}/menus/{menu['id']}", json={"cantidad_total": 1}, headers=encargado).status_code == 400
    # Bajar el cupo a 4 funciona
    ajustado = cliente.patch(f"{API}/menus/{menu['id']}", json={"cantidad_total": 4}, headers=encargado).json()
    # Quedan 2 disponibles (4 - 2 vendidos)
    assert ajustado["cantidad_disponible"] == 2
