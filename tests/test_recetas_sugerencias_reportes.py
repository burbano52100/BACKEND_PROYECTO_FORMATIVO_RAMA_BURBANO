"""Pruebas de recetas (costo y margen), sugerencias y reportes."""

# Tipo fecha
from datetime import date

# Períodos del reporte
from app.schemas.reporte import Periodo
# Función que calcula el rango de un período
from app.services.reporte_service import rango_del_periodo
# Constantes y funciones de apoyo de conftest.py
from tests.conftest import API, aleatorio

ARROZ, POLLO, BANDEJA = 1, 3, 12  # ids de los datos de prueba


# Prueba: el costo y el margen de una receta se calculan bien
def test_costo_y_margen_de_una_receta(cliente, encargado):
    # Receta con nombre único, precio $6.000 y 3 ingredientes
    datos = {"nombre": f"Arroz con pollo {aleatorio(6)}", "precio_venta": 6000, "ingredientes": [
        {"material_id": ARROZ, "cantidad": 0.2},    # 0.2 x 4.200 = 840
        {"material_id": POLLO, "cantidad": 0.15},   # 0.15 x 14.500 = 2.175
        {"material_id": BANDEJA, "cantidad": 1},    # 1 x 350 = 350
    ]}
    # Crea la receta
    receta = cliente.post(f"{API}/recetas", json=datos, headers=encargado).json()
    # Costo = 840 + 2.175 + 350 = 3.365
    assert receta["costo_produccion"] == 3365
    # Margen = 6.000 - 3.365 = 2.635
    assert receta["margen"] == 2635
    # Margen % = 2.635 / 6.000 x 100 = 43,92
    assert receta["margen_porcentaje"] == 43.92
    # No hay alerta
    assert receta["alerta_margen_negativo"] is False


# Prueba: la alerta de margen negativo
def test_alerta_de_margen_negativo(cliente, encargado):
    # Busca el Bistec a caballo (cuesta más de lo que se vende)
    bistec = cliente.get(f"{API}/recetas", params={"buscar": "Bistec"}, headers=encargado).json()["items"][0]
    # Margen negativo y alerta activa
    assert bistec["margen"] < 0 and bistec["alerta_margen_negativo"] is True


# Prueba: reglas de los ingredientes
def test_reglas_de_ingredientes(cliente, encargado):
    # Datos base de la receta
    base = {"nombre": f"Receta {aleatorio(6)}", "precio_venta": 5000}
    # Ingrediente repetido
    repetido = cliente.post(f"{API}/recetas", headers=encargado, json={**base, "ingredientes": [
        {"material_id": ARROZ, "cantidad": 1}, {"material_id": ARROZ, "cantidad": 2}]})  # El arroz aparece dos veces
    # Debe responder 422
    assert repetido.status_code == 422
    # Ingrediente que no existe
    inexistente = cliente.post(f"{API}/recetas", headers=encargado,
                               json={**base, "ingredientes": [{"material_id": 99999, "cantidad": 1}]})  # Material 99999
    # Debe responder 404
    assert inexistente.status_code == 404
    # Nombre repetido escrito en minúsculas ("frijolada" ya existe como "Frijolada")
    duplicada = cliente.post(f"{API}/recetas", headers=encargado,
                             json={**base, "nombre": "frijolada", "ingredientes": [{"material_id": ARROZ, "cantidad": 1}]})  # Cuerpo
    # Debe responder 409
    assert duplicada.status_code == 409


# Prueba: cambiar los ingredientes recalcula el costo; luego se elimina la receta
def test_cambiar_ingredientes_recalcula_el_costo_y_eliminar(cliente, encargado):
    # Receta con 1 kg de arroz
    datos = {"nombre": f"Receta {aleatorio(6)}", "precio_venta": 5000,
             "ingredientes": [{"material_id": ARROZ, "cantidad": 1}]}  # Fórmula inicial
    # Crea la receta
    receta = cliente.post(f"{API}/recetas", json=datos, headers=encargado).json()
    # Costo = 1 x 4.200
    assert receta["costo_produccion"] == 4200
    # Cambia la fórmula: 0.5 kg de arroz y 1 bandeja
    actualizada = cliente.patch(f"{API}/recetas/{receta['id']}", headers=encargado,
                                json={"ingredientes": [{"material_id": ARROZ, "cantidad": 0.5}, {"material_id": BANDEJA, "cantidad": 1}]})  # Nueva fórmula
    # Nuevo costo = 2.100 + 350 = 2.450
    assert actualizada.status_code == 200 and actualizada.json()["costo_produccion"] == 2450
    # Elimina la receta
    assert cliente.delete(f"{API}/recetas/{receta['id']}", headers=encargado).status_code == 200
    # Ya no existe: 404
    assert cliente.get(f"{API}/recetas/{receta['id']}", headers=encargado).status_code == 404


