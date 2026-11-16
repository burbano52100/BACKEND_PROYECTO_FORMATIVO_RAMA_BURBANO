# GastroSENA API — Sistema de Almuerzos

API REST construida con **FastAPI** y **PostgreSQL** para el proyecto formativo del programa
Análisis y Desarrollo de Software — SENA, Centro de Gestión y Desarrollo Sostenible
Surcolombiano (CGDSS), ficha 3312744. Actividad **EA4: Api Rest del proyecto formativo**.

---

## ¿Qué es GastroSENA?

GastroSENA es el sistema de **reserva, venta y control de almuerzos** del SENA en el
**Tecnoparque Agroecológico Yamboró** (Pitalito, Huila).

**El problema:** las reservas, los cobros, las deudas de los instructores y el inventario de la
cocina se manejaban a mano. No se sabía con certeza cuántos almuerzos había que preparar, quién
había pagado, cuánto debía cada instructor ni qué ingredientes estaban por agotarse o vencerse.

**La solución:** esta API centraliza toda esa información en PostgreSQL y la expone de forma
segura para que la aplicación web (o cualquier otro cliente) la consulte y la actualice según el
rol de cada persona. Es la versión **EA4** del proyecto (FastAPI + PostgreSQL + JWT, con
arquitectura por capas), construida a partir del documento
[`docs/Especificacion_Requisitos_GastroSENA.docx`](docs/Especificacion_Requisitos_GastroSENA.docx).

## ¿Qué hace?

| Módulo | Qué permite |
|---|---|
| **Autenticación** | Iniciar sesión con correo y contraseña, renovar el token, ver el perfil y cambiar la contraseña. Bloquea la cuenta 15 minutos tras 5 intentos fallidos. |
| **Usuarios y beneficiarios** | El Encargado registra las cuentas, asigna roles, desactiva usuarios y marca aprendices como **beneficiarios** (almuerzo a $0). |
| **Fichas y grupos** | Grupos de formación (ficha, programa, jornada, vocero). Estadísticas del día y lista de aprendices de cada ficha que reservaron, con su estado de pago. |
| **Menú del Día** | El Encargado configura un menú por fecha con precios diferenciados y cupo. Cada persona ve el menú con **su** precio. |
| **Reservas y consumos** | Aprendices reservan, invitados compran e instructores consumen a su cuenta mensual. Se descuenta el cupo, se controla el horario y se puede cancelar. El Encargado marca **Pagado / No pagado**. |
| **Cartera de deudas** | Saldo de cada instructor (consumido − pagado), días vencidos, estado de la deuda, registro de pagos y cuenta mensual del instructor. |
| **Inventario** | Materiales con código de barras, estado del stock (**Bueno, Bajo, Crítico, Venciendo**), entradas, salidas y **mermas** con **kardex**. |
| **Recetas** | Fórmula de cada plato con cálculo automático de **costo de producción, margen y alerta de margen negativo**. |
| **Sugerencias** | Todos envían sugerencias; el Encargado las ve con contadores y las atiende o responde. |
| **Reportes** | Ventas e ingresos por día, semana, mes, trimestre, semestre o año, por tipo de cliente y por día; indicadores del Encargado. |

## Tipos de usuario y permisos

| Rol | Quién es |
|---|---|
| **encargado** | Responsable del servicio. Es el administrador del sistema: único que gestiona usuarios y asigna roles. |
| **instructor** | Docente que consume almuerzos y los paga con una cuenta mensual. |
| **aprendiz** | Estudiante que reserva su almuerzo. Si es beneficiario, el almuerzo le cuesta $0. |
| **invitado** | Visitante externo que compra el almuerzo a precio de invitado. |

**Matriz de roles y permisos** (el backend la verifica en cada endpoint: **401** sin token o con token inválido, **403** si el rol no tiene permiso):

