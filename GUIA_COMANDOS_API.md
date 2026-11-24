# Guía de comandos de GastroSENA API

API REST de reservas de almuerzos del SENA Tecnoparque Yamboró. Python + FastAPI + PostgreSQL (esquema `gastrosena`). Todos los endpoints de módulos empiezan con `/api/v1`.

Estado verificado el 24/11/2026: base `gastrosena_db` creada con 11 tablas, 4 bases en el servidor (`gastrosena_db` y las del sistema), y 59/59 pruebas en verde.

## Carpetas clave del código (subrayadas)

Estas son las carpetas que hacen funcionar la API; si falta alguna, no arranca o no responde.

- **<u>app/</u>** — código fuente principal.
  - **<u>app/main.py</u>** (archivo) — crea la aplicación, engancha los 10 routers bajo `/api/v1` y revisa que la BD tenga las columnas actuales al arrancar.
  - **<u>app/routers/</u>** — 53 operaciones en 36 rutas bajo `/api/v1` más `GET /` de salud; reciben la petición y revisan el rol.
  - **<u>app/services/</u>** — las reglas del negocio: precios, cupos, stock, deudas y horarios.
  - **<u>app/repositories/</u>** — las consultas reales a PostgreSQL.
  - **<u>app/models/</u>** — las tablas de SQLAlchemy.
  - **<u>app/schemas/</u>** — validación del JSON que entra y de las respuestas donde se declaró `response_model`.
  - **<u>app/core/</u>** — configuración, JWT, contraseñas, permisos, errores y horario de reservas.
  - **<u>app/database/</u>** — conexión, sesiones y auditoría; `obtener_bd()` se usa en cada petición.
- **<u>database/</u>** — scripts SQL (tablas, datos de prueba, usuario y auditoría); sin ellos no hay base de datos.
- **<u>tests/</u>** — 59 pruebas automáticas que validan cada módulo.
- **<u>docs/</u>** — colección de Postman y documento de requisitos (apoyo, no ejecución).

Todo lo de abajo se ejecuta en **PowerShell**, desde la raíz del proyecto:

```powershell
cd "<ruta donde clonaste el proyecto>"
```

---

## 1. Instalación

No es un proyecto Node: **no hay `npm run dev`**. El equivalente es `uvicorn ... --reload`.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip list
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

---

## 2. Base de datos

Scripts en orden para recrear la base (pide la contraseña de `postgres`, dejada en `1234` para desarrollo):

```powershell
$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
& $psql -U postgres -c "DROP DATABASE IF EXISTS gastrosena_db"
& $psql -U postgres -c "CREATE DATABASE gastrosena_db"
& $psql -U postgres -d gastrosena_db -f database\01_ddl.sql
& $psql -U postgres -d gastrosena_db -f database\02_dml.sql
& $psql -U postgres -d gastrosena_db -f database\03_dcl.sql
```

`03_dcl.sql` crea o actualiza `api_gastrosena` con contraseña `1234`.

Si la base ya existía y no quieres borrarla, actualiza sin perder datos:

```powershell
.\ACTUALIZAR-BASE-DE-DATOS.bat
```

O manualmente:

```powershell
& $psql -U postgres -d gastrosena_db -f database\04_auditoria.sql
& $psql -U postgres -d gastrosena_db -f database\05_compatibilidad.sql
```

Comprobación rápida:

```powershell
& $psql -U postgres -d gastrosena_db -c "SET search_path TO gastrosena; SELECT count(*) FROM usuarios;"
```

---

