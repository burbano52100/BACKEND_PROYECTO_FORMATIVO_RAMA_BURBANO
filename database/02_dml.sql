-- Script con los datos de prueba de GastroSENA
-- Se ejecuta después de 01_ddl.sql
--
-- Usuarios para probar (correo / contraseña):
--   encargado@gastrosena.com     Encargado123
--   instructor@gastrosena.com    Instructor123
--   aprendiz@gastrosena.com      Aprendiz123
--   beneficiario@gastrosena.com  Aprendiz123
--   invitado@gastrosena.com      Invitado123
--   inactivo@gastrosena.com      Aprendiz123  (esta cuenta está desactivada)
--
-- Las contraseñas están encriptadas con bcrypt, por eso se ven raras

-- Le digo a PostgreSQL que el archivo tiene tildes y eñes
SET client_encoding = 'UTF8';
-- Trabajo dentro del esquema gastrosena
SET search_path TO gastrosena;


-- ROLES (quedan con id 1, 2, 3 y 4 en este orden)
INSERT INTO roles (nombre, descripcion) VALUES
('encargado', 'Administra el servicio: usuarios, menú, ventas, cartera, inventario y sugerencias'), -- id 1
('instructor', 'Consume almuerzos y los paga con una cuenta mensual'), -- id 2
('aprendiz', 'Reserva su almuerzo y consulta sus consumos'), -- id 3
('invitado', 'Visitante que compra el almuerzo a precio de invitado'); -- id 4


-- FICHAS (10 fichas)
INSERT INTO fichas (codigo, programa, jornada, vocero, cantidad_estudiantes) VALUES
('2847251', 'Análisis y Desarrollo de Software', 'DIURNA', 'Laura Méndez', 28), -- id 1
('2847252', 'Gastronomía', 'DIURNA', 'Camilo Rojas', 25), -- id 2
('2847253', 'Cocina', 'MIXTA', 'Valentina Ortiz', 22), -- id 3
('2847254', 'Producción Agropecuaria Ecológica', 'DIURNA', 'Andrés Muñoz', 30), -- id 4
('2847255', 'Control de Calidad del Café', 'DIURNA', 'Daniela Pérez', 20), -- id 5
('2847256', 'Panadería', 'NOCTURNA', 'Julián Castro', 18), -- id 6
('2847257', 'Gestión Empresarial', 'MIXTA', 'Sara López', 26), -- id 7
('2847258', 'Producción de Especies Menores', 'DIURNA', 'Mateo Gómez', 24), -- id 8
('2847259', 'Mesa y Bar', 'NOCTURNA', 'Isabella Díaz', 19), -- id 9
('2847260', 'Agroindustria Alimentaria', 'FIN_DE_SEMANA', 'Tomás Ruiz', 21); -- id 10


