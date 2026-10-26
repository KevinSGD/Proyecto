-- REINICIA LA BASE: BORRA TODOS LOS DATOS y deja un conjunto minimo con UNA sola area.
-- Conserva las tablas y la version de Alembic. Todo en una sola transaccion: si algo falla no se aplica nada.
-- Candado: solo corre si la base se llama 'scheduler'.
--
-- Deja listo para generar horario (corrida factible):
--   1 institucion, 1 campus, periodo 2026-2 activo, tipo de horario Diurno
--   1 area (Ingenieria) con 5 materias, 4 docentes (con contrato, disponibilidad y especialidades),
--   3 aulas con disponibilidad, y 1 oferta APROBADA con sus 5 grupos
--   usuarios: director@udemo.edu / director123 y coordinador@udemo.edu / coordinador123 (area Ingenieria)

DO $$
BEGIN
  IF current_database() <> 'scheduler' THEN
    RAISE EXCEPTION 'Candado: la base es %, no scheduler. No se borra nada.', current_database();
  END IF;
END
$$;

DO $$
DECLARE t text;
BEGIN
  SELECT string_agg(format('%I', tablename), ', ') INTO t
  FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version';
  EXECUTE 'TRUNCATE TABLE ' || t || ' RESTART IDENTITY CASCADE';
  RAISE NOTICE 'Base vaciada';
END
$$;

