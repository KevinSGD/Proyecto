"""Benchmark del motor de optimización — pensado para ejecutarse en el
servidor AWS EC2 (Debian 13, t3.micro).

Corre cuatro escenarios (pequeño, mediano, grande y curricula_completo) de
extremo a extremo a través de SolverEngine, imprime el entorno de ejecución
(CPU, RAM, SO) y las estadísticas reales de cada corrida con la mayor
precisión posible — incluyendo tiempo de CPU real (usuario + sistema) y
pico de memoria RSS del proceso, medidos a nivel de sistema operativo.

Uso (desde la carpeta backend):
    python -m scripts.benchmark_aws
"""
from __future__ import annotations

import json
import os
import platform
import resource
import sys
import time

sys.path.insert(0, ".")

from app.core.utils.types import generate_id
from app.solver.config import SolverConfiguration
from app.solver.context import (
    OptimizationProblem,
    SolverClassroom,
    SolverGroup,
    SolverInstructor,
    SolverTimeConfig,
)
from app.solver.engine import SolverEngine


# ── entorno de ejecución (se auto-documenta) ────────────────────────────────
def print_environment() -> None:
    print("=" * 60)
    print("ENTORNO DE EJECUCIÓN")
    print("=" * 60)
    print(f"Sistema operativo : {platform.platform()}")
    print(f"Python            : {platform.python_version()}")
    print(f"Procesadores(vCPU): {os.cpu_count()}")
    # CPU model + RAM (Linux)
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    print(f"CPU               : {line.split(':', 1)[1].strip()}")
                    break
    except OSError:
        pass
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    kb = int(line.split()[1])
                    print(f"Memoria RAM       : {kb / 1024 / 1024:.2f} GB")
                    break
    except OSError:
        pass
    try:
        import ortools
        print(f"OR-Tools          : {ortools.__version__}")
    except Exception:
        pass
    print()


# ── escenarios ──────────────────────────────────────────────────────────────
def make_small() -> OptimizationProblem:
    i1, i2 = generate_id(), generate_id()
    r1, r2 = generate_id(), generate_id()
    s1, s2 = generate_id(), generate_id()
    st = generate_id()
    days = [1, 2, 3]
    slots = {(w, h) for w in days for h in range(1, 6)}
    groups = [
        SolverGroup(id=generate_id(), subject_id=s1, group_number=1, expected_enrollment=30,
                    modality="presencial", schedule_type_id=st, num_blocks=2, block_durations=(2, 2),
                    candidate_instructors=[i1, i2], compatible_classrooms=[r1, r2]),
        SolverGroup(id=generate_id(), subject_id=s2, group_number=1, expected_enrollment=25,
                    modality="presencial", schedule_type_id=st, num_blocks=1, block_durations=(3,),
                    candidate_instructors=[i1], compatible_classrooms=[r1]),
    ]
    instructors = [
        SolverInstructor(id=i1, max_daily_periods=6, max_weekly_periods=12, min_weekly_periods=0,
                         max_days=5, available_slots=set(slots),
                         preferences={groups[0].id: 8, groups[1].id: 5}),
        SolverInstructor(id=i2, max_daily_periods=4, max_weekly_periods=8, min_weekly_periods=0,
                         max_days=5, available_slots=set(slots)),
    ]
    classrooms = [SolverClassroom(id=r1, capacity=40, available_slots=set(slots)),
                  SolverClassroom(id=r2, capacity=35, available_slots=set(slots))]
    return OptimizationProblem(institution_id=generate_id(), period_id=generate_id(),
                              groups=groups, instructors=instructors, classrooms=classrooms,
                              time_config=SolverTimeConfig(days=days, periods_per_day=5))


