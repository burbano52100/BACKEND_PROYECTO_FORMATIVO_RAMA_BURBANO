# Este es el archivo principal de la API, aquí se crea la aplicación
# Para correrla: uvicorn app.main:aplicacion --reload

# FastAPI es la clase para crear la API
from fastapi import FastAPI
# RequestValidationError es el error que sale cuando mandan datos que no son válidos
from fastapi.exceptions import RequestValidationError
# CORSMiddleware sirve para dejar que una página web use la API
from fastapi.middleware.cors import CORSMiddleware
# HTTPException de starlette es la que usa FastAPI por dentro para todos los errores
from starlette.exceptions import HTTPException as excepcion_http
# IntegrityError es el error que sale cuando PostgreSQL rechaza un cambio
from sqlalchemy.exc import IntegrityError

# asynccontextmanager sirve para decir qué se hace cuando la API arranca
from contextlib import asynccontextmanager

# Traigo la lista de páginas que pueden usar la API
from app.core.config import origenes_cors
# Traigo la función que revisa si la base de datos tiene la auditoría
from app.database.conexion import falta_auditoria
# Traigo las funciones que arreglan los errores
from app.core.errores import manejar_errores, manejar_datos_malos, manejar_error_integridad, manejar_error_interno
# Traigo todos los archivos de rutas
from app.routers import auth, usuarios, fichas, menus, reservas, cartera, inventario, recetas, sugerencias, reportes

# Esto se ejecuta una vez cuando la API arranca (antes de recibir peticiones)
@asynccontextmanager
async def al_arrancar(aplicacion):
    # Si la base de datos no tiene las columnas de auditoría, no dejo que la API arranque y explico qué hacer
    if falta_auditoria():
        # Muestro el error en la consola
        raise Exception("La base de datos no tiene las columnas de auditoría. Ejecute ACTUALIZAR-BASE-DE-DATOS.bat (o database/04_auditoria.sql con el usuario postgres) y vuelva a encender la API.")
    # Aquí la API queda funcionando
    yield


# Creo la aplicación (el título y la descripción salen en /docs)
aplicacion = FastAPI(
    title="GastroSENA API",  # Nombre de la API
    description="API para reservar y controlar los almuerzos del SENA Tecnoparque Yamboró. Primero inicie sesión y luego pegue el token_acceso en el botón Authorize.",  # Explicación
    version="1.0",  # Versión
    lifespan=al_arrancar,  # Lo que se revisa al arrancar
)

# Configuro el CORS para que las páginas de la lista puedan usar la API
aplicacion.add_middleware(
    CORSMiddleware,  # El middleware de CORS
    allow_origins=origenes_cors,  # Páginas que pueden usar la API
    allow_credentials=True,  # Deja mandar el token
    allow_methods=["*"],  # Deja usar todos los métodos (GET, POST, PUT, PATCH, DELETE)
    allow_headers=["*"],  # Deja mandar todos los encabezados
)

# Le digo a la API que use mi función para los errores normales
aplicacion.add_exception_handler(excepcion_http, manejar_errores)
# Le digo a la API que use mi función para los errores de datos malos
aplicacion.add_exception_handler(RequestValidationError, manejar_datos_malos)
# Si PostgreSQL rechaza un cambio respondo 409 sin mostrar el error técnico
aplicacion.add_exception_handler(IntegrityError, manejar_error_integridad)
# Cualquier otro error que no esperábamos sale como 500 sin mostrar detalles técnicos
aplicacion.add_exception_handler(Exception, manejar_error_interno)

# Agrego las rutas de inicio de sesión
aplicacion.include_router(auth.enrutador, prefix="/api/v1")
# Agrego las rutas de usuarios
aplicacion.include_router(usuarios.enrutador, prefix="/api/v1")
# Agrego las rutas de fichas
aplicacion.include_router(fichas.enrutador, prefix="/api/v1")
# Agrego las rutas de menús
aplicacion.include_router(menus.enrutador, prefix="/api/v1")
# Agrego las rutas de reservas
aplicacion.include_router(reservas.enrutador, prefix="/api/v1")
# Agrego las rutas de cartera
aplicacion.include_router(cartera.enrutador, prefix="/api/v1")
# Agrego las rutas de inventario
aplicacion.include_router(inventario.enrutador, prefix="/api/v1")
# Agrego las rutas de recetas
aplicacion.include_router(recetas.enrutador, prefix="/api/v1")
# Agrego las rutas de sugerencias
aplicacion.include_router(sugerencias.enrutador, prefix="/api/v1")
# Agrego las rutas de reportes
aplicacion.include_router(reportes.enrutador, prefix="/api/v1")


# Ruta de inicio para saber si la API está funcionando
@aplicacion.get("/", summary="Saber si la API está funcionando", description="Responde un mensaje de bienvenida. **Rol requerido:** ninguno (es pública).")
def inicio():
    # Devuelvo un mensaje de bienvenida
    return {"mensaje": "La API de GastroSENA está funcionando. Vaya a /docs para ver la documentación"}


# Otro nombre para la aplicación, por si alguien la corre con: uvicorn app.main:app
app = aplicacion
