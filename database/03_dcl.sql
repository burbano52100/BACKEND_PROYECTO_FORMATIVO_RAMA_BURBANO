-- Script para crear el usuario de la base de datos que usa la API
-- La API no se conecta con postgres sino con este usuario que tiene menos permisos (es más seguro)
-- Se ejecuta con el usuario postgres después de 01_ddl.sql y 02_dml.sql
-- OJO: la contraseña tiene que ser la misma que está en bd_contrasena del archivo .env

-- Creo el usuario de la API (si ya existe sale un error en esta línea, pero no pasa nada)
CREATE USER api_gastrosena WITH PASSWORD 'CambieEstaClave2026';

-- Le doy permiso para conectarse a la base de datos
GRANT CONNECT ON DATABASE gastrosena_db TO api_gastrosena;
-- Le doy permiso para usar el esquema gastrosena (pero no para crear tablas)
GRANT USAGE ON SCHEMA gastrosena TO api_gastrosena;

-- Permisos de cada tabla (solo lo que la API necesita)
-- Los roles solo se pueden leer
GRANT SELECT ON gastrosena.roles TO api_gastrosena;
-- Los usuarios no se borran, solo se desactivan
GRANT SELECT, INSERT, UPDATE ON gastrosena.usuarios TO api_gastrosena;
-- Las fichas se pueden borrar si no tienen aprendices
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.fichas TO api_gastrosena;
-- Los menús se pueden borrar si no tienen reservas
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.menus TO api_gastrosena;
-- Las reservas no se borran, solo se cancelan
GRANT SELECT, INSERT, UPDATE ON gastrosena.reservas TO api_gastrosena;
-- Los pagos no se cambian ni se borran
GRANT SELECT, INSERT ON gastrosena.pagos_instructor TO api_gastrosena;
-- Los materiales se pueden borrar si no tienen historial
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.materiales TO api_gastrosena;
-- El kardex no se cambia ni se borra
GRANT SELECT, INSERT ON gastrosena.movimientos_inventario TO api_gastrosena;
-- Las recetas tienen CRUD completo
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.recetas TO api_gastrosena;
-- Los ingredientes se borran cuando se cambia o se borra la receta
GRANT SELECT, INSERT, UPDATE, DELETE ON gastrosena.receta_ingredientes TO api_gastrosena;
-- Las sugerencias no se borran, solo se atienden
GRANT SELECT, INSERT, UPDATE ON gastrosena.sugerencias TO api_gastrosena;

-- Permiso para usar las secuencias de los SERIAL (sin esto no se pueden crear registros nuevos)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gastrosena TO api_gastrosena;
