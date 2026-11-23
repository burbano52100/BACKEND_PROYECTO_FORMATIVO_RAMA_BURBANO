-- Script para crear las tablas de GastroSENA
-- Antes de ejecutarlo hay que crear la base de datos: CREATE DATABASE gastrosena_db;
-- Después se ejecuta este archivo conectado a gastrosena_db (en pgAdmin con el Query Tool)

-- Le digo a PostgreSQL que el archivo tiene tildes y eñes (en Windows a veces salen mal si no)
SET client_encoding = 'UTF8';

-- Borro el esquema si ya existe (OJO: esto borra todas las tablas y los datos)
DROP SCHEMA IF EXISTS gastrosena CASCADE;
-- Creo el esquema del proyecto (es como una carpeta para las tablas)
CREATE SCHEMA gastrosena;
-- Le digo que todo lo que cree de aquí para abajo quede en el esquema gastrosena
SET search_path TO gastrosena;


-- Tabla de roles
CREATE TABLE roles (
    -- Id del rol, SERIAL hace que el número se ponga solo (1, 2, 3...)
    id SERIAL PRIMARY KEY,
    -- Nombre del rol, no se puede repetir y solo puede ser uno de estos 4
    nombre VARCHAR(20) NOT NULL UNIQUE CHECK (nombre IN ('encargado', 'instructor', 'aprendiz', 'invitado')),
    -- Descripción del rol
    descripcion VARCHAR(150)
);