-- USUARIOS (12 usuarios)
INSERT INTO usuarios (documento, nombre, correo, telefono, contrasena, rol_id, ficha_id, es_beneficiario, activo) VALUES
('1083000001', 'Marta Lucía Rojas', 'encargado@gastrosena.com', '3104567890', '$2b$10$elAlppC4AFChDTvtS6U7/.3.ZltWaDCNZaaY0kd0nZSpub/uGK/ja', 1, NULL, FALSE, TRUE), -- id 1 encargada
('1083000002', 'Carlos Andrés Muñoz', 'instructor@gastrosena.com', '3112223344', '$2b$10$//KFz2sbTRuYKCt.xpb7r.ZY.Wi./fkgR6VQco0Aq6d3SFO1kUNV6', 2, NULL, FALSE, TRUE), -- id 2 instructor con deuda vencida
('1083000003', 'Diana Patricia Cerón', 'diana.ceron@gastrosena.com', '3123334455', '$2b$10$//KFz2sbTRuYKCt.xpb7r.ZY.Wi./fkgR6VQco0Aq6d3SFO1kUNV6', 2, NULL, FALSE, TRUE), -- id 3 instructora con deuda
('1083000004', 'Jorge Iván Salazar', 'jorge.salazar@gastrosena.com', '3134445566', '$2b$10$//KFz2sbTRuYKCt.xpb7r.ZY.Wi./fkgR6VQco0Aq6d3SFO1kUNV6', 2, NULL, FALSE, TRUE), -- id 4 instructor al día
('1083000005', 'Laura Méndez Vargas', 'aprendiz@gastrosena.com', '3145556677', '$2b$10$OdO7h8EZBtl7c6sc9..4y.gU24Jfogtpyi59w87g4Fo1QZrC8uWH.', 3, 1, FALSE, TRUE), -- id 5 aprendiz de ADSO
('1083000006', 'Sebastián Calle Ortiz', 'sebastian.calle@gastrosena.com', '3156667788', '$2b$10$OdO7h8EZBtl7c6sc9..4y.gU24Jfogtpyi59w87g4Fo1QZrC8uWH.', 3, 1, FALSE, TRUE), -- id 6 aprendiz de ADSO
('1083000007', 'Camilo Rojas Peña', 'beneficiario@gastrosena.com', '3167778899', '$2b$10$OdO7h8EZBtl7c6sc9..4y.gU24Jfogtpyi59w87g4Fo1QZrC8uWH.', 3, 2, TRUE, TRUE), -- id 7 aprendiz beneficiario
('1083000008', 'Valentina Ortiz Gil', 'valentina.ortiz@gastrosena.com', '3178889900', '$2b$10$OdO7h8EZBtl7c6sc9..4y.gU24Jfogtpyi59w87g4Fo1QZrC8uWH.', 3, 3, FALSE, TRUE), -- id 8 aprendiz
('1083000009', 'Andrés Muñoz Cruz', 'andres.munoz@gastrosena.com', '3189990011', '$2b$10$OdO7h8EZBtl7c6sc9..4y.gU24Jfogtpyi59w87g4Fo1QZrC8uWH.', 3, 4, TRUE, TRUE), -- id 9 aprendiz beneficiario
('1083000010', 'Daniela Pérez Ríos', 'inactivo@gastrosena.com', '3190001122', '$2b$10$OdO7h8EZBtl7c6sc9..4y.gU24Jfogtpyi59w87g4Fo1QZrC8uWH.', 3, 5, FALSE, FALSE), -- id 10 aprendiz inactiva
('1083000011', 'Pedro Ruiz Gómez', 'invitado@gastrosena.com', '3201112233', '$2b$10$hOdcCFijV5gnNiKy07BYKevwx9IvO3jsTGcP04k1ROgjMMFGK4tXy', 4, NULL, FALSE, TRUE), -- id 11 invitado
('1083000012', 'Ana León Cárdenas', 'ana.leon@correo.com', '3212223344', '$2b$10$hOdcCFijV5gnNiKy07BYKevwx9IvO3jsTGcP04k1ROgjMMFGK4tXy', 4, NULL, FALSE, TRUE); -- id 12 invitada