-- Institucion, campus, area y tipo de horario usan los mismos ids fijos que los seeds; el resto usa
-- un rango propio (...c###) para que correr seed_demo despues no choque por ids duplicados.
-- Institucion, campus, periodo, tipo de horario
INSERT INTO institutions (id, name, abbreviation, address, email, phone, website, logo_url, is_active, metadata)
VALUES ('00000000-0000-4000-a000-000000000001', 'Universidad Demo', 'UDEMO', '', 'admin@udemo.edu', '', '', '', true, '{}');

INSERT INTO campuses (id, institution_id, name, code, address, city, is_active)
VALUES ('00000000-0000-4000-a000-000000000010', '00000000-0000-4000-a000-000000000001', 'Campus Principal', 'MAIN', 'Av. Universidad S/N', 'Ciudad Demo', true);

INSERT INTO academic_periods (id, institution_id, name, year, period_number, status, is_active, start_date, end_date)
VALUES ('00000000-0000-4000-a000-00000000c0c0', '00000000-0000-4000-a000-000000000001', '2026-2', 2026, 2, 'active', true, '2026-08-01', '2026-12-15');

INSERT INTO schedule_types (id, institution_id, name, schedule_type, active_days, start_period, end_period, slot_duration_minutes, start_hour)
VALUES ('00000000-0000-4000-a000-000000006001', '00000000-0000-4000-a000-000000000001', 'Diurno', 'regular', '[0,1,2,3,4]', 1, 12, 60, 7);

-- Roles y usuarios
INSERT INTO roles (id, institution_id, name, description, is_system, is_active) VALUES
  ('00000000-0000-4000-a000-000000000a01', '00000000-0000-4000-a000-000000000001', 'super_admin',      'Administrador del sistema', true, true),
  ('00000000-0000-4000-a000-000000000a02', '00000000-0000-4000-a000-000000000001', 'director',         'Director academico',        true, true),
  ('00000000-0000-4000-a000-000000000a03', '00000000-0000-4000-a000-000000000001', 'area_coordinator', 'Coordinador de area',       true, true),
  ('00000000-0000-4000-a000-000000000a04', '00000000-0000-4000-a000-000000000001', 'viewer',           'Solo lectura',              true, true);

INSERT INTO users (id, institution_id, role_id, email, name, phone, is_active, hashed_password) VALUES
  ('00000000-0000-4000-a000-000000000b01', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000a02',
   'director@udemo.edu', 'Carlos Mendoza', '', true, '$2b$12$OkwuAZTzkGfjjIaDRuMeouPWfzv23LuD8z4hrVcIskU408muU6ylW'),
  ('00000000-0000-4000-a000-000000000b02', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000a03',
   'coordinador@udemo.edu', 'Maria Lopez', '', true, '$2b$12$6rNBmNTXMtMFoKu1WOiQYeskK3E1TeSmiOd6aUTcPN9LxYzOgh.8K');

-- La unica area
INSERT INTO academic_areas (id, institution_id, name, code, description, is_active)
VALUES ('00000000-0000-4000-a000-000000000101', '00000000-0000-4000-a000-000000000001', 'Ingenieria', 'ING', 'Area de ingenieria y tecnologia', true);

INSERT INTO user_areas (id, user_id, area_id)
VALUES (gen_random_uuid(), '00000000-0000-4000-a000-000000000b02', '00000000-0000-4000-a000-000000000101');

-- Materias (5)
INSERT INTO subjects (id, institution_id, area_id, code, name, credit_hours, weekly_hours, modality_default, is_active) VALUES
  ('00000000-0000-4000-a000-00000000c201', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS101', 'Introduccion a la Ingenieria', 3, 3, 'presential', true),
  ('00000000-0000-4000-a000-00000000c202', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS102', 'Programacion',                 3, 3, 'presential', true),
  ('00000000-0000-4000-a000-00000000c203', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS103', 'Estructuras de Datos',          3, 3, 'presential', true),
  ('00000000-0000-4000-a000-00000000c204', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS104', 'Bases de Datos',                3, 3, 'presential', true),
  ('00000000-0000-4000-a000-00000000c205', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS105', 'Redes de Computadores',        2, 2, 'presential', true);

-- Docentes (4) con contrato, y especialidades
INSERT INTO instructors (id, institution_id, area_id, employee_code, first_name, last_name, email, phone, is_active) VALUES
  ('00000000-0000-4000-a000-00000000c101', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS-D1', 'Ana',    'Martinez',  'ana.martinez@udemo.edu',   '', true),
  ('00000000-0000-4000-a000-00000000c102', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS-D2', 'Jose',   'Rodriguez', 'jose.rodriguez@udemo.edu', '', true),
  ('00000000-0000-4000-a000-00000000c103', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS-D3', 'Laura',  'Hernandez', 'laura.hernandez@udemo.edu', '', true),
  ('00000000-0000-4000-a000-00000000c104', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-000000000101', 'SIS-D4', 'Miguel', 'Torres',    'miguel.torres@udemo.edu',  '', true);

INSERT INTO instructor_contracts (id, instructor_id, contract_type, max_daily_periods, max_weekly_periods, min_weekly_periods, max_days, is_active)
SELECT gen_random_uuid(), id, 'tiempo_completo', 8, 30, 0, 5, true FROM instructors;

INSERT INTO instructor_specialties (id, instructor_id, subject_id, proficiency_level) VALUES
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c101', '00000000-0000-4000-a000-00000000c201', 5),
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c101', '00000000-0000-4000-a000-00000000c202', 5),
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c102', '00000000-0000-4000-a000-00000000c202', 5),
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c102', '00000000-0000-4000-a000-00000000c203', 5),
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c103', '00000000-0000-4000-a000-00000000c203', 5),
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c103', '00000000-0000-4000-a000-00000000c204', 5),
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c104', '00000000-0000-4000-a000-00000000c204', 5),
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c104', '00000000-0000-4000-a000-00000000c205', 5),
  (gen_random_uuid(), '00000000-0000-4000-a000-00000000c104', '00000000-0000-4000-a000-00000000c201', 5);

-- Edificio y aulas (3, capacidad 40)
INSERT INTO buildings (id, campus_id, name, code, floors, is_active)
VALUES ('00000000-0000-4000-a000-00000000c301', '00000000-0000-4000-a000-000000000010', 'Edificio de Sistemas', 'ED-S', 2, true);

INSERT INTO classrooms (id, institution_id, building_id, name, code, capacity, floor, is_virtual, is_active) VALUES
  ('00000000-0000-4000-a000-00000000c401', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-00000000c301', 'Aula S101', 'S101', 40, 1, false, true),
  ('00000000-0000-4000-a000-00000000c402', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-00000000c301', 'Aula S102', 'S102', 40, 1, false, true),
  ('00000000-0000-4000-a000-00000000c403', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-00000000c301', 'Aula S103', 'S103', 40, 2, false, true);

-- Disponibilidad Lun-Vie, periodos 1-12, de docentes y aulas
INSERT INTO instructor_availabilities (id, instructor_id, period_id, day_of_week, period, is_available)
SELECT gen_random_uuid(), i.id, '00000000-0000-4000-a000-00000000c0c0', d, h, true
FROM instructors i, generate_series(0, 4) d, generate_series(1, 12) h;

INSERT INTO classroom_availabilities (id, classroom_id, period_id, day_of_week, period, is_available)
SELECT gen_random_uuid(), c.id, '00000000-0000-4000-a000-00000000c0c0', d, h, true
FROM classrooms c, generate_series(0, 4) d, generate_series(1, 12) h;

-- Oferta aprobada con sus lineas y 5 grupos (1 por materia)
INSERT INTO academic_offerings (id, institution_id, period_id, area_id, status, observations, created_by)
VALUES ('00000000-0000-4000-a000-00000000c702', '00000000-0000-4000-a000-000000000001', '00000000-0000-4000-a000-00000000c0c0',
        '00000000-0000-4000-a000-000000000101', 'approved', '', '00000000-0000-4000-a000-000000000b02');

INSERT INTO offering_lines (id, offering_id, subject_id, num_groups, expected_enrollment_per_group, modality, schedule_type_id)
SELECT gen_random_uuid(), '00000000-0000-4000-a000-00000000c702', s.id, 1, 30, 'presential', '00000000-0000-4000-a000-000000006001'
FROM subjects s;

INSERT INTO groups (id, offering_line_id, subject_id, group_number, expected_enrollment, modality, schedule_type_id, priority)
SELECT gen_random_uuid(), l.id, l.subject_id, 1, 30, 'presential', '00000000-0000-4000-a000-000000006001', 3
FROM offering_lines l;