def make_medium() -> OptimizationProblem:
    days = [1, 2, 3, 4, 5]
    ppd = 8
    slots = {(w, h) for w in days for h in range(1, ppd + 1)}
    inst = [generate_id() for _ in range(5)]
    rooms = [generate_id() for _ in range(4)]
    subj = [generate_id() for _ in range(8)]
    st = generate_id()
    instructors = [SolverInstructor(id=inst[i], max_daily_periods=ppd, max_weekly_periods=20,
                   min_weekly_periods=4, max_days=5, available_slots=set(slots)) for i in range(5)]
    classrooms = [SolverClassroom(id=rooms[i], capacity=30 + i * 10, available_slots=set(slots)) for i in range(4)]
    configs = [(2, (2, 2), 30), (1, (3,), 25), (2, (2, 1), 20), (1, (4,), 35), (2, (2, 2), 28),
               (1, (2,), 22), (2, (3, 2), 40), (1, (2,), 18), (2, (2, 2), 32), (1, (3,), 26)]
    groups = []
    for idx, (nb, dur, enr) in enumerate(configs):
        cand = [inst[idx % 5], inst[(idx + 1) % 5]]
        comp = [r for i, r in enumerate(rooms) if classrooms[i].capacity >= enr] or [rooms[-1]]
        groups.append(SolverGroup(id=generate_id(), subject_id=subj[idx % len(subj)], group_number=1,
                      expected_enrollment=enr, modality="presencial", schedule_type_id=st,
                      num_blocks=nb, block_durations=dur, candidate_instructors=cand, compatible_classrooms=comp))
    for i, ins in enumerate(instructors):
        ins.preferences = {g.id: 5 + (i + j) % 6 for j, g in enumerate(groups)}
    return OptimizationProblem(institution_id=generate_id(), period_id=generate_id(),
                              groups=groups, instructors=instructors, classrooms=classrooms,
                              time_config=SolverTimeConfig(days=days, periods_per_day=ppd))


def make_large() -> OptimizationProblem:
    """30 grupos, 10 docentes, 8 aulas, 5 días × 10 periodos.

    Incorpora disponibilidad parcial y preferencias para ejercitar también
    las restricciones de disponibilidad (HD-09/HD-10) y de afinidad."""
    days = [1, 2, 3, 4, 5]
    ppd = 10
    full = {(w, h) for w in days for h in range(1, ppd + 1)}
    n_inst, n_rooms, n_subj = 10, 8, 20
    inst = [generate_id() for _ in range(n_inst)]
    rooms = [generate_id() for _ in range(n_rooms)]
    subj = [generate_id() for _ in range(n_subj)]
    st = generate_id()
    # disponibilidad parcial: cada docente no está disponible un día distinto
    instructors = []
    for i in range(n_inst):
        blocked_day = days[i % len(days)]
        avail = {(w, h) for (w, h) in full if w != blocked_day}
        instructors.append(SolverInstructor(id=inst[i], max_daily_periods=ppd, max_weekly_periods=24,
                           min_weekly_periods=4, max_days=5, available_slots=avail))
    classrooms = [SolverClassroom(id=rooms[i], capacity=25 + i * 8, available_slots=set(full)) for i in range(n_rooms)]
    patterns = [(2, (2, 2), 30), (1, (3,), 25), (2, (2, 1), 22), (1, (4,), 35), (2, (3, 2), 40)]
    groups = []
    for idx in range(30):
        nb, dur, enr = patterns[idx % len(patterns)]
        cand = [inst[idx % n_inst], inst[(idx + 3) % n_inst], inst[(idx + 6) % n_inst]]
        comp = [r for i, r in enumerate(rooms) if classrooms[i].capacity >= enr] or [rooms[-1]]
        groups.append(SolverGroup(id=generate_id(), subject_id=subj[idx % n_subj], group_number=1 + idx // n_subj,
                      expected_enrollment=enr, modality="presencial", schedule_type_id=st,
                      num_blocks=nb, block_durations=dur, candidate_instructors=cand, compatible_classrooms=comp))
    for i, ins in enumerate(instructors):
        ins.preferences = {g.id: 4 + (i + j) % 7 for j, g in enumerate(groups)}
    return OptimizationProblem(institution_id=generate_id(), period_id=generate_id(),
                              groups=groups, instructors=instructors, classrooms=classrooms,
                              time_config=SolverTimeConfig(days=days, periods_per_day=ppd))


