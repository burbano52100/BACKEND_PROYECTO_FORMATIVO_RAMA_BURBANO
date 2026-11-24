-- Migra una base creada con el esquema antiguo (password_hash / creado_en /
-- actualizado_por / actualizado_en / atendida_por) al esquema que usa hoy la API.
-- No borra datos: solo renombra columnas y agrega las que faltaban.
-- Se puede ejecutar varias veces.

SET client_encoding = 'UTF8';
SET search_path TO gastrosena;

BEGIN;

DO $$
DECLARE
    pareja text[];
    parejas text[][] := ARRAY[
        ['usuarios', 'password_hash', 'contrasena'],
        ['usuarios', 'creado_en', 'fecha_creacion'],
        ['usuarios', 'actualizado_por', 'modificado_por'],
        ['usuarios', 'actualizado_en', 'fecha_modificacion'],
        ['fichas', 'creado_en', 'fecha_creacion'],
        ['fichas', 'actualizado_por', 'modificado_por'],
        ['fichas', 'actualizado_en', 'fecha_modificacion'],
        ['menus', 'creado_en', 'fecha_creacion'],
        ['menus', 'actualizado_por', 'modificado_por'],
        ['menus', 'actualizado_en', 'fecha_modificacion'],
        ['reservas', 'creado_en', 'fecha_creacion'],
        ['reservas', 'actualizado_por', 'modificado_por'],
        ['reservas', 'actualizado_en', 'fecha_modificacion'],
        ['pagos_instructor', 'creado_en', 'fecha_pago'],
        ['pagos_instructor', 'actualizado_por', 'modificado_por'],
        ['pagos_instructor', 'actualizado_en', 'fecha_modificacion'],
        ['materiales', 'creado_en', 'fecha_creacion'],
        ['materiales', 'actualizado_por', 'modificado_por'],
        ['materiales', 'actualizado_en', 'fecha_modificacion'],
        ['recetas', 'creado_en', 'fecha_creacion'],
        ['recetas', 'actualizado_por', 'modificado_por'],
        ['recetas', 'actualizado_en', 'fecha_modificacion'],
        ['sugerencias', 'creado_en', 'fecha_creacion'],
        ['sugerencias', 'atendida_por', 'modificado_por'],
        ['sugerencias', 'atendida_en', 'fecha_respuesta'],
        ['movimientos_inventario', 'creado_por', 'usuario_id'],
        ['movimientos_inventario', 'creado_en', 'fecha']
    ];
BEGIN
    FOREACH pareja SLICE 1 IN ARRAY parejas LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'gastrosena' AND table_name = pareja[1] AND column_name = pareja[2]
        ) AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'gastrosena' AND table_name = pareja[1] AND column_name = pareja[3]
        ) THEN
            EXECUTE format('ALTER TABLE %I RENAME COLUMN %I TO %I', pareja[1], pareja[2], pareja[3]);
        END IF;
    END LOOP;
END;
$$;

ALTER TABLE sugerencias ADD COLUMN IF NOT EXISTS fecha_modificacion TIMESTAMP;
UPDATE sugerencias SET fecha_modificacion = fecha_respuesta WHERE fecha_modificacion IS NULL;

COMMIT;
