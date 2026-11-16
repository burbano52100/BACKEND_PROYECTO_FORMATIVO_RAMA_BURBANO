# Guía del proyecto GastroSENA API

Esta guía explica **qué hace cada carpeta, cada archivo y cada tabla** del proyecto, y **qué datos de prueba** trae la base de datos. Está pensada para estudiar antes de la sustentación: cada módulo está separado y sigue el mismo orden (qué hace → tablas → datos → archivos → endpoints → reglas → pruebas).

> Las fechas de los datos de prueba son **relativas al día en que se ejecuta `02_dml.sql`**. Los ejemplos de esta guía suponen que se ejecutó el **16/11/2026**.

---

## Índice

- [Parte 1 — Mapa general de carpetas](#parte-1--mapa-general-de-carpetas)
- [Parte 2 — Cómo viaja una petición por las capas](#parte-2--cómo-viaja-una-petición-por-las-capas)
- [Parte 3 — Archivos de la raíz](#parte-3--archivos-de-la-raíz)
- [Parte 4 — Archivos compartidos por todos los módulos](#parte-4--archivos-compartidos-por-todos-los-módulos)
- [Parte 5 — La base de datos](#parte-5--la-base-de-datos)
- [Parte 6 — Los módulos](#parte-6--los-módulos)
  - [Módulo 1. Autenticación](#módulo-1-autenticación)
  - [Módulo 2. Usuarios, roles y beneficiarios](#módulo-2-usuarios-roles-y-beneficiarios)
  - [Módulo 3. Fichas y grupos](#módulo-3-fichas-y-grupos)
  - [Módulo 4. Menú del Día](#módulo-4-menú-del-día)
  - [Módulo 5. Reservas y consumos](#módulo-5-reservas-y-consumos)
  - [Módulo 6. Cartera de deudas](#módulo-6-cartera-de-deudas)
  - [Módulo 7. Inventario y kardex](#módulo-7-inventario-y-kardex)
  - [Módulo 8. Recetas](#módulo-8-recetas)
  - [Módulo 9. Sugerencias](#módulo-9-sugerencias)
  - [Módulo 10. Reportes e indicadores](#módulo-10-reportes-e-indicadores)
- [Parte 7 — Pruebas y documentación](#parte-7--pruebas-y-documentación)
- [Parte 8 — Glosario para la sustentación](#parte-8--glosario-para-la-sustentación)

---

## Parte 1 — Mapa general de carpetas

```
api_proyecto_formativo/
│
├── app/                    ← TODO el código de la API
│   ├── main.py             ← Punto de entrada: crea la app y conecta las rutas
│   ├── core/               ← Configuración, seguridad, permisos y errores (lo transversal)
│   ├── database/           ← Conexión a PostgreSQL
│   ├── models/             ← Clases que representan las TABLAS (SQLAlchemy)
│   ├── schemas/            ← Clases que VALIDAN los datos que entran y salen (Pydantic)
│   ├── repositories/       ← Consultas a la base de datos (única capa que usa SQL)
│   ├── services/           ← Reglas de negocio (la "lógica" del sistema)
│   └── routers/            ← Endpoints HTTP (las URL de la API)
│
├── database/               ← Scripts SQL: 01_ddl (estructura), 02_dml (datos), 03_dcl (permisos)
├── docs/                   ← Especificación de requisitos, colección de Postman y esta guía
├── tests/                  ← Pruebas automáticas con pytest
│
├── requirements.txt        ← Librerías de Python que hay que instalar
├── .env.example            ← Plantilla de variables de entorno (sin claves reales)
├── .gitignore              ← Archivos que Git no debe subir (.env, venv, cachés)
└── README.md               ← Descripción del proyecto e instrucciones de ejecución
```

### Qué hace cada carpeta de `app/`

| Carpeta | Responsabilidad | Ejemplo | Nunca hace |
|---|---|---|---|
| `routers/` | Recibe la petición HTTP, exige el rol y devuelve la respuesta con su código | `POST /api/v1/reservas` → 201 | Reglas de negocio ni SQL |
| `schemas/` | Define qué campos llegan y salen, con tipos, longitudes y formatos | El correo debe ser válido; la contraseña, segura | Consultar la base de datos |
| `services/` | Aplica las reglas del negocio y decide qué error lanzar | "Un menú agotado no recibe reservas" | Conocer HTTP (no sabe qué es un 404) |
| `repositories/` | Hace las consultas (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) | Buscar un usuario por correo | Reglas de negocio |
| `models/` | Representa cada tabla de PostgreSQL como una clase de Python | `Usuario` ↔ tabla `usuarios` | Validar datos del cliente |
| `database/` | Abre y cierra la conexión con PostgreSQL | Una sesión por petición | — |
| `core/` | Lo que usan todas las capas: configuración, JWT, bcrypt, roles, errores | Verificar el token | — |

> **Regla de oro de la arquitectura:** cada capa solo habla con la capa de abajo.
> `routers → services → repositories → models → PostgreSQL`

### Los archivos `__init__.py`

Todas las carpetas de `app/` y `tests/` tienen un `__init__.py`. Le indican a Python que la carpeta es un **paquete**, para poder escribir `from app.models import Usuario`. Están vacíos, excepto `app/models/__init__.py`, que importa todos los modelos en un solo lugar.

---

## Parte 2 — Cómo viaja una petición por las capas

Ejemplo: un aprendiz reserva el almuerzo de hoy con `POST /api/v1/reservas` y el cuerpo `{"menu_id": 11}`.

```
 Cliente (Swagger, Postman o frontend)
   │  POST /api/v1/reservas
   │  Authorization: Bearer eyJhbGci...
   │  {"menu_id": 11}
   ▼
 app/main.py ............................ CORS y búsqueda de la ruta /api/v1/reservas
   ▼
 app/routers/reservas.py ................ función reservar()
   │
   ├─► app/schemas/reserva.py ........... ReservaCrear valida el cuerpo:
   │                                      menu_id entero > 0 y ningún campo extra
   │                                      (si envía "valor" → 422)
   │
   ├─► app/core/permisos.py ............. dependencia "Comensal":
   │     ├─► app/core/seguridad.py ...... decodifica el JWT (firma, vencimiento y tipo)
   │     ├─► app/services/auth_service.py  busca al usuario y verifica que esté activo
   │     └─► ¿rol aprendiz, instructor o invitado?  si no → 403
   │
   ├─► app/database/conexion.py ......... abre una sesión de base de datos
   ▼
 app/services/reserva_service.py ........ ReservaService.reservar():
   │   ✔ horario 7:00 a 21:00            ✔ el menú existe (404)
   │   ✔ el menú está activo (400)        ✔ no es de una fecha pasada (400)
   │   ✔ hay cupo (400)                   ✔ no tiene otra reserva vigente (409)
   │   → calcula el precio según el rol y descuenta 1 del cupo
   ▼
 app/repositories/reserva_repository.py . registrar(): INSERT + COMMIT (una sola transacción)
   ▼
 app/models/reserva.py ↔ tabla gastrosena.reservas en PostgreSQL
   ▼
 Respuesta 201 con la forma de ReservaSalida (app/schemas/reserva.py)
```

**Si algo falla**, el servicio lanza una excepción de `app/core/excepciones.py` (por ejemplo `ReglaNegocioError("El menú está agotado.")`) y `app/core/errores.py` la convierte en esta respuesta:

```json
{ "estado": 400, "mensaje": "El menú está agotado.", "detalles": null }
```

---

## Parte 3 — Archivos de la raíz

| Archivo | Qué hace |
|---|---|
| `requirements.txt` | Lista de librerías: `fastapi` (framework), `uvicorn` (servidor), `sqlalchemy` (ORM), `psycopg[binary]` (driver de PostgreSQL), `pydantic[email]` (validación y correos), `pydantic-settings` (lee el `.env`), `PyJWT` (tokens), `bcrypt` (cifrado de contraseñas), `pytest` y `httpx` (pruebas). Se instala con `pip install -r requirements.txt`. |
| `.env.example` | Plantilla con todas las variables de entorno y valores de ejemplo. Se copia como `.env`. |
| `.env` | **No existe hasta que usted lo crea.** Tiene las claves reales y **no se sube a GitHub**. |
| `.gitignore` | Le dice a Git que ignore `.env`, `venv/`, `__pycache__/`, `.pytest_cache/`, `.vscode/` y `.idea/`. |
| `README.md` | Presentación del proyecto: qué es, módulos, roles, reglas, endpoints, instalación, usuarios de prueba e integrantes. |

### Variables del `.env`

| Variable | Valor de ejemplo | Para qué sirve |
|---|---|---|
| `DB_HOST` / `DB_PORT` | `localhost` / `5432` | Dónde está PostgreSQL |
| `DB_NAME` | `gastrosena_db` | Nombre de la base de datos |
| `DB_SCHEMA` | `gastrosena` | Esquema propio del proyecto (no `public`) |
| `DB_USER` / `DB_PASSWORD` | `api_gastrosena` / `CambieEstaClave2026` | Usuario con privilegios mínimos creado en `03_dcl.sql` |
| `JWT_SECRET_KEY` | (64 caracteres aleatorios) | Firma los tokens. **Mínimo 32 caracteres**, o la API no arranca |
| `JWT_ALGORITHM` | `HS256` | Algoritmo de firma del JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Duración del token de acceso |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Duración del token de actualización |
| `MAX_LOGIN_ATTEMPTS` / `LOCKOUT_MINUTES` | `5` / `15` | Bloqueo tras intentos fallidos |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Páginas web autorizadas para llamar la API |
| `HORA_INICIO_RESERVAS` / `HORA_FIN_RESERVAS` | `07:00` / `21:00` | Horario para reservar y cancelar |
| `DIAS_ALERTA_VENCIMIENTO` | `7` | Un material está "VENCIENDO" si vence en 7 días o menos |
| `PORCENTAJE_STOCK_CRITICO` | `50` | Stock "CRÍTICO" si es ≤ 50 % del mínimo |
| `DIAS_PLAZO_PAGO` | `5` | Días después del corte mensual para pagar antes de quedar en mora |

---

## Parte 4 — Archivos compartidos por todos los módulos

Estos archivos no pertenecen a un módulo: los usan todos.

### `app/main.py` — punto de entrada

1. Configura el log (mensajes con fecha y nivel en la consola).
2. Crea la aplicación `FastAPI` con su título, descripción y versión, que aparecen en Swagger.
3. Agrega el **CORS**: solo los orígenes del `.env` pueden llamar la API desde un navegador.
4. Registra los manejadores de errores (`registrar_manejadores`).
5. Conecta los 10 routers con el prefijo `/api/v1`.

### Carpeta `app/core/`

| Archivo | Qué hace |
|---|---|
| `config.py` | Clase `Settings` que lee el `.env` con *pydantic-settings*. Si falta una variable obligatoria o la clave JWT es corta, la API no arranca y dice qué falta. También convierte `CORS_ORIGINS` en una lista. |
| `seguridad.py` | **bcrypt:** `cifrar_password` (10 rondas, con sal aleatoria) y `verificar_password`. **JWT:** `crear_access_token`, `crear_refresh_token` y `decodificar_token`, que valida la firma, el vencimiento y el **tipo** (`access` o `refresh`), para que un refresh no sirva como access. |
| `permisos.py` | `obtener_usuario_actual` lee el encabezado `Authorization: Bearer ...` (401 si falta). `requiere_roles(...)` deja pasar solo ciertos roles (403). Define los atajos `Encargado`, `Instructor`, `Comensal` (aprendiz, instructor o invitado) y `CualquierRol`. Agrega el botón **Authorize** de Swagger. |
| `roles.py` | Enum `Roles` con los 4 nombres: `encargado`, `instructor`, `aprendiz` e `invitado`. |
| `excepciones.py` | Errores propios de la aplicación: `ReglaNegocioError` (400), `NoAutenticadoError` (401), `PermisoDenegadoError` (403), `NoEncontradoError` (404) y `ConflictoError` (409). Los servicios los lanzan **sin saber nada de HTTP**. |
| `errores.py` | Convierte **cualquier** error en el JSON uniforme `{estado, mensaje, detalles}`. Traduce al español los errores de validación de Pydantic (422), convierte el `IntegrityError` de la base de datos en 409 y responde los errores inesperados con un 500 genérico, **sin detalles técnicos** (el detalle queda en el log). Además, `respuestas_error()` documenta en Swagger los códigos de error de cada endpoint. |
| `tiempo.py` | Hora oficial de Colombia (UTC-5): `ahora()`, `hoy()`, `en_horario()` y `ultimo_dia_del_mes()`. |

### `app/database/conexion.py`

- Construye la URL de conexión con `URL.create`, que escapa caracteres especiales de la contraseña.
- `engine`: el motor de SQLAlchemy con `pool_pre_ping` (verifica que la conexión siga viva antes de usarla).
- `SessionLocal`: fábrica de sesiones.
- `get_db()`: abre **una sesión por petición** y la cierra al final. Si no se hizo `commit`, los cambios se deshacen.
- `SesionDB`: atajo para recibir la sesión en los routers.

### `app/models/base.py` y `app/models/__init__.py`

- `Base`: clase padre de todos los modelos. Fija el esquema `gastrosena` para que no se use `public`.
- `Auditoria`: agrega las columnas `creado_por`, `creado_en`, `actualizado_por` y `actualizado_en` a las tablas que la heredan. **Así se cumple la auditoría que pide el EA4.**
- `__init__.py`: reúne todos los modelos para importarlos desde un solo lugar.

### `app/schemas/comunes.py`

| Elemento | Qué valida o hace |
|---|---|
| `Password` | 8 a 64 caracteres, con al menos una mayúscula, una minúscula y un número, y máximo 72 bytes (límite de bcrypt) |
| `Documento` | 6 a 10 dígitos, sin puntos ni espacios |
| `Telefono` | 10 dígitos: celular (`3XXXXXXXXX`) o fijo (`60XXXXXXXX`) |
| `Correo` | Correo válido, que se guarda en minúsculas |
| `FechaNoPasada` | No puede ser anterior a hoy |
| `Valor`, `PrecioMenu`, `Cantidad` | Valores con `Decimal` (sin errores de redondeo) y con sus rangos |
| `Dinero`, `Medida` | Hacen que los `Decimal` salgan como número en el JSON |
| `EsquemaEntrada` | Base de toda entrada: quita espacios sobrantes y **rechaza campos que no existen** (`extra="forbid"`) |
| `PaginacionBase` | Parámetros `pagina` (desde 1) y `tamano` (1 a 100, 10 por defecto) |
| `Pagina[T]` y `armar_pagina()` | Respuesta paginada: `items`, `total`, `pagina`, `tamano` y `paginas` |
| `Mensaje`, `ErrorRespuesta` | Respuesta simple con un mensaje y estructura única de los errores |

### `app/repositories/paginacion.py`

- `contar()`: cuántos registros devuelve una consulta en total.
- `paginar()`: aplica `OFFSET` y `LIMIT` y devuelve la página pedida junto con el total.

---

## Parte 5 — La base de datos

### Los tres scripts (carpeta `database/`), en orden

| Script | Tipo | Qué hace |
|---|---|---|
| `01_ddl.sql` | **DDL** (definición) | **Borra** el esquema si existe (`DROP SCHEMA ... CASCADE`) y crea el esquema `gastrosena` con 11 tablas, llaves primarias y foráneas, `NOT NULL`, `UNIQUE`, `CHECK`, `DEFAULT`, índices y comentarios (diccionario de datos). |
| `02_dml.sql` | **DML** (datos) | Inserta los datos de prueba. Las llaves foráneas se buscan con subconsultas y las fechas son relativas a `CURRENT_DATE`. Al final recalcula el cupo de los menús y el stock de los materiales para que siempre cuadren. |
| `03_dcl.sql` | **DCL** (permisos) | Crea el rol `api_gastrosena` (no es superusuario) y le da **solo** los permisos que la API necesita en cada tabla. |

> Ejecutar `01_ddl.sql` otra vez **borra todos los datos**. Sirve para dejar la base limpia después de las pruebas.

### Las 11 tablas y cómo se relacionan

```
                         ┌─────────┐
                         │  roles  │
                         └────┬────┘
                              │ 1..N
 ┌─────────┐  1..N   ┌────────▼────────┐   1..N   ┌──────────────────┐
 │ fichas  ├────────►│    usuarios     ├─────────►│ pagos_instructor │
 └─────────┘         └──┬───────────┬──┘          └──────────────────┘
                        │ 1..N      │ 1..N
               ┌────────▼───┐   ┌───▼─────────┐
               │  reservas  │   │ sugerencias │
               └────────▲───┘   └─────────────┘
                        │ N..1
                   ┌────┴───┐
                   │ menus  │
                   └────────┘

 ┌────────────┐ 1..N ┌────────────────────────┐
 │ materiales ├─────►│ movimientos_inventario │   (kardex)
 └─────┬──────┘      └────────────────────────┘
       │ 1..N
 ┌─────▼───────────────┐ N..1 ┌─────────┐
 │ receta_ingredientes ├─────►│ recetas │
 └─────────────────────┘      └─────────┘

 Además, casi todas las tablas tienen creado_por / actualizado_por → usuarios (auditoría).
```

### Cantidad de datos de prueba

| Tabla | Registros | Módulo donde se explica |
|---|---:|---|
| `roles` | 4 | [Usuarios](#módulo-2-usuarios-roles-y-beneficiarios) |
| `usuarios` | 12 | [Usuarios](#módulo-2-usuarios-roles-y-beneficiarios) |
| `fichas` | 10 | [Fichas](#módulo-3-fichas-y-grupos) |
| `menus` | 12 | [Menú del Día](#módulo-4-menú-del-día) |
| `reservas` | 19 | [Reservas](#módulo-5-reservas-y-consumos) |
| `pagos_instructor` | 3 | [Cartera](#módulo-6-cartera-de-deudas) |
| `materiales` | 14 | [Inventario](#módulo-7-inventario-y-kardex) |
| `movimientos_inventario` | 22 | [Inventario](#módulo-7-inventario-y-kardex) |
| `recetas` | 10 | [Recetas](#módulo-8-recetas) |
| `receta_ingredientes` | 48 | [Recetas](#módulo-8-recetas) |
| `sugerencias` | 10 | [Sugerencias](#módulo-9-sugerencias) |

### Permisos del rol `api_gastrosena` (`03_dcl.sql`)

| Tabla | SELECT | INSERT | UPDATE | DELETE | Por qué |
|---|:-:|:-:|:-:|:-:|---|
| `roles` | ✔ | | | | Los roles son fijos |
| `usuarios` | ✔ | ✔ | ✔ | | Se desactivan, no se borran |
| `fichas` | ✔ | ✔ | ✔ | ✔ | Se borran si no tienen aprendices |
| `menus` | ✔ | ✔ | ✔ | ✔ | Se borran si no tienen reservas |
| `reservas` | ✔ | ✔ | ✔ | | Se cancelan, no se borran |
| `pagos_instructor` | ✔ | ✔ | | | Un pago es inmutable |
| `materiales` | ✔ | ✔ | ✔ | ✔ | Se borran si no tienen historial |
| `movimientos_inventario` | ✔ | ✔ | | | El kardex es inmutable |
| `recetas` | ✔ | ✔ | ✔ | ✔ | — |
| `receta_ingredientes` | ✔ | ✔ | ✔ | ✔ | — |
| `sugerencias` | ✔ | ✔ | ✔ | | — |

El rol tampoco puede crear tablas (`GRANT USAGE` sin `CREATE`). Además, su `search_path` apunta a `gastrosena`.

---

## Parte 6 — Los módulos

Cada módulo sigue la misma estructura: **qué hace → tablas → datos de prueba → archivos → endpoints → reglas → pruebas.**

---

## Módulo 1. Autenticación

### Qué hace
Permite iniciar sesión con correo y contraseña, renovar el token, ver el propio perfil y cambiar la propia contraseña. Bloquea la cuenta después de 5 intentos fallidos.

### Tablas
No tiene tabla propia: usa `usuarios`, en especial estas columnas:

| Columna | Tipo | Para qué |
|---|---|---|
| `correo` | `VARCHAR(120) UNIQUE` | Usuario del login |
| `password_hash` | `VARCHAR(60)` | Contraseña cifrada con bcrypt (nunca la contraseña real) |
| `activo` | `BOOLEAN` | Una cuenta inactiva no puede ingresar |
| `intentos_fallidos` | `SMALLINT ≥ 0` | Cuenta los intentos fallidos seguidos |
| `bloqueado_hasta` | `TIMESTAMPTZ` | Hasta cuándo está bloqueada la cuenta |

### Datos de prueba (usuarios para iniciar sesión)

| Rol | Correo | Contraseña | Particularidad |
|---|---|---|---|
| Encargado | `encargado@gastrosena.com` | `Encargado123` | Administrador |
| Instructor | `instructor@gastrosena.com` | `Instructor123` | Tiene deuda **vencida** |
| Aprendiz | `aprendiz@gastrosena.com` | `Aprendiz123` | Ficha 2847251 (ADSO) |
| Beneficiario | `beneficiario@gastrosena.com` | `Aprendiz123` | Almuerzo a $0 |
| Invitado | `invitado@gastrosena.com` | `Invitado123` | Paga $8.000 |
| Inactivo | `inactivo@gastrosena.com` | `Aprendiz123` | **No puede ingresar** (403) |

Los demás instructores, aprendices e invitados usan las mismas contraseñas de su rol.

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Router | `app/routers/auth.py` | Los 4 endpoints del módulo |
| Schemas | `app/schemas/auth.py` | `LoginEntrada`, `RefreshEntrada`, `CambioPasswordEntrada` y `TokenRespuesta` |
| Service | `app/services/auth_service.py` | Login, bloqueo, emisión de tokens y cambio de contraseña |
| Repository | `app/repositories/usuario_repository.py` | `obtener_por_correo`, `obtener_por_id` y `guardar` |
| Core | `app/core/seguridad.py` y `app/core/permisos.py` | bcrypt, JWT y verificación de roles |

### Endpoints

| Método | Ruta | Rol | Respuesta |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Público | 200 con `access_token`, `refresh_token`, `expira_en` y `rol` |
| POST | `/api/v1/auth/refresh` | Refresh token | 200 con tokens nuevos |
| GET | `/api/v1/auth/perfil` | Cualquiera | 200 con los datos del usuario (sin contraseña) |
| PUT | `/api/v1/auth/password` | Cualquiera | 200 `{"mensaje": "La contraseña se cambió correctamente."}` |

### Reglas de negocio
1. **Mismo mensaje** si el correo no existe o si la contraseña está mal ("Correo o contraseña incorrectos."), para no revelar qué correos están registrados.
2. Cada contraseña incorrecta suma un intento. **Al quinto**, la cuenta se bloquea 15 minutos y responde 403 con los minutos que faltan.
3. Un login correcto reinicia el contador de intentos.
4. Una cuenta inactiva responde 403: "La cuenta está inactiva".
5. El access token dura 30 minutos y el refresh token, 7 días. Cada token lleva su `tipo`, así que un refresh **no sirve** como access.
6. Si la cuenta se desactiva, sus tokens dejan de servir de inmediato, porque cada petición verifica que siga activa.
7. Para cambiar la contraseña hay que enviar la actual. La nueva debe ser distinta y cumplir la política.

### Pruebas (`tests/test_auth.py`, 12 pruebas)
Login exitoso, credenciales incorrectas (401), cuenta inactiva (403), petición sin token (401), token inválido (401), token vencido (401), el refresh no sirve como access, el perfil no expone la contraseña, bloqueo tras 5 intentos, cambio de contraseña, roles sin permiso (403) y ruta inexistente con el formato de error.

---

## Módulo 2. Usuarios, roles y beneficiarios

### Qué hace
El **Encargado** registra las cuentas, asigna el rol, asigna la ficha a los aprendices, desactiva usuarios y marca a los aprendices **beneficiarios** (almuerzo gratis).

### Tablas

**`roles`**

| Columna | Tipo y restricciones |
|---|---|
| `id` | `INTEGER` identidad, PK |
| `nombre` | `VARCHAR(20) UNIQUE`, `CHECK` en (encargado, instructor, aprendiz, invitado) |
| `descripcion` | `VARCHAR(150)` |

**`usuarios`**

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `documento` | `VARCHAR(10) UNIQUE`, `CHECK` 6 a 10 dígitos |
| `nombre` | `VARCHAR(100) NOT NULL` |
| `correo` | `VARCHAR(120) UNIQUE`, `CHECK` formato de correo |
| `telefono` | `VARCHAR(10)`, `CHECK` 10 dígitos |
| `password_hash` | `VARCHAR(60) NOT NULL` (bcrypt) |
| `rol_id` | FK → `roles` |
| `ficha_id` | FK → `fichas` (solo aprendices) |
| `es_beneficiario` | `BOOLEAN DEFAULT FALSE` |
| `activo` | `BOOLEAN DEFAULT TRUE` (borrado lógico) |
| `intentos_fallidos`, `bloqueado_hasta` | Bloqueo de la cuenta |
| `creado_por`, `creado_en`, `actualizado_por`, `actualizado_en` | Auditoría |

Índices: `idx_usuarios_rol` e `idx_usuarios_ficha`.

### Datos de prueba

**Roles** (sus id en una base nueva)

| id | Nombre | Descripción |
|---:|---|---|
| 1 | encargado | Administra el servicio: usuarios, menú, ventas, cartera, inventario, grupos y sugerencias |
| 2 | instructor | Consume almuerzos y los paga con una cuenta mensual |
| 3 | aprendiz | Reserva su almuerzo y consulta sus consumos |
| 4 | invitado | Visitante que compra el almuerzo a precio de invitado |

**Usuarios (12)**

| id | Documento | Nombre | Correo | Rol | Ficha | Beneficiario | Activo |
|---:|---|---|---|---|---|:-:|:-:|
| 1 | 1083000001 | Marta Lucía Rojas | encargado@gastrosena.com | encargado | — | | ✔ |
| 2 | 1083000002 | Carlos Andrés Muñoz | instructor@gastrosena.com | instructor | — | | ✔ |
| 3 | 1083000003 | Diana Patricia Cerón | diana.ceron@gastrosena.com | instructor | — | | ✔ |
| 4 | 1083000004 | Jorge Iván Salazar | jorge.salazar@gastrosena.com | instructor | — | | ✔ |
| 5 | 1083000005 | Laura Méndez Vargas | aprendiz@gastrosena.com | aprendiz | 2847251 | | ✔ |
| 6 | 1083000006 | Sebastián Calle Ortiz | sebastian.calle@gastrosena.com | aprendiz | 2847251 | | ✔ |
| 7 | 1083000007 | Camilo Rojas Peña | beneficiario@gastrosena.com | aprendiz | 2847252 | ✔ | ✔ |
| 8 | 1083000008 | Valentina Ortiz Gil | valentina.ortiz@gastrosena.com | aprendiz | 2847253 | | ✔ |
| 9 | 1083000009 | Andrés Muñoz Cruz | andres.munoz@gastrosena.com | aprendiz | 2847254 | ✔ | ✔ |
| 10 | 1083000010 | Daniela Pérez Ríos | inactivo@gastrosena.com | aprendiz | 2847255 | | ✘ |
| 11 | 1083000011 | Pedro Ruiz Gómez | invitado@gastrosena.com | invitado | — | | ✔ |
| 12 | 1083000012 | Ana León Cárdenas | ana.leon@correo.com | invitado | — | | ✔ |

Las contraseñas ya están guardadas como hash bcrypt (`$2b$10$...`). El encargado se inserta primero porque él "crea" a todos los demás (`creado_por`).

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Model | `app/models/usuario.py` | Clases `Rol` y `Usuario`. El usuario carga su rol y su ficha en la misma consulta (`lazy="joined"`) |
| Schemas | `app/schemas/usuario.py` | `UsuarioCrear`, `UsuarioActualizar`, `BeneficiarioEntrada`, `UsuarioSalida` (**sin contraseña**), `UsuarioResumen`, `RolSalida` y `FiltrosUsuario` |
| Repository | `app/repositories/usuario_repository.py` | Buscar por id o correo, saber si existe un correo o documento, listar con filtros, contar aprendices activos, bloquear la fila y listar roles |
| Service | `app/services/usuario_service.py` | Crear, actualizar, desactivar, cambiar beneficiario y validar ficha según el rol |
| Router | `app/routers/usuarios.py` | Los 7 endpoints del módulo |

### Endpoints (todos solo para el encargado)

| Método | Ruta | Qué hace | Código |
|---|---|---|---|
| GET | `/api/v1/usuarios` | Lista con filtros (`buscar`, `rol_id`, `ficha_id`, `activo`, `es_beneficiario`) y paginación | 200 |
| GET | `/api/v1/usuarios/{id}` | Consulta un usuario | 200 / 404 |
| POST | `/api/v1/usuarios` | Registra una cuenta | 201 |
| PATCH | `/api/v1/usuarios/{id}` | Actualiza nombre, teléfono, rol, ficha o estado | 200 |
| DELETE | `/api/v1/usuarios/{id}` | Desactiva (borrado lógico) | 200 |
| PATCH | `/api/v1/usuarios/{id}/beneficiario` | Agrega o quita la condición de beneficiario | 200 |
| GET | `/api/v1/roles` | Lista los 4 roles | 200 |

### Reglas de negocio
1. Correo y documento son **únicos** (409).
2. El `rol_id` debe existir (404).
3. **Un aprendiz debe tener una ficha activa.** Los demás roles no pueden tener ficha ni ser beneficiarios (400).
4. **Nadie puede cambiar su propio rol ni desactivar su propia cuenta** (403).
5. `DELETE` no borra el registro: pone `activo = false`, porque el usuario aparece en la auditoría de otras tablas.
6. Reactivar una cuenta (`activo: true`) también la desbloquea.
7. Solo un **aprendiz activo** puede ser beneficiario. Si ya lo es, responde 409.
8. La contraseña se guarda cifrada con bcrypt y **nunca** se devuelve.

### Pruebas (`tests/test_usuarios.py`, primeras 9 de 12)
Crear un aprendiz con ficha, reglas de ficha según el rol, correo o documento duplicado (409), datos inválidos (422 en español), el encargado no cambia su rol ni se desactiva, un usuario desactivado no inicia sesión, el beneficiario reserva a $0, solo los aprendices son beneficiarios y listar con filtros.

---

## Módulo 3. Fichas y grupos

### Qué hace
Administra las **fichas** (grupos de formación del SENA). Muestra estadísticas del día y la lista de aprendices de cada ficha que reservaron, con su estado de pago.

### Tabla `fichas`

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `codigo` | `VARCHAR(10) UNIQUE`, `CHECK` 6 a 10 dígitos |
| `programa` | `VARCHAR(120) NOT NULL` |
| `jornada` | `CHECK` en (DIURNA, NOCTURNA, MIXTA, FIN_DE_SEMANA) |
| `vocero` | `VARCHAR(100)`, dato informativo |
| `cantidad_estudiantes` | `INTEGER DEFAULT 0`, `CHECK` entre 0 y 60 |
| `activo` | `BOOLEAN DEFAULT TRUE` |
| Auditoría | `creado_por`, `creado_en`, `actualizado_por`, `actualizado_en` |

### Datos de prueba (10 fichas)

| id | Código | Programa | Jornada | Vocero | Estudiantes |
|---:|---|---|---|---|---:|
| 1 | 2847251 | Análisis y Desarrollo de Software | DIURNA | Laura Méndez | 28 |
| 2 | 2847252 | Gastronomía | DIURNA | Camilo Rojas | 25 |
| 3 | 2847253 | Cocina | MIXTA | Valentina Ortiz | 22 |
| 4 | 2847254 | Producción Agropecuaria Ecológica | DIURNA | Andrés Muñoz | 30 |
| 5 | 2847255 | Control de Calidad del Café | DIURNA | Daniela Pérez | 20 |
| 6 | 2847256 | Panadería | NOCTURNA | Julián Castro | 18 |
| 7 | 2847257 | Gestión Empresarial | MIXTA | Sara López | 26 |
| 8 | 2847258 | Producción de Especies Menores | DIURNA | Mateo Gómez | 24 |
| 9 | 2847259 | Mesa y Bar | NOCTURNA | Isabella Díaz | 19 |
| 10 | 2847260 | Agroindustria Alimentaria | FIN_DE_SEMANA | Tomás Ruiz | 21 |

**Estadísticas de hoy** con estos datos (`GET /fichas/estadisticas`): 10 grupos, 233 estudiantes, 5 aprendices activos con cuenta, 4 almuerzos de aprendices reservados hoy y un promedio de 0,4 por grupo.

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Model | `app/models/ficha.py` | Clase `Ficha` (hereda `Auditoria`) |
| Schemas | `app/schemas/ficha.py` | `Jornada`, `FichaCrear`, `FichaActualizar` (el código no se cambia), `FichaSalida`, `FichaResumen`, `FiltrosFicha`, `EstadisticasGrupos` y `ReservaDeFicha` |
| Repository | `app/repositories/ficha_repository.py` | Buscar, saber si existe un código, listar, saber si tiene usuarios, totales de fichas activas, guardar y eliminar |
| Service | `app/services/ficha_service.py` | CRUD, estadísticas y reservas del día. También usa los repositorios de reservas y usuarios |
| Router | `app/routers/fichas.py` | Los 7 endpoints del módulo |

### Endpoints (todos solo para el encargado)

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/v1/fichas` | Lista con filtros (`buscar`, `jornada`, `activo`) |
| GET | `/api/v1/fichas/estadisticas?fecha=` | Totales y promedio de almuerzos por grupo |
| GET | `/api/v1/fichas/{id}` | Consulta una ficha |
| GET | `/api/v1/fichas/{id}/reservas?fecha=` | Aprendices de la ficha que reservaron ese día y su estado de pago |
| POST | `/api/v1/fichas` | Crea una ficha (201) |
| PATCH | `/api/v1/fichas/{id}` | Actualiza programa, jornada, vocero o cantidad |
| DELETE | `/api/v1/fichas/{id}` | Elimina la ficha (lógico o físico) |

### Reglas de negocio
1. El código de ficha es único (409) y no se puede cambiar.
2. **Eliminar:** si la ficha tiene aprendices, se desactiva (borrado lógico). Si no tiene, se borra definitivamente.
3. No se puede asignar una ficha inactiva a un aprendiz.

### Pruebas (`tests/test_usuarios.py`, últimas 3 de 12)
CRUD de fichas, una ficha con aprendices se desactiva, y las estadísticas y reservas de la ficha.

---

## Módulo 4. Menú del Día

### Qué hace
El Encargado publica **un menú por fecha**, con precio de aprendiz, precio de invitado y cupo. Cualquier persona puede ver el menú de hoy y los próximos, **con el precio que le corresponde** según su rol.

### Tabla `menus`

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `fecha` | `DATE UNIQUE` (un menú por día) |
| `nombre`, `descripcion` | `VARCHAR(100)` y `VARCHAR(500)` |
| `precio_aprendiz`, `precio_invitado` | `NUMERIC(10,2) ≥ 0` |
| `cantidad_total` | `INTEGER > 0` (cupo) |
| `cantidad_disponible` | `INTEGER ≥ 0`, con `CHECK` disponible ≤ total |
| `activo` | `BOOLEAN DEFAULT TRUE` |
| Auditoría | sí |

### Datos de prueba (12 menús)

Todos cuestan **$5.000** para aprendices e instructores y **$8.000** para invitados, con un cupo de **80**.

| Fecha (ej. 16/11/2026) | Nombre | Reservas vigentes | Cupo disponible |
|---|---|---:|---:|
| Día 15 antes del inicio del mes (17/10) | Cerdo en salsa | 1 | 79 |
| Hoy − 9 (07/11) | Arroz con pollo | 0 | 80 |
| Hoy − 8 (08/11) | Frijolada | 0 | 80 |
| Hoy − 7 (09/11) | Carne guisada con papa | 0 | 80 |
| Hoy − 6 (10/11) | Sudado de pollo | 0 | 80 |
| Hoy − 5 (11/11) | Lentejas con arroz | 2 | 78 |
| Hoy − 4 (12/11) | Pollo asado con ensalada | 0 | 80 |
| Hoy − 3 (13/11) | Sopa de verduras y seco | 2 (+1 cancelada) | 78 |
| Hoy − 2 (14/11) | Pescado frito | 3 | 77 |
| Ayer (15/11) | Ajiaco | 4 | 76 |
| **Hoy (16/11)** | **Bandeja campesina** | **6** | **74** |
| Mañana (17/11) | Arroz chino | 0 | 80 |

Gracias a las fechas relativas, **siempre hay menú de hoy y de mañana** sin importar cuándo se ejecute el script.

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Model | `app/models/menu.py` | Clase `Menu`. Usa `Numeric` (`Decimal`) para el dinero, no `float` |
| Schemas | `app/schemas/menu.py` | `MenuCrear`, `MenuActualizar` (la fecha no cambia), `MenuSalida` (calcula `vendidos` y `agotado`), `MenuParaComensal` (agrega `precio_para_mi` y `mi_reserva`) y `FiltrosMenu` |
| Repository | `app/repositories/menu_repository.py` | Buscar por id o fecha, `obtener_para_actualizar` (**SELECT ... FOR UPDATE**), saber si tiene reservas, listar y próximos activos |
| Service | `app/services/menu_service.py` | Crear, actualizar, eliminar, menú de hoy y próximos. Usa `calcular_tarifa` de reservas |
| Router | `app/routers/menus.py` | Los 7 endpoints del módulo |

### Endpoints

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| GET | `/api/v1/menus/hoy` | Cualquiera | Menú de hoy con mi precio y mi reserva |
| GET | `/api/v1/menus/proximos` | Cualquiera | Hasta 14 menús activos desde hoy |
| GET | `/api/v1/menus` | Encargado | Historial con filtros `desde`, `hasta` y `activo` |
| GET | `/api/v1/menus/{id}` | Cualquiera | Consulta un menú |
| POST | `/api/v1/menus` | Encargado | Configura un menú (201) |
| PATCH | `/api/v1/menus/{id}` | Encargado | Actualiza nombre, descripción, precios o cupo |
| DELETE | `/api/v1/menus/{id}` | Encargado | Elimina el menú (lógico o físico) |

### Reglas de negocio
1. **Un solo menú por fecha** (409), y la fecha no puede ser pasada (422).
2. Al crear un menú, el cupo disponible es igual al cupo total.
3. No se modifica el menú de una fecha que ya pasó.
4. **El cupo nuevo no puede ser menor que los almuerzos ya vendidos.** Si se cambia el cupo, el disponible se recalcula.
5. **Eliminar:** si el menú tiene reservas, se desactiva (borrado lógico) y deja de recibir reservas. Si no tiene, se borra definitivamente.
6. `SELECT ... FOR UPDATE` bloquea la fila del menú, para que dos personas no tomen el último cupo al mismo tiempo.

### Pruebas (`tests/test_menus_reservas.py`, junto con las de reservas)
Crear un menú con el cupo completo, un solo menú por fecha, datos inválidos (422), eliminar en forma lógica o física y no bajar el cupo de lo vendido.

---

## Módulo 5. Reservas y consumos

### Qué hace
Los **aprendices reservan**, los **invitados compran** y los **instructores consumen a su cuenta mensual**. La API calcula el precio, descuenta el cupo, controla el horario y permite cancelar. El Encargado marca cada reserva como **Pagado** o **No pagado**.

### Tabla `reservas`

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `menu_id` | FK → `menus` |
| `usuario_id` | FK → `usuarios` |
| `tipo` | `CHECK` en (APRENDIZ, BENEFICIARIO, INSTRUCTOR, INVITADO) |
| `valor` | `NUMERIC(10,2) ≥ 0` |
| `estado` | `CHECK` en (RESERVADO, PENDIENTE, PAGADO, NO_PAGADO, CANCELADA), `DEFAULT 'RESERVADO'` |
| Auditoría | `creado_por` (quién reservó) y `actualizado_por` (quién marcó el pago) |

**Índice único parcial:** `uq_reservas_menu_usuario ON (menu_id, usuario_id) WHERE estado <> 'CANCELADA'`. Garantiza en la base de datos **una sola reserva vigente por persona y por menú** (las canceladas no cuentan).

### Estados de una reserva

```
 Aprendiz / Invitado:    RESERVADO ──(Encargado)──► PAGADO  o  NO_PAGADO
                             │
                             └──(la misma persona)──► CANCELADA   (el cupo vuelve al menú)

 Beneficiario:           PAGADO desde el inicio (valor $0)

 Instructor:             PENDIENTE ──(pago que salda la deuda en Cartera)──► PAGADO
```

### Datos de prueba (19 reservas)

| Día del menú | Persona | Tipo | Valor | Estado |
|---|---|---|---:|---|
| Hoy | Laura (aprendiz) | APRENDIZ | 5.000 | RESERVADO |
| Hoy | Sebastián | APRENDIZ | 5.000 | PAGADO |
| Hoy | Camilo (beneficiario) | BENEFICIARIO | 0 | PAGADO |
| Hoy | Pedro (invitado) | INVITADO | 8.000 | PAGADO |
| Hoy | Carlos (instructor) | INSTRUCTOR | 5.000 | PENDIENTE |
| Hoy | Valentina | APRENDIZ | 5.000 | NO_PAGADO |
| Ayer | Laura | APRENDIZ | 5.000 | PAGADO |
| Ayer | Andrés (beneficiario) | BENEFICIARIO | 0 | PAGADO |
| Ayer | Ana (invitada) | INVITADO | 8.000 | PAGADO |
| Ayer | Diana (instructora) | INSTRUCTOR | 5.000 | PENDIENTE |
| Hoy − 2 | Sebastián | APRENDIZ | 5.000 | PAGADO |
| Hoy − 2 | Carlos | INSTRUCTOR | 5.000 | PENDIENTE |
| Hoy − 2 | Jorge (instructor) | INSTRUCTOR | 5.000 | PAGADO |
| Hoy − 3 | Valentina | APRENDIZ | 5.000 | PAGADO |
| Hoy − 3 | Jorge | INSTRUCTOR | 5.000 | PAGADO |
| Hoy − 3 | Laura | APRENDIZ | 5.000 | CANCELADA |
| Hoy − 5 | Camilo | BENEFICIARIO | 0 | PAGADO |
| Hoy − 5 | Pedro | INVITADO | 8.000 | PAGADO |
| Mes anterior | Carlos | INSTRUCTOR | 5.000 | PENDIENTE |

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Model | `app/models/reserva.py` | Clase `Reserva` (con su `menu` y su `usuario`). En este archivo también está `PagoInstructor` (ver Cartera) |
| Schemas | `app/schemas/reserva.py` | `TipoReserva`, `EstadoReserva`, `ReservaCrear` (**solo `menu_id`**), `EstadoPagoEntrada` (PAGADO o NO_PAGADO), `ReservaSalida`, `FiltrosReserva` y `FiltrosMisReservas` |
| Repository | `app/repositories/reserva_repository.py` | Reserva vigente de una persona, listar con filtros, historial propio, aprendices de una ficha, conteos y consumo en un rango |
| Service | `app/services/reserva_service.py` | `calcular_tarifa()`, `reservar`, `cancelar`, `marcar_pago`, `obtener` y listados |
| Router | `app/routers/reservas.py` | Los 6 endpoints del módulo |

### Endpoints

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | `/api/v1/reservas` | Aprendiz, instructor o invitado | Reserva o compra (201) |
| GET | `/api/v1/reservas/mias` | Aprendiz, instructor o invitado | Mis consumos, filtrados por estado |
| GET | `/api/v1/reservas` | Encargado | Todas las ventas: filtros por fecha, rango, estado, tipo, usuario y ficha |
| GET | `/api/v1/reservas/{id}` | Cualquiera | El Encargado ve cualquiera; los demás, solo las propias |
| PATCH | `/api/v1/reservas/{id}/cancelar` | Aprendiz, instructor o invitado | Cancela la propia reserva |
| PATCH | `/api/v1/reservas/{id}/pago` | Encargado | Marca PAGADO o NO_PAGADO |

### Precio según el rol (`calcular_tarifa`)

| Rol | Tipo | Valor | Estado inicial |
|---|---|---|---|
| Aprendiz | APRENDIZ | `precio_aprendiz` ($5.000) | RESERVADO |
| Aprendiz beneficiario | BENEFICIARIO | $0 | PAGADO |
| Instructor | INSTRUCTOR | `precio_aprendiz` ($5.000), a su cuenta mensual | PENDIENTE |
| Invitado | INVITADO | `precio_invitado` ($8.000) | RESERVADO |
| Encargado | — | No puede reservar | — |

### Reglas de negocio
1. Solo se reserva o cancela **entre las 7:00 a. m. y las 9:00 p. m.** (400).
2. El menú debe existir (404), estar activo, no ser de una fecha pasada y tener cupo (400).
3. **Una reserva vigente por persona y por menú** (409).
4. **El precio lo calcula la API.** Si el cliente envía `valor` o `estado`, responde 422.
5. Cada reserva descuenta 1 del cupo. Cancelar lo devuelve. Todo ocurre en una sola transacción.
6. Solo se cancela la **propia** reserva, en estado RESERVADO o PENDIENTE (o la de un beneficiario), de hoy o de un día futuro.
7. El Encargado no marca el pago de los instructores (se paga en la Cartera), ni el de los beneficiarios (no tiene costo), ni el de una reserva cancelada.

### Pruebas (`tests/test_menus_reservas.py`, 15 pruebas en total con menús)
Precio según el tipo de cuenta, una sola reserva por persona y menú, menú agotado, no se puede enviar el precio, menú inexistente (404), fuera del horario, el horario incluye los extremos, cancelar devuelve el cupo, el encargado marca el pago y las reservas se reflejan en grupos y consumos.

---

## Módulo 6. Cartera de deudas

### Qué hace
Lleva la **cuenta mensual de los instructores**: cuánto consumieron, cuánto pagaron, cuánto deben y si la deuda está vencida. El Encargado registra los pagos, y cada instructor puede ver su propia cuenta.

### Tablas
- **`pagos_instructor`** (propia del módulo)

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `instructor_id` | FK → `usuarios` |
| `valor` | `NUMERIC(12,2) > 0` |
| `metodo` | `CHECK` en (EFECTIVO, TRANSFERENCIA, NOMINA) |
| `observacion` | `VARCHAR(255)` |
| `creado_por`, `creado_en` | Auditoría (sin "actualizado": un pago **no se edita**) |

- **`reservas`**: aporta los consumos de tipo INSTRUCTOR.

### Datos de prueba

**Pagos (3)**

| Instructor | Valor | Método | Observación |
|---|---:|---|---|
| Carlos Andrés Muñoz | 5.000 | EFECTIVO | Abono parcial |
| Jorge Iván Salazar | 4.000 | NOMINA | Descuento de nómina |
| Jorge Iván Salazar | 6.000 | TRANSFERENCIA | Pago del saldo |

**Cartera resultante** (calculada por la API, no guardada en una tabla)

| Instructor | Consumido | Pagado | Saldo | Estado | Por qué |
|---|---:|---:|---:|---|---|
| Carlos Andrés Muñoz | 15.000 | 5.000 | **10.000** | **VENCIDA** | Tiene un consumo del mes anterior: el corte fue el 31/10 y el plazo de 5 días venció el 05/11 |
| Diana Patricia Cerón | 5.000 | 0 | **5.000** | **ACTIVA** | Solo debe consumos de este mes, dentro del plazo |
| Jorge Iván Salazar | 10.000 | 10.000 | 0 | AL_DIA | Pagó todo |

**Resumen:** 2 deudores, deuda total de $15.000, promedio de $7.500 y mayor deuda de $10.000.

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Model | `app/models/reserva.py` | Clase `PagoInstructor` |
| Schemas | `app/schemas/cartera.py` | `MetodoPago`, `EstadoCuenta` (AL_DIA, ACTIVA, VENCIDA), `PagoCrear`, `PagoSalida`, `DeudaInstructor`, `ResumenCartera`, `CarteraSalida`, `DetalleCartera`, `PagoRegistrado` y `MiCuenta` |
| Repository | `app/repositories/cartera_repository.py` | `resumen_instructores()`: consulta combinada con subconsultas (consumido, pagado, pendientes y consumo pendiente más antiguo). `pagos_de()`. `registrar_pago()`: guarda el pago y, si salda la deuda, marca los consumos como PAGADO en la misma transacción |
| Service | `app/services/cartera_service.py` | Calcula la deuda, el estado y los días vencidos. Lista deudores, muestra el detalle, registra pagos y arma la cuenta mensual |
| Router | `app/routers/cartera.py` | Los 4 endpoints del módulo |

### Endpoints

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| GET | `/api/v1/cartera?solo_vencidas=` | Encargado | Instructores con deuda (de mayor a menor) y resumen |
| GET | `/api/v1/cartera/mi-cuenta` | Instructor | Mi saldo, estado, consumos del mes y próximo corte |
| GET | `/api/v1/cartera/{instructor_id}` | Encargado | Deuda e historial de pagos de un instructor |
| POST | `/api/v1/cartera/{instructor_id}/pagos` | Encargado | Registra un pago (201) |

### Reglas de negocio
1. **Saldo = total consumido − total pagado.** Las reservas canceladas no cuentan.
2. **Deuda VENCIDA:** el corte es el último día del mes del consumo pendiente más antiguo, más 5 días de plazo (`DIAS_PLAZO_PAGO`). Pasada esa fecha, se cuentan los días vencidos. *(Regla propuesta, pendiente de validar con el Encargado.)*
3. **Un pago no puede superar la deuda** (400), y no se registran pagos si no hay deuda.
4. **Si el pago salda la deuda**, todos los consumos PENDIENTE del instructor pasan a PAGADO.
5. La fila del instructor se bloquea mientras se registra el pago, para que dos pagos simultáneos no superen la deuda.
6. Solo los usuarios con rol instructor tienen cuenta mensual (400 si no lo es, 404 si no existe).
7. El promedio de deuda solo considera a los instructores que deben algo.

### Pruebas (`tests/test_cartera.py`, 6 pruebas)
El resumen es coherente, el filtro de vencidas, el flujo de pago parcial y total, el pago a quien no es instructor o no existe, el pago con datos inválidos y la cuenta del instructor.

---

## Módulo 7. Inventario y kardex

### Qué hace
Controla los **materiales e ingredientes** de la cocina: código de barras, costo, stock, stock mínimo y vencimiento. Calcula el estado de cada material (**Bueno, Bajo, Crítico o Venciendo**). Registra **entradas, salidas y mermas** en el **kardex**, que funciona como historial.

### Tablas

**`materiales`**

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `codigo_barras` | `VARCHAR(14) UNIQUE`, `CHECK` 8 a 14 dígitos |
| `nombre` | `VARCHAR(100)` (índice en `lower(nombre)`) |
| `categoria` | `CHECK` en (PROTEINA, GRANO, VERDURA, FRUTA, LACTEO, ABARROTE, DESECHABLE) |
| `unidad_medida` | `CHECK` en (KG, G, L, ML, UND) |
| `costo_unitario` | `NUMERIC(12,2) > 0` |
| `stock`, `stock_minimo` | `NUMERIC(12,3) ≥ 0` |
| `fecha_vencimiento` | `DATE` (opcional) |
| `activo` | Borrado lógico |
| Auditoría | sí |

**`movimientos_inventario`** (kardex)

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `material_id` | FK → `materiales` |
| `tipo` | `CHECK` en (ENTRADA, SALIDA, MERMA) |
| `cantidad` | `NUMERIC(12,3) > 0` |
| `saldo` | `NUMERIC(12,3) ≥ 0`: stock que quedó **después** del movimiento |
| `concepto` | Motivo (en una merma, la razón) |
| `creado_por`, `creado_en` | Quién y cuándo |

### Cómo se calcula el estado del stock (en este orden)

| Orden | Estado | Condición |
|---:|---|---|
| 1 | **VENCIENDO** | Vence en 7 días o menos |
| 2 | **CRITICO** | Stock ≤ 50 % del mínimo |
| 3 | **BAJO** | Stock ≤ mínimo |
| 4 | **BUENO** | Ninguna de las anteriores |

PostgreSQL lo calcula con un `CASE` en la misma consulta (`expresion_estado` en el repositorio).

### Datos de prueba: materiales (14)

| id | Código | Nombre | Categoría | Unidad | Costo | Stock | Mínimo | Vence | Estado (16/11) |
|---:|---|---|---|---|---:|---:|---:|---|---|
| 1 | 7702001000011 | Arroz blanco | GRANO | KG | 4.200 | 38 | 20 | — | BUENO |
| 2 | 7702001000028 | Fríjol rojo | GRANO | KG | 9.800 | 9 | 10 | — | BAJO |
| 3 | 7702001000035 | Pechuga de pollo | PROTEINA | KG | 14.500 | 20 | 15 | en 4 días | VENCIENDO |
| 4 | 7702001000042 | Carne de res | PROTEINA | KG | 22.000 | 8 | 10 | en 20 días | BAJO |
| 5 | 7702001000059 | Papa pastusa | VERDURA | KG | 2.500 | 40 | 20 | — | BUENO |
| 6 | 7702001000066 | Tomate chonto | VERDURA | KG | 3.800 | 3 | 8 | en 30 días | CRITICO |
| 7 | 7702001000073 | Cebolla cabezona | VERDURA | KG | 3.200 | 12 | 5 | — | BUENO |
| 8 | 7702001000080 | Aceite vegetal | ABARROTE | L | 9.500 | 15 | 6 | — | BUENO |
| 9 | 7702001000097 | Huevo AA | PROTEINA | UND | 550 | 180 | 60 | en 15 días | BUENO |
| 10 | 7702001000103 | Leche entera | LACTEO | L | 4.200 | 20 | 10 | en 6 días | VENCIENDO |
| 11 | 7702001000110 | Plátano verde | FRUTA | UND | 700 | 70 | 40 | — | BUENO |
| 12 | 7702001000127 | Bandeja desechable | DESECHABLE | UND | 350 | 380 | 100 | — | BUENO |
| 13 | 7702001000134 | Lenteja | GRANO | KG | 7.600 | 10 | 8 | — | BUENO |
| 14 | 7702001000141 | Sal refinada | ABARROTE | KG | 1.800 | 0 | 2 | — | CRITICO |

La **sal refinada** no tiene movimientos ni está en recetas, así que se puede **eliminar físicamente**. Sirve para probar esa regla.

### Datos de prueba: kardex (22 movimientos)

- **13 ENTRADAS de "Stock inicial"**, hace 10 días, una por cada material excepto la sal.
- **9 movimientos hace 2 días:**

| Material | Tipo | Cantidad | Saldo | Concepto |
|---|---|---:|---:|---|
| Arroz blanco | SALIDA | 12 | 38 | Preparación de almuerzos |
| Fríjol rojo | SALIDA | 6 | 9 | Preparación de frijolada |
| Pechuga de pollo | SALIDA | 10 | 20 | Preparación de almuerzos |
| Carne de res | **MERMA** | 2 | 10 | Carne con mal olor al abrir el empaque |
| Carne de res | SALIDA | 2 | 8 | Preparación de carne guisada |
| Tomate chonto | **MERMA** | 7 | 3 | Tomates dañados por exceso de maduración |
| Aceite vegetal | SALIDA | 3 | 15 | Fritos del día |
| Plátano verde | SALIDA | 30 | 70 | Tajadas y patacones |
| Bandeja desechable | SALIDA | 120 | 380 | Despacho de almuerzos |

El stock de cada material es el **saldo de su último movimiento**: el script lo recalcula al final.

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Model | `app/models/inventario.py` | Clases `Material` y `MovimientoInventario` (con su `material` y su `responsable`) |
| Schemas | `app/schemas/inventario.py` | `Categoria`, `UnidadMedida`, `EstadoStock`, `TipoMovimiento`, `MaterialCrear` (con `stock_inicial`), `MaterialActualizar` (**sin stock**), `MaterialSalida`, `MovimientoCrear`, `MovimientoSalida` (calcula las columnas `entrada` y `salida` del kardex), `FiltrosMaterial` y `FiltrosKardex` |
| Repository | `app/repositories/inventario_repository.py` | `expresion_estado` (CASE), buscar con estado, `obtener_para_actualizar` (FOR UPDATE), saber si existe un código, listar, consultar movimientos o uso en recetas, crear con la primera entrada y listar el kardex |
| Service | `app/services/inventario_service.py` | CRUD de materiales, `registrar_movimiento` y `kardex` |
| Router | `app/routers/inventario.py` | Los 7 endpoints del módulo |

### Endpoints (todos solo para el encargado)

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/v1/inventario/materiales` | Control de stock con filtros (`buscar` por nombre o código de barras, `categoria`, `estado`, `activo`) |
| GET | `/api/v1/inventario/materiales/{id}` | Consulta un material con su estado |
| POST | `/api/v1/inventario/materiales` | Agrega un material (201) |
| PATCH | `/api/v1/inventario/materiales/{id}` | Edita nombre, categoría, costo, mínimo o vencimiento |
| DELETE | `/api/v1/inventario/materiales/{id}` | Elimina el material (lógico o físico) |
| POST | `/api/v1/inventario/movimientos` | Registra una entrada, salida o merma (201) |
| GET | `/api/v1/inventario/kardex` | Kardex con filtros (`material_id`, `tipo`, `desde`, `hasta`) |

### Reglas de negocio
1. El código de barras es único (409).
2. **El stock solo cambia con movimientos.** No se puede editar a mano: si se envía `stock` en el PATCH, responde 422.
3. **El stock inicial genera una ENTRADA** en el kardex.
4. **Una salida o merma no puede dejar el stock en negativo** (400 "Stock insuficiente...").
5. El movimiento y el nuevo stock se guardan **en una sola transacción**, con la fila bloqueada (`FOR UPDATE`).
6. **No se elimina un material que use una receta activa** (400, con los nombres de las recetas).
7. Si tiene historial en el kardex o en recetas, se desactiva (lógico). Si no, se borra definitivamente.
8. El kardex **no se edita ni se borra**. Hasta el rol de la base de datos lo impide (solo SELECT e INSERT).

### Pruebas (`tests/test_inventario.py`, 10 pruebas)
Estado del stock, búsqueda por código de barras, el stock inicial genera una entrada, código duplicado o inválido, la salida y la merma actualizan el saldo, una salida mayor al stock (400), una merma sin razón (422), el stock no se edita directamente, eliminar un material y el kardex filtrado por mermas.

---

## Módulo 8. Recetas

### Qué hace
Guarda la **fórmula de cada plato** (qué ingredientes lleva y cuánto de cada uno) y calcula de forma automática el **costo de producción**, el **margen** y una **alerta si el margen es negativo**.

### Tablas

**`recetas`**

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `nombre` | `VARCHAR(100) UNIQUE` |
| `descripcion` | `VARCHAR(500)` |
| `precio_venta` | `NUMERIC(10,2) > 0` |
| `activo` | `BOOLEAN` |
| Auditoría | sí |

**`receta_ingredientes`**

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `receta_id` | FK → `recetas` **ON DELETE CASCADE** (si se borra la receta, se borra su fórmula) |
| `material_id` | FK → `materiales` |
| `cantidad` | `NUMERIC(12,3) > 0`: cantidad por plato |
| — | `UNIQUE (receta_id, material_id)`: un material no se repite en la misma receta |

### Cómo se calcula el costo

```
costo de cada ingrediente = cantidad por plato × costo unitario del material
costo de producción       = suma de los costos de los ingredientes
margen                    = precio de venta − costo de producción
margen %                  = margen ÷ precio de venta × 100
alerta_margen_negativo    = margen < 0
```

**Ejemplo, Arroz con pollo:**

| Ingrediente | Cantidad | Costo unitario | Costo |
|---|---:|---:|---:|
| Arroz blanco | 0,120 KG | 4.200 | 504 |
| Pechuga de pollo | 0,150 KG | 14.500 | 2.175 |
| Cebolla cabezona | 0,020 KG | 3.200 | 64 |
| Aceite vegetal | 0,010 L | 9.500 | 95 |
| Bandeja desechable | 1 UND | 350 | 350 |
| **Costo de producción** | | | **3.188** |

Margen = 5.000 − 3.188 = **1.812 (36,24 %)**.

### Datos de prueba (10 recetas y 48 ingredientes)

| Receta | Precio de venta | Costo de producción | Margen | Margen % |
|---|---:|---:|---:|---:|
| Arroz con pollo | 5.000 | 3.188 | 1.812 | 36,24 % |
| Frijolada | 5.000 | 3.000 | 2.000 | 40,00 % |
| Carne guisada con papa | 5.000 | 4.760 | 240 | 4,80 % |
| Sudado de pollo | 5.000 | 3.510 | 1.490 | 29,80 % |
| Lentejas con arroz | 5.000 | 2.864 | 2.136 | 42,72 % |
| Pollo asado con ensalada | 8.000 | 4.779 | 3.221 | 40,26 % |
| **Bistec a caballo** | 5.000 | 5.720 | **−720** | **−14,40 % ⚠** |
| Huevos pericos con arroz | 5.000 | 2.156 | 2.844 | 56,88 % |
| Patacón con hogao | 5.000 | 2.499 | 2.501 | 50,02 % |
| Sopa de verduras | 5.000 | 1.836 | 3.164 | 63,28 % |

El **Bistec a caballo** cuesta más de lo que se vende: es el dato preparado para mostrar la **alerta de margen negativo**.

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Model | `app/models/receta.py` | Clases `Receta` (con su lista de `ingredientes`, `cascade="all, delete-orphan"`) y `RecetaIngrediente` (con su `material`) |
| Schemas | `app/schemas/receta.py` | `IngredienteEntrada`, `Ingredientes` (1 a 30, sin repetidos), `RecetaCrear`, `RecetaActualizar`, `IngredienteSalida`, `RecetaSalida` y `FiltrosReceta` |
| Repository | `app/repositories/receta_repository.py` | Buscar, saber si existe un nombre (sin importar mayúsculas), listar, reemplazar ingredientes, guardar y eliminar |
| Service | `app/services/receta_service.py` | CRUD y `_con_costos()`, que hace el cálculo de costo y margen |
| Router | `app/routers/recetas.py` | Los 5 endpoints del módulo |

### Endpoints (todos solo para el encargado)

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/v1/recetas` | Lista con costo y margen (filtros `buscar` y `activo`) |
| GET | `/api/v1/recetas/{id}` | Consulta una receta con su desglose de costos |
| POST | `/api/v1/recetas` | Crea una receta (201) |
| PATCH | `/api/v1/recetas/{id}` | Actualiza la receta. Si trae ingredientes, **reemplaza toda la fórmula** |
| DELETE | `/api/v1/recetas/{id}` | La borra junto con su fórmula |

### Reglas de negocio
1. El nombre es único **sin importar mayúsculas** ("Ajiaco" = "AJIACO") (409).
2. Una receta lleva de 1 a 30 ingredientes, sin materiales repetidos (422).
3. Cada ingrediente debe existir en el inventario (404) y estar activo (400).
4. El costo se recalcula con el **costo unitario actual** del material cada vez que se consulta la receta.
5. Las recetas no tienen movimientos asociados, así que se borran físicamente.

### Pruebas (`tests/test_recetas_sugerencias_reportes.py`, primeras 4 de 9)
Costo y margen de una receta, alerta de margen negativo, reglas de los ingredientes, y cambiar los ingredientes recalcula el costo y permite eliminar.

---

## Módulo 9. Sugerencias

### Qué hace
**Todos** los usuarios pueden enviar sugerencias. El Encargado las ve en un buzón, con las pendientes primero y contadores, y las **atiende**, con respuesta opcional.

### Tabla `sugerencias`

| Columna | Tipo y restricciones |
|---|---|
| `id` | PK |
| `usuario_id` | FK → `usuarios` (quién la envió) |
| `asunto` | `VARCHAR(100)` |
| `mensaje` | `VARCHAR(500)` |
| `estado` | `CHECK` en (PENDIENTE, ATENDIDA), `DEFAULT 'PENDIENTE'` |
| `respuesta` | `VARCHAR(500)` |
| `atendida_por`, `atendida_en` | Quién la atendió y cuándo |
| `creado_en` | Cuándo se envió |

### Datos de prueba (10 sugerencias: 5 pendientes y 5 atendidas)

| Autor | Asunto | Estado | Respuesta |
|---|---|---|---|
| Laura (aprendiz) | Más opciones vegetarianas | PENDIENTE | — |
| Sebastián | Horario de entrega | ATENDIDA | Desde la próxima semana se abre a las 11:30. |
| Camilo (beneficiario) | Agradecimiento | ATENDIDA | ¡Con gusto! Sigue adelante con tu formación. |
| Pedro (invitado) | Pago con transferencia | PENDIENTE | — |
| Carlos (instructor) | Corte de la cuenta | PENDIENTE | — |
| Valentina | Porciones | ATENDIDA | Gracias, ajustamos el gramaje de la receta. |
| Andrés | Jugo natural | PENDIENTE | — |
| Diana (instructora) | Cubiertos | ATENDIDA | Se aumentó el pedido de cubiertos. |
| Ana (invitada) | Muy buena atención | ATENDIDA | Gracias por visitarnos. |
| Jorge (instructor) | Menú de la semana | PENDIENTE | — |

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Model | `app/models/sugerencia.py` | Clase `Sugerencia` (con su `usuario`) |
| Schemas | `app/schemas/sugerencia.py` | `EstadoSugerencia`, `SugerenciaCrear`, `AtenderEntrada`, `SugerenciaSalida`, `ContadoresSugerencias`, `PaginaSugerencias` y `FiltrosSugerencia` |
| Repository | `app/repositories/sugerencia_repository.py` | Buscar, listar (pendientes primero), listar las de un usuario, contadores y guardar |
| Service | `app/services/sugerencia_service.py` | Crear, listar, listar las propias y atender |
| Router | `app/routers/sugerencias.py` | Los 4 endpoints del módulo |

### Endpoints

| Método | Ruta | Rol | Qué hace |
|---|---|---|---|
| POST | `/api/v1/sugerencias` | Cualquiera | Envía una sugerencia (201) |
| GET | `/api/v1/sugerencias/mias` | Cualquiera | Mis sugerencias |
| GET | `/api/v1/sugerencias` | Encargado | Buzón completo con contadores (total, atendidas y pendientes) y filtro por estado |
| PATCH | `/api/v1/sugerencias/{id}/atender` | Encargado | Cambia el estado a ATENDIDA, con respuesta opcional |

### Reglas de negocio
1. La sugerencia queda asociada a quien la envía, sacado del token (no se puede enviar a nombre de otro).
2. Asunto de 3 a 100 caracteres y mensaje de 3 a 500 (422).
3. Una sugerencia ya atendida no se puede atender otra vez (400).

### Pruebas (`tests/test_recetas_sugerencias_reportes.py`, pruebas 5 y 6 de 9)
Flujo completo de sugerencias y mensaje demasiado largo.

---

## Módulo 10. Reportes e indicadores

### Qué hace
Calcula las **ventas** (cantidad de almuerzos) y los **ingresos** de un período (día, semana, mes, trimestre, semestre o año), separados por tipo de cliente y por día. También entrega los **indicadores** del panel del Encargado.

### Tablas
No tiene tabla propia. **Consulta `reservas` + `menus`** con `GROUP BY`, sin contar las reservas canceladas. Para los indicadores también usa la cartera y las sugerencias.

### Datos que muestra con los datos de prueba (hoy)

**Indicadores (`GET /reportes/indicadores`):**

| Indicador | Valor | De dónde sale |
|---|---|---|
| `ventas_hoy` | 6 | Reservas vigentes del menú de hoy |
| `ingresos_hoy` | 28.000 | 5.000 + 5.000 + 0 + 8.000 + 5.000 + 5.000 |
| `instructores_con_deuda` | 2 | Carlos y Diana |
| `deuda_pendiente` | 15.000 | 10.000 + 5.000 |
| `sugerencias_pendientes` | 5 | Buzón |

### Cómo se calcula el rango de cada período (`rango_del_periodo`)

| Período | Desde | Hasta |
|---|---|---|
| `dia` | La fecha | La misma fecha |
| `semana` | El lunes de esa semana | El domingo |
| `mes` | El día 1 | El último día del mes |
| `trimestre` | El primer día del trimestre (ene, abr, jul, oct) | El último día del trimestre |
| `semestre` | 1 de enero o 1 de julio | 30 de junio o 31 de diciembre |
| `anio` | 1 de enero | 31 de diciembre |

### Archivos

| Capa | Archivo | Qué hace en este módulo |
|---|---|---|
| Schemas | `app/schemas/reporte.py` | `Periodo`, `FiltrosVentas`, `VentasPorTipo`, `VentasPorDia`, `ReporteVentas` e `Indicadores` |
| Repository | `app/repositories/reporte_repository.py` | `ventas_por_dia` y `ventas_por_tipo` (`COUNT` y `SUM` agrupados) |
| Service | `app/services/reporte_service.py` | `rango_del_periodo()`, `ventas()` e `indicadores()`. Usa `CarteraService` y el repositorio de sugerencias |
| Router | `app/routers/reportes.py` | Los 2 endpoints del módulo |

### Endpoints (solo para el encargado)

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/v1/reportes/ventas?periodo=mes&fecha=2026-11-16` | Ventas e ingresos del período, por tipo y por día |
| GET | `/api/v1/reportes/indicadores` | Indicadores de hoy del Encargado |

### Pruebas (`tests/test_recetas_sugerencias_reportes.py`, últimas 3 de 9)
El reporte de ventas cuadra, el rango de cada período y los indicadores del encargado.

---

## Parte 7 — Pruebas y documentación

### Carpeta `tests/` (64 pruebas con pytest)

| Archivo | Pruebas | Qué cubre |
|---|---:|---|
| `conftest.py` | — | Configuración compartida: abre el horario de reservas para que las pruebas corran a cualquier hora, crea el cliente de prueba (`TestClient`), inicia sesión con cada rol y trae las funciones de ayuda `crear_usuario`, `crear_menu`, `reservar` y `aleatorio` |
| `test_auth.py` | 12 | Login, tokens, bloqueo, contraseña, 401 y 403 |
| `test_usuarios.py` | 12 | Usuarios, beneficiarios y fichas |
| `test_menus_reservas.py` | 15 | Menús, reservas, horario, cupo y pagos |
| `test_cartera.py` | 6 | Deudas, pagos y cuenta mensual |
| `test_inventario.py` | 10 | Materiales, estados, kardex y mermas |
| `test_recetas_sugerencias_reportes.py` | 9 | Costos, sugerencias y reportes |

Las pruebas **crean registros**, así que deben correr en una base de pruebas, que después se limpia ejecutando otra vez los 3 scripts SQL. Algunas usan los id de los datos de prueba (por ejemplo, `ROL_APRENDIZ = 3`, `FICHA_ADSO = 1` y `POLLO = 3`), por lo que esperan una base recién creada.

### Carpeta `docs/`

| Archivo | Qué es |
|---|---|
| `Especificacion_Requisitos_GastroSENA.docx` | Anexo 2: los requisitos funcionales (RF01–RF51), roles, reglas y requisitos no funcionales. Los comentarios del código citan estos RF |
| `GastroSENA_API.postman_collection.json` | Colección de Postman con **51 peticiones** con pruebas, en 6 carpetas: 1. Autenticación (11), 2. Usuarios y beneficiarios (8), 3. Menú del Día y reservas (13), 4. Cartera de instructores (4), 5. Inventario y recetas (8), 6. Sugerencias y reportes (7). Los logins guardan los tokens en variables (`token_encargado`, `token_aprendiz`, ...) |
| `GUIA_DEL_PROYECTO.md` | Esta guía |

---

## Parte 8 — Glosario para la sustentación

| Término | Qué significa en este proyecto |
|---|---|
| **API REST** | Servicio que recibe peticiones HTTP (GET, POST, PATCH, PUT, DELETE) y responde en JSON |
| **FastAPI** | Framework de Python con el que se construyó la API. Genera Swagger automáticamente |
| **Uvicorn** | Servidor que ejecuta la API (`uvicorn app.main:app --reload`) |
| **Swagger / OpenAPI** | Documentación interactiva en `http://localhost:8000/docs` |
| **ORM (SQLAlchemy)** | Permite trabajar con las tablas como clases de Python en lugar de escribir SQL a mano |
| **Pydantic** | Librería que valida los datos con los *schemas* |
| **JWT** | Token firmado que demuestra quién es el usuario. Se envía en `Authorization: Bearer ...` |
| **Access token / Refresh token** | El primero dura 30 minutos y se usa en cada petición. El segundo dura 7 días y solo sirve para pedir tokens nuevos |
| **bcrypt** | Algoritmo que cifra las contraseñas en un solo sentido, con sal aleatoria. No se puede descifrar: solo se compara |
| **401 vs 403** | 401: no sé quién es usted (sin token o con token inválido). 403: sé quién es, pero su rol no tiene permiso |
| **404 / 409 / 422** | 404: no existe. 409: ya existe un valor único. 422: los datos enviados no son válidos |
| **Borrado lógico** | En lugar de borrar el registro, se marca `activo = false` para conservar el historial |
| **Auditoría** | Columnas `creado_por`, `creado_en`, `actualizado_por` y `actualizado_en` |
| **Transacción** | Varios cambios que se guardan todos juntos o ninguno (`commit`). Ejemplo: la reserva y el descuento del cupo |
| **SELECT ... FOR UPDATE** | Bloquea una fila mientras se modifica, para que dos peticiones simultáneas no choquen |
| **Kardex** | Historial de entradas, salidas y mermas de inventario con el saldo resultante |
| **Merma** | Pérdida de material (dañado o vencido). Se registra con su razón |
| **CORS** | Lista de páginas web autorizadas para llamar la API desde un navegador |
| **Variables de entorno (.env)** | Configuración y claves fuera del código. El `.env` no se sube a GitHub |
| **DDL / DML / DCL** | Scripts SQL de estructura, de datos y de permisos |
| **Esquema `gastrosena`** | "Carpeta" propia del proyecto dentro de la base de datos, en lugar de `public` |
| **Rol de privilegios mínimos** | `api_gastrosena` solo puede hacer lo que la API necesita, no es superusuario |