MATERIAS_PLAN_ESTUDIOS = [
    # Ciencias básicas
    "Matemáticas Básicas", "Algebra Lineal", "Física Mecánica y LAB",
    "Cálculo Diferencial", "Matemáticas Discretas", "Física Electromagnética y LAB",
    "Cálculo Integral", "Probabilidad y Estadística",
    "Ecuaciones Diferenciales", "Calculo Vectorial",
    "Matemáticas Especiales", "Métodos Numéricos",
    # Desarrollo de software
    "Lógica de programación", "TGS", "Orientación a la ingeniería",
    "Programación orientada a objetos",
    "Estructura de datos", "Análisis y diseño de software",
    "Taller de programación", "Patrones y metodologías de la construcción de software",
    "Computación gráfica",
    "Ingeniería web 1", "Arquitectura de software", "Diseño de interfaces",
    "Ingeniería web 2", "Estándares y métricas de calidad de software", "Legislación informática",
    "Computación móvil",
    "Desarrollo de software seguro", "Gerencia de proyectos de software", "Inteligencia artificial",
    # Ciencia de Datos
    "Teoría de Bases de Datos", "Inteligencia de Negocios",
    "Sistemas Expertos", "Sistemas Transaccionales",
    # Infraestructura TI
    "Arquitectura de Hardware", "Infraestructura Tecnológica I", "Infraestructura Tecnológica II",
    "Sistemas Operativos", "Sistemas Distribuidos", "Nuevas Tecnologías de Desarrollo",
    # Básicas de Ingeniería
    "Contabilidad General", "Optimización Lineal", "Modelamiento Estocástico", "Práctica Empresarial",
    # Investigativo
    "Estrategias del Pensamiento para la Investigación", "Fundamentos de Investigación",
    "Investigación Cualitativa", "Investigación Cuantitativa",
    "Proyecto de Investigación I", "Proyecto de Investigación II",
    "Proyecto de Investigación III", "Proyecto de Investigación IV",
    # Idiomas
    "Inglés Inicial", "Inglés Básico I", "Inglés Básico 2", "Inglés Preintermedio",
    "Inglés Intermedio", "Inglés Intermedio Alto", "Inglés Avanzado",
    # Humanidades transversales
    "Catedra Manuela Beltrán", "Comunicación oral y escrita", "Filosofía",
    "Constitución Política", "Educación Ambiental", "Ética",
]


def make_curricula_completo() -> OptimizationProblem:
    """Programa académico completo: 66 materias reales repartidas en 8 semestres
    y 8 áreas de formación (un grupo por materia), 6 días × 12 periodos.

    Es el escenario más grande de los cuatro: ejercita el motor con el volumen
    de datos de un periodo académico real completo, no sintético."""
    days = [1, 2, 3, 4, 5, 6]
    ppd = 12
    full = {(w, h) for w in days for h in range(1, ppd + 1)}
    n_subj = len(MATERIAS_PLAN_ESTUDIOS)
    n_inst, n_rooms = 24, 18
    inst = [generate_id() for _ in range(n_inst)]
    rooms = [generate_id() for _ in range(n_rooms)]
    subj = [generate_id() for _ in range(n_subj)]
    st = generate_id()
    # disponibilidad parcial: cada docente no está disponible un día distinto
    instructors = []
    for i in range(n_inst):
        blocked_day = days[i % len(days)]
        avail = {(w, h) for (w, h) in full if w != blocked_day}
        instructors.append(SolverInstructor(id=inst[i], max_daily_periods=ppd, max_weekly_periods=22,
                           min_weekly_periods=4, max_days=6, available_slots=avail))
    classrooms = [SolverClassroom(id=rooms[i], capacity=25 + (i % 6) * 10, available_slots=set(full)) for i in range(n_rooms)]
    patterns = [(2, (2, 2), 30), (1, (3,), 25), (2, (2, 1), 22), (1, (4,), 35), (2, (3, 2), 40), (1, (2,), 20)]
    groups = []
    for idx in range(n_subj):
        nb, dur, enr = patterns[idx % len(patterns)]
        cand = [inst[idx % n_inst], inst[(idx + 5) % n_inst], inst[(idx + 11) % n_inst]]
        comp = [r for i, r in enumerate(rooms) if classrooms[i].capacity >= enr] or [rooms[-1]]
        groups.append(SolverGroup(id=generate_id(), subject_id=subj[idx], group_number=1,
                      expected_enrollment=enr, modality="presencial", schedule_type_id=st,
                      num_blocks=nb, block_durations=dur, candidate_instructors=cand, compatible_classrooms=comp))
    for i, ins in enumerate(instructors):
        ins.preferences = {g.id: 4 + (i + j) % 7 for j, g in enumerate(groups)}
    return OptimizationProblem(institution_id=generate_id(), period_id=generate_id(),
                              groups=groups, instructors=instructors, classrooms=classrooms,
                              time_config=SolverTimeConfig(days=days, periods_per_day=ppd))


