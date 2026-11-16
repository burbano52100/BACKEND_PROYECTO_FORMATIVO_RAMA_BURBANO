-- =============================================================
-- GastroSENA - DCL: rol de conexión de la API con privilegios mínimos
-- sobre el esquema del proyecto (diferente del superusuario postgres).
-- Ejecutar como postgres después de 01_ddl.sql y 02_dml.sql:
--   psql -U postgres -d gastrosena_db -f database/03_dcl.sql
--
-- Cambie la contraseña: debe ser la misma de DB_PASSWORD en el .env.
-- =============================================================

-- El texto de este archivo viene en UTF-8
SET client_encoding = 'UTF8';

-- Crea el rol solo si no existe. Un rol nuevo no es superusuario,
-- no crea bases de datos ni otros roles.
-- DO $$ ... $$ ejecuta un bloque de código PL/pgSQL (el lenguaje de programación de PostgreSQL)
DO $$
-- Inicio del bloque
BEGIN
    -- Si en el catálogo pg_roles NO existe un rol llamado api_gastrosena...
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_gastrosena') THEN
        -- ...lo crea con permiso para iniciar sesión (LOGIN) y esta contraseña
        CREATE ROLE api_gastrosena LOGIN PASSWORD 'CambieEstaClave2026';
    -- Fin del IF
    END IF;
-- Fin del bloque
END
-- Cierra el bloque DO
$$;

-- Permiso para conectarse a la base de datos actual
-- Otro bloque PL/pgSQL (se usa porque el nombre de la base de datos no se escribe fijo)
DO $$
-- Inicio del bloque
BEGIN
    -- Arma y ejecuta "GRANT CONNECT ON DATABASE gastrosena_db TO api_gastrosena"; %I pone el nombre de la base actual
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO api_gastrosena', current_database());
-- Fin del bloque
END
-- Cierra el bloque DO
$$;

-- Usa el esquema, pero no puede crear objetos en él
-- USAGE permite ver las tablas del esquema; sin CREATE no puede crear tablas nuevas
GRANT USAGE ON SCHEMA gastrosena TO api_gastrosena;

-- Cada tabla recibe solo lo que la API necesita
GRANT SELECT                         ON gastrosena.roles                  TO api_gastrosena;  -- los roles solo se leen
GRANT SELECT, INSERT, UPDATE         ON gastrosena.usuarios               TO api_gastrosena;  -- se desactivan, no se borran
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.fichas                 TO api_gastrosena;  -- se borran si no tienen aprendices
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.menus                  TO api_gastrosena;  -- se borran si no tienen reservas
GRANT SELECT, INSERT, UPDATE         ON gastrosena.reservas               TO api_gastrosena;  -- se cancelan, no se borran
GRANT SELECT, INSERT                 ON gastrosena.pagos_instructor       TO api_gastrosena;  -- inmutables
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.materiales             TO api_gastrosena;  -- se borran si no tienen historial
GRANT SELECT, INSERT                 ON gastrosena.movimientos_inventario TO api_gastrosena;  -- kardex inmutable
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.recetas                TO api_gastrosena;  -- CRUD completo
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.receta_ingredientes    TO api_gastrosena;  -- la fórmula se reemplaza
GRANT SELECT, INSERT, UPDATE         ON gastrosena.sugerencias            TO api_gastrosena;  -- se atienden, no se borran

-- Busca las tablas en el esquema del proyecto sin escribir "gastrosena."
-- Cada vez que api_gastrosena se conecte, su search_path será gastrosena
ALTER ROLE api_gastrosena SET search_path TO gastrosena;
