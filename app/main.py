# Este es el archivo principal de la API, aquí se crea la aplicación
# Para correrla: uvicorn app.main:app --reload

# FastAPI es la clase para crear la API
from fastapi import FastAPI
# CORSMiddleware sirve para dejar que una página web use la API
from fastapi.middleware.cors import CORSMiddleware

# Traigo la lista de páginas que pueden usar la API
from app.config import CORS_ORIGINS
# Traigo todos los archivos de rutas
from app.routers import auth, usuarios, fichas, menus, reservas, cartera, inventario, recetas, sugerencias, reportes

# Creo la aplicación (el título y la descripción salen en /docs)
app = FastAPI(
    title="GastroSENA API",  # Nombre de la API
    description="API para reservar y controlar los almuerzos del SENA Tecnoparque Yamboró. Primero haga login y luego pegue el access_token en el botón Authorize.",  # Explicación
    version="1.0",  # Versión
)

# Configuro el CORS para que las páginas de la lista puedan usar la API
app.add_middleware(
    CORSMiddleware,  # El middleware de CORS
    allow_origins=CORS_ORIGINS,  # Páginas que pueden usar la API
    allow_credentials=True,  # Deja mandar el token
    allow_methods=["*"],  # Deja usar todos los métodos (GET, POST, PUT, PATCH, DELETE)
    allow_headers=["*"],  # Deja mandar todos los encabezados
)

# Agrego las rutas de login
app.include_router(auth.router, prefix="/api/v1")
# Agrego las rutas de usuarios
app.include_router(usuarios.router, prefix="/api/v1")
# Agrego las rutas de fichas
app.include_router(fichas.router, prefix="/api/v1")
# Agrego las rutas de menús
app.include_router(menus.router, prefix="/api/v1")
# Agrego las rutas de reservas
app.include_router(reservas.router, prefix="/api/v1")
# Agrego las rutas de cartera
app.include_router(cartera.router, prefix="/api/v1")
# Agrego las rutas de inventario
app.include_router(inventario.router, prefix="/api/v1")
# Agrego las rutas de recetas
app.include_router(recetas.router, prefix="/api/v1")
# Agrego las rutas de sugerencias
app.include_router(sugerencias.router, prefix="/api/v1")
# Agrego las rutas de reportes
app.include_router(reportes.router, prefix="/api/v1")


# Ruta de inicio para saber si la API está funcionando
@app.get("/")
def inicio():
    # Devuelvo un mensaje de bienvenida
    return {"mensaje": "La API de GastroSENA está funcionando. Vaya a /docs para ver la documentación"}
