# GastroSENA API

API REST para el sistema de almuerzos del SENA - Tecnoparque Agroecológico Yamboró (Pitalito, Huila).
Es el proyecto formativo del programa Análisis y Desarrollo de Software (ADSO), ficha 3312744.
Actividad **EA4: Api Rest del proyecto formativo**.

## ¿Qué hace?

Antes las reservas de almuerzo, los cobros, lo que deben los instructores y el inventario de la cocina se
llevaban a mano. Con esta API todo queda guardado en PostgreSQL y se puede consultar según el rol de cada persona.

- **Inicio de sesión** con correo y contraseña. Devuelve un token JWT.
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
│   ├── main.py              # Archivo principal, aquí se crea la API
│   ├── core/                # Cosas generales que usan todos los módulos
│   │   ├── config.py        # Lee las variables del archivo .env
│   │   ├── seguridad.py     # Contraseñas y tokens
│   │   ├── permisos.py      # Saber quién hace la petición y revisar su rol
│   │   ├── roles.py         # Listas de roles para los permisos
│   │   ├── excepciones.py   # Funciones para responder los errores (400, 401, 403, 404, 409, 422)
│   │   ├── errores.py       # Pone todos los errores en español con la forma {"detalle": ...}
│   │   └── tiempo.py        # Horario para reservar
│   ├── database/
│   │   └── conexion.py      # Conexión con PostgreSQL y funciones para buscar, guardar y borrar
│   ├── models/              # Las tablas de la base de datos (un archivo por módulo)
│   ├── schemas/             # Validación de los datos que llegan y de las respuestas con response_model
│   ├── repositories/        # Las consultas a la base de datos
│   ├── services/            # Las reglas del negocio
│   └── routers/             # Las rutas (endpoints) de cada módulo
├── database/
│   ├── 01_ddl.sql           # Crea las tablas
│   ├── 02_dml.sql           # Datos de prueba
│   ├── 03_dcl.sql           # Usuario y permisos de la base de datos
│   ├── 04_auditoria.sql     # Solo si la base ya existía: le agrega las columnas de auditoría
│   └── 05_compatibilidad.sql # Solo si la base ya existía: renombra columnas al esquema actual
├── docs/                    # Documento de requisitos y colección de Postman
├── tests/                   # Pruebas con pytest
├── pytest.ini               # Le dice a pytest que las funciones de prueba empiezan con prueba_
├── requirements.txt
├── .env.example
└── README.md
```

Cada módulo (usuarios, fichas, menús, reservas, cartera, inventario, recetas, sugerencias y reportes)
tiene su archivo en cada carpeta. Una petición pasa así:

`routers` (revisa el rol) → `services` (revisa las reglas) → `repositories` (consulta la base de datos)

## Nombres en el código

- Las carpetas y los archivos tienen los nombres de la estructura original (`app`, `core`, `models`, `services`...).
- Las clases, funciones y variables están en español y en minúsculas, igual que las rutas y los campos del JSON.
- Los modelos (tablas) empiezan con `modelo_`, por ejemplo `modelo_usuario`, para que no se confundan con las variables.
- Los esquemas se llaman por lo que hacen, por ejemplo `usuario_crear` o `menu_respuesta`.
- Las variables del archivo `.env` también están en minúsculas, por ejemplo `bd_contrasena` o `clave_secreta_jwt`.
- Solo quedan en inglés los nombres que vienen de las librerías (`FastAPI`, `Column`, `BaseModel`, `HTTPException`...)
  y los que Python o pytest exigen así (`__init__.py`, `conftest.py`, `__tablename__`, `model_config`).

## Cómo instalarlo (Windows)

1. Crear el entorno virtual e instalar las librerías:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
 2. Recrear la base de datos con el esquema actual y ejecutar los scripts **en orden** (pide la contraseña de postgres, que en este proyecto se dejó en `1234`):

   ```powershell
   $psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
   & $psql -U postgres -c "DROP DATABASE IF EXISTS gastrosena_db"
   & $psql -U postgres -c "CREATE DATABASE gastrosena_db"
   & $psql -U postgres -d gastrosena_db -f database\01_ddl.sql
   & $psql -U postgres -d gastrosena_db -f database\02_dml.sql
   & $psql -U postgres -d gastrosena_db -f database\03_dcl.sql
   ```

   `03_dcl.sql` crea `api_gastrosena` con contraseña `1234` y, si ya existía, le actualiza la contraseña.
   También se puede hacer en pgAdmin abriendo cada archivo en el Query Tool.

   **¿Ya tenía la base creada de antes y no quiere borrarla?** No ejecute el `DROP DATABASE`; ejecute los dos scripts de actualización (se pueden repetir):

   ```powershell
   & $psql -U postgres -d gastrosena_db -f database\04_auditoria.sql
   & $psql -U postgres -d gastrosena_db -f database\05_compatibilidad.sql
   ```
3. Copiar el archivo `.env.example`, ponerle de nombre `.env` y llenar los datos.
   El ejemplo ya trae una `clave_secreta_jwt` de 64 caracteres solo para desarrollo; en producción se debe cambiar por una generada así:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
4. Correr la API:

   ```powershell
   uvicorn app.main:aplicacion --reload
   ```
5. Abrir **http://localhost:8000/docs**, iniciar sesión en `POST /api/v1/autenticacion/ingresar`, copiar el `token_acceso`
   y pegarlo en el botón **Authorize**.

## Usuarios de prueba

| Rol                            | Correo                      | Contraseña   |
| ------------------------------ | --------------------------- | ------------- |
| Encargado                      | encargado@gastrosena.com    | Encargado123  |
| Instructor (con deuda vencida) | instructor@gastrosena.com   | Instructor123 |
| Aprendiz                       | aprendiz@gastrosena.com     | Aprendiz123   |
| Aprendiz beneficiario          | beneficiario@gastrosena.com | Aprendiz123   |
| Invitado                       | invitado@gastrosena.com     | Invitado123   |
| Cuenta desactivada             | inactivo@gastrosena.com     | Aprendiz123   |

## Roles

| Rol        | Qué puede hacer                                                                                                                                       |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| encargado  | Todo lo de administrar: usuarios, fichas, menús, ver reservas, marcar pagos, cartera, inventario, recetas, sugerencias y reportes. No puede reservar. |
| instructor | Reservar almuerzos (se cargan a su cuenta del mes), ver su cuenta y mandar sugerencias.                                                                |
| aprendiz   | Reservar almuerzos, cancelarlos y mandar sugerencias. Si es beneficiario el almuerzo vale $0.                                                          |
| invitado   | Comprar almuerzos al precio de invitado y mandar sugerencias.                                                                                          |

Si no se manda el token la API responde **401** y si el rol no tiene permiso responde **403**.

## Endpoints

Hay **53 operaciones en 36 rutas bajo `/api/v1`** más `GET /` de salud (54 operaciones en total). Todas las operaciones bajo `/api/v1` necesitan token menos `ingresar` y `renovar`; `GET /` es pública y no lleva prefijo. `saltar` va de 0 en adelante y `limite` de 1 a 100.

| Método | Ruta                        | Qué hace                                                          | Quién                         |
| ------- | --------------------------- | ------------------------------------------------------------------ | ------------------------------ |
| POST    | /autenticacion/ingresar     | Iniciar sesión                                                    | todos                          |
| POST    | /autenticacion/renovar      | Pedir tokens nuevos                                                | todos                          |
| GET     | /autenticacion/perfil       | Ver mi perfil                                                      | todos                          |
| PUT     | /autenticacion/contrasena   | Cambiar mi contraseña                                             | todos                          |
| GET     | /roles                      | Ver los roles                                                      | encargado                      |
| GET     | /usuarios                   | Ver los usuarios (filtros: buscar, rol_id, activo, saltar, limite) | encargado                      |
| GET     | /usuarios/{id}              | Ver un usuario                                                     | encargado                      |
| POST    | /usuarios                   | Crear un usuario                                                   | encargado                      |
| PUT     | /usuarios/{id}              | Actualizar un usuario                                              | encargado                      |
| DELETE  | /usuarios/{id}              | Desactivar un usuario                                              | encargado                      |
| PATCH   | /usuarios/{id}/beneficiario | Poner o quitar beneficiario                                        | encargado                      |
| GET     | /fichas                     | Ver las fichas                                                     | encargado                      |
| GET     | /fichas/estadisticas        | Estadísticas de los grupos                                        | encargado                      |
| GET     | /fichas/{id}                | Ver una ficha                                                      | encargado                      |
| GET     | /fichas/{id}/reservas       | Aprendices de la ficha que reservaron                              | encargado                      |
| POST    | /fichas                     | Crear una ficha                                                    | encargado                      |
| PUT     | /fichas/{id}                | Actualizar una ficha                                               | encargado                      |
| DELETE  | /fichas/{id}                | Eliminar una ficha                                                 | encargado                      |
| GET     | /menus/hoy                  | Menú de hoy con mi precio                                         | todos                          |
| GET     | /menus/proximos             | Menús de hoy en adelante                                          | todos                          |
| GET     | /menus                      | Ver todos los menús                                               | encargado                      |
| GET     | /menus/{id}                 | Ver un menú                                                       | todos                          |
| POST    | /menus                      | Crear un menú                                                     | encargado                      |
| PUT     | /menus/{id}                 | Actualizar un menú                                                | encargado                      |
| DELETE  | /menus/{id}                 | Eliminar un menú                                                  | encargado                      |
| POST    | /reservas                   | Reservar o comprar                                                 | aprendiz, instructor, invitado |
| GET     | /reservas/mias              | Ver mis reservas                                                   | aprendiz, instructor, invitado |
| GET     | /reservas                   | Ver todas las reservas                                             | encargado                      |
| GET     | /reservas/{id}              | Ver una reserva (403 si es ajena)                                  | autenticado; el encargado ve todas |
| PATCH   | /reservas/{id}/cancelar     | Cancelar mi reserva                                                | aprendiz, instructor, invitado |
| PATCH   | /reservas/{id}/pago         | Marcar PAGADO o NO_PAGADO                                          | encargado                      |
| GET     | /cartera                    | Instructores que deben                                             | encargado                      |
| GET     | /cartera/mi-cuenta          | Mi cuenta del mes                                                  | instructor                     |
| GET     | /cartera/{id}               | Cuenta de un instructor                                            | encargado                      |
| POST    | /cartera/{id}/pagos         | Registrar un pago                                                  | encargado                      |
| GET     | /inventario/materiales      | Ver los materiales                                                 | encargado                      |
| GET     | /inventario/materiales/{id} | Ver un material                                                    | encargado                      |
| POST    | /inventario/materiales      | Crear un material                                                  | encargado                      |
| PUT     | /inventario/materiales/{id} | Actualizar un material                                             | encargado                      |
| DELETE  | /inventario/materiales/{id} | Eliminar un material                                               | encargado                      |
| POST    | /inventario/movimientos     | Entrada, salida o merma                                            | encargado                      |
| GET     | /inventario/kardex          | Ver el kardex                                                      | encargado                      |
| GET     | /recetas                    | Ver las recetas con su costo                                       | encargado                      |
| GET     | /recetas/{id}               | Ver una receta                                                     | encargado                      |
| POST    | /recetas                    | Crear una receta                                                   | encargado                      |
| PUT     | /recetas/{id}               | Actualizar una receta                                              | encargado                      |
| DELETE  | /recetas/{id}               | Eliminar una receta                                                | encargado                      |
| POST    | /sugerencias                | Mandar una sugerencia                                              | todos                          |
| GET     | /sugerencias/mias           | Ver mis sugerencias                                                | todos                          |
| GET     | /sugerencias                | Ver el buzón con contadores                                       | encargado                      |
| PATCH   | /sugerencias/{id}/atender   | Atender una sugerencia                                             | encargado                      |
| GET     | /reportes/ventas            | Ventas por periodo (dia, semana, mes, anio)                        | encargado                      |
| GET     | /reportes/indicadores       | Indicadores de hoy                                                 | encargado                      |

Todos los errores salen con la misma forma: `{"detalle": "El menú no existe"}`. Si los datos que se mandan no son válidos sale el error 422 con la lista de campos malos, por ejemplo `{"detalle": ["Falta el campo contrasena"]}`.

| Código | Cuándo sale                                                                                                                                                                                      |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 400     | No se cumple una regla del negocio (por ejemplo, reservar un menú agotado)                                                                                                                       |
| 401     | No mandaron el token, es falso o ya se venció                                                                                                                                                    |
| 403     | El rol no tiene permiso; al iniciar sesión también sale si la cuenta está bloqueada o inactiva (en rutas con token esos casos salen 401)                                                     |
| 404     | El registro no existe                                                                                                                                                                             |
| 409     | Ya existe un registro con un valor que no se puede repetir (correo, documento, código de la ficha, menú del día, código de barras, nombre de la receta o una segunda reserva del mismo menú) |
| 422     | Datos inválidos: falta un campo, tipo incorrecto, correo mal formado, precio negativo, `saltar < 0` o `limite` fuera de 1..100. Los enums inválidos que se revisan en el servicio salen 400      |
| 500     | Error interno. Al usuario solo le sale "Ocurrió un error interno, intente más tarde"; el detalle técnico queda en la consola del servidor. Si la BD tiene columnas antiguas, arranca fallando con la lista de columnas faltantes                     |

En **/docs** cada ruta dice qué hace, qué rol necesita y qué errores puede responder.

## Auditoría

Las tablas principales (usuarios, fichas, menús, reservas, pagos, materiales, recetas y sugerencias) guardan **quién creó el registro** (`creado_por`), **cuándo** (`fecha_creacion` o `fecha_pago`), **quién lo modificó por última vez** (`modificado_por`) y **cuándo** (`fecha_modificacion`).
No hay que hacer nada en cada servicio: `core/permisos.py` guarda en la sesión el id de quien hace la petición y la función `poner_auditoria` de `database/conexion.py` llena esas columnas antes de guardar. Los movimientos del kardex guardan el usuario en `usuario_id`.

## Reglas del negocio

- Solo se puede reservar o cancelar entre las 7:00 a. m. y las 9:00 p. m., hora de Colombia (UTC-5).
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
- Después de 5 intentos fallidos la cuenta se bloquea 15 minutos. Al cambiar la contraseña, los tokens anteriores dejan de servir.
- Los usuarios no se borran, se desactivan. Las fichas, menús y materiales que tienen datos relacionados también se desactivan en vez de borrarse.

## Pruebas

**Estado verificado (24/11/2026):** base `gastrosena_db` recreada con 11 tablas; `postgres` y `api_gastrosena` con contraseña `1234` solo para desarrollo; `59/59` pruebas en verde.

- **pytest**: hay 59 pruebas en la carpeta `tests` (incluye la auditoría, los errores 409 y 500 y que cada ruta esté documentada). Crean datos, entonces es mejor correrlas con una base de datos de prueba.
  ```powershell
  pytest -v
  ```
- **Postman**: importar `docs/GastroSENA_API.postman_collection.json` y correrla con el Collection Runner (89 peticiones).
  Las peticiones de iniciar sesión guardan los tokens solas en las variables.
  Trae casos que salen bien y casos que fallan a propósito: datos inválidos (422), registros repetidos (409), registros que no existen (404),
  sin token o con token vencido (401), rol sin permiso (403) y las reglas del negocio (400).
  También se puede correr desde la consola con Newman: `newman run docs/GastroSENA_API.postman_collection.json`

## Integrantes

Equipo **"Los Extraditables"**:

| Nombre                            | Rol en el equipo              |
| --------------------------------- | ----------------------------- |
| Breyner Julián Calderón Garcés | Desarrollador del sistema     |
| Johan Sebastián Burbano Vargas   | Responsable de la API         |
|                                   | Líder del proyecto           |
|                                   | Responsable de base de datos  |
|                                   | Responsable de pruebas        |
|                                   | Responsable de documentación |

## Documentos

- Requisitos: [`docs/Especificacion_Requisitos_GastroSENA.docx`](docs/Especificacion_Requisitos_GastroSENA.docx)
- Colección de Postman: [`docs/GastroSENA_API.postman_collection.json`](docs/GastroSENA_API.postman_collection.json)
- Repositorio del proyecto principal: https://github.com/burbano52100/Poryecto-Fromativo-
