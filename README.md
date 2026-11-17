# GastroSENA API

API REST para el sistema de almuerzos del SENA - Tecnoparque Agroecológico Yamboró (Pitalito, Huila).
Es el proyecto formativo del programa Análisis y Desarrollo de Software (ADSO), ficha 3312744.
Actividad **EA4: Api Rest del proyecto formativo**.

## ¿Qué hace?

Antes las reservas de almuerzo, los cobros, lo que deben los instructores y el inventario de la cocina se
llevaban a mano. Con esta API todo queda guardado en PostgreSQL y se puede consultar según el rol de cada persona.

- **Login** con correo y contraseña. Devuelve un token JWT.
- **Usuarios**: el encargado crea las cuentas, les pone el rol y marca a los aprendices beneficiarios (almuerzo gratis).
- **Fichas**: los grupos de los aprendices, con estadísticas de cuántos reservaron.
- **Menú del día**: el encargado crea un menú por día con su precio y cantidad de almuerzos.
- **Reservas**: los aprendices reservan, los invitados compran y los instructores cargan el almuerzo a su cuenta del mes.
- **Cartera**: cuánto debe cada instructor y los pagos que hace.
- **Inventario**: materiales de la cocina, entradas, salidas, mermas y kardex.
- **Recetas**: los ingredientes de cada plato y cuánto cuesta hacerlo.
- **Sugerencias**: todos pueden mandar sugerencias y el encargado las responde.
- **Reportes**: ventas por día, semana, mes o año e indicadores del día.

## Tecnologías

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- JWT (PyJWT)
- bcrypt
- pytest
- Postman

## Carpetas del proyecto

```
api_proyecto_formativo/
├── app/
│   ├── main.py          # Archivo principal, aquí se crea la API
│   ├── config.py        # Lee las variables del archivo .env
│   ├── database.py      # Conexión con PostgreSQL
│   ├── models.py        # Las tablas de la base de datos
│   ├── schemas.py       # Validación de los datos que llegan
│   ├── seguridad.py     # Contraseñas, tokens y permisos
│   └── routers/         # Las rutas de cada módulo
│       ├── auth.py
│       ├── usuarios.py
│       ├── fichas.py
│       ├── menus.py
│       ├── reservas.py
│       ├── cartera.py
│       ├── inventario.py
│       ├── recetas.py
│       ├── sugerencias.py
│       └── reportes.py
├── database/
│   ├── 01_ddl.sql       # Crea las tablas
│   ├── 02_dml.sql       # Datos de prueba
│   └── 03_dcl.sql       # Usuario y permisos de la base de datos
├── docs/                # Documento de requisitos y colección de Postman
├── tests/               # Pruebas con pytest
├── requirements.txt
├── .env.example
└── README.md
```

## Cómo instalarlo (Windows)

1. Crear el entorno virtual e instalar las librerías:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Crear la base de datos y ejecutar los scripts **en orden** (pide la contraseña de postgres):
   ```powershell
   $psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
   & $psql -U postgres -c "CREATE DATABASE gastrosena_db"
   & $psql -U postgres -d gastrosena_db -f database\01_ddl.sql
   & $psql -U postgres -d gastrosena_db -f database\02_dml.sql
   & $psql -U postgres -d gastrosena_db -f database\03_dcl.sql
   ```
   También se puede hacer en pgAdmin abriendo cada archivo en el Query Tool.
   Si el usuario `api_gastrosena` ya existía, el `03_dcl.sql` muestra un error en el `CREATE USER`, pero los permisos sí se dan.

3. Copiar el archivo `.env.example`, ponerle de nombre `.env` y llenar los datos.
   En `JWT_SECRET_KEY` hay que poner una clave larga. Se puede sacar con:
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. Correr la API:
   ```powershell
   uvicorn app.main:app --reload
   ```