| Recurso / operación | Encargado | Instructor | Aprendiz | Invitado |
|---|:-:|:-:|:-:|:-:|
| Usuarios, roles y beneficiarios | ✔ | | | |
| Fichas y grupos | ✔ | | | |
| Menú: configurar, editar, eliminar, historial | ✔ | | | |
| Menú de hoy y próximos (con mi precio) | ✔ | ✔ | ✔ | ✔ |
| Reservar / comprar, mis consumos, cancelar la propia | | ✔ | ✔ | ✔ |
| Ver todas las reservas, marcar pago | ✔ | | | |
| Cartera: deudores, detalle, registrar pagos | ✔ | | | |
| Cartera: mi cuenta mensual | | ✔ | | |
| Inventario, kardex y recetas | ✔ | | | |
| Enviar sugerencias y ver las mías | ✔ | ✔ | ✔ | ✔ |
| Buzón completo y atender sugerencias | ✔ | | | |
| Reportes e indicadores | ✔ | | | |
| Mi perfil y cambiar mi contraseña | ✔ | ✔ | ✔ | ✔ |

## Reglas de negocio

Todas viven en la capa `services/` (nunca en las rutas):

| # | Regla | Requisito |
|---|---|---|
| RN-01 | Solo se reserva o cancela entre las **7:00 a. m. y las 9:00 p. m.** | RF09 |
| RN-02 | **Una reserva por persona y por menú** (409); una cancelada no cuenta. | RF09 |
| RN-03 | No se reserva un menú **agotado**, inactivo o de una fecha pasada; cada reserva **descuenta el cupo**. | RF08, RF17 |
| RN-04 | El **precio lo calcula la API** según el rol: aprendiz $5.000, beneficiario $0, invitado $8.000; al instructor se le carga a su cuenta mensual. | RF08, RF11, RF12 |
| RN-05 | **Un solo menú por fecha**, con fecha desde hoy; el cupo no puede quedar por debajo de lo vendido. | RF16 |
| RN-06 | Solo el Encargado marca Pagado / No pagado; los consumos de instructores **se pagan por la cartera**. | RF42 |
| RN-07 | Un **pago no puede superar la deuda**; si la salda, todos los consumos pendientes quedan **PAGADOS**. | RF23 |
| RN-08 | Una deuda está **VENCIDA** cuando pasa el corte mensual más el plazo de pago (5 días, configurable). | RF22 |
| RN-09 | Una salida o merma **no puede dejar el stock en negativo**; movimiento y stock se guardan en una sola transacción. | RF36, RF37 |
| RN-10 | El stock **solo cambia con movimientos**; el stock inicial genera una ENTRADA en el kardex. El kardex no se edita ni se borra. | RF29, RF30, RF35 |
| RN-11 | No se elimina un material que use una **receta activa**. | RF31 |
| RN-12 | Solo los **aprendices** pertenecen a una ficha y pueden ser beneficiarios; no se agrega dos veces el mismo beneficiario. | RF45 |
| RN-13 | Nadie puede **cambiar su propio rol ni desactivar su propia cuenta**; una cuenta inactiva no inicia sesión. | EA4 |
| RN-14 | **Borrado lógico** de los registros con movimientos asociados: usuarios, fichas con aprendices, menús con reservas y materiales con kardex. | EA4 |

## Endpoints (53, todos con el prefijo `/api/v1`)

Todos son privados excepto `POST /auth/login` (y `POST /auth/refresh`, que exige un refresh token).
La documentación interactiva, con descripción, parámetros, cuerpo, respuestas, códigos de estado y
rol requerido de cada endpoint, está en **http://localhost:8000/docs**.

<details>
<summary><b>Ver la lista completa</b></summary>

