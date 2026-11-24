@echo off
setlocal EnableExtensions
title Actualizar la base de datos de GastroSENA
cd /d "%~dp0"

rem Este archivo actualiza una base antigua sin borrar datos: agrega la auditoria
rem (quien creo y quien modifico cada registro) y renombra las columnas viejas
rem (password_hash, creado_en, actualizado_*) a las que usa el codigo actual.
rem Se puede ejecutar varias veces sin danar nada.

echo.
echo  Buscando psql (el programa de consola de PostgreSQL)...
set "PSQL="
where psql >nul 2>nul
if not errorlevel 1 set "PSQL=psql"
if not defined PSQL for /d %%D in ("C:\Program Files\PostgreSQL\*") do if exist "%%D\bin\psql.exe" set "PSQL=%%D\bin\psql.exe"
if not defined PSQL goto :sin_psql
echo  Usando: %PSQL%

echo.
echo  Ahora se ejecutan database\04_auditoria.sql y database\05_compatibilidad.sql en gastrosena_db.
echo  Escriba la contrasena del usuario postgres cuando la pida (no se ve al escribir).
echo.
set "PGCLIENTENCODING=UTF8"
"%PSQL%" -h localhost -U postgres -d gastrosena_db -v ON_ERROR_STOP=1 -q -f "%~dp0database\04_auditoria.sql"
if errorlevel 1 goto :error
"%PSQL%" -h localhost -U postgres -d gastrosena_db -v ON_ERROR_STOP=1 -q -f "%~dp0database\05_compatibilidad.sql"
if errorlevel 1 goto :error

echo.
echo  ============================================================
echo   LISTO. La base de datos ya tiene la auditoria y las columnas actuales.
echo   Vuelva a encender la API (o INICIAR-PAGINA.bat).
echo  ============================================================
echo.
if /i not "%~1"=="silencioso" pause
exit /b 0

:sin_psql
echo.
echo  ERROR: no encontre psql. Abra pgAdmin, conectese a gastrosena_db,
echo  abra database\04_auditoria.sql y database\05_compatibilidad.sql en el Query Tool y ejecutelos.
echo.
if /i not "%~1"=="silencioso" pause
exit /b 1

:error
echo.
echo  ERROR: no se pudo actualizar la base. Revise la contrasena de postgres
echo  y que PostgreSQL este encendido con la base gastrosena_db.
echo.
if /i not "%~1"=="silencioso" pause
exit /b 1