## 3. Configuración `.env`

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
notepad .env
```

Variables que lee `app/core/config.py`:

```text
bd_servidor=localhost
bd_puerto=5432
bd_nombre=gastrosena_db
bd_usuario=api_gastrosena
bd_contrasena=1234
clave_secreta_jwt=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
minutos_token_acceso=30
dias_token_renovar=7
origenes_cors=http://localhost:5173,https://burbano52100.github.io
hora_apertura=7
hora_cierre=21
```

`clave_secreta_jwt` es obligatoria: si falta, tiene menos de 32 caracteres o parece un ejemplo, la API no arranca. El valor de arriba es solo de desarrollo; cámbielo en producción por el generado con `python -c "import secrets; print(secrets.token_hex(32))"`.

---

## 4. Correr la API

Modo desarrollo (recarga automática):

```powershell
uvicorn app.main:aplicacion --reload
```

Equivalentes:

```powershell
python -m uvicorn app.main:aplicacion --reload
uvicorn app.main:app --reload
uvicorn app.main:aplicacion --reload --host 0.0.0.0 --port 8000
uvicorn app.main:aplicacion --host 0.0.0.0 --port 8000
```

URLs:

| URL | Qué es |
|---|---|
| http://localhost:8000/ | Mensaje de estado (pública) |
| http://localhost:8000/docs | Swagger / Authorize |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/openapi.json | Especificación OpenAPI |

Si cambias el puerto, reemplaza `8000` en todos los ejemplos.

---

## 5. Preparar los comandos de las peticiones

En PowerShell, `curl` es unalias de `Invoke-WebRequest`; usa `curl.exe` o `Invoke-RestMethod`.

```powershell
$base = "http://localhost:8000/api/v1"

function Conectar([string]$correo, [string]$clave) {
  $cuerpo = @{ correo = $correo; contrasena = $clave } | ConvertTo-Json
  $respuesta = Invoke-RestMethod -Uri "$base/autenticacion/ingresar" -Method Post -ContentType "application/json" -Body $cuerpo
  $script:auth = "Authorization: Bearer $($respuesta.token_acceso)"
  return $respuesta
}

