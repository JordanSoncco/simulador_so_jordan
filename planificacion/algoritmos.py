"""
============================================================================
 MÓDULO 1: ALGORITMOS DE PLANIFICACIÓN DE PROCESOS
 Autor : Jordan Oliber Soncco Machaca
 Curso : Sistemas Operativos - Grupo A
 Docente: Ing. Donia Alizandra Ruelas Acero
 Universidad Nacional del Altiplano (UNA Puno)
============================================================================

 Contiene la lógica matemática de las 4 políticas de planificación:
   1. FCFS (First Come First Served) — No Expulsivo
   2. SJF (Shortest Job First) — No Expulsivo
   3. SRTF (Shortest Remaining Time First) — Expulsivo
   4. Round Robin — Expulsivo con Quantum q configurable
============================================================================
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
import copy


# ─────────────────────────────────────────────────────────────
#  Fundamento Teórico por Política
# ─────────────────────────────────────────────────────────────
INFO_TEORICA_POLITICAS: Dict[str, Dict[str, str]] = {
    "FCFS": {
        "nombre_corto": "FCFS",
        "nombre_completo": "First Come, First Served (Primero en Llegar, Primero en ser Servido)",
        "tipo": "No Expulsiva (Non-Preemptive)",
        "criterio": "Orden cronológico de llegada (T.LL). En caso de empate, se respeta el orden de ingreso (FIFO).",
        "ventajas": "Sencillo de implementar con una cola FIFO; sin sobrecarga por cambios de contexto; libre de inanición.",
        "desventajas": "Puede sufrir el 'Efecto Convoy': un proceso largo al inicio retrasa a todos los procesos cortos posteriores.",
        "formulas": "T.R. = T.F. - T.LL   |   T.E. = T.R. - T.S.   |   TR̄ = Σ T.R. / #P   |   TĒ = Σ T.E. / #P",
    },
    "SJF (No Expulsivo)": {
        "nombre_corto": "SJF",
        "nombre_completo": "Shortest Job First (El Trabajo Más Corto Primero)",
        "tipo": "No Expulsiva (Non-Preemptive)",
        "criterio": "Selecciona de la Cola de Listos el proceso disponible con menor Tiempo de Servicio (T.S.). Corre hasta terminar.",
        "ventajas": "Minimiza de manera óptima el Tiempo de Espera Promedio (TĒ) entre las políticas no expulsivas.",
        "desventajas": "Riesgo de inanición (starvation) para procesos largos si llegan continuamente procesos cortos.",
        "formulas": "T.R. = T.F. - T.LL   |   T.E. = T.R. - T.S.   |   TR̄ = Σ T.R. / #P   |   TĒ = Σ T.E. / #P",
    },
    "SRTF (Expulsivo)": {
        "nombre_corto": "SRTF",
        "nombre_completo": "Shortest Remaining Time First (Menor Tiempo Restante Primero)",
        "tipo": "Expulsiva / Apropiativa (Preemptive)",
        "criterio": "En cada unidad de tiempo evalúa la Cola de Listos y asigna la CPU al proceso con menor tiempo restante.",
        "ventajas": "Minimiza óptimamente el Tiempo de Espera Promedio (TĒ) global al dar prioridad inmediata a ráfagas cortas.",
        "desventajas": "Mayor cantidad de cambios de contexto por expulsiones; posible inanición de procesos largos.",
        "formulas": "T.R. = T.F. - T.LL   |   T.E. = T.R. - T.S.   |   TR̄ = Σ T.R. / #P   |   TĒ = Σ T.E. / #P",
    },
    "Round Robin (Expulsivo)": {
        "nombre_corto": "RR",
        "nombre_completo": "Round Robin (Planificación Cíclica por Turnos con Quantum q)",
        "tipo": "Expulsiva / Apropiativa (Preemptive)",
        "criterio": "Cola FIFO circular donde cada proceso ejecuta hasta un máximo de 'q' unidades (Quantum) por turno.",
        "ventajas": "Reparto equitativo de CPU; ideal para sistemas interactivos y de tiempo compartido; sin inanición.",
        "desventajas": "Si q es muy grande se comporta como FCFS; si q es muy pequeño incrementa los cambios de contexto.",
        "formulas": "T.R. = T.F. - T.LL   |   T.E. = T.R. - T.S.   |   TR̄ = Σ T.R. / #P   |   TĒ = Σ T.E. / #P",
    },
}


# ─────────────────────────────────────────────────────────────
#  Estructura de Resultado (Sin varianza)
# ─────────────────────────────────────────────────────────────
@dataclass
class Resultado:
    """Encapsula todos los datos calculados por una política de planificación."""
    algoritmo: str
    gantt: List[Tuple[str, int, int]]                   # Bloques compactados (proceso, inicio, fin)
    gantt_unitario: Dict[int, str]                      # t -> nombre_proceso en [t, t+1]
    tabla: List[Dict[str, Any]]                         # Métricas por proceso (en orden original)
    promedio_te: float = 0.0
    promedio_tr: float = 0.0
    num_procesos: int = 0                               # #P (Cantidad de procesos)
    suma_rafagas: int = 0                               # Σ T.S.
    suma_tr: int = 0                                    # Σ T.R.
    suma_te: int = 0                                    # Σ T.E.
    tiempo_total: int = 0                               # Tiempo final total del diagrama
    tiempo_idle: int = 0                                # Unidades de CPU ociosa
    uso_cpu_pct: float = 100.0                          # Porcentaje de utilización de CPU
    quantum: int = 2                                    # Quantum usado (para RR)
    colas_por_tiempo: Dict[int, List[str]] = field(default_factory=dict)
    tiempos_fin: Dict[str, int] = field(default_factory=dict)
    tiempos_inicio: Dict[str, int] = field(default_factory=dict)
    traza: List[str] = field(default_factory=list)


def _compactar_gantt(gantt_crudo: List[Tuple[str, int, int]]) -> List[Tuple[str, int, int]]:
    """Une bloques consecutivos del mismo proceso."""
    if not gantt_crudo:
        return []
    compacto: List[Tuple[str, int, int]] = [gantt_crudo[0]]
    for nombre, inicio, fin in gantt_crudo[1:]:
        ult_nombre, ult_inicio, ult_fin = compacto[-1]
        if nombre == ult_nombre and inicio == ult_fin:
            compacto[-1] = (ult_nombre, ult_inicio, fin)
        else:
            compacto.append((nombre, inicio, fin))
    return compacto


def _construir_resultado(
    algoritmo: str,
    procesos_orig: List[Dict[str, Any]],
    gantt_crudo: List[Tuple[str, int, int]],
    tiempos_fin: Dict[str, int],
    tiempos_inicio: Dict[str, int],
    colas_por_tiempo: Dict[int, List[str]],
    traza: List[str],
    quantum: int = 2,
) -> Resultado:
    gantt = _compactar_gantt(gantt_crudo)
    gantt_unitario = {ini: nom for nom, ini, _ in gantt_crudo}

    tabla: List[Dict[str, Any]] = []
    lista_te: List[int] = []
    lista_tr: List[int] = []

    for p in procesos_orig:
        nombre = p["nombre"]
        llegada = int(p["llegada"])
        rafaga = int(p["rafaga"])
        fin = int(tiempos_fin[nombre])
        ti = int(tiempos_inicio.get(nombre, llegada))

        tr = fin - llegada          # T.R. = T.F. - T.LL
        te = tr - rafaga            # T.E. = T.R. - T.S.

        tabla.append({
            "nombre": nombre,
            "llegada": llegada,
            "rafaga": rafaga,
            "ti": ti,
            "fin": fin,
            "tr": tr,
            "te": te,
        })
        lista_tr.append(tr)
        lista_te.append(te)

    n = len(procesos_orig)
    suma_rafagas = sum(int(p["rafaga"]) for p in procesos_orig)
    suma_tr = sum(lista_tr)
    suma_te = sum(lista_te)
    prom_tr = suma_tr / n if n else 0.0
    prom_te = suma_te / n if n else 0.0

    tiempo_total = max((fin for _, _, fin in gantt), default=0)
    tiempo_idle = sum(fin - ini for nom, ini, fin in gantt if nom == "IDLE")
    uso_cpu_pct = ((tiempo_total - tiempo_idle) / tiempo_total * 100.0) if tiempo_total > 0 else 100.0

    return Resultado(
        algoritmo=algoritmo,
        gantt=gantt,
        gantt_unitario=gantt_unitario,
        tabla=tabla,
        promedio_te=prom_te,
        promedio_tr=prom_tr,
        num_procesos=n,
        suma_rafagas=suma_rafagas,
        suma_tr=suma_tr,
        suma_te=suma_te,
        tiempo_total=tiempo_total,
        tiempo_idle=tiempo_idle,
        uso_cpu_pct=uso_cpu_pct,
        quantum=quantum,
        colas_por_tiempo=colas_por_tiempo,
        tiempos_fin=tiempos_fin,
        tiempos_inicio=tiempos_inicio,
        traza=traza,
    )


# ═════════════════════════════════════════════════════════════
#  1. FCFS — First Come First Served (No Expulsivo)
# ═════════════════════════════════════════════════════════════
def fcfs(procesos: List[Dict[str, Any]]) -> Resultado:
    n = len(procesos)
    orden = sorted(range(n), key=lambda i: (procesos[i]["llegada"], i))
    completados_set = set()
    gantt_crudo: List[Tuple[str, int, int]] = []
    tiempos_fin: Dict[str, int] = {}
    tiempos_inicio: Dict[str, int] = {}
    colas_por_tiempo: Dict[int, List[str]] = {}
    traza: List[str] = []
    tiempo_actual = 0

    for idx in orden:
        p = procesos[idx]
        nombre = p["nombre"]
        llegada = p["llegada"]
        rafaga = p["rafaga"]

        if tiempo_actual < llegada:
            traza.append(
                f"t = {tiempo_actual}..{llegada}: CPU inactiva (IDLE) esperando la llegada de {nombre} en t = {llegada}."
            )
            for t in range(tiempo_actual, llegada):
                gantt_crudo.append(("IDLE", t, t + 1))
                colas_por_tiempo[t] = ["IDLE"]
            tiempo_actual = llegada

        inicio = tiempo_actual
        fin = inicio + rafaga
        tiempos_inicio[nombre] = inicio
        traza.append(
            f"t = {inicio}: Entra {nombre} (T.LL={llegada}, T.S.={rafaga}) por orden de llegada y ejecuta hasta t = {fin}."
        )

        for t in range(inicio, fin):
            gantt_crudo.append((nombre, t, t + 1))
            en_espera = [
                procesos[j]["nombre"]
                for j in orden
                if j != idx and j not in completados_set and procesos[j]["llegada"] <= t
            ]
            colas_por_tiempo[t] = [nombre] + en_espera

        tiempos_fin[nombre] = fin
        completados_set.add(idx)
        traza.append(f"t = {fin}: Finaliza {nombre} (+). T.F. = {fin}, T.R. = {fin - llegada}, T.E. = {fin - llegada - rafaga}.")
        tiempo_actual = fin

    return _construir_resultado(
        "FCFS", procesos, gantt_crudo, tiempos_fin, tiempos_inicio, colas_por_tiempo, traza
    )


# ═════════════════════════════════════════════════════════════
#  2. SJF — Shortest Job First (No Expulsivo)
# ═════════════════════════════════════════════════════════════
def sjf(procesos: List[Dict[str, Any]]) -> Resultado:
    n = len(procesos)
    pendientes = list(range(n))
    gantt_crudo: List[Tuple[str, int, int]] = []
    tiempos_fin: Dict[str, int] = {}
    tiempos_inicio: Dict[str, int] = {}
    colas_por_tiempo: Dict[int, List[str]] = {}
    traza: List[str] = []
    tiempo_actual = 0

    while pendientes:
        disponibles = [i for i in pendientes if procesos[i]["llegada"] <= tiempo_actual]

        if not disponibles:
            prox = min(pendientes, key=lambda i: (procesos[i]["llegada"], i))
            t_prox = procesos[prox]["llegada"]
            traza.append(
                f"t = {tiempo_actual}..{t_prox}: CPU inactiva (IDLE) hasta la llegada de {procesos[prox]['nombre']} en t = {t_prox}."
            )
            for t in range(tiempo_actual, t_prox):
                gantt_crudo.append(("IDLE", t, t + 1))
                colas_por_tiempo[t] = ["IDLE"]
            tiempo_actual = t_prox
            continue

        elegido = min(disponibles, key=lambda i: (procesos[i]["rafaga"], i))
        p = procesos[elegido]
        nombre = p["nombre"]
        inicio = tiempo_actual
        fin = inicio + p["rafaga"]
        tiempos_inicio[nombre] = inicio

        cola_nombres = [
            f"{procesos[i]['nombre']}(T.S.={procesos[i]['rafaga']})"
            for i in sorted(disponibles, key=lambda i: (procesos[i]["rafaga"], i))
        ]
        traza.append(
            f"t = {inicio}: Disponibles [{', '.join(cola_nombres)}] → Se elige {nombre} por menor T.S.={p['rafaga']}."
        )

        pendientes.remove(elegido)

        for t in range(inicio, fin):
            gantt_crudo.append((nombre, t, t + 1))
            esperando_t = sorted(
                [i for i in pendientes if procesos[i]["llegada"] <= t],
                key=lambda i: (procesos[i]["rafaga"], i),
            )
            colas_por_tiempo[t] = [nombre] + [procesos[i]["nombre"] for i in esperando_t]

        tiempos_fin[nombre] = fin
        traza.append(
            f"t = {fin}: Finaliza {nombre} (+). T.F. = {fin}, T.R. = {fin - p['llegada']}, T.E. = {fin - p['llegada'] - p['rafaga']}."
        )
        tiempo_actual = fin

    return _construir_resultado(
        "SJF (No Expulsivo)", procesos, gantt_crudo, tiempos_fin, tiempos_inicio, colas_por_tiempo, traza
    )


# ═════════════════════════════════════════════════════════════
#  3. SRTF — Shortest Remaining Time First (Expulsivo)
# ═════════════════════════════════════════════════════════════
def srtf(procesos: List[Dict[str, Any]]) -> Resultado:
    n = len(procesos)
    restante = [int(p["rafaga"]) for p in procesos]
    completados = 0
    tiempo_actual = 0
    gantt_crudo: List[Tuple[str, int, int]] = []
    tiempos_fin: Dict[str, int] = {}
    tiempos_inicio: Dict[str, int] = {}
    colas_por_tiempo: Dict[int, List[str]] = {}
    traza: List[str] = []

    t_max = max(p["llegada"] for p in procesos) + sum(p["rafaga"] for p in procesos) + 5
    ultimo_ejecutado: str | None = None

    while completados < n and tiempo_actual < t_max:
        disponibles = [
            i for i in range(n)
            if procesos[i]["llegada"] <= tiempo_actual and restante[i] > 0
        ]

        if not disponibles:
            prox = min(
                (i for i in range(n) if restante[i] > 0),
                key=lambda i: (procesos[i]["llegada"], i),
            )
            t_prox = procesos[prox]["llegada"]
            traza.append(f"t = {tiempo_actual}..{t_prox}: CPU inactiva (IDLE).")
            for t in range(tiempo_actual, t_prox):
                gantt_crudo.append(("IDLE", t, t + 1))
                colas_por_tiempo[t] = ["IDLE"]
            tiempo_actual = t_prox
            ultimo_ejecutado = "IDLE"
            continue

        disponibles_ordenados = sorted(disponibles, key=lambda i: (restante[i], i))
        elegido = disponibles_ordenados[0]
        nombre = procesos[elegido]["nombre"]

        if nombre not in tiempos_inicio:
            tiempos_inicio[nombre] = tiempo_actual

        if nombre != ultimo_ejecutado:
            resumen_cola = ", ".join(
                f"{procesos[i]['nombre']}(rest={restante[i]})" for i in disponibles_ordenados
            )
            traza.append(
                f"t = {tiempo_actual}: Cola [{resumen_cola}] → Ejecuta {nombre} (menor restante = {restante[elegido]})."
            )
            ultimo_ejecutado = nombre

        colas_por_tiempo[tiempo_actual] = [procesos[i]["nombre"] for i in disponibles_ordenados]
        gantt_crudo.append((nombre, tiempo_actual, tiempo_actual + 1))
        restante[elegido] -= 1
        tiempo_actual += 1

        if restante[elegido] == 0:
            tiempos_fin[nombre] = tiempo_actual
            completados += 1
            p_orig = procesos[elegido]
            traza.append(
                f"t = {tiempo_actual}: Finaliza {nombre} (+). T.F. = {tiempo_actual}, "
                f"T.R. = {tiempo_actual - p_orig['llegada']}, T.E. = {tiempo_actual - p_orig['llegada'] - p_orig['rafaga']}."
            )
            ultimo_ejecutado = None

    return _construir_resultado(
        "SRTF (Expulsivo)", procesos, gantt_crudo, tiempos_fin, tiempos_inicio, colas_por_tiempo, traza
    )


# ═════════════════════════════════════════════════════════════
#  4. ROUND ROBIN — Expulsivo con Quantum q configurable
# ═════════════════════════════════════════════════════════════
def round_robin(procesos: List[Dict[str, Any]], quantum: int = 2) -> Resultado:
    n = len(procesos)
    restante = [int(p["rafaga"]) for p in procesos]
    en_cola = [False] * n
    cola: deque[int] = deque()
    gantt_crudo: List[Tuple[str, int, int]] = []
    tiempos_fin: Dict[str, int] = {}
    tiempos_inicio: Dict[str, int] = {}
    colas_por_tiempo: Dict[int, List[str]] = {}
    traza: List[str] = []
    tiempo_actual = 0
    completados = 0

    orden = sorted(range(n), key=lambda i: (procesos[i]["llegada"], i))

    for i in orden:
        if procesos[i]["llegada"] == 0:
            cola.append(i)
            en_cola[i] = True

    t_max = max(p["llegada"] for p in procesos) + sum(p["rafaga"] for p in procesos) + 5

    while completados < n and tiempo_actual < t_max:
        if not cola:
            pendientes_idx = [i for i in range(n) if restante[i] > 0]
            if not pendientes_idx:
                break
            prox = min(pendientes_idx, key=lambda i: (procesos[i]["llegada"], i))
            t_prox = procesos[prox]["llegada"]
            traza.append(f"t = {tiempo_actual}..{t_prox}: CPU inactiva (IDLE).")
            for t in range(tiempo_actual, t_prox):
                gantt_crudo.append(("IDLE", t, t + 1))
                colas_por_tiempo[t] = ["IDLE"]
            tiempo_actual = t_prox

            for i in orden:
                if not en_cola[i] and restante[i] > 0 and procesos[i]["llegada"] <= tiempo_actual:
                    cola.append(i)
                    en_cola[i] = True
            continue

        idx = cola.popleft()
        p = procesos[idx]
        nombre = p["nombre"]

        if nombre not in tiempos_inicio:
            tiempos_inicio[nombre] = tiempo_actual

        ejecucion = min(quantum, restante[idx])
        inicio = tiempo_actual
        fin = inicio + ejecucion

        traza.append(
            f"t = {inicio}: Turno de {nombre} por {ejecucion} u.t. (quantum={quantum}, restante={restante[idx]})."
        )

        for t in range(inicio, fin):
            for i in orden:
                if i != idx and not en_cola[i] and restante[i] > 0 and procesos[i]["llegada"] <= t:
                    cola.append(i)
                    en_cola[i] = True
                    traza.append(f"  ↳ En t = {t}: Llega {procesos[i]['nombre']} y se encola.")

            gantt_crudo.append((nombre, t, t + 1))
            colas_por_tiempo[t] = [nombre] + [procesos[k]["nombre"] for k in cola]

        restante[idx] -= ejecucion
        tiempo_actual = fin

        for i in orden:
            if i != idx and not en_cola[i] and restante[i] > 0 and procesos[i]["llegada"] <= tiempo_actual:
                cola.append(i)
                en_cola[i] = True
                traza.append(f"  ↳ En t = {tiempo_actual}: Llega {procesos[i]['nombre']} y entra a la Cola de Listos.")

        if restante[idx] == 0:
            tiempos_fin[nombre] = tiempo_actual
            completados += 1
            traza.append(
                f"t = {tiempo_actual}: Finaliza {nombre} (+). T.F. = {tiempo_actual}, "
                f"T.R. = {tiempo_actual - p['llegada']}, T.E. = {tiempo_actual - p['llegada'] - p['rafaga']}."
            )
        else:
            cola.append(idx)
            traza.append(
                f"t = {tiempo_actual}: {nombre} agota su quantum (restan {restante[idx]} u.t.) y pasa al final de la cola: {[procesos[k]['nombre'] for k in cola]}."
            )

    return _construir_resultado(
        "Round Robin (Expulsivo)",
        procesos,
        gantt_crudo,
        tiempos_fin,
        tiempos_inicio,
        colas_por_tiempo,
        traza,
        quantum=quantum,
    )


ALGORITMOS = {
    "FCFS": fcfs,
    "SJF (No Expulsivo)": sjf,
    "SRTF (Expulsivo)": srtf,
    "Round Robin (Expulsivo)": round_robin,
}


def ejecutar(nombre_algo: str, procesos: List[Dict[str, Any]], quantum: int = 2) -> Resultado:
    if not procesos:
        raise ValueError("La lista de procesos está vacía.")
    procesos_copia = copy.deepcopy(procesos)
    if nombre_algo == "Round Robin (Expulsivo)":
        return round_robin(procesos_copia, quantum)
    func = ALGORITMOS.get(nombre_algo)
    if func is None:
        raise ValueError(f"Algoritmo '{nombre_algo}' no reconocido.")
    return func(procesos_copia)


def comparar_todos(procesos: List[Dict[str, Any]], quantum: int = 2) -> Dict[str, Resultado]:
    resultados: Dict[str, Resultado] = {}
    for nombre_algo in ALGORITMOS:
        procesos_copia = copy.deepcopy(procesos)
        if nombre_algo == "Round Robin (Expulsivo)":
            resultados[nombre_algo] = round_robin(procesos_copia, quantum)
        else:
            resultados[nombre_algo] = ALGORITMOS[nombre_algo](procesos_copia)
    return resultados
