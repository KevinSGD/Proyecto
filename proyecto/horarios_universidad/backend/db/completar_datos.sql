-- Completa los datos que el solver necesita para poder generar un horario.
-- Idempotente: solo agrega lo que falta y no modifica registros existentes
-- (salvo subir la capacidad de un aula si es menor que la matricula de algun grupo).
--
-- Para cada periodo activo:
--   1. contrato activo a los docentes que no tienen (tiempo completo, 30 periodos/semana)
--   2. disponibilidad Lun-Vie, periodos 1-12, a docentes y aulas que no tienen ninguna
--   3. al menos un docente calificado en cada materia que ya tiene grupos
--   4. capacidad suficiente en las aulas para la matricula esperada de los grupos
DO $$
DECLARE
  p record;
  n integer;
  pendientes integer;
BEGIN
  FOR p IN SELECT id, institution_id FROM academic_periods WHERE is_active LOOP
    RAISE NOTICE 'Periodo activo %', p.id;

    INSERT INTO instructor_contracts
      (id, instructor_id, contract_type, max_daily_periods, max_weekly_periods, min_weekly_periods, max_days, is_active)
    SELECT gen_random_uuid(), i.id, 'tiempo_completo', 8, 30, 4, 5, true
    FROM instructors i
    WHERE i.institution_id = p.institution_id AND i.is_active
      AND NOT EXISTS (SELECT 1 FROM instructor_contracts c WHERE c.instructor_id = i.id AND c.is_active);
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  contratos creados: %', n;

    INSERT INTO instructor_availabilities (id, instructor_id, period_id, day_of_week, period, is_available)
    SELECT gen_random_uuid(), i.id, p.id, d.d, h.h, true
    FROM instructors i
    CROSS JOIN generate_series(0, 4) AS d(d)
    CROSS JOIN generate_series(1, 12) AS h(h)
    WHERE i.institution_id = p.institution_id AND i.is_active
      AND NOT EXISTS (SELECT 1 FROM instructor_availabilities a WHERE a.instructor_id = i.id AND a.period_id = p.id);
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  disponibilidad de docentes (franjas): %', n;

    INSERT INTO classroom_availabilities (id, classroom_id, period_id, day_of_week, period, is_available)
    SELECT gen_random_uuid(), c.id, p.id, d.d, h.h, true
    FROM classrooms c
    CROSS JOIN generate_series(0, 4) AS d(d)
    CROSS JOIN generate_series(1, 12) AS h(h)
    WHERE c.institution_id = p.institution_id AND c.is_active
      AND NOT EXISTS (SELECT 1 FROM classroom_availabilities a WHERE a.classroom_id = c.id AND a.period_id = p.id);
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  disponibilidad de aulas (franjas): %', n;

    -- Materias con grupos y sin ningun docente calificado: se reparten entre los docentes activos
    INSERT INTO instructor_specialties (id, instructor_id, subject_id, proficiency_level)
    SELECT gen_random_uuid(), pick.instructor_id, sub.subject_id, 5
    FROM (
      SELECT s.id AS subject_id, row_number() OVER (ORDER BY s.code) AS rn
      FROM subjects s
      WHERE s.institution_id = p.institution_id
        AND EXISTS (SELECT 1 FROM groups g WHERE g.subject_id = s.id)
        AND NOT EXISTS (SELECT 1 FROM instructor_specialties sp WHERE sp.subject_id = s.id)
    ) sub
    JOIN (
      SELECT i.id AS instructor_id,
             row_number() OVER (ORDER BY i.employee_code) AS rn,
             count(*) OVER () AS total
      FROM instructors i
      WHERE i.institution_id = p.institution_id AND i.is_active
    ) pick ON pick.rn = ((sub.rn - 1) % pick.total) + 1;
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  especialidades creadas: %', n;

    UPDATE classrooms c
    SET capacity = m.max_enrollment
    FROM (
      SELECT max(g.expected_enrollment) AS max_enrollment
      FROM groups g JOIN subjects s ON s.id = g.subject_id
      WHERE s.institution_id = p.institution_id
    ) m
    WHERE c.institution_id = p.institution_id AND c.is_active AND NOT c.is_virtual
      AND m.max_enrollment IS NOT NULL
      AND c.capacity < m.max_enrollment
      AND NOT EXISTS (
        SELECT 1 FROM classrooms c2
        WHERE c2.institution_id = p.institution_id AND c2.is_active AND c2.capacity >= m.max_enrollment
      )
      AND c.id = (SELECT id FROM classrooms WHERE institution_id = p.institution_id AND is_active AND NOT is_virtual
                  ORDER BY capacity DESC, code LIMIT 1);
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE '  aulas con capacidad ajustada: %', n;

    SELECT count(*) INTO pendientes
    FROM subjects s
    WHERE s.institution_id = p.institution_id
      AND EXISTS (SELECT 1 FROM groups g WHERE g.subject_id = s.id)
      AND NOT EXISTS (SELECT 1 FROM instructor_specialties sp WHERE sp.subject_id = s.id);
    IF pendientes > 0 THEN
      RAISE NOTICE '  ATENCION: % materia(s) con grupos siguen sin docente (no hay docentes activos)', pendientes;
    END IF;
  END LOOP;
END
$$;
