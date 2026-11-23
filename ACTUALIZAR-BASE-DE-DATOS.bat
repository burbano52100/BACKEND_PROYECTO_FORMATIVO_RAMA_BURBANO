@echo off
setlocal EnableExtensions
title Actualizar la base de datos de GastroSENA
cd /d "%~dp0"

rem Este archivo le agrega a la base gastrosena_db las columnas de auditoria
rem (quien creo y quien modifico cada registro) sin borrar ningun dato.
rem Solo hace falta una vez, si la base se creo antes de que existiera la auditoria.
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
echo  Ahora se ejecuta database\04_auditoria.sql en la base gastrosena_db.
echo  Escriba la contrasena del usuario postgres cuando la pida (no se ve al escribir).
echo.
set "PGCLIENTENCODING=UTF8"
"%PSQL%" -h localhost -U postgres -d gastrosena_db -v ON_ERROR_STOP=1 -q -f "%~dp0database\04_auditoria.sql"
if errorlevel 1 goto :error

echo.
echo  ============================================================
echo   LISTO. La base de datos ya tiene la auditoria.
echo   Vuelva a encender la API (o INICIAR-PAGINA.bat).
echo  ============================================================
echo.
if /i not "%~1"=="silencioso" pause
exit /b 0

:sin_psql
echo.
echo  ERROR: no encontre psql. Abra pgAdmin, conectese a gastrosena_db,
echo  abra database\04_auditoria.sql en el Query Tool y ejecutelo.
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