5. Abrir **http://localhost:8000/docs**, hacer login en `POST /api/v1/auth/login`, copiar el `access_token`
   y pegarlo en el botón **Authorize**.

## Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Encargado | encargado@gastrosena.com | Encargado123 |
| Instructor (con deuda vencida) | instructor@gastrosena.com | Instructor123 |
| Aprendiz | aprendiz@gastrosena.com | Aprendiz123 |
| Aprendiz beneficiario | beneficiario@gastrosena.com | Aprendiz123 |
| Invitado | invitado@gastrosena.com | Invitado123 |
| Cuenta desactivada | inactivo@gastrosena.com | Aprendiz123 |

## Roles

| Rol | Qué puede hacer |
|---|---|
| encargado | Todo lo de administrar: usuarios, fichas, menús, ver reservas, marcar pagos, cartera, inventario, recetas, sugerencias y reportes. No puede reservar. |
| instructor | Reservar almuerzos (se cargan a su cuenta del mes), ver su cuenta y mandar sugerencias. |
| aprendiz | Reservar almuerzos, cancelarlos y mandar sugerencias. Si es beneficiario el almuerzo vale $0. |
| invitado | Comprar almuerzos al precio de invitado y mandar sugerencias. |

Si no se manda el token la API responde **401** y si el rol no tiene permiso responde **403**.

## Endpoints

Todas las rutas empiezan con `/api/v1`. Todas necesitan token menos el login y el refresh.

| Método | Ruta | Qué hace | Quién |
|---|---|---|---|
| POST | /auth/login | Iniciar sesión | todos |
| POST | /auth/refresh | Pedir tokens nuevos | todos |
| GET | /auth/perfil | Ver mi perfil | todos |
| PUT | /auth/password | Cambiar mi contraseña | todos |
| GET | /roles | Ver los roles | encargado |
| GET | /usuarios | Ver los usuarios (filtros: buscar, rol_id, activo, skip, limit) | encargado |
| GET | /usuarios/{id} | Ver un usuario | encargado |
| POST | /usuarios | Crear un usuario | encargado |
| PUT | /usuarios/{id} | Actualizar un usuario | encargado |
| DELETE | /usuarios/{id} | Desactivar un usuario | encargado |
| PATCH | /usuarios/{id}/beneficiario | Poner o quitar beneficiario | encargado |
| GET | /fichas | Ver las fichas | encargado |
| GET | /fichas/estadisticas | Estadísticas de los grupos | encargado |
| GET | /fichas/{id} | Ver una ficha | encargado |
| GET | /fichas/{id}/reservas | Aprendices de la ficha que reservaron | encargado |
| POST | /fichas | Crear una ficha | encargado |
| PUT | /fichas/{id} | Actualizar una ficha | encargado |
| DELETE | /fichas/{id} | Eliminar una ficha | encargado |
| GET | /menus/hoy | Menú de hoy con mi precio | todos |
| GET | /menus/proximos | Menús de hoy en adelante | todos |
| GET | /menus | Ver todos los menús | encargado |
| GET | /menus/{id} | Ver un menú | todos |
| POST | /menus | Crear un menú | encargado |
| PUT | /menus/{id} | Actualizar un menú | encargado |
| DELETE | /menus/{id} | Eliminar un menú | encargado |
| POST | /reservas | Reservar o comprar | aprendiz, instructor, invitado |
| GET | /reservas/mias | Ver mis reservas | aprendiz, instructor, invitado |
| GET | /reservas | Ver todas las reservas | encargado |
| GET | /reservas/{id} | Ver una reserva | todos (solo las propias) |
| PATCH | /reservas/{id}/cancelar | Cancelar mi reserva | aprendiz, instructor, invitado |
| PATCH | /reservas/{id}/pago | Marcar PAGADO o NO_PAGADO | encargado |
| GET | /cartera | Instructores que deben | encargado |
| GET | /cartera/mi-cuenta | Mi cuenta del mes | instructor |
| GET | /cartera/{id} | Cuenta de un instructor | encargado |
| POST | /cartera/{id}/pagos | Registrar un pago | encargado |
| GET | /inventario/materiales | Ver los materiales | encargado |
| GET | /inventario/materiales/{id} | Ver un material | encargado |
| POST | /inventario/materiales | Crear un material | encargado |
| PUT | /inventario/materiales/{id} | Actualizar un material | encargado |
| DELETE | /inventario/materiales/{id} | Eliminar un material | encargado |
| POST | /inventario/movimientos | Entrada, salida o merma | encargado |
| GET | /inventario/kardex | Ver el kardex | encargado |
| GET | /recetas | Ver las recetas con su costo | encargado |
| GET | /recetas/{id} | Ver una receta | encargado |
| POST | /recetas | Crear una receta | encargado |
| PUT | /recetas/{id} | Actualizar una receta | encargado |
| DELETE | /recetas/{id} | Eliminar una receta | encargado |
| POST | /sugerencias | Mandar una sugerencia | todos |
| GET | /sugerencias/mias | Ver mis sugerencias | todos |
| GET | /sugerencias | Ver el buzón con contadores | encargado |
| PATCH | /sugerencias/{id}/atender | Atender una sugerencia | encargado |
| GET | /reportes/ventas | Ventas por periodo (dia, semana, mes, anio) | encargado |
| GET | /reportes/indicadores | Indicadores de hoy | encargado |

