-- =============================================================
-- GastroSENA - Sistema de Almuerzos (API EA4)
-- DDL: esquema propio del proyecto (no se usa public), tablas,
-- llaves primarias y foráneas, NOT NULL, UNIQUE, CHECK, valores
-- por defecto e índices en las columnas de búsqueda frecuente.
--
-- Ejecutar como superusuario (postgres) conectado a la base de datos:
--   psql -U postgres -c "CREATE DATABASE gastrosena_db"
--   psql -U postgres -d gastrosena_db -f database/01_ddl.sql
--
-- CUIDADO: DROP SCHEMA ... CASCADE borra el esquema y todos sus datos.
-- =============================================================

-- El archivo está en UTF-8; en Windows psql usa otra codificación por defecto.
-- Le indica a PostgreSQL que el texto de este archivo viene en UTF-8 (tildes y eñes)
SET client_encoding = 'UTF8';

-- Borra el esquema si ya existía, con todas sus tablas y datos (CASCADE)
DROP SCHEMA IF EXISTS gastrosena CASCADE;
-- Crea el esquema del proyecto (una "carpeta" dentro de la base de datos)
CREATE SCHEMA gastrosena;
-- Desde aquí, las tablas se crean dentro de gastrosena sin escribir "gastrosena."
SET search_path TO gastrosena;

-- -------------------------------------------------------------
-- Roles: encargado, instructor, aprendiz e invitado
-- -------------------------------------------------------------
-- Crea la tabla roles
CREATE TABLE roles (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria; PostgreSQL genera el número (1, 2, 3...)
    nombre      VARCHAR(20)  NOT NULL UNIQUE  -- Nombre obligatorio y sin repetirse
                CHECK (nombre IN ('encargado', 'instructor', 'aprendiz', 'invitado')),  -- Solo acepta estos 4 valores
    descripcion VARCHAR(150)  -- Descripción opcional
);  -- Fin de la tabla roles

-- -------------------------------------------------------------
-- Fichas (grupos de formación). El vocero es solo un dato informativo.
-- La llave foránea de auditoría hacia usuarios se agrega más abajo.
-- -------------------------------------------------------------
-- Crea la tabla fichas
CREATE TABLE fichas (
    id                   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    codigo               VARCHAR(10)  NOT NULL UNIQUE CHECK (codigo ~ '^[0-9]{6,10}$'),  -- Número de ficha único de 6 a 10 dígitos (~ = expresión regular)
    programa             VARCHAR(120) NOT NULL,  -- Programa de formación (obligatorio)
    jornada              VARCHAR(15)  NOT NULL  -- Jornada (obligatoria)...
                         CHECK (jornada IN ('DIURNA', 'NOCTURNA', 'MIXTA', 'FIN_DE_SEMANA')),  -- ...solo uno de estos valores
    vocero               VARCHAR(100),  -- Vocero del grupo (opcional)
    cantidad_estudiantes INTEGER      NOT NULL DEFAULT 0 CHECK (cantidad_estudiantes BETWEEN 0 AND 60),  -- Entre 0 y 60; 0 si no se indica
    activo               BOOLEAN      NOT NULL DEFAULT TRUE,  -- FALSE = ficha desactivada (borrado lógico)
    creado_por           INTEGER,  -- Auditoría: usuario que la creó (su llave foránea se agrega más abajo)
    creado_en            TIMESTAMPTZ  NOT NULL DEFAULT now(),  -- Auditoría: fecha y hora de creación (now() = ahora)
    actualizado_por      INTEGER,  -- Auditoría: usuario que la modificó
    actualizado_en       TIMESTAMPTZ  -- Auditoría: fecha y hora de la última modificación
);  -- Fin de la tabla fichas