-- MENÚS (12 menús, las fechas son contando desde hoy para que siempre haya menú de hoy)
-- cantidad_disponible = 80 menos las reservas que se hacen más abajo
INSERT INTO menus (fecha, nombre, descripcion, precio_aprendiz, precio_invitado, cantidad_total, cantidad_disponible) VALUES
(CURRENT_DATE - 40, 'Cerdo en salsa', 'Cerdo en salsa criolla, arroz, papa y jugo', 5000, 8000, 80, 79), -- id 1 hace 40 días
(CURRENT_DATE - 9, 'Arroz con pollo', 'Arroz con pollo, papa a la francesa, ensalada y jugo', 5000, 8000, 80, 80), -- id 2 hace 9 días
(CURRENT_DATE - 8, 'Frijolada', 'Fríjoles, arroz, huevo, tajadas de plátano y jugo', 5000, 8000, 80, 80), -- id 3 hace 8 días
(CURRENT_DATE - 7, 'Carne guisada con papa', 'Carne guisada, papa, arroz, ensalada y jugo', 5000, 8000, 80, 80), -- id 4 hace 7 días
(CURRENT_DATE - 6, 'Sudado de pollo', 'Sudado de pollo con papa, arroz y jugo', 5000, 8000, 80, 80), -- id 5 hace 6 días
(CURRENT_DATE - 5, 'Lentejas con arroz', 'Lentejas, arroz, huevo, plátano y jugo', 5000, 8000, 80, 78), -- id 6 hace 5 días
(CURRENT_DATE - 4, 'Pollo asado con ensalada', 'Pollo asado, papa salada, ensalada y jugo', 5000, 8000, 80, 80), -- id 7 hace 4 días
(CURRENT_DATE - 3, 'Sopa de verduras y seco', 'Sopa de verduras, arroz, carne desmechada y jugo', 5000, 8000, 80, 78), -- id 8 hace 3 días
(CURRENT_DATE - 2, 'Pescado frito', 'Mojarra frita, arroz, patacón, ensalada y jugo', 5000, 8000, 80, 77), -- id 9 hace 2 días
(CURRENT_DATE - 1, 'Ajiaco', 'Ajiaco con pollo, arroz, aguacate y jugo', 5000, 8000, 80, 76), -- id 10 ayer
(CURRENT_DATE, 'Bandeja campesina', 'Fríjoles, arroz, carne molida, huevo, plátano y jugo', 5000, 8000, 80, 74), -- id 11 hoy
(CURRENT_DATE + 1, 'Arroz chino', 'Arroz chino, papa a la francesa, ensalada y jugo', 5000, 8000, 80, 80); -- id 12 mañana


-- RESERVAS (19 reservas)
INSERT INTO reservas (menu_id, usuario_id, tipo, valor, estado) VALUES
(11, 5, 'APRENDIZ', 5000, 'RESERVADO'), -- hoy: Laura todavía no paga
(11, 6, 'APRENDIZ', 5000, 'PAGADO'), -- hoy: Sebastián pagó
(11, 7, 'BENEFICIARIO', 0, 'PAGADO'), -- hoy: Camilo es beneficiario
(11, 11, 'INVITADO', 8000, 'PAGADO'), -- hoy: Pedro pagó
(11, 2, 'INSTRUCTOR', 5000, 'PENDIENTE'), -- hoy: Carlos a su cuenta
(11, 8, 'APRENDIZ', 5000, 'NO_PAGADO'), -- hoy: Valentina no pagó
(10, 5, 'APRENDIZ', 5000, 'PAGADO'), -- ayer: Laura
(10, 9, 'BENEFICIARIO', 0, 'PAGADO'), -- ayer: Andrés beneficiario
(10, 12, 'INVITADO', 8000, 'PAGADO'), -- ayer: Ana
(10, 3, 'INSTRUCTOR', 5000, 'PENDIENTE'), -- ayer: Diana a su cuenta
(9, 6, 'APRENDIZ', 5000, 'PAGADO'), -- hace 2 días: Sebastián
(9, 2, 'INSTRUCTOR', 5000, 'PENDIENTE'), -- hace 2 días: Carlos a su cuenta
(9, 4, 'INSTRUCTOR', 5000, 'PAGADO'), -- hace 2 días: Jorge ya pagó
(8, 8, 'APRENDIZ', 5000, 'PAGADO'), -- hace 3 días: Valentina
(8, 4, 'INSTRUCTOR', 5000, 'PAGADO'), -- hace 3 días: Jorge ya pagó
(8, 5, 'APRENDIZ', 5000, 'CANCELADA'), -- hace 3 días: Laura canceló
(6, 7, 'BENEFICIARIO', 0, 'PAGADO'), -- hace 5 días: Camilo beneficiario
(6, 11, 'INVITADO', 8000, 'PAGADO'), -- hace 5 días: Pedro
(1, 2, 'INSTRUCTOR', 5000, 'PENDIENTE'); -- hace 40 días: Carlos (por esto su deuda está vencida)


