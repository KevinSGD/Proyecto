import multiprocessing
import time
from ortools.sat.python import cp_model
from scheduler.infrastructure.optimization.model_builder import build_model


def solve(cfg, data):
    model, meta = build_model(cfg, data)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = cfg["max_time_seconds"]
    solver.parameters.num_search_workers = max(1, multiprocessing.cpu_count())

    t0 = time.time()
    status = solver.Solve(model)
    t1 = time.time()

    return {
        "solver": solver,
        "status": status,
        "elapsed": round(t1 - t0, 3),
        "meta": meta,
        "num_vars": len(model.Proto().variables),
        "num_constraints": len(model.Proto().constraints),
    }