-- -------------------------------------------------------------
-- Usuarios: contraseña cifrada con bcrypt; bloqueo por intentos fallidos
-- -------------------------------------------------------------
-- Crea la tabla usuarios
CREATE TABLE usuarios (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    documento         VARCHAR(10)  NOT NULL UNIQUE CHECK (documento ~ '^[0-9]{6,10}$'),  -- Documento único de 6 a 10 dígitos
    nombre            VARCHAR(100) NOT NULL,  -- Nombre completo
    correo            VARCHAR(120) NOT NULL UNIQUE  -- Correo único (con él se inicia sesión)...
                      CHECK (correo ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),  -- ...con formato texto@texto.texto (~* ignora mayúsculas)
    telefono          VARCHAR(10)  CHECK (telefono ~ '^[0-9]{10}$'),  -- Teléfono opcional de 10 dígitos
    password_hash     VARCHAR(60)  NOT NULL,  -- Contraseña cifrada con bcrypt (60 caracteres)
    rol_id            INTEGER      NOT NULL REFERENCES roles (id),  -- Llave foránea: el rol debe existir en roles
    ficha_id          INTEGER      REFERENCES fichas (id),  -- Llave foránea opcional: la ficha del aprendiz
    es_beneficiario   BOOLEAN      NOT NULL DEFAULT FALSE,  -- TRUE = almuerzo a $0
    activo            BOOLEAN      NOT NULL DEFAULT TRUE,  -- FALSE = cuenta desactivada
    intentos_fallidos SMALLINT     NOT NULL DEFAULT 0 CHECK (intentos_fallidos >= 0),  -- Intentos fallidos de login (nunca negativo)
    bloqueado_hasta   TIMESTAMPTZ,  -- Hasta cuándo está bloqueada la cuenta (NULL = no bloqueada)
    creado_por        INTEGER      REFERENCES usuarios (id),  -- Auditoría: quién lo creó (otro usuario de esta misma tabla)
    creado_en         TIMESTAMPTZ  NOT NULL DEFAULT now(),  -- Auditoría: cuándo se creó
    actualizado_por   INTEGER      REFERENCES usuarios (id),  -- Auditoría: quién lo modificó
    actualizado_en    TIMESTAMPTZ  -- Auditoría: cuándo se modificó
);  -- Fin de la tabla usuarios

-- Índice para buscar rápido los usuarios por rol
CREATE INDEX idx_usuarios_rol   ON usuarios (rol_id);
-- Índice para buscar rápido los usuarios por ficha
CREATE INDEX idx_usuarios_ficha ON usuarios (ficha_id);

-- Ahora que existe la tabla usuarios, se agregan las llaves foráneas de auditoría de fichas
ALTER TABLE fichas
    ADD CONSTRAINT fk_fichas_creado_por      FOREIGN KEY (creado_por)      REFERENCES usuarios (id),  -- creado_por debe ser un usuario
    ADD CONSTRAINT fk_fichas_actualizado_por FOREIGN KEY (actualizado_por) REFERENCES usuarios (id);  -- actualizado_por también

-- -------------------------------------------------------------
-- Menú del Día: un solo menú por fecha; el cupo se descuenta al reservar
-- -------------------------------------------------------------
-- Crea la tabla menus
CREATE TABLE menus (
    id                  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    fecha               DATE          NOT NULL UNIQUE,  -- Fecha del menú; UNIQUE = un solo menú por día
    nombre              VARCHAR(100)  NOT NULL,  -- Nombre del plato
    descripcion         VARCHAR(500)  NOT NULL,  -- Qué incluye el almuerzo
    precio_aprendiz     NUMERIC(10,2) NOT NULL CHECK (precio_aprendiz >= 0),  -- Precio para aprendices (decimal exacto, no negativo)
    precio_invitado     NUMERIC(10,2) NOT NULL CHECK (precio_invitado >= 0),  -- Precio para invitados
    cantidad_total      INTEGER       NOT NULL CHECK (cantidad_total > 0),  -- Cupo total (mayor que 0)
    cantidad_disponible INTEGER       NOT NULL CHECK (cantidad_disponible >= 0),  -- Cupo restante (nunca negativo)
    activo              BOOLEAN       NOT NULL DEFAULT TRUE,  -- FALSE = menú desactivado
    creado_por          INTEGER       NOT NULL REFERENCES usuarios (id),  -- Auditoría: encargado que lo creó
    creado_en           TIMESTAMPTZ   NOT NULL DEFAULT now(),  -- Auditoría: cuándo
    actualizado_por     INTEGER       REFERENCES usuarios (id),  -- Auditoría: quién lo modificó
    actualizado_en      TIMESTAMPTZ,  -- Auditoría: cuándo se modificó
    CONSTRAINT ck_menus_cupo CHECK (cantidad_disponible <= cantidad_total)  -- El disponible nunca supera el total
);  -- Fin de la tabla menus