# Prueba: flujo completo del buzón de sugerencias
def test_flujo_de_sugerencias(cliente, encargado, aprendiz):
    # El aprendiz envía una sugerencia
    enviada = cliente.post(f"{API}/sugerencias", json={"asunto": "Postre", "mensaje": "¿Pueden incluir postre?"},
                           headers=aprendiz)  # Encabezado del aprendiz
    # Debe responder 201
    assert enviada.status_code == 201
    # Id de la sugerencia
    sugerencia_id = enviada.json()["id"]

    # El encargado consulta el buzón
    buzon = cliente.get(f"{API}/sugerencias", params={"tamano": 100}, headers=encargado).json()
    # Contadores
    contadores = buzon["contadores"]
    # Total = atendidas + pendientes
    assert contadores["total"] == contadores["atendidas"] + contadores["pendientes"]
    # Estados en el orden en que llegaron
    estados = [s["estado"] for s in buzon["items"]]
    assert estados == sorted(estados, key=lambda e: e != "PENDIENTE")  # pendientes primero

    # El aprendiz no puede atender: 403
    assert cliente.patch(f"{API}/sugerencias/{sugerencia_id}/atender", json={}, headers=aprendiz).status_code == 403
    # El encargado la atiende con una respuesta
    atendida = cliente.patch(f"{API}/sugerencias/{sugerencia_id}/atender", json={"respuesta": "Lo evaluaremos."},
                             headers=encargado)  # Encabezado del encargado
    # Queda ATENDIDA
    assert atendida.json()["estado"] == "ATENDIDA"
    # Atenderla otra vez responde 400
    assert cliente.patch(f"{API}/sugerencias/{sugerencia_id}/atender", json={}, headers=encargado).status_code == 400
    # El aprendiz consulta sus sugerencias
    mias = cliente.get(f"{API}/sugerencias/mias", headers=aprendiz).json()["items"]
    # Ve la respuesta del encargado
    assert mias[0]["respuesta"] == "Lo evaluaremos."


# Prueba: una sugerencia con mensaje demasiado largo
def test_sugerencia_con_mensaje_muy_largo(cliente, aprendiz):
    # Mensaje de 501 caracteres
    respuesta = cliente.post(f"{API}/sugerencias", json={"asunto": "Largo", "mensaje": "x" * 501}, headers=aprendiz)
    # Debe responder 422
    assert respuesta.status_code == 422
    # Con el mensaje en español
    assert respuesta.json()["detalles"][0]["mensaje"] == "Debe tener máximo 500 caracteres."


# Prueba: los totales del reporte de ventas cuadran
def test_reporte_de_ventas_cuadra(cliente, encargado):
    # Reporte del mes
    reporte = cliente.get(f"{API}/reportes/ventas", params={"periodo": "mes"}, headers=encargado).json()
    # Total = suma por día
    assert reporte["total_almuerzos"] == sum(d["almuerzos"] for d in reporte["por_dia"])
    # Total = suma por tipo
    assert reporte["total_almuerzos"] == sum(t["almuerzos"] for t in reporte["por_tipo"])
    # Ingresos = suma de ingresos por tipo
    assert reporte["total_ingresos"] == sum(t["ingresos"] for t in reporte["por_tipo"])
    # Un período que no existe responde 422
    assert cliente.get(f"{API}/reportes/ventas", params={"periodo": "decada"}, headers=encargado).status_code == 422


# Prueba: el rango de fechas de cada período
def test_rango_de_cada_periodo():
    fecha = date(2026, 11, 18)  # miércoles
    # Semana: lunes 16 a domingo 22
    assert rango_del_periodo(Periodo.SEMANA, fecha) == (date(2026, 11, 16), date(2026, 11, 22))
    # Mes: 1 al 30 de noviembre
    assert rango_del_periodo(Periodo.MES, fecha) == (date(2026, 11, 1), date(2026, 11, 30))
    # Trimestre: octubre a diciembre
    assert rango_del_periodo(Periodo.TRIMESTRE, fecha) == (date(2026, 10, 1), date(2026, 12, 31))
    # Semestre: julio a diciembre
    assert rango_del_periodo(Periodo.SEMESTRE, fecha) == (date(2026, 7, 1), date(2026, 12, 31))
    # Año completo
    assert rango_del_periodo(Periodo.ANIO, fecha) == (date(2026, 1, 1), date(2026, 12, 31))


# Prueba: los indicadores del encargado
def test_indicadores_del_encargado(cliente, encargado):
    # Consulta los indicadores
    indicadores = cliente.get(f"{API}/reportes/indicadores", headers=encargado).json()
    # Consulta el resumen de la cartera
    cartera = cliente.get(f"{API}/cartera", headers=encargado).json()["resumen"]
    # Los instructores con deuda deben coincidir con la cartera
    assert indicadores["instructores_con_deuda"] == cartera["total_deudores"]
    # Hoy hay al menos una venta (los datos de prueba tienen reservas de hoy)
    assert indicadores["ventas_hoy"] >= 1
