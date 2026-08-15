"""Benchmark del motor de optimización — pensado para ejecutarse en el
servidor AWS EC2 (Debian 13, t3.micro).

Corre tres escenarios (pequeño, mediano y grande) de extremo a extremo a
través de SolverEngine, imprime el entorno de ejecución (CPU, RAM, SO) y
las estadísticas reales de cada corrida con la mayor precisión posible.

Uso (desde la carpeta backend):
    python -m scripts.benchmark_aws
"""
from __future__ import annotations

import json
import os
import platform
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


def run(label: str, problem: OptimizationProblem, max_time: int) -> dict:
    workers = os.cpu_count() or 1
    config = SolverConfiguration(max_time_seconds=max_time, num_workers=workers, random_seed=42)
    t0 = time.perf_counter()
    result = SolverEngine(config=config).solve(problem)
    wall = time.perf_counter() - t0
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
        "memoria_mb": s.memory_usage_mb,
        "t_construccion_modelo_s": round(s.timings.get("model_build", 0), 4),
        "t_restricciones_s": round(s.timings.get("constraints", 0), 4),
        "t_objetivo_s": round(s.timings.get("objective", 0), 4),
        "t_solve_cpsat_s": round(s.timings.get("solve", 0), 4),
        "t_total_motor_s": round(s.timings.get("total", 0), 4),
        "t_total_wall_s": round(wall, 4),
    }
    print(f"[{label}] estado={row['estado']} objetivo={row['objetivo']} "
          f"solve={row['t_solve_cpsat_s']}s total={row['t_total_motor_s']}s "
          f"vars={row['variables']} restr={row['restricciones']} mem={row['memoria_mb']}MB")
    return row


def main() -> None:
    print_environment()
    rows = [
        run("pequeno", make_small(), max_time=10),
        run("mediano", make_medium(), max_time=60),
        run("grande", make_large(), max_time=120),
    ]
    print()
    print("=" * 60)
    print("RESULTADOS (JSON)")
    print("=" * 60)
    print(json.dumps(rows, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
