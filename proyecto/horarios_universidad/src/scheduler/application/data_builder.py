import random
from typing import Optional


def norm(txt: str) -> str:
    return (
        txt.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .strip()
    )


def build_data(cfg):
    random.seed(cfg["seed"])

    asignaturas = [
        ("Lógica de Programación", 3, "Desarrollo de Software"),
        ("Programación Orientada a Objetos", 3, "Desarrollo de Software"),
        ("Estructura de Datos", 3, "Desarrollo de Software"),
        ("Taller de Programación", 2, "Desarrollo de Software"),
        ("Ingeniería Web I", 3, "Desarrollo de Software"),
        ("Ingeniería Web II", 3, "Desarrollo de Software"),
        ("Computación Móvil", 3, "Desarrollo de Software"),
        ("Desarrollo de Software Seguro", 3, "Desarrollo de Software"),
        ("Procesos de Software", 2, "Desarrollo de Software"),
        ("Ingeniería de Requisitos de Software", 2, "Desarrollo de Software"),
        ("Análisis y Diseño del Software", 4, "Desarrollo de Software"),
        ("Patrones y Metodologías de la Construcción del Software", 3, "Desarrollo de Software"),
        ("Arquitectura del Software", 4, "Desarrollo de Software"),
        ("Estándares y Métricas de Calidad del Software", 3, "Desarrollo de Software"),
        ("Pruebas de Software", 3, "Desarrollo de Software"),
        ("Gerencia de Proyectos de Software", 3, "Desarrollo de Software"),
        ("Orientación a la Ingeniería", 1, "Desarrollo de Software"),
        ("Arquitectura de Hardware", 3, "Infraestructura TI"),
        ("Infraestructura Tecnológica I", 3, "Infraestructura TI"),
        ("Infraestructura Tecnológica II", 3, "Infraestructura TI"),
        ("Sistemas Operativos", 3, "Infraestructura TI"),
        ("Sistemas Distribuidos", 3, "Infraestructura TI"),
        ("Gestión de Bases de Datos", 4, "Ciencia de Datos"),
        ("Inteligencia de Negocios", 3, "Ciencia de Datos"),
        ("Sistemas Transaccionales", 4, "Ciencia de Datos"),
        ("Comunicación Oral y Escrita", 2, "Humanidades"),
        ("Cátedra Manuela Beltrán", 1, "Humanidades"),
        ("Filosofía", 2, "Humanidades"),
        ("Ética", 2, "Humanidades"),
        ("Matemáticas Básicas", 3, "Ciencias Básicas"),
        ("Cálculo Diferencial", 3, "Ciencias Básicas"),
        ("Cálculo Integral", 3, "Ciencias Básicas"),
        ("Física Mecánica", 3, "Ciencias Básicas"),
        ("Física Electromagnética", 3, "Ciencias Básicas"),
        ("Proyecto de Investigación I", 2, "Investigación"),
        ("Proyecto de Investigación II", 2, "Investigación"),
        ("Proyecto de Investigación III", 2, "Investigación"),
        ("Proyecto de Investigación IV", 2, "Investigación"),
        ("Contabilidad General", 2, "Investigación"),
        ("Práctica Empresarial", 3, "Investigación"),
        ("Inglés Inicial", 1, "Idiomas"),
        ("Inglés Básico I", 1, "Idiomas"),
        ("Inglés Básico II", 1, "Idiomas"),
        ("Inglés Preintermedio", 1, "Idiomas"),
        ("Inglés Intermedio", 1, "Idiomas"),
        ("Inglés Intermedio Alto", 1, "Idiomas"),
        ("Inglés Avanzado", 1, "Idiomas"),
        ("Electiva I", 2, "Electivas"),
        ("Electiva II", 2, "Electivas"),
        ("Electiva III", 2, "Electivas"),
    ]

    materias = [a[0] for a in asignaturas]
    creditos = [a[1] for a in asignaturas]
    areas = [a[2] for a in asignaturas]
    num_cursos = len(asignaturas)

    virtuales = {
        "ingles inicial",
        "ingles basico i",
        "ingles basico ii",
        "ingles preintermedio",
        "ingles intermedio",
        "ingles intermedio alto",
        "ingles avanzado",
        "contabilidad general",
        "proyecto de investigacion ii",
        "proyecto de investigacion iii",
        "proyecto de investigacion iv",
        "practica empresarial",
        "electiva i",
        "electiva ii",
        "electiva iii",
    }

    humanidades_comun = {
        "comunicacion oral y escrita",
        "catedra manuela beltran",
        "etica",
        "filosofia",
    }

    tipo_materia = {}
    for c, nom in enumerate(materias):
        nn = norm(nom)
        area_n = norm(areas[c])
        if nn in virtuales:
            tipo_materia[c] = "virtual"
        elif nn == "proyecto de investigacion i":
            tipo_materia[c] = "presencial_comun"
        elif nn in humanidades_comun:
            tipo_materia[c] = "presencial_comun"
        elif area_n == "ciencias basicas":
            tipo_materia[c] = "presencial_comun"
        else:
            tipo_materia[c] = "presencial_pc"

    cursos_activos = [c for c in range(num_cursos) if tipo_materia[c] != "virtual"]
    profesores = [f"Prof_{i+1:02d}" for i in range(cfg["num_profes"])]

    num_salones = cfg["num_salones_comunes"] + cfg["num_salones_pc"]
    salones = [f"Salon_{i+1:02d}" for i in range(num_salones)]
    tipo_salon = {}
    capacidad_salon = {}
    for s in range(num_salones):
        tipo_salon[s] = "comun" if s < cfg["num_salones_comunes"] else "pc"
        capacidad_salon[s] = 25

    return {
        "asignaturas": asignaturas,
        "materias": materias,
        "creditos": creditos,
        "areas": areas,
        "num_cursos": num_cursos,
        "tipo_materia": tipo_materia,
        "cursos_activos": cursos_activos,
        "profesores": profesores,
        "salones": salones,
        "tipo_salon": tipo_salon,
        "capacidad_salon": capacidad_salon,
        "num_salones": num_salones,
    }


