# Lógica del buzón de sugerencias

# datetime es la fecha y hora actual
from datetime import datetime

# Modelo de sugerencia para crear sugerencias nuevas
from app.models.sugerencia import modelo_sugerencia
# Funciones para responder los errores
from app.core.excepciones import error_regla, error_no_encontrado
# Funciones para buscar y guardar en la base de datos
from app.database.conexion import guardar, guardar_cambios, buscar_por_id
# Repositorio de sugerencias
from app.repositories import sugerencia_repository


# Función que convierte una sugerencia en un diccionario con el nombre de quien la mandó
def convertir_sugerencia(sugerencia):
    # Armo el diccionario con los datos de la sugerencia
    return {
        "id": sugerencia.id,  # Id de la sugerencia
        "usuario_id": sugerencia.usuario_id,  # Id de quien la mandó
        "nombre_usuario": sugerencia.usuario.nombre,  # Nombre de quien la mandó
        "asunto": sugerencia.asunto,  # Asunto
        "mensaje": sugerencia.mensaje,  # Mensaje
        "estado": sugerencia.estado,  # PENDIENTE o ATENDIDA
        "respuesta": sugerencia.respuesta,  # Respuesta del encargado
        "fecha_creacion": sugerencia.fecha_creacion,  # Cuándo se mandó
        "fecha_respuesta": sugerencia.fecha_respuesta,  # Cuándo se respondió
    }


# Función para mandar una sugerencia
def enviar_sugerencia(bd, datos, usuario):
    # Creo la sugerencia con el usuario que la manda
    nueva_sugerencia = modelo_sugerencia(
        usuario_id=usuario.id,  # Quién la manda
        asunto=datos.asunto,  # Asunto
        mensaje=datos.mensaje,  # Mensaje
        estado="PENDIENTE",  # Empieza pendiente
    )
    # La guardo y la devuelvo
    return guardar(bd, nueva_sugerencia)


# Función para ver mis sugerencias
def mis_sugerencias(bd, usuario):
    # Le pido al repositorio las sugerencias de la persona
    return sugerencia_repository.listar_de_usuario(bd, usuario.id)


# Función para ver el buzón con los contadores
def listar_sugerencias(bd, estado, saltar, limite):
    # Traigo las sugerencias
    sugerencias = sugerencia_repository.listar(bd, estado, saltar, limite)
    # Aquí voy a guardar las sugerencias convertidas
    lista = []
    # Recorro las sugerencias
    for sugerencia in sugerencias:
        # Agrego cada sugerencia convertida
        lista.append(convertir_sugerencia(sugerencia))
    # Devuelvo los contadores y la lista
    return {
        "contadores": {  # Cuántas sugerencias hay
            "total": sugerencia_repository.contar_todas(bd),  # Todas
            "pendientes": sugerencia_repository.contar_por_estado(bd, "PENDIENTE"),  # Sin atender
            "atendidas": sugerencia_repository.contar_por_estado(bd, "ATENDIDA"),  # Ya atendidas
        },
        "sugerencias": lista,  # Lista de sugerencias
    }


# Función para atender o responder una sugerencia
def atender_sugerencia(bd, sugerencia_id, datos):
    # Busco la sugerencia
    sugerencia = buscar_por_id(bd, modelo_sugerencia, sugerencia_id)
    # Si no existe
    if sugerencia is None:
        # Respondo 404
        error_no_encontrado("La sugerencia no existe")
    # Si ya fue atendida
    if sugerencia.estado == "ATENDIDA":
        # Respondo 400
        error_regla("La sugerencia ya fue atendida")
    # Cambio el estado
    sugerencia.estado = "ATENDIDA"
    # Guardo la respuesta
    sugerencia.respuesta = datos.respuesta
    # Guardo la fecha de hoy como fecha de respuesta
    sugerencia.fecha_respuesta = datetime.now()
    # Guardo los cambios
    guardar_cambios(bd, sugerencia)
    # Devuelvo la sugerencia
    return convertir_sugerencia(sugerencia)