| Método | Ruta | Descripción | Rol |
|---|---|---|---|
| POST | `/auth/login` | Iniciar sesión | público |
| POST | `/auth/refresh` | Renovar tokens | refresh token |
| GET | `/auth/perfil` | Mi perfil | todos |
| PUT | `/auth/password` | Cambiar mi contraseña | todos |
| GET | `/usuarios` | Listar (filtros y paginación) | encargado |
| GET | `/usuarios/{id}` | Consultar | encargado |
| POST | `/usuarios` | Registrar | encargado |
| PATCH | `/usuarios/{id}` | Actualizar | encargado |
| DELETE | `/usuarios/{id}` | Desactivar (borrado lógico) | encargado |
| PATCH | `/usuarios/{id}/beneficiario` | Agregar o quitar beneficiario | encargado |
| GET | `/roles` | Listar roles | encargado |
| GET | `/fichas` | Listar | encargado |
| GET | `/fichas/estadisticas` | Estadísticas de grupos | encargado |
| GET | `/fichas/{id}` | Consultar | encargado |
| GET | `/fichas/{id}/reservas` | Aprendices que reservaron | encargado |
| POST / PATCH / DELETE | `/fichas`, `/fichas/{id}` | Crear, actualizar, eliminar | encargado |
| GET | `/menus/hoy` | Menú de hoy con mi precio | todos |
| GET | `/menus/proximos` | Próximos menús con mi precio | todos |
| GET | `/menus` | Historial de menús | encargado |
| GET | `/menus/{id}` | Consultar | todos |
| POST / PATCH / DELETE | `/menus`, `/menus/{id}` | Configurar, actualizar, eliminar | encargado |
| POST | `/reservas` | Reservar o comprar | aprendiz, instructor, invitado |
| GET | `/reservas/mias` | Mis consumos | aprendiz, instructor, invitado |
| GET | `/reservas` | Todas las reservas (ventas) | encargado |
| GET | `/reservas/{id}` | Consultar (propia o cualquiera si es encargado) | todos |
| PATCH | `/reservas/{id}/cancelar` | Cancelar mi reserva | aprendiz, instructor, invitado |
| PATCH | `/reservas/{id}/pago` | Marcar Pagado / No pagado | encargado |
| GET | `/cartera` | Instructores con deuda y resumen | encargado |
| GET | `/cartera/mi-cuenta` | Mi cuenta mensual | instructor |
| GET | `/cartera/{instructor_id}` | Deuda e historial de pagos | encargado |
| POST | `/cartera/{instructor_id}/pagos` | Registrar pago | encargado |
| GET | `/inventario/materiales` | Control de stock | encargado |
| GET | `/inventario/materiales/{id}` | Consultar material | encargado |
| POST / PATCH / DELETE | `/inventario/materiales`, `/inventario/materiales/{id}` | Agregar, editar, eliminar | encargado |
| POST | `/inventario/movimientos` | Entrada, salida o merma | encargado |
| GET | `/inventario/kardex` | Kardex e historial de mermas | encargado |
| GET | `/recetas`, `/recetas/{id}` | Listar y consultar con costo y margen | encargado |
| POST / PATCH / DELETE | `/recetas`, `/recetas/{id}` | Crear, actualizar, eliminar | encargado |
| POST | `/sugerencias` | Enviar sugerencia | todos |
| GET | `/sugerencias/mias` | Mis sugerencias | todos |
| GET | `/sugerencias` | Buzón con contadores | encargado |
| PATCH | `/sugerencias/{id}/atender` | Atender o responder | encargado |
| GET | `/reportes/ventas` | Ventas e ingresos por período | encargado |
| GET | `/reportes/indicadores` | Indicadores del Encargado | encargado |

</details>

**Procesos de negocio** (además de los CRUD): reservar o comprar, cancelar una reserva, marcar el
pago, menú del día con precio por rol, cálculo de la cartera, registro de pagos con saldo
automático, cuenta mensual del instructor, movimientos de inventario con kardex, costo y margen
de recetas, estadísticas de grupos, reporte de ventas por período e indicadores.

**Estructura de los errores** (siempre la misma, en español; códigos 400, 401, 403, 404, 409, 422 y 500):

```json
{
  "estado": 422,
  "mensaje": "Los datos enviados no son válidos.",
  "detalles": [{"campo": "precio_aprendiz", "mensaje": "Debe ser mayor o igual que 0."}]
}
```

## Arquitectura por capas

