-- Agrega docentes y aulas de RESPALDO para que el solver tenga holgura.
-- Idempotente (codigos RESP-*). No modifica ni borra registros existentes.
-- Correr DESPUES de completar_datos.sql.
-- Es deliberadamente pequeno: demasiados candidatos agrandan el modelo y el solver
-- puede agotar su tiempo (timeout) sin encontrar solucion.
--
-- Por cada periodo activo agrega:
--   * 2 docentes (RESP-1..2): contrato de 40 periodos/semana, disponibilidad Lun-Vie 1-12,
--     calificados SOLO en las materias con grupos que tengan menos de 2 docentes calificados
--   * 2 aulas presenciales (RESP-A1..2) con capacidad >= la mayor matricula esperada,
--     disponibilidad Lun-Vie 1-12 y TODOS los recursos de la institucion
--   * 1 aula virtual (RESP-V1), solo si hay grupos virtuales y no existe ninguna
DO $$
DECLARE
  p record;
  n integer;
  cap integer;
BEGIN
  FOR p IN SELECT id, institution_id FROM academic_periods WHERE is_active LOOP
    RAISE NOTICE 'Periodo activo %', p.id;

    INSERT INTO instructors (id, institution_id, area_id, employee_code, first_name, last_name, email, phone, is_active)
    SELECT gen_random_uuid(), p.institution_id, NULL, 'RESP-' || g, 'Docente', 'Respaldo ' || g,
           'respaldo' || g || '@udemo.edu', '', true
    FROM generate_series(1, 2) AS g
    WHERE NOT EXISTS (
      SELECT 1 FROM instructors i
      WHERE i.institution_id = p.institution_id AND i.employee_code = 'RESP-' || g
    );
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  docentes de respaldo creados: %', n;

    INSERT INTO instructor_contracts
      (id, instructor_id, contract_type, max_daily_periods, max_weekly_periods, min_weekly_periods, max_days, is_active)
    SELECT gen_random_uuid(), i.id, 'tiempo_completo', 8, 40, 0, 5, true
    FROM instructors i
    WHERE i.institution_id = p.institution_id AND i.employee_code LIKE 'RESP-%'
      AND NOT EXISTS (SELECT 1 FROM instructor_contracts c WHERE c.instructor_id = i.id AND c.is_active);

    INSERT INTO instructor_availabilities (id, instructor_id, period_id, day_of_week, period, is_available)
    SELECT gen_random_uuid(), i.id, p.id, d.d, h.h, true
    FROM instructors i
    CROSS JOIN generate_series(0, 4) AS d(d)
    CROSS JOIN generate_series(1, 12) AS h(h)
    WHERE i.institution_id = p.institution_id AND i.employee_code LIKE 'RESP-%'
      AND NOT EXISTS (SELECT 1 FROM instructor_availabilities a WHERE a.instructor_id = i.id AND a.period_id = p.id);

    INSERT INTO instructor_specialties (id, instructor_id, subject_id, proficiency_level)
    SELECT gen_random_uuid(), i.id, s.id, 5
    FROM instructors i
    CROSS JOIN subjects s
    WHERE i.institution_id = p.institution_id AND i.employee_code LIKE 'RESP-%'
      AND s.institution_id = p.institution_id
      AND EXISTS (SELECT 1 FROM groups g WHERE g.subject_id = s.id)
      AND (SELECT count(*) FROM instructor_specialties sp
           JOIN instructors q ON q.id = sp.instructor_id
           WHERE sp.subject_id = s.id AND q.employee_code NOT LIKE 'RESP-%') < 2
    ON CONFLICT (instructor_id, subject_id) DO NOTHING;
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  especialidades de respaldo: %', n;

    SELECT greatest(60, coalesce(max(g.expected_enrollment), 0)) INTO cap
    FROM groups g JOIN subjects s ON s.id = g.subject_id
    WHERE s.institution_id = p.institution_id;

    INSERT INTO classrooms (id, institution_id, building_id, name, code, capacity, floor, is_virtual, is_active)
    SELECT gen_random_uuid(), p.institution_id, NULL, 'Aula Respaldo ' || g, 'RESP-A' || g, cap, 1, false, true
    FROM generate_series(1, 2) AS g
    WHERE NOT EXISTS (
      SELECT 1 FROM classrooms c
      WHERE c.institution_id = p.institution_id AND c.code = 'RESP-A' || g
    );
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  aulas de respaldo creadas: % (capacidad %)', n, cap;

    IF EXISTS (
         SELECT 1 FROM groups g JOIN subjects s ON s.id = g.subject_id
         WHERE s.institution_id = p.institution_id AND g.modality = 'virtual'
       )
       AND NOT EXISTS (
         SELECT 1 FROM classrooms c
         WHERE c.institution_id = p.institution_id AND c.is_virtual AND c.is_active
       ) THEN
      INSERT INTO classrooms (id, institution_id, building_id, name, code, capacity, floor, is_virtual, is_active)
      SELECT gen_random_uuid(), p.institution_id, NULL, 'Aula Virtual Respaldo', 'RESP-V1', cap, 0, true, true
      WHERE NOT EXISTS (
        SELECT 1 FROM classrooms c WHERE c.institution_id = p.institution_id AND c.code = 'RESP-V1'
      );
      RAISE NOTICE '  aula virtual de respaldo creada';
    END IF;

    INSERT INTO classroom_availabilities (id, classroom_id, period_id, day_of_week, period, is_available)
    SELECT gen_random_uuid(), c.id, p.id, d.d, h.h, true
    FROM classrooms c
    CROSS JOIN generate_series(0, 4) AS d(d)
    CROSS JOIN generate_series(1, 12) AS h(h)
    WHERE c.institution_id = p.institution_id AND c.code LIKE 'RESP-%'
      AND NOT EXISTS (SELECT 1 FROM classroom_availabilities a WHERE a.classroom_id = c.id AND a.period_id = p.id);

    INSERT INTO room_resources (id, classroom_id, resource_id, quantity)
    SELECT gen_random_uuid(), c.id, r.id, 1
    FROM classrooms c
    CROSS JOIN resources r
    WHERE c.institution_id = p.institution_id AND c.code LIKE 'RESP-%' AND NOT c.is_virtual
      AND r.institution_id = p.institution_id
    ON CONFLICT (classroom_id, resource_id) DO NOTHING;
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  recursos asignados a aulas de respaldo: %', n;
  END LOOP;
END
$$;
