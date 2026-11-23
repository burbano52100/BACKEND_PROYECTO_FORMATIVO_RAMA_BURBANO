# Pruebas de las recetas, las sugerencias y los reportes

# Traigo las ayudas de las pruebas
from tests.ayudas import cliente, api, cabecera_encargado, cabecera_aprendiz, numero_al_azar


# Prueba: el costo de la receta se calcula bien
def prueba_costo_de_la_receta():
    # Pido el bistec a caballo (id 7), que cuesta más de lo que se vende
    receta = cliente.get(api + "/recetas/7", headers=cabecera_encargado).json()
    # Cuesta 5720 hacerlo
    assert receta["costo_produccion"] == 5720
    # Se pierden 720
    assert receta["margen"] == -720
    # Tiene que salir la alerta
    assert receta["alerta_margen_negativo"] == True


# Prueba: un material no se puede repetir en la misma receta
def prueba_receta_con_material_repetido():
    # Armo una receta con el arroz dos veces
    datos = {"nombre": "Receta repetida " + numero_al_azar(), "precio_venta": 5000, "ingredientes": [{"material_id": 1, "cantidad": 0.1}, {"material_id": 1, "cantidad": 0.2}]}
    # Intento crearla
    respuesta = cliente.post(api + "/recetas", json=datos, headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: crear, actualizar y eliminar una receta
def prueba_crear_actualizar_y_eliminar_receta():
    # Armo la receta con arroz (4200 el kilo) y papa (2500 el kilo)
    datos = {"nombre": "Receta de prueba " + numero_al_azar(), "precio_venta": 5000, "ingredientes": [{"material_id": 1, "cantidad": 0.5}, {"material_id": 5, "cantidad": 0.2}]}
    # Creo la receta
    respuesta = cliente.post(api + "/recetas", json=datos, headers=cabecera_encargado)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Saco la receta
    receta = respuesta.json()
    # El costo es 0.5 x 4200 + 0.2 x 2500 = 2600
    assert receta["costo_produccion"] == 2600
    # Le cambio los ingredientes por solo arroz
    respuesta = cliente.put(api + "/recetas/" + str(receta["id"]), json={"ingredientes": [{"material_id": 1, "cantidad": 1}]}, headers=cabecera_encargado)
    # El costo ahora es 4200
    assert respuesta.json()["costo_produccion"] == 4200
    # Elimino la receta
    respuesta = cliente.delete(api + "/recetas/" + str(receta["id"]), headers=cabecera_encargado)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Si la busco ya no existe
    respuesta = cliente.get(api + "/recetas/" + str(receta["id"]), headers=cabecera_encargado)
    # Tiene que responder 404
    assert respuesta.status_code == 404


# Prueba: mandar una sugerencia y que la encargada la atienda
def prueba_enviar_y_atender_sugerencia():
    # La aprendiz manda una sugerencia
    respuesta = cliente.post(api + "/sugerencias", json={"asunto": "Prueba", "mensaje": "Esta es una sugerencia de prueba"}, headers=cabecera_aprendiz)
    # Tiene que responder 201
    assert respuesta.status_code == 201
    # Saco la sugerencia
    sugerencia = respuesta.json()
    # Tiene que quedar pendiente
    assert sugerencia["estado"] == "PENDIENTE"
    # La encargada la atiende
    respuesta = cliente.patch(api + "/sugerencias/" + str(sugerencia["id"]) + "/atender", json={"respuesta": "Gracias"}, headers=cabecera_encargado)
    # Tiene que quedar atendida
    assert respuesta.json()["estado"] == "ATENDIDA"
    # Si la intento atender otra vez responde 400
    respuesta = cliente.patch(api + "/sugerencias/" + str(sugerencia["id"]) + "/atender", json={"respuesta": "Otra vez"}, headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400
    # La aprendiz ve sus sugerencias
    mias = cliente.get(api + "/sugerencias/mias", headers=cabecera_aprendiz).json()
    # La sugerencia tiene que estar en la lista
    assert mias[0]["id"] == sugerencia["id"]


# Prueba: el buzón trae los contadores
def prueba_buzon_con_contadores():
    # Pido el buzón
    respuesta = cliente.get(api + "/sugerencias", headers=cabecera_encargado)
    # Saco los contadores
    contadores = respuesta.json()["contadores"]
    # El total tiene que ser pendientes más atendidas
    assert contadores["total"] == contadores["pendientes"] + contadores["atendidas"]


# Prueba: el reporte de ventas
def prueba_reporte_de_ventas():
    # Pido las ventas del mes
    respuesta = cliente.get(api + "/reportes/ventas?periodo=mes", headers=cabecera_encargado)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Tiene que haber ventas (por lo menos las de hoy)
    assert respuesta.json()["total_almuerzos"] > 0
    # Un periodo que no existe responde 400
    respuesta = cliente.get(api + "/reportes/ventas?periodo=siglo", headers=cabecera_encargado)
    # Tiene que responder 400
    assert respuesta.status_code == 400


# Prueba: los indicadores del encargado
def prueba_indicadores():
    # Pido los indicadores
    respuesta = cliente.get(api + "/reportes/indicadores", headers=cabecera_encargado)
    # Tiene que responder 200
    assert respuesta.status_code == 200
    # Hoy se vendieron almuerzos
    assert respuesta.json()["ventas_hoy"] > 0
