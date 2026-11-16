-- =============================================================
-- GastroSENA - DML: datos de prueba coherentes con el servicio de
-- almuerzos del Tecnoparque Yamboró. Ejecutar después de 01_ddl.sql:
--   psql -U postgres -d gastrosena_db -f database/02_dml.sql
--
-- - Las llaves foráneas se buscan con subconsultas (no dependen de los id).
-- - Las fechas son relativas a CURRENT_DATE: siempre hay menú de hoy.
-- - El cupo de los menús y el stock de los materiales se calculan al final
--   a partir de las reservas y del kardex, para que siempre cuadren.
--
-- Contraseñas (cifradas con bcrypt, 10 rondas):
--   encargado@gastrosena.com     Encargado123
--   instructor@gastrosena.com    Instructor123  (y demás instructores)
--   aprendiz@gastrosena.com      Aprendiz123    (y demás aprendices)
--   beneficiario@gastrosena.com  Aprendiz123    (aprendiz beneficiario: almuerzo $0)
--   invitado@gastrosena.com      Invitado123    (y demás invitados)
--   inactivo@gastrosena.com      Aprendiz123    (cuenta inactiva: no puede ingresar)
-- =============================================================

-- El texto de este archivo viene en UTF-8 (tildes y eñes)
SET client_encoding = 'UTF8';
-- Las tablas se buscan en el esquema gastrosena (no hace falta escribir gastrosena.tabla)
SET search_path TO gastrosena;

-- ---------------------------------------------------------------- roles
-- Inserta los 4 roles; PostgreSQL les asigna los id 1, 2, 3 y 4 en este orden
INSERT INTO roles (nombre, descripcion) VALUES
    ('encargado',  'Administra el servicio: usuarios, menú, ventas, cartera, inventario, grupos y sugerencias'),  -- id 1
    ('instructor', 'Consume almuerzos y los paga con una cuenta mensual'),  -- id 2
    ('aprendiz',   'Reserva su almuerzo y consulta sus consumos'),  -- id 3
    ('invitado',   'Visitante que compra el almuerzo a precio de invitado');  -- id 4

-- ---------------------------------------------------------------- encargado (crea el resto)
-- Inserta primero a la encargada, porque ella aparece como creadora (creado_por) de los demás registros
INSERT INTO usuarios (documento, nombre, correo, telefono, password_hash, rol_id) VALUES
    ('1083000001', 'Marta Lucía Rojas', 'encargado@gastrosena.com', '3104567890',  -- documento, nombre, correo y teléfono
     '$2b$10$elAlppC4AFChDTvtS6U7/.3.ZltWaDCNZaaY0kd0nZSpub/uGK/ja',  -- hash bcrypt de "Encargado123"
     (SELECT id FROM roles WHERE nombre = 'encargado'));  -- subconsulta: busca el id del rol encargado