$renovar = Conectar "encargado@gastrosena.com" "Encargado123"
$renovar.token_acceso
$renovar.token_renovar
$renovar.rol
```

Cambiar de usuario cuando quieras:

```powershell
Conectar "aprendiz@gastrosena.com" "Aprendiz123"
Conectar "instructor@gastrosena.com" "Instructor123"
Conectar "invitado@gastrosena.com" "Invitado123"
```

Todas las peticiones protegidas usan `-H $auth`.

### Usuarios de prueba

| Rol | Correo | Contraseña |
|---|---|---|
| encargado | encargado@gastrosena.com | Encargado123 |
| instructor (deuda vencida) | instructor@gastrosena.com | Instructor123 |
| aprendiz | aprendiz@gastrosena.com | Aprendiz123 |
| aprendiz beneficiario | beneficiario@gastrosena.com | Aprendiz123 |
| invitado | invitado@gastrosena.com | Invitado123 |
| inactiva (no puede entrar) | inactivo@gastrosena.com | Aprendiz123 |

### Roles

| Rol | Permisos |
|---|---|
| encargado | Administra todo; **no puede reservar** |
| instructor | Reserva a cuenta del mes, ve su cuenta y envía sugerencias |
| aprendiz | Reserva, cancela y envía sugerencias; beneficiario paga $0 |
| invitado | Compra almuerzo y envía sugerencias |

---

## 6. Comandos por router

### 6.1 Autenticación — `/autenticacion`

```powershell
curl.exe -s "$base/autenticacion/ingresar" -H "Content-Type: application/json" -d '{"correo":"encargado@gastrosena.com","contrasena":"Encargado123"}'
```

```powershell
curl.exe -s "$base/autenticacion/renovar" -H "Content-Type: application/json" -d '{"token_renovar":"PEGAR_TOKEN_RENOVAR"}'
```

```powershell
curl.exe -s "$base/autenticacion/perfil" -H $auth
```

```powershell
curl.exe -s -X PUT "$base/autenticacion/contrasena" -H $auth -H "Content-Type: application/json" -d '{"contrasena_actual":"Encargado123","contrasena_nueva":"Encargado456"}'
```

### 6.2 Usuarios y roles — `/roles`, `/usuarios` (solo encargado)

```powershell
curl.exe -s "$base/roles" -H $auth
```

```powershell
curl.exe -s "$base/usuarios" -H $auth
curl.exe -s "$base/usuarios?buscar=Laura&rol_id=3&activo=true&saltar=0&limite=10" -H $auth
```

```powershell
curl.exe -s "$base/usuarios/5" -H $auth
```

```powershell
curl.exe -s "$base/usuarios" -H $auth -H "Content-Type: application/json" -d '{"documento":"1083000099","nombre":"Juan Perez","correo":"juan.perez@gastrosena.com","telefono":"3109998877","contrasena":"JuanPerez123","rol_id":3,"ficha_id":1,"es_beneficiario":false}'
```

```powershell
curl.exe -s -X PUT "$base/usuarios/5" -H $auth -H "Content-Type: application/json" -d '{"nombre":"Laura Mendez Vargas","telefono":"3145556677"}'
```

```powershell
curl.exe -s -X DELETE "$base/usuarios/5" -H $auth
```

```powershell
curl.exe -s -X PATCH "$base/usuarios/5/beneficiario" -H $auth -H "Content-Type: application/json" -d '{"es_beneficiario":true}'
```

Roles: `1=encargado`, `2=instructor`, `3=aprendiz`, `4=invitado`.

### 6.3 Fichas — `/fichas` (solo encargado)

```powershell
curl.exe -s "$base/fichas" -H $auth
curl.exe -s "$base/fichas?buscar=ADS&jornada=DIURNA&activo=true&saltar=0&limite=10" -H $auth
```

```powershell
curl.exe -s "$base/fichas/estadisticas" -H $auth
curl.exe -s "$base/fichas/estadisticas?fecha=2026-11-23" -H $auth
```

```powershell
curl.exe -s "$base/fichas/1" -H $auth
```

```powershell
curl.exe -s "$base/fichas/1/reservas" -H $auth
curl.exe -s "$base/fichas/1/reservas?fecha=2026-11-23" -H $auth
```

```powershell
curl.exe -s "$base/fichas" -H $auth -H "Content-Type: application/json" -d '{"codigo":"2847261","programa":"Análisis y Desarrollo de Software","jornada":"DIURNA","vocero":"Persona Vocera","cantidad_estudiantes":25}'
```

```powershell
curl.exe -s -X PUT "$base/fichas/1" -H $auth -H "Content-Type: application/json" -d '{"programa":"ADSO","vocero":"Nueva Vocera","cantidad_estudiantes":30}'
```

```powershell
curl.exe -s -X DELETE "$base/fichas/1" -H $auth
```

Jornadas válidas: `DIURNA`, `NOCTURNA`, `MIXTA`, `FIN_DE_SEMANA`.

### 6.4 Menús — `/menus`

```powershell
curl.exe -s "$base/menus/hoy" -H $auth
curl.exe -s "$base/menus/proximos" -H $auth
```

```powershell
curl.exe -s "$base/menus" -H $auth
curl.exe -s "$base/menus?desde=2026-11-01&hasta=2026-11-30&activo=true&saltar=0&limite=10" -H $auth
```

```powershell
curl.exe -s "$base/menus/11" -H $auth
```

Crear menú (una fecha futura y única; `11` es el menú de hoy en los datos de prueba):

```powershell
$fecha = (Get-Date).AddDays(30).ToString("yyyy-MM-dd")
$cuerpo = @{ fecha=$fecha; nombre="Arroz con pollo"; descripcion="Arroz, pollo, papa y jugo"; precio_aprendiz=5000; precio_invitado=8000; cantidad_total=80 } | ConvertTo-Json
curl.exe -s "$base/menus" -H $auth -H "Content-Type: application/json" -d $cuerpo
```

```powershell
curl.exe -s -X PUT "$base/menus/11" -H $auth -H "Content-Type: application/json" -d '{"nombre":"Bandeja campesina especial","precio_aprendiz":5000,"precio_invitado":8500,"cantidad_total":90}'
```

```powershell
curl.exe -s -X DELETE "$base/menus/11" -H $auth
```

### 6.5 Reservas — `/reservas`

```powershell
curl.exe -s "$base/reservas" -H $auth -H "Content-Type: application/json" -d '{"menu_id":12}'
```

```powershell
curl.exe -s "$base/reservas/mias" -H $auth
curl.exe -s "$base/reservas/mias?estado=RESERVADO" -H $auth
```

```powershell
curl.exe -s "$base/reservas" -H $auth
curl.exe -s "$base/reservas?fecha=2026-11-23&estado=PAGADO&tipo=APRENDIZ&saltar=0&limite=10" -H $auth
```

```powershell
curl.exe -s "$base/reservas/1" -H $auth
```

```powershell
curl.exe -s -X PATCH "$base/reservas/1/cancelar" -H $auth
```

```powershell
curl.exe -s -X PATCH "$base/reservas/1/pago" -H $auth -H "Content-Type: application/json" -d '{"estado":"PAGADO"}'
```

Estados usados: `RESERVADO`, `PENDIENTE` (instructor), `PAGADO`, `NO_PAGADO`, `CANCELADA`. Solo se puede reservar/cancelar de 7:00 a 21:00, hora de Colombia (UTC-5) (`hora_apertura`/`hora_cierre` del `.env`).

### 6.6 Cartera — `/cartera`

```powershell
curl.exe -s "$base/cartera" -H $auth
curl.exe -s "$base/cartera?solo_vencidas=true" -H $auth
```

```powershell
Conectar "instructor@gastrosena.com" "Instructor123"
curl.exe -s "$base/cartera/mi-cuenta" -H $auth
Conectar "encargado@gastrosena.com" "Encargado123"
```

```powershell
curl.exe -s "$base/cartera/2" -H $auth
```

```powershell
curl.exe -s "$base/cartera/2/pagos" -H $auth -H "Content-Type: application/json" -d '{"valor":2000,"metodo":"EFECTIVO","observacion":"Abono parcial"}'
```

Métodos de pago: `EFECTIVO`, `TRANSFERENCIA`, `NOMINA`.

### 6.7 Inventario — `/inventario`

```powershell
curl.exe -s "$base/inventario/materiales" -H $auth
curl.exe -s "$base/inventario/materiales?buscar=arroz&categoria=GRANO&estado=BAJO&activo=true&saltar=0&limite=10" -H $auth
```

```powershell
curl.exe -s "$base/inventario/materiales/1" -H $auth
```

```powershell
$codigo = "77" + (Get-Random -Minimum 1000000000 -Maximum 9999999999)
$cuerpo = @{ codigo_barras=$codigo; nombre="Arroz blanco"; categoria="GRANO"; unidad_medida="KG"; costo_unitario=4200; stock_inicial=20; stock_minimo=10 } | ConvertTo-Json
curl.exe -s "$base/inventario/materiales" -H $auth -H "Content-Type: application/json" -d $cuerpo
```

```powershell
curl.exe -s -X PUT "$base/inventario/materiales/1" -H $auth -H "Content-Type: application/json" -d '{"nombre":"Arroz blanco premium","costo_unitario":4500,"stock_minimo":15}'
```

```powershell
curl.exe -s -X DELETE "$base/inventario/materiales/1" -H $auth
```

```powershell
curl.exe -s "$base/inventario/movimientos" -H $auth -H "Content-Type: application/json" -d '{"material_id":1,"tipo":"ENTRADA","cantidad":10,"concepto":"Compra de reposicion"}'
```

```powershell
curl.exe -s "$base/inventario/kardex" -H $auth
curl.exe -s "$base/inventario/kardex?material_id=1&tipo=SALIDA&saltar=0&limite=10" -H $auth
```

Tipos de movimiento: `ENTRADA`, `SALIDA`, `MERMA`. Categorías: `PROTEINA`, `GRANO`, `VERDURA`, `FRUTA`, `LACTEO`, `ABARROTE`, `DESECHABLE`. Unidades: `KG`, `G`, `L`, `ML`, `UND`. Estados de stock: `BUENO`, `BAJO`, `CRITICO`, `VENCIENDO`.

### 6.8 Recetas — `/recetas` (solo encargado)

```powershell
curl.exe -s "$base/recetas" -H $auth
curl.exe -s "$base/recetas?buscar=pollo&activo=true&saltar=0&limite=10" -H $auth
```

```powershell
curl.exe -s "$base/recetas/1" -H $auth
```

```powershell
$cuerpo = @{ nombre="Nueva receta de pollo"; descripcion="Pollo con arroz"; precio_venta=5000; ingredientes=@(@{material_id=1; cantidad=0.12}, @{material_id=3; cantidad=0.15}) } | ConvertTo-Json -Depth 5
curl.exe -s "$base/recetas" -H $auth -H "Content-Type: application/json" -d $cuerpo
```

```powershell
$cuerpo = @{ nombre="Receta ajustada"; precio_venta=5500; ingredientes=@(@{material_id=1; cantidad=0.2}, @{material_id=9; cantidad=2}) } | ConvertTo-Json -Depth 5
curl.exe -s -X PUT "$base/recetas/1" -H $auth -H "Content-Type: application/json" -d $cuerpo
```

```powershell
curl.exe -s -X DELETE "$base/recetas/1" -H $auth
```

### 6.9 Sugerencias — `/sugerencias`

```powershell
curl.exe -s "$base/sugerencias" -H $auth -H "Content-Type: application/json" -d '{"asunto":"Mas opciones vegetarianas","mensaje":"Por favor incluir un menu vegetariano una vez por semana."}'
```

```powershell
curl.exe -s "$base/sugerencias/mias" -H $auth
```

```powershell
curl.exe -s "$base/sugerencias" -H $auth
curl.exe -s "$base/sugerencias?estado=PENDIENTE&saltar=0&limite=10" -H $auth
```

```powershell
curl.exe -s -X PATCH "$base/sugerencias/1/atender" -H $auth -H "Content-Type: application/json" -d '{"respuesta":"Gracias, lo tendremos en cuenta."}'
```

Estados: `PENDIENTE`, `ATENDIDA`.

### 6.10 Reportes — `/reportes` (solo encargado)

```powershell
curl.exe -s "$base/reportes/ventas" -H $auth
curl.exe -s "$base/reportes/ventas?periodo=dia" -H $auth
curl.exe -s "$base/reportes/ventas?periodo=semana&fecha=2026-11-23" -H $auth
curl.exe -s "$base/reportes/ventas?periodo=mes&fecha=2026-11-01" -H $auth
curl.exe -s "$base/reportes/ventas?periodo=anio&fecha=2026-01-01" -H $auth
```

```powershell
curl.exe -s "$base/reportes/indicadores" -H $auth
```

Periodos válidos: `dia`, `semana`, `mes`, `anio`.

---

## 7. Tabla rápida de URLs

53 operaciones en 36 rutas bajo `/api/v1` + `GET /` de salud = 54 operaciones. En los listados, `saltar` va desde 0 y `limite` entre 1 y 100.

| Método | Ruta | Rol |
|---|---|---|
| GET | `/` | público |
| POST | `/api/v1/autenticacion/ingresar` | público |
| POST | `/api/v1/autenticacion/renovar` | público |
| GET | `/api/v1/autenticacion/perfil` | autenticado |
| PUT | `/api/v1/autenticacion/contrasena` | autenticado |
| GET | `/api/v1/roles` | encargado |
| GET | `/api/v1/usuarios` | encargado |
| GET | `/api/v1/usuarios/{id}` | encargado |
| POST | `/api/v1/usuarios` | encargado |
| PUT | `/api/v1/usuarios/{id}` | encargado |
| DELETE | `/api/v1/usuarios/{id}` | encargado |
| PATCH | `/api/v1/usuarios/{id}/beneficiario` | encargado |
| GET | `/api/v1/fichas` | encargado |
| GET | `/api/v1/fichas/estadisticas` | encargado |
| GET | `/api/v1/fichas/{id}` | encargado |
| GET | `/api/v1/fichas/{id}/reservas` | encargado |
| POST | `/api/v1/fichas` | encargado |
| PUT | `/api/v1/fichas/{id}` | encargado |
| DELETE | `/api/v1/fichas/{id}` | encargado |
| GET | `/api/v1/menus/hoy` | autenticado |
| GET | `/api/v1/menus/proximos` | autenticado |
| GET | `/api/v1/menus` | encargado |
| GET | `/api/v1/menus/{id}` | autenticado |
| POST | `/api/v1/menus` | encargado |
| PUT | `/api/v1/menus/{id}` | encargado |
| DELETE | `/api/v1/menus/{id}` | encargado |
| POST | `/api/v1/reservas` | aprendiz, instructor, invitado |
| GET | `/api/v1/reservas/mias` | aprendiz, instructor, invitado |
| GET | `/api/v1/reservas` | encargado |
| GET | `/api/v1/reservas/{id}` | autenticado (propias o todas si encargado) |
| PATCH | `/api/v1/reservas/{id}/cancelar` | aprendiz, instructor, invitado |
| PATCH | `/api/v1/reservas/{id}/pago` | encargado |
| GET | `/api/v1/cartera` | encargado |
| GET | `/api/v1/cartera/mi-cuenta` | instructor |
| GET | `/api/v1/cartera/{id}` | encargado |
| POST | `/api/v1/cartera/{id}/pagos` | encargado |
| GET | `/api/v1/inventario/materiales` | encargado |
| GET | `/api/v1/inventario/materiales/{id}` | encargado |
| POST | `/api/v1/inventario/materiales` | encargado |
| PUT | `/api/v1/inventario/materiales/{id}` | encargado |
| DELETE | `/api/v1/inventario/materiales/{id}` | encargado |
| POST | `/api/v1/inventario/movimientos` | encargado |
| GET | `/api/v1/inventario/kardex` | encargado |
| GET | `/api/v1/recetas` | encargado |
| GET | `/api/v1/recetas/{id}` | encargado |
| POST | `/api/v1/recetas` | encargado |
| PUT | `/api/v1/recetas/{id}` | encargado |
| DELETE | `/api/v1/recetas/{id}` | encargado |
| POST | `/api/v1/sugerencias` | autenticado |
| GET | `/api/v1/sugerencias/mias` | autenticado |
| GET | `/api/v1/sugerencias` | encargado |
| PATCH | `/api/v1/sugerencias/{id}/atender` | encargado |
| GET | `/api/v1/reportes/ventas` | encargado |
| GET | `/api/v1/reportes/indicadores` | encargado |

---

## 8. Pruebas

```powershell
pytest -v
pytest tests\test_auth.py -v
pytest -k reserva -v
```

Las pruebas crean datos: mejor correrlas contra una base de prueba.

Postman / Newman:

```powershell
newman run docs\GastroSENA_API.postman_collection.json
```

La colección guarda los tokens sola y trae casos buenos y malos (401, 403, 404, 409, 422, 400).

---

## 9. Errores y solución rápida

| Código | Significado |
|---|---|
| 400 | Regla de negocio incumplida (menú agotado, horario, stock negativo, etc.) |
| 401 | Falta token, token inválido/vencido, cuenta desactivada o bloqueada, o contraseña cambiada después de emitir el token; al renovar también sale si la cuenta no está activa |
| 403 | El rol no tiene permiso; al iniciar sesión también sale si la cuenta está bloqueada o inactiva |
| 404 | El registro no existe |
| 409 | Valor repetido (correo, documento, ficha, menú del día, reserva duplicada...) |
| 422 | JSON inválido, campos con formato incorrecto o paginación fuera de rango (`saltar < 0`, `limite` fuera de 1..100). Los enums inválidos que revisa el servicio salen 400 |
| 500 | Error interno (el detalle técnico queda en la consola) |

Todas las respuestas de error tienen la forma `{"detalle": "..."}`.

Problemas comunes:

```powershell
Get-Process python | Stop-Process -Force
netstat -ano | findstr :8000
```

Si la API no arranca y dice "La base de datos está desactualizada; faltan: ...", ejecuta el paso 2 de la sección Base de datos (recrear o aplicar `04_auditoria.sql` y `05_compatibilidad.sql`) y vuelve a correr `uvicorn`. El error 500 genérico al iniciar sesión también aparecía por esa causa: la columna esperada era `usuarios.contrasena` y la base antigua tenía `password_hash`.