-- -------------------------------------------------------------
-- Reservas y compras de almuerzo (consumos)
-- -------------------------------------------------------------
-- Crea la tabla reservas
CREATE TABLE reservas (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    menu_id         INTEGER       NOT NULL REFERENCES menus (id),  -- Llave foránea: menú reservado
    usuario_id      INTEGER       NOT NULL REFERENCES usuarios (id),  -- Llave foránea: persona que reservó
    tipo            VARCHAR(15)   NOT NULL  -- Tipo de reserva...
                    CHECK (tipo IN ('APRENDIZ', 'BENEFICIARIO', 'INSTRUCTOR', 'INVITADO')),  -- ...solo estos 4 valores
    valor           NUMERIC(10,2) NOT NULL CHECK (valor >= 0),  -- Valor cobrado (0 para beneficiarios)
    estado          VARCHAR(10)   NOT NULL DEFAULT 'RESERVADO'  -- Estado; RESERVADO si no se indica...
                    CHECK (estado IN ('RESERVADO', 'PENDIENTE', 'PAGADO', 'NO_PAGADO', 'CANCELADA')),  -- ...solo estos 5 valores
    creado_por      INTEGER       NOT NULL REFERENCES usuarios (id),  -- Auditoría: quién reservó
    creado_en       TIMESTAMPTZ   NOT NULL DEFAULT now(),  -- Auditoría: cuándo
    actualizado_por INTEGER       REFERENCES usuarios (id),  -- Auditoría: quién marcó el pago o canceló
    actualizado_en  TIMESTAMPTZ  -- Auditoría: cuándo
);  -- Fin de la tabla reservas

-- Una sola reserva vigente por persona y por menú (las canceladas no cuentan)
-- Índice único PARCIAL: solo aplica a las filas cuyo estado no es CANCELADA
CREATE UNIQUE INDEX uq_reservas_menu_usuario ON reservas (menu_id, usuario_id) WHERE estado <> 'CANCELADA';
-- Índice para buscar las reservas de una persona
CREATE INDEX idx_reservas_usuario ON reservas (usuario_id);
-- Índice para filtrar por estado
CREATE INDEX idx_reservas_estado  ON reservas (estado);

-- -------------------------------------------------------------
-- Pagos de la cuenta mensual de los instructores (inmutables)
-- -------------------------------------------------------------
-- Crea la tabla pagos_instructor
CREATE TABLE pagos_instructor (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    instructor_id INTEGER       NOT NULL REFERENCES usuarios (id),  -- Llave foránea: instructor que paga
    valor         NUMERIC(12,2) NOT NULL CHECK (valor > 0),  -- Valor pagado (mayor que 0)
    metodo        VARCHAR(15)   NOT NULL CHECK (metodo IN ('EFECTIVO', 'TRANSFERENCIA', 'NOMINA')),  -- Método de pago permitido
    observacion   VARCHAR(255),  -- Nota opcional
    creado_por    INTEGER       NOT NULL REFERENCES usuarios (id),  -- Auditoría: encargado que lo registró
    creado_en     TIMESTAMPTZ   NOT NULL DEFAULT now()  -- Auditoría: cuándo
);  -- Fin de la tabla pagos_instructor

-- Índice para buscar los pagos de un instructor
CREATE INDEX idx_pagos_instructor ON pagos_instructor (instructor_id);

