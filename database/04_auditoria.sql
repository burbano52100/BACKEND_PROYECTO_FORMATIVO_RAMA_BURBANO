-- Script para agregar la auditoría a una base de datos que ya existía
-- SOLO hace falta si la base gastrosena_db se creó ANTES de que 01_ddl.sql tuviera las columnas de auditoría.
-- Si la base se crea desde cero con 01_ddl.sql, 02_dml.sql y 03_dcl.sql, este archivo no hace falta.
-- No borra nada: solo agrega las columnas que faltan. Se puede ejecutar varias veces sin dañar nada.
-- Se ejecuta con el usuario postgres conectado a gastrosena_db:
--   psql -U postgres -d gastrosena_db -f database\04_auditoria.sql

-- Le digo a PostgreSQL que el archivo tiene tildes y eñes
SET client_encoding = 'UTF8';
-- Trabajo dentro del esquema gastrosena
SET search_path TO gastrosena;

-- Columnas de auditoría de cada tabla principal:
--   creado_por          id del usuario que creó el registro
--   modificado_por      id del usuario que lo modificó por última vez
--   fecha_modificacion  fecha y hora de la última modificación
ALTER TABLE fichas ADD COLUMN IF NOT EXISTS creado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE fichas ADD COLUMN IF NOT EXISTS modificado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE fichas ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS creado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS modificado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;

ALTER TABLE menus ADD COLUMN IF NOT EXISTS creado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE menus ADD COLUMN IF NOT EXISTS modificado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE menus ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;

ALTER TABLE reservas ADD COLUMN IF NOT EXISTS creado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE reservas ADD COLUMN IF NOT EXISTS modificado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE reservas ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;

ALTER TABLE pagos_instructor ADD COLUMN IF NOT EXISTS creado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE pagos_instructor ADD COLUMN IF NOT EXISTS modificado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE pagos_instructor ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;

ALTER TABLE materiales ADD COLUMN IF NOT EXISTS creado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE materiales ADD COLUMN IF NOT EXISTS modificado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE materiales ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;

ALTER TABLE recetas ADD COLUMN IF NOT EXISTS creado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE recetas ADD COLUMN IF NOT EXISTS modificado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE recetas ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;

ALTER TABLE sugerencias ADD COLUMN IF NOT EXISTS creado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE sugerencias ADD COLUMN IF NOT EXISTS modificado_por INTEGER REFERENCES usuarios(id);
ALTER TABLE sugerencias ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;

-- Los registros que ya existían quedan como creados por la encargada (id 1), igual que en 02_dml.sql
UPDATE fichas SET creado_por = 1 WHERE creado_por IS NULL;
UPDATE usuarios SET creado_por = 1 WHERE creado_por IS NULL AND id <> 1;
UPDATE menus SET creado_por = 1 WHERE creado_por IS NULL;
UPDATE reservas SET creado_por = usuario_id WHERE creado_por IS NULL;
UPDATE pagos_instructor SET creado_por = 1 WHERE creado_por IS NULL;
UPDATE materiales SET creado_por = 1 WHERE creado_por IS NULL;
UPDATE recetas SET creado_por = 1 WHERE creado_por IS NULL;
UPDATE sugerencias SET creado_por = usuario_id WHERE creado_por IS NULL;