def run(label: str, problem: OptimizationProblem, max_time: int) -> dict:
    workers = os.cpu_count() or 1
    config = SolverConfiguration(max_time_seconds=max_time, num_workers=workers, random_seed=42)

    # Snapshot de CPU/RAM a nivel de SO antes de resolver (stdlib, sin dependencias).
    cpu_before = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter()
    result = SolverEngine(config=config).solve(problem)
    wall = time.perf_counter() - t0
    cpu_after = resource.getrusage(resource.RUSAGE_SELF)

    cpu_user_s = cpu_after.ru_utime - cpu_before.ru_utime
    cpu_sys_s = cpu_after.ru_stime - cpu_before.ru_stime
    cpu_total_s = cpu_user_s + cpu_sys_s
    # % de CPU respecto al tiempo de reloj — puede superar 100% si el solver
    # usa varios hilos/núcleos en paralelo (num_workers).
    cpu_pct = (cpu_total_s / wall * 100) if wall > 0 else 0.0
    # Pico de RSS del proceso completo hasta este punto (ru_maxrss en KB en Linux).
    # Es acumulado desde que arrancó el script, no exclusivo de este escenario.
    ram_pico_proceso_mb = cpu_after.ru_maxrss / 1024

    s = result.statistics
    row = {
        "escenario": label,
        "grupos": s.groups_total, "docentes": s.instructors_total, "aulas": s.rooms_total,
        "slots": s.time_slots_total, "workers": workers,
        "estado": result.status.value, "asignaciones": len(result.assignments),
        "variables": s.num_variables, "restricciones": s.num_constraints,
        "restr_duras": s.hard_constraints_total, "restr_blandas": s.soft_constraints_total,
        "objetivo": s.objective_value, "gap": s.gap,
        "workload_spread": s.workload_spread, "avg_preference": s.avg_preference_score,
        "room_utilization_pct": s.room_utilization_pct,
        "memoria_python_mb": s.memory_usage_mb,
        "t_construccion_modelo_s": round(s.timings.get("model_build", 0), 4),
        "t_restricciones_s": round(s.timings.get("constraints", 0), 4),
        "t_objetivo_s": round(s.timings.get("objective", 0), 4),
        "t_solve_cpsat_s": round(s.timings.get("solve", 0), 4),
        "t_total_motor_s": round(s.timings.get("total", 0), 4),
        "t_total_wall_s": round(wall, 4),
        "cpu_usuario_s": round(cpu_user_s, 4),
        "cpu_sistema_s": round(cpu_sys_s, 4),
        "cpu_total_s": round(cpu_total_s, 4),
        "cpu_pct_vs_wall": round(cpu_pct, 1),
        "ram_pico_proceso_mb": round(ram_pico_proceso_mb, 2),
    }
    print(
        f"[{label}] estado={row['estado']} objetivo={row['objetivo']}\n"
        f"  tiempos: solve={row['t_solve_cpsat_s']}s motor_total={row['t_total_motor_s']}s wall={row['t_total_wall_s']}s\n"
        f"  cpu:     usuario={row['cpu_usuario_s']}s sistema={row['cpu_sistema_s']}s "
        f"total={row['cpu_total_s']}s ({row['cpu_pct_vs_wall']}% vs wall, {workers} workers)\n"
        f"  ram:     pico_proceso={row['ram_pico_proceso_mb']}MB  python_heap={row['memoria_python_mb']}MB\n"
        f"  modelo:  variables={row['variables']} restricciones={row['restricciones']}"
    )
    return row


def main() -> None:
    print_environment()
    proc_cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    wall_start = time.perf_counter()

    rows = [
        run("curricula_completo", make_curricula_completo(), max_time=300),
    ]

    wall_total = time.perf_counter() - wall_start
    proc_cpu_end = resource.getrusage(resource.RUSAGE_SELF)
    cpu_total = (proc_cpu_end.ru_utime - proc_cpu_start.ru_utime) + (
        proc_cpu_end.ru_stime - proc_cpu_start.ru_stime
    )

    print()
    print("=" * 60)
    print("RESUMEN GENERAL")
    print("=" * 60)
    print(f"Tiempo total (wall)   : {wall_total:.2f}s")
    print(f"Tiempo CPU total      : {cpu_total:.2f}s")
    print(f"Pico RAM del proceso  : {proc_cpu_end.ru_maxrss / 1024:.2f} MB")

    print()
    print("=" * 60)
    print("RESULTADOS (JSON)")
    print("=" * 60)
    print(json.dumps(rows, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