-- PAGOS DE INSTRUCTORES
-- Carlos consumió 15.000 y abonó 5.000, debe 10.000
-- Jorge consumió 10.000 y pagó todo
-- Diana debe 5.000 y no ha pagado
INSERT INTO pagos_instructor (instructor_id, valor, metodo, observacion) VALUES
(2, 5000, 'EFECTIVO', 'Abono parcial'), -- Carlos
(4, 4000, 'NOMINA', 'Descuento de nómina'), -- Jorge
(4, 6000, 'TRANSFERENCIA', 'Pago del saldo'); -- Jorge


-- MATERIALES (14 materiales, el stock ya tiene en cuenta los movimientos de abajo)
INSERT INTO materiales (codigo_barras, nombre, categoria, unidad_medida, costo_unitario, stock, stock_minimo, fecha_vencimiento) VALUES
('7702001000011', 'Arroz blanco', 'GRANO', 'KG', 4200, 38, 20, NULL), -- id 1
('7702001000028', 'Fríjol rojo', 'GRANO', 'KG', 9800, 9, 10, NULL), -- id 2 stock bajo
('7702001000035', 'Pechuga de pollo', 'PROTEINA', 'KG', 14500, 20, 15, CURRENT_DATE + 4), -- id 3 se está venciendo
('7702001000042', 'Carne de res', 'PROTEINA', 'KG', 22000, 8, 10, CURRENT_DATE + 20), -- id 4 stock bajo
('7702001000059', 'Papa pastusa', 'VERDURA', 'KG', 2500, 40, 20, NULL), -- id 5
('7702001000066', 'Tomate chonto', 'VERDURA', 'KG', 3800, 3, 8, CURRENT_DATE + 30), -- id 6 stock crítico
('7702001000073', 'Cebolla cabezona', 'VERDURA', 'KG', 3200, 12, 5, NULL), -- id 7
('7702001000080', 'Aceite vegetal', 'ABARROTE', 'L', 9500, 15, 6, NULL), -- id 8
('7702001000097', 'Huevo AA', 'PROTEINA', 'UND', 550, 180, 60, CURRENT_DATE + 15), -- id 9
('7702001000103', 'Leche entera', 'LACTEO', 'L', 4200, 20, 10, CURRENT_DATE + 6), -- id 10 se está venciendo
('7702001000110', 'Plátano verde', 'FRUTA', 'UND', 700, 70, 40, NULL), -- id 11
('7702001000127', 'Bandeja desechable', 'DESECHABLE', 'UND', 350, 380, 100, NULL), -- id 12
('7702001000134', 'Lenteja', 'GRANO', 'KG', 7600, 10, 8, NULL), -- id 13
('7702001000141', 'Sal refinada', 'ABARROTE', 'KG', 1800, 0, 2, NULL); -- id 14 sin movimientos