-- Tabla de fichas (grupos de formación)
CREATE TABLE fichas (
    -- Id de la ficha
    id SERIAL PRIMARY KEY,
    -- Número de la ficha, no se puede repetir
    codigo VARCHAR(10) NOT NULL UNIQUE,
    -- Programa de formación
    programa VARCHAR(120) NOT NULL,
    -- Jornada de la ficha
    jornada VARCHAR(15) NOT NULL CHECK (jornada IN ('DIURNA', 'NOCTURNA', 'MIXTA', 'FIN_DE_SEMANA')),
    -- Vocero del grupo (puede quedar vacío)
    vocero VARCHAR(100),
    -- Cantidad de estudiantes, si no se pone queda en 0
    cantidad_estudiantes INTEGER NOT NULL DEFAULT 0 CHECK (cantidad_estudiantes >= 0 AND cantidad_estudiantes <= 60),
    -- Si la ficha está activa
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    -- Auditoría: id del usuario que creó el registro (la API lo pone sola)
    creado_por INTEGER,
    -- Auditoría: id del usuario que lo modificó por última vez
    modificado_por INTEGER,
    -- Auditoría: fecha y hora de la última modificación
    fecha_modificacion TIMESTAMP,
    -- Fecha en que se creó, se pone sola con la fecha de ahora
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de usuarios
CREATE TABLE usuarios (
    -- Id del usuario
    id SERIAL PRIMARY KEY,
    -- Documento, no se puede repetir
    documento VARCHAR(10) NOT NULL UNIQUE,
    -- Nombre completo
    nombre VARCHAR(100) NOT NULL,
    -- Correo, no se puede repetir
    correo VARCHAR(120) NOT NULL UNIQUE,
    -- Teléfono (puede quedar vacío)
    telefono VARCHAR(10),
    -- Contraseña encriptada con bcrypt
    contrasena VARCHAR(100) NOT NULL,
    -- Rol del usuario (llave foránea a roles)
    rol_id INTEGER NOT NULL REFERENCES roles(id),
    -- Ficha del usuario, solo para aprendices (llave foránea a fichas)
    ficha_id INTEGER REFERENCES fichas(id),
    -- Si es beneficiario no paga el almuerzo
    es_beneficiario BOOLEAN NOT NULL DEFAULT FALSE,
    -- Si está activo puede iniciar sesión
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    -- Intentos fallidos al iniciar sesión
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    -- Hasta cuándo está bloqueada la cuenta
    bloqueado_hasta TIMESTAMP,
    -- Auditoría: id del usuario que creó el registro (la API lo pone sola)
    creado_por INTEGER,
    -- Auditoría: id del usuario que lo modificó por última vez
    modificado_por INTEGER,
    -- Auditoría: fecha y hora de la última modificación
    fecha_modificacion TIMESTAMP,
    -- Fecha en que se creó
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de menús (uno por día)
CREATE TABLE menus (
    -- Id del menú
    id SERIAL PRIMARY KEY,
    -- Fecha del menú, no se puede repetir (un menú por día)
    fecha DATE NOT NULL UNIQUE,
    -- Nombre del plato
    nombre VARCHAR(100) NOT NULL,
    -- Lo que trae el almuerzo
    descripcion VARCHAR(500) NOT NULL,
    -- Precio para aprendices e instructores (no puede ser negativo)
    precio_aprendiz NUMERIC(10,2) NOT NULL CHECK (precio_aprendiz >= 0),
    -- Precio para invitados (no puede ser negativo)
    precio_invitado NUMERIC(10,2) NOT NULL CHECK (precio_invitado >= 0),
    -- Cuántos almuerzos hay en total
    cantidad_total INTEGER NOT NULL CHECK (cantidad_total > 0),
    -- Cuántos almuerzos quedan (nunca puede ser negativo)
    cantidad_disponible INTEGER NOT NULL CHECK (cantidad_disponible >= 0),
    -- Si el menú está activo
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    -- Auditoría: id del usuario que creó el registro (la API lo pone sola)
    creado_por INTEGER,
    -- Auditoría: id del usuario que lo modificó por última vez
    modificado_por INTEGER,
    -- Auditoría: fecha y hora de la última modificación
    fecha_modificacion TIMESTAMP,
    -- Fecha en que se creó
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de reservas
CREATE TABLE reservas (
    -- Id de la reserva
    id SERIAL PRIMARY KEY,
    -- Menú que se reservó (llave foránea a menus)
    menu_id INTEGER NOT NULL REFERENCES menus(id),
    -- Usuario que reservó (llave foránea a usuarios)
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    -- Tipo de reserva
    tipo VARCHAR(15) NOT NULL CHECK (tipo IN ('APRENDIZ', 'BENEFICIARIO', 'INSTRUCTOR', 'INVITADO')),
    -- Lo que tiene que pagar
    valor NUMERIC(10,2) NOT NULL CHECK (valor >= 0),
    -- Estado de la reserva
    estado VARCHAR(15) NOT NULL DEFAULT 'RESERVADO' CHECK (estado IN ('RESERVADO', 'PENDIENTE', 'PAGADO', 'NO_PAGADO', 'CANCELADA')),
    -- Auditoría: id del usuario que creó el registro (la API lo pone sola)
    creado_por INTEGER,
    -- Auditoría: id del usuario que lo modificó por última vez
    modificado_por INTEGER,
    -- Auditoría: fecha y hora de la última modificación
    fecha_modificacion TIMESTAMP,
    -- Fecha en que se hizo
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de pagos de los instructores
CREATE TABLE pagos_instructor (
    -- Id del pago
    id SERIAL PRIMARY KEY,
    -- Instructor que pagó (llave foránea a usuarios)
    instructor_id INTEGER NOT NULL REFERENCES usuarios(id),
    -- Cuánto pagó (tiene que ser más de 0)
    valor NUMERIC(12,2) NOT NULL CHECK (valor > 0),
    -- Cómo pagó
    metodo VARCHAR(15) NOT NULL CHECK (metodo IN ('EFECTIVO', 'TRANSFERENCIA', 'NOMINA')),
    -- Nota del pago
    observacion VARCHAR(255),
    -- Auditoría: id del usuario que creó el registro (la API lo pone sola)
    creado_por INTEGER,
    -- Auditoría: id del usuario que lo modificó por última vez
    modificado_por INTEGER,
    -- Auditoría: fecha y hora de la última modificación
    fecha_modificacion TIMESTAMP,
    -- Fecha del pago
    fecha_pago TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de materiales del inventario
CREATE TABLE materiales (
    -- Id del material
    id SERIAL PRIMARY KEY,
    -- Código de barras, no se puede repetir
    codigo_barras VARCHAR(14) NOT NULL UNIQUE,
    -- Nombre del material
    nombre VARCHAR(100) NOT NULL,
    -- Categoría
    categoria VARCHAR(15) NOT NULL CHECK (categoria IN ('PROTEINA', 'GRANO', 'VERDURA', 'FRUTA', 'LACTEO', 'ABARROTE', 'DESECHABLE')),
    -- Unidad de medida
    unidad_medida VARCHAR(5) NOT NULL CHECK (unidad_medida IN ('KG', 'G', 'L', 'ML', 'UND')),
    -- Costo de una unidad (más de 0)
    costo_unitario NUMERIC(12,2) NOT NULL CHECK (costo_unitario > 0),
    -- Cantidad que hay (nunca negativa)
    stock NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (stock >= 0),
    -- Cantidad mínima que debería haber
    stock_minimo NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),
    -- Fecha de vencimiento (puede quedar vacía)
    fecha_vencimiento DATE,
    -- Si el material está activo
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    -- Auditoría: id del usuario que creó el registro (la API lo pone sola)
    creado_por INTEGER,
    -- Auditoría: id del usuario que lo modificó por última vez
    modificado_por INTEGER,
    -- Auditoría: fecha y hora de la última modificación
    fecha_modificacion TIMESTAMP,
    -- Fecha en que se creó
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de movimientos del inventario (kardex)
CREATE TABLE movimientos_inventario (
    -- Id del movimiento
    id SERIAL PRIMARY KEY,
    -- Material que se movió (llave foránea a materiales)
    material_id INTEGER NOT NULL REFERENCES materiales(id),
    -- Usuario que hizo el movimiento (llave foránea a usuarios)
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    -- Tipo de movimiento
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('ENTRADA', 'SALIDA', 'MERMA')),
    -- Cantidad que se movió (más de 0)
    cantidad NUMERIC(12,3) NOT NULL CHECK (cantidad > 0),
    -- Lo que quedó de stock después del movimiento
    saldo NUMERIC(12,3) NOT NULL CHECK (saldo >= 0),
    -- Por qué se hizo el movimiento
    concepto VARCHAR(255) NOT NULL,
    -- Fecha del movimiento
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de recetas
CREATE TABLE recetas (
    -- Id de la receta
    id SERIAL PRIMARY KEY,
    -- Nombre del plato, no se puede repetir
    nombre VARCHAR(100) NOT NULL UNIQUE,
    -- Descripción del plato
    descripcion VARCHAR(500),
    -- Precio de venta (más de 0)
    precio_venta NUMERIC(10,2) NOT NULL CHECK (precio_venta > 0),
    -- Si la receta está activa
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    -- Auditoría: id del usuario que creó el registro (la API lo pone sola)
    creado_por INTEGER,
    -- Auditoría: id del usuario que lo modificó por última vez
    modificado_por INTEGER,
    -- Auditoría: fecha y hora de la última modificación
    fecha_modificacion TIMESTAMP,
    -- Fecha en que se creó
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de ingredientes de cada receta
CREATE TABLE receta_ingredientes (
    -- Id del ingrediente
    id SERIAL PRIMARY KEY,
    -- Receta a la que pertenece (llave foránea a recetas)
    receta_id INTEGER NOT NULL REFERENCES recetas(id),
    -- Material que se usa (llave foránea a materiales)
    material_id INTEGER NOT NULL REFERENCES materiales(id),
    -- Cuánto se usa en un plato (más de 0)
    cantidad NUMERIC(12,3) NOT NULL CHECK (cantidad > 0),
    -- Un material no se puede repetir en la misma receta
    UNIQUE (receta_id, material_id)
);


-- Tabla de sugerencias
CREATE TABLE sugerencias (
    -- Id de la sugerencia
    id SERIAL PRIMARY KEY,
    -- Usuario que la mandó (llave foránea a usuarios)
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    -- Tema
    asunto VARCHAR(100) NOT NULL,
    -- Mensaje (máximo 500 letras)
    mensaje VARCHAR(500) NOT NULL,
    -- Estado de la sugerencia
    estado VARCHAR(10) NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'ATENDIDA')),
    -- Respuesta del encargado
    respuesta VARCHAR(500),
    -- Auditoría: id del usuario que creó el registro (la API lo pone sola)
    creado_por INTEGER,
    -- Auditoría: id del usuario que lo modificó por última vez
    modificado_por INTEGER,
    -- Auditoría: fecha y hora de la última modificación
    fecha_modificacion TIMESTAMP,
    -- Fecha en que se mandó
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Fecha en que se respondió
    fecha_respuesta TIMESTAMP
);


-- Índices para que las búsquedas más comunes sean más rápidas
-- Índice para buscar usuarios por rol
CREATE INDEX idx_usuarios_rol ON usuarios(rol_id);
-- Índice para buscar las reservas de un usuario
CREATE INDEX idx_reservas_usuario ON reservas(usuario_id);
-- Índice para buscar las reservas de un menú
CREATE INDEX idx_reservas_menu ON reservas(menu_id);
-- Índice para buscar los movimientos de un material
CREATE INDEX idx_movimientos_material ON movimientos_inventario(material_id);
-- Índice para buscar los ingredientes de una receta
CREATE INDEX idx_ingredientes_receta ON receta_ingredientes(receta_id);

-- Llaves foráneas de la auditoría: creado_por y modificado_por apuntan a la tabla usuarios
-- Se agregan al final porque la tabla fichas se crea antes que la tabla usuarios
-- Auditoría de fichas
ALTER TABLE fichas ADD CONSTRAINT fk_fichas_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id);
ALTER TABLE fichas ADD CONSTRAINT fk_fichas_modificado_por FOREIGN KEY (modificado_por) REFERENCES usuarios(id);
-- Auditoría de usuarios
ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id);
ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_modificado_por FOREIGN KEY (modificado_por) REFERENCES usuarios(id);
-- Auditoría de menus
ALTER TABLE menus ADD CONSTRAINT fk_menus_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id);
ALTER TABLE menus ADD CONSTRAINT fk_menus_modificado_por FOREIGN KEY (modificado_por) REFERENCES usuarios(id);
-- Auditoría de reservas
ALTER TABLE reservas ADD CONSTRAINT fk_reservas_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id);
ALTER TABLE reservas ADD CONSTRAINT fk_reservas_modificado_por FOREIGN KEY (modificado_por) REFERENCES usuarios(id);
-- Auditoría de pagos_instructor
ALTER TABLE pagos_instructor ADD CONSTRAINT fk_pagos_instructor_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id);
ALTER TABLE pagos_instructor ADD CONSTRAINT fk_pagos_instructor_modificado_por FOREIGN KEY (modificado_por) REFERENCES usuarios(id);
-- Auditoría de materiales
ALTER TABLE materiales ADD CONSTRAINT fk_materiales_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id);
ALTER TABLE materiales ADD CONSTRAINT fk_materiales_modificado_por FOREIGN KEY (modificado_por) REFERENCES usuarios(id);
-- Auditoría de recetas
ALTER TABLE recetas ADD CONSTRAINT fk_recetas_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id);
ALTER TABLE recetas ADD CONSTRAINT fk_recetas_modificado_por FOREIGN KEY (modificado_por) REFERENCES usuarios(id);
-- Auditoría de sugerencias
ALTER TABLE sugerencias ADD CONSTRAINT fk_sugerencias_creado_por FOREIGN KEY (creado_por) REFERENCES usuarios(id);
ALTER TABLE sugerencias ADD CONSTRAINT fk_sugerencias_modificado_por FOREIGN KEY (modificado_por) REFERENCES usuarios(id);
