"""Punto de entrada de la API: crea la aplicación y registra las rutas."""

# logging configura los mensajes que se muestran en la consola del servidor
import logging

# FastAPI es la clase con la que se crea la aplicación web
from fastapi import FastAPI
# Middleware que controla qué páginas web pueden llamar la API desde el navegador (CORS)
from fastapi.middleware.cors import CORSMiddleware

# Configuración leída del .env
from app.core.config import settings
# Función que registra los manejadores de errores (respuestas de error uniformes)
from app.core.errores import registrar_manejadores
# Importa los 10 módulos de rutas (cada uno tiene un "router" con sus endpoints)
from app.routers import (
    # Login, refresh, perfil y cambio de contraseña
    auth,
    # Deudas y pagos de instructores
    cartera,
    # Fichas y grupos
    fichas,
    # Materiales y kardex
    inventario,
    # Menú del Día
    menus,
    # Recetas con costo y margen
    recetas,
    # Ventas e indicadores
    reportes,
    # Reservas y consumos
    reservas,
    # Buzón de sugerencias
    sugerencias,
    # Usuarios, beneficiarios y roles
    usuarios,
)

# Muestra en la consola los mensajes de nivel INFO o superior, con fecha, nivel, origen y texto
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Crea la aplicación; estos datos aparecen en la documentación de Swagger (/docs)
app = FastAPI(
    # Título de la API
    title="GastroSENA API",
    # Texto de presentación que se ve en Swagger (en formato Markdown)
    description=(
        "API REST del sistema de almuerzos del SENA - Tecnoparque Agroecológico Yamboró (Pitalito, Huila). "
        "Proyecto formativo ADSO, ficha 3312744.\n\n"
        "1. Inicie sesión en **POST /api/v1/auth/login**.\n"
        "2. Copie el `access_token` y péguelo en el botón **Authorize**."
    ),
    # Versión de la API
    version="1.0.0",
)

# CORS: solo los orígenes autorizados en el .env pueden llamar la API desde un navegador (RT11)
app.add_middleware(
    # Middleware de CORS de FastAPI
    CORSMiddleware,
    # Lista de páginas web autorizadas (sale de CORS_ORIGINS en el .env)
    allow_origins=settings.cors_origins,
    # Permite enviar credenciales (encabezados de autorización) desde esas páginas
    allow_credentials=True,
    # Métodos HTTP permitidos
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    # Encabezados permitidos: el token y el tipo de contenido (JSON)
    allow_headers=["Authorization", "Content-Type"],
)

# Registra los manejadores de errores para que todas las respuestas de error tengan la misma forma
registrar_manejadores(app)

# Recorre los 10 módulos de rutas en este orden (es el orden en que aparecen en Swagger)
for modulo in (auth, usuarios, fichas, menus, reservas, cartera, inventario, recetas, sugerencias, reportes):
    # Agrega las rutas del módulo con el prefijo /api/v1 (ejemplo: /api/v1/auth/login)
    app.include_router(modulo.router, prefix="/api/v1")