-- MOVIMIENTOS DEL INVENTARIO (kardex, 22 movimientos hechos por la encargada id 1)
INSERT INTO movimientos_inventario (material_id, usuario_id, tipo, cantidad, saldo, concepto, fecha) VALUES
(1, 1, 'ENTRADA', 50, 50, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- arroz
(2, 1, 'ENTRADA', 15, 15, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- fríjol
(3, 1, 'ENTRADA', 30, 30, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- pollo
(4, 1, 'ENTRADA', 12, 12, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- carne
(5, 1, 'ENTRADA', 40, 40, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- papa
(6, 1, 'ENTRADA', 10, 10, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- tomate
(7, 1, 'ENTRADA', 12, 12, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- cebolla
(8, 1, 'ENTRADA', 18, 18, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- aceite
(9, 1, 'ENTRADA', 180, 180, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- huevo
(10, 1, 'ENTRADA', 20, 20, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- leche
(11, 1, 'ENTRADA', 100, 100, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- plátano
(12, 1, 'ENTRADA', 500, 500, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- bandejas
(13, 1, 'ENTRADA', 10, 10, 'Stock inicial', CURRENT_TIMESTAMP - INTERVAL '10 days'), -- lenteja
(1, 1, 'SALIDA', 12, 38, 'Preparación de almuerzos', CURRENT_TIMESTAMP - INTERVAL '2 days'), -- arroz: 50 - 12 = 38
(2, 1, 'SALIDA', 6, 9, 'Preparación de frijolada', CURRENT_TIMESTAMP - INTERVAL '2 days'), -- fríjol: 15 - 6 = 9
(3, 1, 'SALIDA', 10, 20, 'Preparación de almuerzos', CURRENT_TIMESTAMP - INTERVAL '2 days'), -- pollo: 30 - 10 = 20
(4, 1, 'MERMA', 2, 10, 'Carne con mal olor al abrir el empaque', CURRENT_TIMESTAMP - INTERVAL '2 days'), -- carne: 12 - 2 = 10
(4, 1, 'SALIDA', 2, 8, 'Preparación de carne guisada', CURRENT_TIMESTAMP - INTERVAL '2 days'), -- carne: 10 - 2 = 8
(6, 1, 'MERMA', 7, 3, 'Tomates dañados por exceso de maduración', CURRENT_TIMESTAMP - INTERVAL '2 days'), -- tomate: 10 - 7 = 3
(8, 1, 'SALIDA', 3, 15, 'Fritos del día', CURRENT_TIMESTAMP - INTERVAL '2 days'), -- aceite: 18 - 3 = 15
(11, 1, 'SALIDA', 30, 70, 'Tajadas y patacones', CURRENT_TIMESTAMP - INTERVAL '2 days'), -- plátano: 100 - 30 = 70
(12, 1, 'SALIDA', 120, 380, 'Despacho de almuerzos', CURRENT_TIMESTAMP - INTERVAL '2 days'); -- bandejas: 500 - 120 = 380


-- RECETAS (10 recetas)
INSERT INTO recetas (nombre, descripcion, precio_venta) VALUES
('Arroz con pollo', 'Plato fuerte con pollo desmechado', 5000), -- id 1
('Frijolada', 'Fríjoles con arroz, huevo y plátano', 5000), -- id 2
('Carne guisada con papa', 'Carne de res guisada con papa y arroz', 5000), -- id 3
('Sudado de pollo', 'Pollo sudado con papa y tomate', 5000), -- id 4
('Lentejas con arroz', 'Lentejas con arroz, huevo y plátano', 5000), -- id 5
('Pollo asado con ensalada', 'Pollo asado, papa y ensalada de tomate', 8000), -- id 6
('Bistec a caballo', 'Bistec de res con huevo frito y arroz', 5000), -- id 7 (cuesta más de lo que se vende)
('Huevos pericos con arroz', 'Huevos revueltos con tomate y cebolla', 5000), -- id 8
('Patacón con hogao', 'Patacones con hogao de tomate y cebolla', 5000), -- id 9
('Sopa de verduras', 'Sopa de papa, plátano y verduras', 5000); -- id 10


-- INGREDIENTES DE LAS RECETAS (receta_id, material_id, cantidad por plato)
INSERT INTO receta_ingredientes (receta_id, material_id, cantidad) VALUES
(1, 1, 0.120), (1, 3, 0.150), (1, 7, 0.020), (1, 8, 0.010), (1, 12, 1), -- arroz con pollo
(2, 2, 0.100), (2, 1, 0.100), (2, 11, 1), (2, 9, 1), (2, 12, 1), -- frijolada
(3, 4, 0.150), (3, 5, 0.200), (3, 6, 0.050), (3, 1, 0.100), (3, 12, 1), -- carne guisada
(4, 3, 0.150), (4, 5, 0.150), (4, 6, 0.050), (4, 1, 0.100), (4, 12, 1), -- sudado de pollo
(5, 13, 0.100), (5, 1, 0.120), (5, 9, 1), (5, 11, 1), (5, 12, 1), -- lentejas
(6, 3, 0.250), (6, 6, 0.080), (6, 5, 0.200), (6, 12, 1), -- pollo asado
(7, 4, 0.200), (7, 9, 1), (7, 1, 0.100), (7, 12, 1), -- bistec a caballo
(8, 9, 2), (8, 6, 0.050), (8, 7, 0.030), (8, 1, 0.100), (8, 12, 1), -- huevos pericos
(9, 11, 2), (9, 6, 0.080), (9, 7, 0.050), (9, 8, 0.030), (9, 12, 1), -- patacón con hogao
(10, 5, 0.200), (10, 11, 1), (10, 6, 0.050), (10, 7, 0.030), (10, 12, 1); -- sopa de verduras


-- SUGERENCIAS (10 sugerencias, 5 pendientes y 5 atendidas)
INSERT INTO sugerencias (usuario_id, asunto, mensaje, estado, respuesta, fecha_respuesta) VALUES
(5, 'Más opciones vegetarianas', 'Sería bueno tener un menú vegetariano al menos una vez por semana.', 'PENDIENTE', NULL, NULL), -- Laura
(6, 'Horario de entrega', 'La fila a las 12:00 es muy larga, podrían abrir a las 11:30.', 'ATENDIDA', 'Desde la próxima semana se abre a las 11:30.', CURRENT_TIMESTAMP), -- Sebastián
(7, 'Agradecimiento', 'Gracias por el apoyo con el almuerzo.', 'ATENDIDA', '¡Con gusto! Sigue adelante con tu formación.', CURRENT_TIMESTAMP), -- Camilo
(11, 'Pago con transferencia', '¿Se puede pagar el almuerzo por transferencia?', 'PENDIENTE', NULL, NULL), -- Pedro
(2, 'Corte de la cuenta', '¿Podrían enviar el corte de la cuenta mensual por correo?', 'PENDIENTE', NULL, NULL), -- Carlos
(8, 'Porciones', 'La porción de proteína del jueves fue pequeña.', 'ATENDIDA', 'Gracias, ajustamos el gramaje de la receta.', CURRENT_TIMESTAMP), -- Valentina
(9, 'Jugo natural', 'Me gustaría que el jugo fuera sin azúcar.', 'PENDIENTE', NULL, NULL), -- Andrés
(3, 'Cubiertos', 'Faltaron cubiertos desechables el martes.', 'ATENDIDA', 'Se aumentó el pedido de cubiertos.', CURRENT_TIMESTAMP), -- Diana
(12, 'Muy buena atención', 'Excelente servicio durante la visita al Tecnoparque.', 'ATENDIDA', 'Gracias por visitarnos.', CURRENT_TIMESTAMP), -- Ana
(4, 'Menú de la semana', 'Publicar el menú de toda la semana el lunes ayudaría a planear.', 'PENDIENTE', NULL, NULL); -- Jorge


-- AUDITORÍA DE LOS DATOS DE PRUEBA
-- Los datos de arriba los registró la encargada (id 1), así que ella queda como quien los creó
UPDATE fichas SET creado_por = 1;
-- Usuarios: los creó la encargada (ella misma no tiene quién la creó)
UPDATE usuarios SET creado_por = 1 WHERE id <> 1;
-- Menús creados por la encargada
UPDATE menus SET creado_por = 1;
-- Cada reserva la creó la persona que reservó
UPDATE reservas SET creado_por = usuario_id;
-- Los pagos los registró la encargada
UPDATE pagos_instructor SET creado_por = 1;
-- Materiales creados por la encargada
UPDATE materiales SET creado_por = 1;
-- Recetas creadas por la encargada
UPDATE recetas SET creado_por = 1;
-- Cada sugerencia la creó quien la mandó
UPDATE sugerencias SET creado_por = usuario_id;
-- Las sugerencias atendidas las modificó la encargada cuando respondió
UPDATE sugerencias SET modificado_por = 1, fecha_modificacion = fecha_respuesta WHERE estado = 'ATENDIDA';