-- -------------------------------------------------------------
-- Inventario: materiales e ingredientes de la cocina
-- El stock solo cambia mediante movimientos (kardex)
-- -------------------------------------------------------------
-- Crea la tabla materiales
CREATE TABLE materiales (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    codigo_barras     VARCHAR(14)   NOT NULL UNIQUE CHECK (codigo_barras ~ '^[0-9]{8,14}$'),  -- Código de barras único de 8 a 14 dígitos
    nombre            VARCHAR(100)  NOT NULL,  -- Nombre del material
    categoria         VARCHAR(15)   NOT NULL  -- Categoría...
                      CHECK (categoria IN ('PROTEINA', 'GRANO', 'VERDURA', 'FRUTA', 'LACTEO', 'ABARROTE', 'DESECHABLE')),  -- ...solo estos valores
    unidad_medida     VARCHAR(5)    NOT NULL CHECK (unidad_medida IN ('KG', 'G', 'L', 'ML', 'UND')),  -- Unidad permitida
    costo_unitario    NUMERIC(12,2) NOT NULL CHECK (costo_unitario > 0),  -- Costo de una unidad (mayor que 0)
    stock             NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (stock >= 0),  -- Cantidad disponible con 3 decimales (nunca negativa)
    stock_minimo      NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),  -- Cantidad mínima deseada
    fecha_vencimiento DATE,  -- Vencimiento (opcional)
    activo            BOOLEAN       NOT NULL DEFAULT TRUE,  -- FALSE = material desactivado
    creado_por        INTEGER       NOT NULL REFERENCES usuarios (id),  -- Auditoría: quién lo creó
    creado_en         TIMESTAMPTZ   NOT NULL DEFAULT now(),  -- Auditoría: cuándo
    actualizado_por   INTEGER       REFERENCES usuarios (id),  -- Auditoría: quién lo modificó
    actualizado_en    TIMESTAMPTZ  -- Auditoría: cuándo se modificó
);  -- Fin de la tabla materiales

-- Índice sobre el nombre en minúsculas (búsquedas sin importar mayúsculas)
CREATE INDEX idx_materiales_nombre    ON materiales (lower(nombre));
-- Índice para filtrar por categoría
CREATE INDEX idx_materiales_categoria ON materiales (categoria);

-- Kardex: cada fila guarda el saldo resultante; no se edita ni se borra
-- Crea la tabla movimientos_inventario
CREATE TABLE movimientos_inventario (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    material_id INTEGER       NOT NULL REFERENCES materiales (id),  -- Llave foránea: material afectado
    tipo        VARCHAR(10)   NOT NULL CHECK (tipo IN ('ENTRADA', 'SALIDA', 'MERMA')),  -- Tipo de movimiento permitido
    cantidad    NUMERIC(12,3) NOT NULL CHECK (cantidad > 0),  -- Cantidad movida (mayor que 0)
    saldo       NUMERIC(12,3) NOT NULL CHECK (saldo >= 0),  -- Stock que quedó después (nunca negativo)
    concepto    VARCHAR(255)  NOT NULL,  -- Motivo del movimiento
    creado_por  INTEGER       NOT NULL REFERENCES usuarios (id),  -- Responsable
    creado_en   TIMESTAMPTZ   NOT NULL DEFAULT now()  -- Fecha y hora
);  -- Fin de la tabla movimientos_inventario

-- Índice para consultar el kardex de un material ordenado por fecha
CREATE INDEX idx_movimientos_material_fecha ON movimientos_inventario (material_id, creado_en);
-- Índice para filtrar por tipo (por ejemplo, solo mermas)
CREATE INDEX idx_movimientos_tipo           ON movimientos_inventario (tipo);

-- -------------------------------------------------------------
-- Recetas (platos) y su fórmula de ingredientes
-- -------------------------------------------------------------
-- Crea la tabla recetas
CREATE TABLE recetas (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    nombre          VARCHAR(100)  NOT NULL UNIQUE,  -- Nombre único del plato
    descripcion     VARCHAR(500),  -- Descripción opcional
    precio_venta    NUMERIC(10,2) NOT NULL CHECK (precio_venta > 0),  -- Precio de venta (mayor que 0)
    activo          BOOLEAN       NOT NULL DEFAULT TRUE,  -- FALSE = receta inactiva
    creado_por      INTEGER       NOT NULL REFERENCES usuarios (id),  -- Auditoría: quién la creó
    creado_en       TIMESTAMPTZ   NOT NULL DEFAULT now(),  -- Auditoría: cuándo
    actualizado_por INTEGER       REFERENCES usuarios (id),  -- Auditoría: quién la modificó
    actualizado_en  TIMESTAMPTZ  -- Auditoría: cuándo se modificó
);  -- Fin de la tabla recetas