```
Petición HTTP ──► routers/       Recibe la petición, valida el rol y devuelve la respuesta con su código
                     │
                     ▼
                  services/      Reglas de negocio; no conoce HTTP (lanza excepciones de core/excepciones)
                     │
                     ▼
                  repositories/  Única capa que consulta y modifica la base de datos
                     │
                     ▼
                  models/  ◄──►  database/  ◄──►  PostgreSQL (esquema gastrosena)

schemas/  valida los datos que entran y salen (salida separada: nunca expone la contraseña)
core/     configuración, JWT, bcrypt, permisos por rol, horario y manejo uniforme de errores
```

## Tecnologías

Python 3.11+ · FastAPI · Uvicorn · PostgreSQL 16+ · SQLAlchemy 2 · psycopg 3 · Pydantic 2 ·
pydantic-settings · PyJWT · bcrypt · pytest · Postman · Git y GitHub.

## Requisitos

- Python 3.11 o superior (probado con 3.15)
- PostgreSQL 16 o superior (probado con 18) y pgAdmin 4 o DBeaver
- Git

## Instalación y ejecución (Windows, PowerShell)

1. **Entrar a la carpeta y crear el entorno virtual:**
   ```powershell
   cd api_proyecto_formativo
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
   Si PowerShell no deja activar el entorno: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

2. **Crear la base de datos** y ejecutar los scripts **en orden**. Se pide la contraseña de `postgres`:
   ```powershell
   $psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
   & $psql -U postgres -c "CREATE DATABASE gastrosena_db"
   & $psql -U postgres -d gastrosena_db -f database\01_ddl.sql
   & $psql -U postgres -d gastrosena_db -f database\02_dml.sql
   & $psql -U postgres -d gastrosena_db -f database\03_dcl.sql
   ```
   Con pgAdmin: cree la base `gastrosena_db` y ejecute cada script en el *Query Tool*.

3. **Configurar el `.env`:** copie `.env.example` como `.env` y ponga en `JWT_SECRET_KEY` el resultado de:
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   `DB_PASSWORD` debe ser la misma contraseña que crea `03_dcl.sql`. La API se conecta con el
   usuario `api_gastrosena`, que tiene privilegios mínimos, y no con `postgres`.

4. **Ejecutar la API:**
   ```powershell
   uvicorn app.main:app --reload
   ```

5. **Abrir http://localhost:8000/docs**. Inicie sesión en `POST /api/v1/auth/login`, copie el
   `access_token` y péguelo en el botón **Authorize**.

> Con Python 3.15 se usa `uvicorn` sin el extra `[standard]`, porque ese extra exige compilar
> `pyyaml` con Visual C++.

## Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| Encargado | encargado@gastrosena.com | Encargado123 |
| Instructor (con deuda vencida) | instructor@gastrosena.com | Instructor123 |
| Aprendiz | aprendiz@gastrosena.com | Aprendiz123 |
| Aprendiz beneficiario | beneficiario@gastrosena.com | Aprendiz123 |
| Invitado | invitado@gastrosena.com | Invitado123 |
| Cuenta inactiva (no puede ingresar) | inactivo@gastrosena.com | Aprendiz123 |

Los datos de prueba (`02_dml.sql`) usan fechas relativas al día de ejecución: siempre hay menú de
hoy y de mañana, reservas recientes, instructores con deuda activa, vencida y al día, materiales en
cada estado de stock y una receta con margen negativo.

## Pruebas

- **Automáticas (pytest):** 64 pruebas de casos exitosos y fallidos: datos inválidos, duplicados,
  registros inexistentes, sin token, token vencido, rol sin permiso, bloqueo de cuenta y cada regla
  de negocio. Ejecútelas contra una base de datos de **pruebas**, porque crean registros:
  ```powershell
  pytest -v
  ```
- **Postman:** importe `docs/GastroSENA_API.postman_collection.json` y ejecútela completa con el
  *Collection Runner*. Son 51 peticiones con pruebas; los logins guardan los tokens en variables.

## Estructura del proyecto

```
api_proyecto_formativo/
├── app/
│   ├── main.py          # Crea la aplicación, CORS, manejo de errores y registra las rutas
│   ├── core/            # config, seguridad (JWT y bcrypt), permisos, roles, tiempo y errores
│   ├── database/        # Conexión a PostgreSQL
│   ├── models/          # Tablas: usuarios, fichas, menús, reservas, inventario, recetas, sugerencias
│   ├── schemas/         # Validación de datos de entrada y salida
│   ├── repositories/    # Única capa que consulta y modifica la base de datos
│   ├── services/        # Reglas de negocio
│   └── routers/         # Endpoints HTTP
├── database/            # 01_ddl.sql, 02_dml.sql, 03_dcl.sql
├── docs/                # Especificación de requisitos y colección de Postman
├── tests/               # Pruebas con pytest
├── requirements.txt
├── .env.example
└── README.md
```

## Del documento de requisitos a la API EA4

La especificación describe el GastroSENA original (Node.js/Express). Para cumplir el instructivo
EA4 se hicieron estas adaptaciones:

- **Registro de cuentas (RF01):** lo hace el **Encargado**, porque el EA4 exige que todos los
  endpoints sean privados menos el login y que solo el administrador gestione usuarios.
- **Inicio de sesión (RF02):** con **correo y contraseña**. El rol se detecta con la cuenta y se
  devuelve en la respuesta, para que el frontend abra el panel correcto (RF03, RF06).
- **Validar el rol en el servidor (RF07):** el rol sale del token JWT y de la base de datos,
  nunca de encabezados enviados por el cliente.
- **Cerrar sesión (RF05):** con JWT, el cliente borra sus tokens. Las cuentas desactivadas
  pierden el acceso de inmediato.
- **Reglas marcadas como "propuesta" en el documento:** se implementaron con valores
  configurables en el `.env`: horario, días de alerta de vencimiento, porcentaje de stock crítico
  y plazo de pago. Faltan dos decisiones por validar con el Encargado: que el instructor pague
  el precio de aprendiz y que una deuda se venza 5 días después del corte mensual.
- **Fuera del alcance de la API:** la información institucional de Yamboró (RF50), el límite de
  registros por IP (RT12) y el despliegue en Render (RT17).

## Cumplimiento del instructivo EA4

- [x] Esquema propio `gastrosena`; DDL con PK, FK, NOT NULL, UNIQUE, CHECK, DEFAULT e índices.
- [x] DML con 10 o más registros por tabla principal; DCL con rol `api_gastrosena` de privilegios mínimos.
- [x] CRUD de las entidades principales, 12 procesos de negocio, paginación y filtros.
- [x] Reglas de negocio en servicios, borrado lógico y auditoría (quién y cuándo creó o modificó).
- [x] Login con correo y contraseña, JWT de acceso con expiración y token de actualización.
- [x] bcrypt, política de contraseñas, bloqueo tras 5 intentos y cambio de la propia contraseña.
- [x] Variables de entorno (`.env` fuera de Git), CORS por lista y errores 500 sin detalles técnicos.
- [x] 4 roles verificados en cada endpoint (401/403); nadie cambia su propio rol ni se desactiva.
- [x] Validación con esquemas (correo, documento, teléfono, fechas, valores monetarios); 409 y 404 en servicios.
- [x] Salida separada de la entrada y errores uniformes en español.
- [x] Swagger con descripción, parámetros, respuestas, códigos y rol de cada endpoint.
- [x] Pruebas con pytest y colección de Postman en `docs/`.

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

## Documentación relacionada

- Especificación de requisitos: [`docs/Especificacion_Requisitos_GastroSENA.docx`](docs/Especificacion_Requisitos_GastroSENA.docx)
- Colección de Postman: [`docs/GastroSENA_API.postman_collection.json`](docs/GastroSENA_API.postman_collection.json)
- Repositorio del proyecto principal: https://github.com/burbano52100/Poryecto-Fromativo-
#   B A C K E N D _ P R O Y E C T O _ F O R M A T I V O _ R A M A _ B U R B A N O  
 