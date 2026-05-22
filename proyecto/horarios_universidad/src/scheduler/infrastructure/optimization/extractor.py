from collections import defaultdict
import pandas as pd


def extract(solution, cfg):
    solver = solution["solver"]
    meta = solution["meta"]

    x = meta["x"]
    materias = meta["materias"]
    profesores = meta["profesores"]
    salones = meta["salones"]
    bpd = meta["bloques_por_dia"]

    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

    def bh_to_day_hour(b):
        return b // bpd, b % bpd

    asignaciones = []
    uso_salones = []
    celda = defaultdict(list)

    for (p, c, gi, b, s), var in x.items():
        if solver.Value(var) == 1:
            d, h = bh_to_day_hour(b)
            bloque_local = h + 1
            curso = f"CUR_{c+1:02d}-G{gi+1}"
            asignaciones.append(
                {
                    "Día": dias[d],
                    "Bloque": bloque_local,
                    "Curso": curso,
                    "Materia": materias[c],
                    "Profesor": profesores[p],
                    "Salón": salones[s],
                }
            )
            uso_salones.append(
                {
                    "Día": dias[d],
                    "Bloque": bloque_local,
                    "Salón": salones[s],
                    "Curso": curso,
                    "Profesor": profesores[p],
                }
            )
            txt = f"{materias[c]}\n{curso} | {profesores[p]} | {salones[s]}"
            celda[(d, bloque_local)].append(txt)

    df_asig = pd.DataFrame(asignaciones)
    if not df_asig.empty:
        df_asig = df_asig.sort_values(["Día", "Bloque", "Salón", "Curso"])

    df_uso = pd.DataFrame(uso_salones)
    if not df_uso.empty:
        df_uso = df_uso.sort_values(["Día", "Bloque", "Salón", "Curso"])

    data_cal = []
    for bl in range(1, bpd + 1):
        fila = {"Bloque": bl}
        for d, dn in enumerate(dias):
            items = celda.get((d, bl), [])
            fila[dn] = "\n\n".join(items) if items else ""
        data_cal.append(fila)

    df_cal = pd.DataFrame(data_cal, columns=["Bloque"] + dias)
    return df_asig, df_cal, df_uso