def _horas_a_creditos(horas) -> int:
    try:
        h = int(horas)
    except (TypeError, ValueError):
        h = 2
    if h < 1:
        return 1
    if h > 4:
        return 4
    return h


def _categoria_a_area_y_tipo(categoria: str):
    c = (categoria or "").strip()
    if c == "Software":
        return "Desarrollo de Software", "presencial_pc"
    if c == "Humanidades":
        return "Humanidades", "presencial_comun"
    if c == "Ciencias Básicas":
        return "Ciencias Básicas", "presencial_comun"
    return "Desarrollo de Software", "presencial_pc"


def nombre_area_desde_categoria_ui(categoria: Optional[str]) -> str:
    area, _ = _categoria_a_area_y_tipo(categoria)
    return area


def _id_materia(v):
    if v is None:
        raise ValueError("Cada materia debe tener un id.")
    try:
        return int(v)
    except (TypeError, ValueError):
        raise ValueError(f"Id de materia invalido: {v!r}.") from None


def build_data_from_ui(cfg, materias_list, profes_list):
    if not materias_list:
        raise ValueError("Debe haber al menos una materia.")
    if not profes_list:
        raise ValueError("Debe haber al menos un profesor.")

    num_cursos = len(materias_list)
    asignaturas = []
    materias = []
    creditos = []
    areas = []
    tipo_materia = {}
    gc_override = [0] * num_cursos
    id_a_curso = {}

    for c, m in enumerate(materias_list):
        mid = _id_materia(m.get("id"))
        id_a_curso[mid] = c
        nombre = (m.get("nombre") or "").strip() or f"Materia_{c + 1}"
        try:
            grupos = int(m.get("grupos") or 1)
        except (TypeError, ValueError):
            grupos = 1
        if grupos < 1:
            grupos = 1
        cr = _horas_a_creditos(m.get("horas"))
        area, tm = _categoria_a_area_y_tipo(m.get("categoria"))
        asignaturas.append((nombre, cr, area))
        materias.append(nombre)
        creditos.append(cr)
        areas.append(area)
        tipo_materia[c] = tm
        gc_override[c] = grupos

    cursos_activos = list(range(num_cursos))
    profesores = []
    for i, p in enumerate(profes_list):
        nom = (p.get("nombre") or "").strip()
        cod = (p.get("codigo") or "").strip()
        profesores.append(nom or cod or f"Profesor_{i + 1:02d}")

    candidatos_override = {}
    for c in cursos_activos:
        elegibles = set()
        for pidx, prof in enumerate(profes_list):
            for mid in prof.get("materias") or []:
                try:
                    mk = int(mid)
                except (TypeError, ValueError):
                    continue
                if id_a_curso.get(mk) == c:
                    elegibles.add(pidx)
                    break
        if not elegibles:
            raise ValueError(f"La materia '{materias[c]}' no tiene profesores asignados.")
        candidatos_override[c] = elegibles

    num_salones = cfg["num_salones_comunes"] + cfg["num_salones_pc"]
    salones = [f"Salon_{i + 1:02d}" for i in range(num_salones)]
    tipo_salon = {}
    capacidad_salon = {}
    cap_comun = int(cfg.get("capacidad_salon_comun", 40))
    cap_pc    = int(cfg.get("capacidad_salon_pc",    30))
    for s in range(num_salones):
        if s < cfg["num_salones_comunes"]:
            tipo_salon[s]     = "comun"
            capacidad_salon[s] = cap_comun
        else:
            tipo_salon[s]     = "pc"
            capacidad_salon[s] = cap_pc

    return {
        "asignaturas": asignaturas,
        "materias": materias,
        "creditos": creditos,
        "areas": areas,
        "num_cursos": num_cursos,
        "tipo_materia": tipo_materia,
        "cursos_activos": cursos_activos,
        "profesores": profesores,
        "salones": salones,
        "tipo_salon": tipo_salon,
        "capacidad_salon": capacidad_salon,
        "num_salones": num_salones,
        "Gc_override": gc_override,
        "candidatos_override": candidatos_override,
    }