Los errores salen así: `{"detail": "El menú no existe"}`

## Reglas del negocio

- Solo se puede reservar o cancelar entre las 7:00 a. m. y las 9:00 p. m.
- Una persona solo puede tener una reserva por menú.
- No se puede reservar un menú agotado, desactivado o de un día que ya pasó. Cada reserva descuenta un almuerzo.
- El precio lo pone la API según el rol: aprendiz $5.000, beneficiario $0, instructor $5.000 (a su cuenta) e invitado $8.000.
- Solo puede haber un menú por día y la cantidad no puede quedar menor que lo que ya se vendió.
- El pago de un instructor no puede ser mayor que lo que debe. Si paga todo, sus consumos quedan PAGADOS.
- La deuda de un instructor queda VENCIDA si tiene un consumo sin pagar de hace más de 30 días.
- Una salida o merma no puede dejar el stock en negativo. Cada movimiento queda guardado en el kardex.
- No se puede eliminar un material que usa una receta activa.
- Solo los aprendices tienen ficha y pueden ser beneficiarios.
- Nadie puede cambiar su propio rol ni desactivar su propia cuenta.
- Después de 5 intentos fallidos la cuenta se bloquea 15 minutos.
- Los usuarios no se borran, se desactivan. Las fichas, menús y materiales que tienen datos relacionados también se desactivan en vez de borrarse.

## Pruebas

- **pytest**: hay 54 pruebas en la carpeta `tests`. Crean datos, entonces es mejor correrlas con una base de datos de prueba.
  ```powershell
  pytest -v
  ```
- **Postman**: importar `docs/GastroSENA_API.postman_collection.json` y correrla con el Collection Runner.
  Los logins guardan los tokens solos en las variables.

## Integrantes

Equipo **"Los Extraditables"**:

| Nombre | Rol en el equipo |
|---|---|
| Breyner Julián Calderón Garcés | Desarrollador del sistema |
| | Líder del proyecto |
| | Responsable de base de datos |
| | Responsable de la API |
| | Responsable de pruebas |
| | Responsable de documentación |

## Documentos

- Requisitos: [`docs/Especificacion_Requisitos_GastroSENA.docx`](docs/Especificacion_Requisitos_GastroSENA.docx)
- Colección de Postman: [`docs/GastroSENA_API.postman_collection.json`](docs/GastroSENA_API.postman_collection.json)
- Repositorio del proyecto principal: https://github.com/burbano52100/Poryecto-Fromativo-