-- Crea la tabla receta_ingredientes (la fórmula de cada plato)
CREATE TABLE receta_ingredientes (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    receta_id   INTEGER       NOT NULL REFERENCES recetas (id) ON DELETE CASCADE,  -- Si se borra la receta, se borran sus ingredientes
    material_id INTEGER       NOT NULL REFERENCES materiales (id),  -- Llave foránea: material usado
    cantidad    NUMERIC(12,3) NOT NULL CHECK (cantidad > 0),  -- Cantidad por plato (mayor que 0)
    CONSTRAINT uq_receta_material UNIQUE (receta_id, material_id)  -- Un material no se repite en la misma receta
);  -- Fin de la tabla receta_ingredientes

-- Índice para saber rápido en qué recetas se usa un material
CREATE INDEX idx_receta_ingredientes_material ON receta_ingredientes (material_id);

-- -------------------------------------------------------------
-- Buzón de sugerencias
-- -------------------------------------------------------------
-- Crea la tabla sugerencias
CREATE TABLE sugerencias (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- Llave primaria autogenerada
    usuario_id   INTEGER      NOT NULL REFERENCES usuarios (id),  -- Llave foránea: quién la envió
    asunto       VARCHAR(100) NOT NULL,  -- Tema
    mensaje      VARCHAR(500) NOT NULL,  -- Texto (máximo 500 caracteres)
    estado       VARCHAR(10)  NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'ATENDIDA')),  -- PENDIENTE por defecto
    respuesta    VARCHAR(500),  -- Respuesta del encargado (opcional)
    atendida_por INTEGER      REFERENCES usuarios (id),  -- Encargado que la atendió
    atendida_en  TIMESTAMPTZ,  -- Cuándo se atendió
    creado_en    TIMESTAMPTZ  NOT NULL DEFAULT now()  -- Cuándo se envió
);  -- Fin de la tabla sugerencias

-- Índice para filtrar por estado
CREATE INDEX idx_sugerencias_estado ON sugerencias (estado);

-- Diccionario de datos (anexo 5)
-- COMMENT ON guarda una descripción dentro de PostgreSQL (se ve en pgAdmin o DBeaver)
COMMENT ON SCHEMA gastrosena IS 'GastroSENA: reserva, venta y control de almuerzos del Tecnoparque Yamboró';  -- Descripción del esquema
COMMENT ON TABLE roles                  IS 'Tipos de cuenta: encargado, instructor, aprendiz e invitado';  -- Descripción de roles
COMMENT ON TABLE fichas                 IS 'Grupos de formación del SENA';  -- Descripción de fichas
COMMENT ON TABLE usuarios               IS 'Cuentas que inician sesión en la API';  -- Descripción de usuarios
COMMENT ON TABLE menus                  IS 'Menú del Día con precios diferenciados y cupo';  -- Descripción de menus
COMMENT ON TABLE reservas               IS 'Reservas de aprendices, consumos de instructores y compras de invitados';  -- Descripción de reservas
COMMENT ON TABLE pagos_instructor       IS 'Pagos registrados por el Encargado a la cuenta mensual de un instructor';  -- Descripción de pagos_instructor
COMMENT ON TABLE materiales             IS 'Materiales e ingredientes del inventario de la cocina';  -- Descripción de materiales
COMMENT ON TABLE movimientos_inventario IS 'Kardex: entradas, salidas y mermas con su saldo';  -- Descripción del kardex
COMMENT ON TABLE recetas                IS 'Platos con precio de venta';  -- Descripción de recetas
COMMENT ON TABLE receta_ingredientes    IS 'Fórmula de cada receta: ingrediente y cantidad por plato';  -- Descripción de receta_ingredientes
COMMENT ON TABLE sugerencias            IS 'Buzón de sugerencias de todos los roles';  -- Descripción de sugerencias
COMMENT ON COLUMN usuarios.es_beneficiario IS 'Aprendiz que recibe el almuerzo sin costo';  -- Descripción de la columna es_beneficiario
COMMENT ON COLUMN reservas.estado          IS 'RESERVADO, PENDIENTE (cuenta mensual), PAGADO, NO_PAGADO o CANCELADA';  -- Descripción de la columna estado
COMMENT ON COLUMN movimientos_inventario.saldo IS 'Stock del material después del movimiento';  -- Descripción de la columna saldo