-- ---------------------------------------------------------------- fichas
-- Inserta las 10 fichas tomando los datos de la lista VALUES de abajo (INSERT ... SELECT)
INSERT INTO fichas (codigo, programa, jornada, vocero, cantidad_estudiantes, creado_por)
SELECT f.codigo, f.programa, f.jornada, f.vocero, f.cantidad,  -- columnas de la lista "f"
       (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com')  -- creado_por = id de la encargada
FROM (VALUES  -- lista de datos escrita dentro de la consulta
    ('2847251', 'Análisis y Desarrollo de Software',  'DIURNA',        'Laura Méndez',    28),  -- id 1 (ADSO)
    ('2847252', 'Gastronomía',                        'DIURNA',        'Camilo Rojas',    25),  -- id 2
    ('2847253', 'Cocina',                             'MIXTA',         'Valentina Ortiz', 22),  -- id 3
    ('2847254', 'Producción Agropecuaria Ecológica',  'DIURNA',        'Andrés Muñoz',    30),  -- id 4
    ('2847255', 'Control de Calidad del Café',        'DIURNA',        'Daniela Pérez',   20),  -- id 5
    ('2847256', 'Panadería',                          'NOCTURNA',      'Julián Castro',   18),  -- id 6
    ('2847257', 'Gestión Empresarial',                'MIXTA',         'Sara López',      26),  -- id 7
    ('2847258', 'Producción de Especies Menores',     'DIURNA',        'Mateo Gómez',     24),  -- id 8
    ('2847259', 'Mesa y Bar',                         'NOCTURNA',      'Isabella Díaz',   19),  -- id 9
    ('2847260', 'Agroindustria Alimentaria',          'FIN_DE_SEMANA', 'Tomás Ruiz',      21)  -- id 10
) AS f (codigo, programa, jornada, vocero, cantidad);  -- le da el nombre "f" a la lista y a sus columnas

-- ---------------------------------------------------------------- usuarios
-- Inserta los otros 11 usuarios (instructores, aprendices e invitados)
INSERT INTO usuarios (documento, nombre, correo, telefono, password_hash, rol_id, ficha_id, es_beneficiario, activo, creado_por)
SELECT u.documento, u.nombre, u.correo, u.telefono,  -- datos de la lista "u"
       CASE u.rol  -- elige el hash de la contraseña según el rol:
           WHEN 'instructor' THEN '$2b$10$//KFz2sbTRuYKCt.xpb7r.ZY.Wi./fkgR6VQco0Aq6d3SFO1kUNV6'  -- "Instructor123"
           WHEN 'aprendiz'   THEN '$2b$10$OdO7h8EZBtl7c6sc9..4y.gU24Jfogtpyi59w87g4Fo1QZrC8uWH.'  -- "Aprendiz123"
           ELSE                   '$2b$10$hOdcCFijV5gnNiKy07BYKevwx9IvO3jsTGcP04k1ROgjMMFGK4tXy'  -- "Invitado123"
       END,  -- fin del CASE
       (SELECT id FROM roles WHERE nombre = u.rol),  -- id del rol según su nombre
       (SELECT id FROM fichas WHERE codigo = u.ficha),  -- id de la ficha según su código (NULL si no tiene)
       u.beneficiario, u.activo,  -- si es beneficiario y si está activo
       (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com')  -- creado_por = id de la encargada
FROM (VALUES  -- lista de datos: documento, nombre, correo, teléfono, rol, ficha, beneficiario, activo
    ('1083000002', 'Carlos Andrés Muñoz',   'instructor@gastrosena.com',      '3112223344', 'instructor', NULL,      FALSE, TRUE),  -- id 2: deuda vencida
    ('1083000003', 'Diana Patricia Cerón',  'diana.ceron@gastrosena.com',     '3123334455', 'instructor', NULL,      FALSE, TRUE),  -- id 3: deuda activa
    ('1083000004', 'Jorge Iván Salazar',    'jorge.salazar@gastrosena.com',   '3134445566', 'instructor', NULL,      FALSE, TRUE),  -- id 4: al día
    ('1083000005', 'Laura Méndez Vargas',   'aprendiz@gastrosena.com',        '3145556677', 'aprendiz',   '2847251', FALSE, TRUE),  -- id 5: aprendiz de ADSO
    ('1083000006', 'Sebastián Calle Ortiz', 'sebastian.calle@gastrosena.com', '3156667788', 'aprendiz',   '2847251', FALSE, TRUE),  -- id 6: aprendiz de ADSO
    ('1083000007', 'Camilo Rojas Peña',     'beneficiario@gastrosena.com',    '3167778899', 'aprendiz',   '2847252', TRUE,  TRUE),  -- id 7: beneficiario
    ('1083000008', 'Valentina Ortiz Gil',   'valentina.ortiz@gastrosena.com', '3178889900', 'aprendiz',   '2847253', FALSE, TRUE),  -- id 8
    ('1083000009', 'Andrés Muñoz Cruz',     'andres.munoz@gastrosena.com',    '3189990011', 'aprendiz',   '2847254', TRUE,  TRUE),  -- id 9: beneficiario
    ('1083000010', 'Daniela Pérez Ríos',    'inactivo@gastrosena.com',        '3190001122', 'aprendiz',   '2847255', FALSE, FALSE),  -- id 10: cuenta inactiva
    ('1083000011', 'Pedro Ruiz Gómez',      'invitado@gastrosena.com',        '3201112233', 'invitado',   NULL,      FALSE, TRUE),  -- id 11: invitado
    ('1083000012', 'Ana León Cárdenas',     'ana.leon@correo.com',            '3212223344', 'invitado',   NULL,      FALSE, TRUE)  -- id 12: invitada
) AS u (documento, nombre, correo, telefono, rol, ficha, beneficiario, activo);  -- nombre de la lista y de sus columnas

-- ---------------------------------------------------------------- menús
-- desplazamiento = días respecto a hoy; NULL = un día del mes anterior
-- Inserta 12 menús; todos cuestan $5.000 (aprendiz) y $8.000 (invitado) y tienen cupo de 80
INSERT INTO menus (fecha, nombre, descripcion, precio_aprendiz, precio_invitado, cantidad_total, cantidad_disponible, creado_por)
SELECT COALESCE(CURRENT_DATE + m.desplazamiento, (date_trunc('month', CURRENT_DATE) - INTERVAL '15 days')::date),  -- fecha = hoy + desplazamiento; si es NULL, 15 días antes del inicio del mes
       m.nombre, m.descripcion, 5000, 8000, 80, 80,  -- precios y cupo (el disponible se recalcula al final)
       (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com')  -- creado_por = id de la encargada
FROM (VALUES  -- lista de datos: desplazamiento, nombre, descripción
    (NULL::int, 'Cerdo en salsa',            'Cerdo en salsa criolla, arroz, papa y jugo'),  -- mes anterior (deuda vencida de Carlos)
    (-9,        'Arroz con pollo',           'Arroz con pollo, papa a la francesa, ensalada y jugo'),  -- hace 9 días
    (-8,        'Frijolada',                 'Fríjoles, arroz, huevo, tajadas de plátano y jugo'),  -- hace 8 días
    (-7,        'Carne guisada con papa',    'Carne guisada, papa, arroz, ensalada y jugo'),  -- hace 7 días
    (-6,        'Sudado de pollo',           'Sudado de pollo con papa, arroz y jugo'),  -- hace 6 días
    (-5,        'Lentejas con arroz',        'Lentejas, arroz, huevo, plátano y jugo'),  -- hace 5 días
    (-4,        'Pollo asado con ensalada',  'Pollo asado, papa salada, ensalada y jugo'),  -- hace 4 días
    (-3,        'Sopa de verduras y seco',   'Sopa de verduras, arroz, carne desmechada y jugo'),  -- hace 3 días
    (-2,        'Pescado frito',             'Mojarra frita, arroz, patacón, ensalada y jugo'),  -- hace 2 días
    (-1,        'Ajiaco',                    'Ajiaco con pollo, arroz, aguacate y jugo'),  -- ayer
    (0,         'Bandeja campesina',         'Fríjoles, arroz, carne molida, huevo, plátano y jugo'),  -- hoy
    (1,         'Arroz chino',               'Arroz chino, papa a la francesa, ensalada y jugo')  -- mañana
) AS m (desplazamiento, nombre, descripcion);  -- nombre de la lista y de sus columnas

-- ---------------------------------------------------------------- reservas y consumos
-- Inserta 19 reservas; cada fila busca el id del usuario (por correo) y del menú (por fecha)
INSERT INTO reservas (menu_id, usuario_id, tipo, valor, estado, creado_por, actualizado_por, actualizado_en)
SELECT me.id, us.id, r.tipo, r.valor, r.estado, us.id,  -- creado_por = la misma persona que reservó
       CASE WHEN r.estado IN ('PAGADO', 'NO_PAGADO') AND r.tipo <> 'BENEFICIARIO'  -- si el encargado marcó el pago (y no es beneficiario)...
            THEN (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com') END,  -- ...actualizado_por = la encargada; si no, NULL
       CASE WHEN r.estado IN ('PAGADO', 'NO_PAGADO') AND r.tipo <> 'BENEFICIARIO' THEN now() END  -- actualizado_en = ahora en el mismo caso
FROM (VALUES  -- lista de datos: correo, días respecto a hoy, tipo, valor y estado
    ('aprendiz@gastrosena.com',        0,    'APRENDIZ',     5000, 'RESERVADO'),  -- hoy: Laura sin pagar
    ('sebastian.calle@gastrosena.com', 0,    'APRENDIZ',     5000, 'PAGADO'),  -- hoy: Sebastián pagó
    ('beneficiario@gastrosena.com',    0,    'BENEFICIARIO',    0, 'PAGADO'),  -- hoy: Camilo a $0
    ('invitado@gastrosena.com',        0,    'INVITADO',     8000, 'PAGADO'),  -- hoy: Pedro pagó $8.000
    ('instructor@gastrosena.com',      0,    'INSTRUCTOR',   5000, 'PENDIENTE'),  -- hoy: Carlos a su cuenta
    ('valentina.ortiz@gastrosena.com', 0,    'APRENDIZ',     5000, 'NO_PAGADO'),  -- hoy: Valentina no pagó
    ('aprendiz@gastrosena.com',        -1,   'APRENDIZ',     5000, 'PAGADO'),  -- ayer: Laura
    ('andres.munoz@gastrosena.com',    -1,   'BENEFICIARIO',    0, 'PAGADO'),  -- ayer: Andrés a $0
    ('ana.leon@correo.com',            -1,   'INVITADO',     8000, 'PAGADO'),  -- ayer: Ana
    ('diana.ceron@gastrosena.com',     -1,   'INSTRUCTOR',   5000, 'PENDIENTE'),  -- ayer: Diana a su cuenta
    ('sebastian.calle@gastrosena.com', -2,   'APRENDIZ',     5000, 'PAGADO'),  -- hace 2 días: Sebastián
    ('instructor@gastrosena.com',      -2,   'INSTRUCTOR',   5000, 'PENDIENTE'),  -- hace 2 días: Carlos a su cuenta
    ('jorge.salazar@gastrosena.com',   -2,   'INSTRUCTOR',   5000, 'PAGADO'),  -- hace 2 días: Jorge (ya pagado)
    ('valentina.ortiz@gastrosena.com', -3,   'APRENDIZ',     5000, 'PAGADO'),  -- hace 3 días: Valentina
    ('jorge.salazar@gastrosena.com',   -3,   'INSTRUCTOR',   5000, 'PAGADO'),  -- hace 3 días: Jorge (ya pagado)
    ('aprendiz@gastrosena.com',        -3,   'APRENDIZ',     5000, 'CANCELADA'),  -- hace 3 días: Laura canceló
    ('beneficiario@gastrosena.com',    -5,   'BENEFICIARIO',    0, 'PAGADO'),  -- hace 5 días: Camilo a $0
    ('invitado@gastrosena.com',        -5,   'INVITADO',     8000, 'PAGADO'),  -- hace 5 días: Pedro
    ('instructor@gastrosena.com',      NULL, 'INSTRUCTOR',   5000, 'PENDIENTE')  -- mes anterior: Carlos (deuda vencida)
) AS r (correo, desplazamiento, tipo, valor, estado)  -- nombre de la lista y de sus columnas
JOIN usuarios us ON us.correo = r.correo  -- une cada fila con su usuario por el correo
JOIN menus me ON me.fecha = COALESCE(CURRENT_DATE + r.desplazamiento,  -- ...y con su menú por la fecha
                                     (date_trunc('month', CURRENT_DATE) - INTERVAL '15 days')::date);  -- (NULL = día del mes anterior)

-- El cupo disponible = cupo total - reservas vigentes
-- Recalcula el cupo de cada menú para que cuadre con las reservas insertadas
UPDATE menus m
SET cantidad_disponible = m.cantidad_total - (  -- cupo total menos...
    SELECT count(*) FROM reservas r WHERE r.menu_id = m.id AND r.estado <> 'CANCELADA');  -- ...las reservas no canceladas de ese menú

-- ---------------------------------------------------------------- pagos de instructores
-- Carlos: consumió 15.000 y abonó 5.000 (saldo 10.000, con consumo del mes anterior: deuda vencida)
-- Jorge: consumió 10.000 y pagó todo (al día). Diana: 5.000 pendientes del mes (deuda activa).
-- Inserta 3 pagos
INSERT INTO pagos_instructor (instructor_id, valor, metodo, observacion, creado_por)
SELECT us.id, p.valor, p.metodo, p.observacion,  -- id del instructor y datos del pago
       (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com')  -- creado_por = id de la encargada
FROM (VALUES  -- lista de datos: correo, valor, método y observación
    ('instructor@gastrosena.com',    5000,  'EFECTIVO', 'Abono parcial'),  -- Carlos abona $5.000
    ('jorge.salazar@gastrosena.com', 4000,  'NOMINA',   'Descuento de nómina'),  -- Jorge paga $4.000
    ('jorge.salazar@gastrosena.com', 6000,  'TRANSFERENCIA', 'Pago del saldo')  -- Jorge paga $6.000 y queda al día
) AS p (correo, valor, metodo, observacion)  -- nombre de la lista y de sus columnas
JOIN usuarios us ON us.correo = p.correo;  -- une cada pago con su instructor por el correo

-- ---------------------------------------------------------------- materiales
-- Inserta 14 materiales (el stock se calcula al final a partir del kardex)
INSERT INTO materiales (codigo_barras, nombre, categoria, unidad_medida, costo_unitario, stock_minimo, fecha_vencimiento, creado_por)
SELECT m.codigo, m.nombre, m.categoria, m.unidad, m.costo, m.minimo,  -- datos de la lista "m"
       CURRENT_DATE + m.vence_en_dias,  -- vencimiento = hoy + días (NULL si no vence)
       (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com')  -- creado_por = id de la encargada
FROM (VALUES  -- lista de datos: código, nombre, categoría, unidad, costo, mínimo, días para vencer
    ('7702001000011', 'Arroz blanco',        'GRANO',      'KG',  4200,  20, NULL::int),  -- id 1
    ('7702001000028', 'Fríjol rojo',         'GRANO',      'KG',  9800,  10, NULL),  -- id 2
    ('7702001000035', 'Pechuga de pollo',    'PROTEINA',   'KG',  14500, 15, 4),  -- id 3: vence en 4 días (VENCIENDO)
    ('7702001000042', 'Carne de res',        'PROTEINA',   'KG',  22000, 10, 20),  -- id 4
    ('7702001000059', 'Papa pastusa',        'VERDURA',    'KG',  2500,  20, NULL),  -- id 5
    ('7702001000066', 'Tomate chonto',       'VERDURA',    'KG',  3800,  8,  30),  -- id 6
    ('7702001000073', 'Cebolla cabezona',    'VERDURA',    'KG',  3200,  5,  NULL),  -- id 7
    ('7702001000080', 'Aceite vegetal',      'ABARROTE',   'L',   9500,  6,  NULL),  -- id 8
    ('7702001000097', 'Huevo AA',            'PROTEINA',   'UND', 550,   60, 15),  -- id 9
    ('7702001000103', 'Leche entera',        'LACTEO',     'L',   4200,  10, 6),  -- id 10: vence en 6 días (VENCIENDO)
    ('7702001000110', 'Plátano verde',       'FRUTA',      'UND', 700,   40, NULL),  -- id 11
    ('7702001000127', 'Bandeja desechable',  'DESECHABLE', 'UND', 350,   100, NULL),  -- id 12
    ('7702001000134', 'Lenteja',             'GRANO',      'KG',  7600,  8,  NULL),  -- id 13
    ('7702001000141', 'Sal refinada',        'ABARROTE',   'KG',  1800,  2,  NULL)  -- id 14: sin movimientos
) AS m (codigo, nombre, categoria, unidad, costo, minimo, vence_en_dias);  -- nombre de la lista y de sus columnas

-- ---------------------------------------------------------------- kardex
-- La sal refinada no tiene movimientos (se puede eliminar físicamente).
-- Inserta 22 movimientos: 13 entradas iniciales y 9 salidas o mermas
INSERT INTO movimientos_inventario (material_id, tipo, cantidad, saldo, concepto, creado_por, creado_en)
SELECT ma.id, k.tipo, k.cantidad, k.saldo, k.concepto,  -- id del material y datos del movimiento
       (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com'),  -- creado_por = id de la encargada
       (CURRENT_DATE + k.dia) + k.hora  -- creado_en = fecha (hoy + días) + hora
FROM (VALUES  -- lista de datos: código, tipo, cantidad, saldo, concepto, días respecto a hoy, hora
    ('7702001000011', 'ENTRADA', 50,  50,  'Stock inicial',                -10, TIME '07:00'),  -- arroz: entran 50
    ('7702001000028', 'ENTRADA', 15,  15,  'Stock inicial',                -10, TIME '07:05'),  -- fríjol: entran 15
    ('7702001000035', 'ENTRADA', 30,  30,  'Stock inicial',                -10, TIME '07:10'),  -- pollo: entran 30
    ('7702001000042', 'ENTRADA', 12,  12,  'Stock inicial',                -10, TIME '07:15'),  -- carne: entran 12
    ('7702001000059', 'ENTRADA', 40,  40,  'Stock inicial',                -10, TIME '07:20'),  -- papa: entran 40
    ('7702001000066', 'ENTRADA', 10,  10,  'Stock inicial',                -10, TIME '07:25'),  -- tomate: entran 10
    ('7702001000073', 'ENTRADA', 12,  12,  'Stock inicial',                -10, TIME '07:30'),  -- cebolla: entran 12
    ('7702001000080', 'ENTRADA', 18,  18,  'Stock inicial',                -10, TIME '07:35'),  -- aceite: entran 18
    ('7702001000097', 'ENTRADA', 180, 180, 'Stock inicial',                -10, TIME '07:40'),  -- huevo: entran 180
    ('7702001000103', 'ENTRADA', 20,  20,  'Stock inicial',                -10, TIME '07:45'),  -- leche: entran 20
    ('7702001000110', 'ENTRADA', 100, 100, 'Stock inicial',                -10, TIME '07:50'),  -- plátano: entran 100
    ('7702001000127', 'ENTRADA', 500, 500, 'Stock inicial',                -10, TIME '07:55'),  -- bandejas: entran 500
    ('7702001000134', 'ENTRADA', 10,  10,  'Stock inicial',                -10, TIME '08:00'),  -- lenteja: entran 10
    ('7702001000011', 'SALIDA',  12,  38,  'Preparación de almuerzos',     -2,  TIME '09:00'),  -- arroz: 50 - 12 = 38
    ('7702001000028', 'SALIDA',  6,   9,   'Preparación de frijolada',     -2,  TIME '09:05'),  -- fríjol: 15 - 6 = 9
    ('7702001000035', 'SALIDA',  10,  20,  'Preparación de almuerzos',     -2,  TIME '09:10'),  -- pollo: 30 - 10 = 20
    ('7702001000042', 'MERMA',   2,   10,  'Carne con mal olor al abrir el empaque', -2, TIME '09:15'),  -- carne: merma, 12 - 2 = 10
    ('7702001000042', 'SALIDA',  2,   8,   'Preparación de carne guisada', -2,  TIME '09:20'),  -- carne: 10 - 2 = 8
    ('7702001000066', 'MERMA',   7,   3,   'Tomates dañados por exceso de maduración', -2, TIME '09:25'),  -- tomate: merma, 10 - 7 = 3
    ('7702001000080', 'SALIDA',  3,   15,  'Fritos del día',               -2,  TIME '09:30'),  -- aceite: 18 - 3 = 15
    ('7702001000110', 'SALIDA',  30,  70,  'Tajadas y patacones',          -2,  TIME '09:35'),  -- plátano: 100 - 30 = 70
    ('7702001000127', 'SALIDA',  120, 380, 'Despacho de almuerzos',        -2,  TIME '09:40')  -- bandejas: 500 - 120 = 380
) AS k (codigo, tipo, cantidad, saldo, concepto, dia, hora)  -- nombre de la lista y de sus columnas
JOIN materiales ma ON ma.codigo_barras = k.codigo;  -- une cada movimiento con su material por el código de barras

-- El stock de cada material es el saldo de su último movimiento
-- Recalcula el stock de cada material
UPDATE materiales m
SET stock = COALESCE((SELECT k.saldo FROM movimientos_inventario k  -- toma el saldo...
                      WHERE k.material_id = m.id  -- ...de los movimientos de ese material...
                      ORDER BY k.creado_en DESC, k.id DESC LIMIT 1), 0);  -- ...el más reciente; 0 si no tiene movimientos

-- ---------------------------------------------------------------- recetas
-- Inserta 10 recetas
INSERT INTO recetas (nombre, descripcion, precio_venta, creado_por)
SELECT r.nombre, r.descripcion, r.precio,  -- datos de la lista "r"
       (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com')  -- creado_por = id de la encargada
FROM (VALUES  -- lista de datos: nombre, descripción, precio de venta
    ('Arroz con pollo',          'Plato fuerte con pollo desmechado',         5000),  -- costo 3.188, margen 1.812
    ('Frijolada',                'Fríjoles con arroz, huevo y plátano',       5000),  -- costo 3.000, margen 2.000
    ('Carne guisada con papa',   'Carne de res guisada con papa y arroz',     5000),  -- costo 4.760, margen 240
    ('Sudado de pollo',          'Pollo sudado con papa y tomate',            5000),  -- costo 3.510, margen 1.490
    ('Lentejas con arroz',       'Lentejas con arroz, huevo y plátano',       5000),  -- costo 2.864, margen 2.136
    ('Pollo asado con ensalada', 'Pollo asado, papa y ensalada de tomate',    8000),  -- costo 4.779, margen 3.221
    ('Bistec a caballo',         'Bistec de res con huevo frito y arroz',     5000),  -- costo 5.720: MARGEN NEGATIVO (-720)
    ('Huevos pericos con arroz', 'Huevos revueltos con tomate y cebolla',     5000),  -- costo 2.156, margen 2.844
    ('Patacón con hogao',        'Patacones con hogao de tomate y cebolla',   5000),  -- costo 2.499, margen 2.501
    ('Sopa de verduras',         'Sopa de papa, plátano y verduras',          5000)  -- costo 1.836, margen 3.164
) AS r (nombre, descripcion, precio);  -- nombre de la lista y de sus columnas

-- Inserta los 48 ingredientes (fórmulas); cada fila busca la receta por nombre y el material por código
INSERT INTO receta_ingredientes (receta_id, material_id, cantidad)
SELECT re.id, ma.id, i.cantidad  -- id de la receta, id del material y cantidad por plato
FROM (VALUES  -- lista de datos: receta, código del material, cantidad por plato
    ('Arroz con pollo',          '7702001000011', 0.120), ('Arroz con pollo',          '7702001000035', 0.150),  -- arroz 0,12 kg y pollo 0,15 kg
    ('Arroz con pollo',          '7702001000073', 0.020), ('Arroz con pollo',          '7702001000080', 0.010),  -- cebolla 0,02 kg y aceite 0,01 L
    ('Arroz con pollo',          '7702001000127', 1),  -- 1 bandeja
    ('Frijolada',                '7702001000028', 0.100), ('Frijolada',                '7702001000011', 0.100),  -- fríjol 0,1 kg y arroz 0,1 kg
    ('Frijolada',                '7702001000110', 1),     ('Frijolada',                '7702001000097', 1),  -- 1 plátano y 1 huevo
    ('Frijolada',                '7702001000127', 1),  -- 1 bandeja
    ('Carne guisada con papa',   '7702001000042', 0.150), ('Carne guisada con papa',   '7702001000059', 0.200),  -- carne 0,15 kg y papa 0,2 kg
    ('Carne guisada con papa',   '7702001000066', 0.050), ('Carne guisada con papa',   '7702001000011', 0.100),  -- tomate 0,05 kg y arroz 0,1 kg
    ('Carne guisada con papa',   '7702001000127', 1),  -- 1 bandeja
    ('Sudado de pollo',          '7702001000035', 0.150), ('Sudado de pollo',          '7702001000059', 0.150),  -- pollo 0,15 kg y papa 0,15 kg
    ('Sudado de pollo',          '7702001000066', 0.050), ('Sudado de pollo',          '7702001000011', 0.100),  -- tomate 0,05 kg y arroz 0,1 kg
    ('Sudado de pollo',          '7702001000127', 1),  -- 1 bandeja
    ('Lentejas con arroz',       '7702001000134', 0.100), ('Lentejas con arroz',       '7702001000011', 0.120),  -- lenteja 0,1 kg y arroz 0,12 kg
    ('Lentejas con arroz',       '7702001000097', 1),     ('Lentejas con arroz',       '7702001000110', 1),  -- 1 huevo y 1 plátano
    ('Lentejas con arroz',       '7702001000127', 1),  -- 1 bandeja
    ('Pollo asado con ensalada', '7702001000035', 0.250), ('Pollo asado con ensalada', '7702001000066', 0.080),  -- pollo 0,25 kg y tomate 0,08 kg
    ('Pollo asado con ensalada', '7702001000059', 0.200), ('Pollo asado con ensalada', '7702001000127', 1),  -- papa 0,2 kg y 1 bandeja
    ('Bistec a caballo',         '7702001000042', 0.200), ('Bistec a caballo',         '7702001000097', 1),  -- carne 0,2 kg y 1 huevo
    ('Bistec a caballo',         '7702001000011', 0.100), ('Bistec a caballo',         '7702001000127', 1),  -- arroz 0,1 kg y 1 bandeja
    ('Huevos pericos con arroz', '7702001000097', 2),     ('Huevos pericos con arroz', '7702001000066', 0.050),  -- 2 huevos y tomate 0,05 kg
    ('Huevos pericos con arroz', '7702001000073', 0.030), ('Huevos pericos con arroz', '7702001000011', 0.100),  -- cebolla 0,03 kg y arroz 0,1 kg
    ('Huevos pericos con arroz', '7702001000127', 1),  -- 1 bandeja
    ('Patacón con hogao',        '7702001000110', 2),     ('Patacón con hogao',        '7702001000066', 0.080),  -- 2 plátanos y tomate 0,08 kg
    ('Patacón con hogao',        '7702001000073', 0.050), ('Patacón con hogao',        '7702001000080', 0.030),  -- cebolla 0,05 kg y aceite 0,03 L
    ('Patacón con hogao',        '7702001000127', 1),  -- 1 bandeja
    ('Sopa de verduras',         '7702001000059', 0.200), ('Sopa de verduras',         '7702001000110', 1),  -- papa 0,2 kg y 1 plátano
    ('Sopa de verduras',         '7702001000066', 0.050), ('Sopa de verduras',         '7702001000073', 0.030),  -- tomate 0,05 kg y cebolla 0,03 kg
    ('Sopa de verduras',         '7702001000127', 1)  -- 1 bandeja
) AS i (receta, codigo, cantidad)  -- nombre de la lista y de sus columnas
JOIN recetas re ON re.nombre = i.receta  -- une con la receta por su nombre
JOIN materiales ma ON ma.codigo_barras = i.codigo;  -- une con el material por su código de barras

-- ---------------------------------------------------------------- sugerencias
-- Inserta 10 sugerencias: 5 pendientes y 5 atendidas
INSERT INTO sugerencias (usuario_id, asunto, mensaje, estado, respuesta, atendida_por, atendida_en)
SELECT us.id, s.asunto, s.mensaje, s.estado, s.respuesta,  -- autor y datos de la sugerencia
       CASE WHEN s.estado = 'ATENDIDA' THEN (SELECT id FROM usuarios WHERE correo = 'encargado@gastrosena.com') END,  -- si está atendida, la atendió la encargada
       CASE WHEN s.estado = 'ATENDIDA' THEN now() END  -- y se atendió ahora; si está pendiente, ambos quedan NULL
FROM (VALUES  -- lista de datos: correo del autor, asunto, mensaje, estado, respuesta
    ('aprendiz@gastrosena.com',        'Más opciones vegetarianas', 'Sería bueno tener un menú vegetariano al menos una vez por semana.', 'PENDIENTE', NULL),  -- Laura
    ('sebastian.calle@gastrosena.com', 'Horario de entrega',        'La fila a las 12:00 es muy larga, podrían abrir a las 11:30.',       'ATENDIDA',  'Desde la próxima semana se abre a las 11:30.'),  -- Sebastián
    ('beneficiario@gastrosena.com',    'Agradecimiento',            'Gracias por el apoyo con el almuerzo.',                             'ATENDIDA',  '¡Con gusto! Sigue adelante con tu formación.'),  -- Camilo
    ('invitado@gastrosena.com',        'Pago con transferencia',    '¿Se puede pagar el almuerzo por transferencia?',                    'PENDIENTE', NULL),  -- Pedro
    ('instructor@gastrosena.com',      'Corte de la cuenta',        '¿Podrían enviar el corte de la cuenta mensual por correo?',         'PENDIENTE', NULL),  -- Carlos
    ('valentina.ortiz@gastrosena.com', 'Porciones',                 'La porción de proteína del jueves fue pequeña.',                     'ATENDIDA',  'Gracias, ajustamos el gramaje de la receta.'),  -- Valentina
    ('andres.munoz@gastrosena.com',    'Jugo natural',              'Me gustaría que el jugo fuera sin azúcar.',                          'PENDIENTE', NULL),  -- Andrés
    ('diana.ceron@gastrosena.com',     'Cubiertos',                 'Faltaron cubiertos desechables el martes.',                          'ATENDIDA',  'Se aumentó el pedido de cubiertos.'),  -- Diana
    ('ana.leon@correo.com',            'Muy buena atención',        'Excelente servicio durante la visita al Tecnoparque.',              'ATENDIDA',  'Gracias por visitarnos.'),  -- Ana
    ('jorge.salazar@gastrosena.com',   'Menú de la semana',         'Publicar el menú de toda la semana el lunes ayudaría a planear.',   'PENDIENTE', NULL)  -- Jorge
) AS s (correo, asunto, mensaje, estado, respuesta)  -- nombre de la lista y de sus columnas
JOIN usuarios us ON us.correo = s.correo;  -- une cada sugerencia con su autor por el correo
