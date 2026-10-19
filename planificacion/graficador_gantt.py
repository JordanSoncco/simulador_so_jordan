"""
============================================================================
 MÓDULO 1: GRAFICADOR DEL PLANO DE GANTT Y FÓRMULAS MATEMÁTICAS
 Autor : Jordan Oliber Soncco Machaca — UNA Puno
============================================================================

 Separa completamente:
   1. El Plano Cartesiano 2D del Diagrama de Gantt (con soporte de vista
      previa interactiva al agregar procesos y animación paso a paso t=0..T).
   2. El lienzo de Fórmulas Matemáticas Paso a Paso (#P, ΣTR/#P, ΣTE/#P y
      recuadro verde de conclusión sin varianza).
============================================================================
"""

from __future__ import annotations
from typing import List, Dict, Any
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.gridspec as gridspec

from .algoritmos import Resultado, INFO_TEORICA_POLITICAS

# Paleta armónica de colores distintos por proceso (Relleno suave, Borde/Texto fuerte)
PALETA_PROCESOS: List[ tuple[str, str] ] = [
    ("#DBEAFE", "#1D4ED8"),  # P0: Azul real
    ("#D1FAE5", "#047857"),  # P1: Verde esmeralda
    ("#FEF3C7", "#B45309"),  # P2: Ámbar / Dorado
    ("#FFE4E6", "#BE123C"),  # P3: Coral / Carmesí
    ("#EDE9FE", "#6D28D9"),  # P4: Violeta
    ("#CFFAFE", "#0E7490"),  # P5: Turquesa / Cian
    ("#FFEDD5", "#C2410C"),  # P6: Naranja intenso
    ("#FCE7F3", "#BE185D"),  # P7: Magenta / Rosa
    ("#ECFCCB", "#3F6212"),  # P8: Verde lima
    ("#E0E7FF", "#3730A3"),  # P9: Índigo
    ("#F3E8FF", "#7E22CE"),  # P10: Púrpura
    ("#CCFBF1", "#0F766E"),  # P11: Verde azulado (Teal)
    ("#FEF9C3", "#854D0E"),  # P12: Ocre
    ("#FFE4E6", "#9F1239"),  # P13: Borgoña
    ("#E0F2FE", "#0369A1"),  # P14: Celeste profundo
]


def _mapa_colores(procesos: List[Dict[str, Any]]) -> Dict[str, tuple[str, str]]:
    """Asigna un par (color_relleno, color_borde) único a cada proceso."""
    return {
        p["nombre"]: PALETA_PROCESOS[idx % len(PALETA_PROCESOS)]
        for idx, p in enumerate(procesos)
    }


def fmt_num(val: float) -> str:
    """Formatea enteros sin decimales y flotantes con hasta 2 decimales."""
    if abs(val - round(val)) < 1e-9:
        return str(int(round(val)))
    return f"{val:.2f}".rstrip("0").rstrip(".")


def configurar_eje_tiempo_gantt(ax: plt.Axes, x0: float, x1: float, max_time: int):
    """
    Configura de forma limpia y nítida los ticks del eje X inferior sin distorsión:
    - Muestra paso 1 cuando el rango visible es menor o igual a 26 u.t.
    - Muestra paso 2 cuando el rango es entre 27 y 48 u.t.
    - Muestra paso 5 cuando el rango es mayor a 48 u.t.
    - Únicamente genera marcas estrictamente dentro del rango visible [x0, x1].
    """
    ancho = max(1.0, x1 - x0)
    if ancho <= 26:
        step = 1
    elif ancho <= 48:
        step = 2
    else:
        step = 5

    t_min = max(0, int(x0))
    t_max = min(max_time, int(x1) + 1)

    # Alinear el primer tick múltiplo de step >= t_min
    inicio = ((t_min + step - 1) // step) * step
    ticks = [t for t in range(inicio, t_max + 1, step) if t >= x0 and t <= x1]

    # Asegurar que los extremos visibles se marquen si corresponden
    if x0 <= 0.05 and 0 not in ticks:
        ticks.insert(0, 0)
    if x1 >= max_time - 0.05 and max_time not in ticks:
        ticks.append(max_time)
    ticks = sorted(list(set(ticks)))

    ax.set_xticks(ticks)
    f_size_tick = 8.5 if ancho <= 25 else (8.0 if ancho <= 50 else 7.5)
    ax.tick_params(
        axis="x",
        which="both",
        direction="out",
        length=4.5,
        width=1.1,
        colors="#C62828",
        labelsize=f_size_tick,
        pad=4,
        bottom=True,
        labelbottom=True,
    )
    for lbl in ax.get_xticklabels():
        lbl.set_color("#C62828")
        lbl.set_fontweight("bold")


def configurar_eje_tiempo_cola(ax: plt.Axes, x0: float, x1: float, max_time: int):
    """Configura los ticks del eje de tiempo superior en el apartado de Cola de Procesos."""
    ancho = max(1.0, x1 - x0)
    if ancho <= 26:
        step = 1
    elif ancho <= 48:
        step = 2
    else:
        step = 5

    t_min = max(0, int(x0))
    t_max = min(max_time, int(x1) + 1)

    inicio = ((t_min + step - 1) // step) * step
    ticks = [t for t in range(inicio, t_max + 1, step) if t >= x0 and t <= x1]

    if x0 <= 0.05 and 0 not in ticks:
        ticks.insert(0, 0)
    if x1 >= max_time - 0.05 and max_time not in ticks:
        ticks.append(max_time)
    ticks = sorted(list(set(ticks)))

    ax.set_xticks(ticks)
    f_size_tick = 8.0 if ancho <= 25 else (7.4 if ancho <= 50 else 6.8)
    ax.tick_params(
        axis="x",
        which="both",
        direction="out",
        length=4.0,
        width=1.0,
        colors="#C62828",
        labelsize=f_size_tick,
        pad=3,
        top=True,
        labeltop=True,
        bottom=False,
        labelbottom=False,
    )
    for lbl in ax.get_xticklabels():
        lbl.set_color("#C62828")
        lbl.set_fontweight("bold")


def dibujar_plano_vacio_o_previa(fig: plt.Figure, procesos: List[Dict[str, Any]], nombre_algo: str):
    """
    Dibuja el Plano de Gantt antes de ejecutar la simulación:
      - Si no hay procesos: muestra el plano cartesiano limpio (sin textos encimados).
      - Si hay procesos agregados: muestra de forma interactiva cada proceso en el eje Y
        con su color propio y su bloque punteado de llegada + duración (T.LL a T.LL + T.S.).
    """
    fig.clear()
    fig.patch.set_facecolor("#FFFFFF")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#FFFFFF")

    # Configurar bordes estilizados: eje Y izquierdo y eje X inferior rojos
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color("#C62828")
    ax.spines["left"].set_linewidth(1.6)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color("#C62828")
    ax.spines["bottom"].set_linewidth(1.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if not procesos:
        max_t = 12
        n_p = 4
        for t in range(1, max_t + 1):
            ax.plot([t, t], [0, n_p + 0.5], linestyle="--", linewidth=0.8, color="#E2E8F0", zorder=1)

        ax.text(
            max_t / 2, n_p / 2 + 0.3,
            "Plano listo — Agrega procesos o carga un archivo .txt para visualizarlos aquí",
            ha="center", va="center", fontsize=10.5, color="#64748B",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=1),
        )
        ax.set_xlim(0, max_t)
        ax.set_ylim(0, n_p + 0.6)
        ax._limites_originales = (ax.get_xlim(), ax.get_ylim())
        configurar_eje_tiempo_gantt(ax, 0, max_t, max_t)
        ax.set_yticks([])
        ax.set_ylabel("Proceso", color="#C62828", fontsize=10, fontweight="bold", labelpad=8)
        fig.subplots_adjust(left=0.065, right=0.985, top=0.89, bottom=0.14)
        return

    # Vista previa interactiva de los procesos ingresados en la cola con su color propio
    n_procs = len(procesos)
    max_time = max(max(int(p["llegada"]) + int(p["rafaga"]) for p in procesos), 10)
    nombres = [p["nombre"] for p in procesos]
    y_map = {nom: n_procs - idx for idx, nom in enumerate(nombres)}
    colores = _mapa_colores(procesos)

    suma_ts = sum(int(p["rafaga"]) for p in procesos)
    ax.set_title(
        f"Vista Previa en Cola ({nombre_algo})  —  #P = {n_procs} procesos  |  Σ T.S. = {suma_ts} u.t.  (Presiona '▶ Iniciar' para simular)",
        loc="left", fontsize=10.5, fontweight="bold", color="#334155", pad=6,
    )

    for t in range(1, max_time + 1):
        ax.plot([t, t], [0, n_procs + 0.55], linestyle="--", linewidth=0.75, color="#E2E8F0", zorder=1)

    f_size_proc = 9.5 if n_procs <= 12 else (8.2 if n_procs <= 18 else 7.4)

    for p in procesos:
        nom = p["nombre"]
        lleg = int(p["llegada"])
        raf = int(p["rafaga"])
        y_c = y_map[nom]
        c_fill, c_borde = colores[nom]

        for t in range(lleg, lleg + raf):
            sq = Rectangle(
                (t + 0.08, y_c - 0.32), 0.84, 0.64,
                facecolor=c_fill, edgecolor=c_borde,
                linestyle="--", linewidth=1.15, alpha=0.75, zorder=2, clip_on=True,
            )
            ax.add_patch(sq)
        ax.plot(lleg, y_c, marker="o", markersize=4.5, color=c_borde, zorder=4, clip_on=True)

    ax.set_xlim(0, max_time)
    ax.set_ylim(0, n_procs + 0.7)
    ax._limites_originales = (ax.get_xlim(), ax.get_ylim())

    configurar_eje_tiempo_gantt(ax, 0, max_time, max_time)

    ax.set_yticks([y_map[nom] for nom in nombres])
    ax.set_yticklabels(nombres, fontsize=f_size_proc, fontweight="bold")
    for tick_lbl, nom in zip(ax.get_yticklabels(), nombres):
        tick_lbl.set_color(colores[nom][1])
    ax.tick_params(axis="y", length=0, pad=5)
    ax.set_ylabel("Proceso", color="#C62828", fontsize=10, fontweight="bold", labelpad=8)
    fig.subplots_adjust(left=0.065, right=0.985, top=0.89, bottom=0.14)


def dibujar_plano_gantt(
    fig: plt.Figure,
    procesos: List[Dict[str, Any]],
    resultado: Resultado,
    paso_actual: int | None = None,
    limites_previos: tuple | None = None,
):
    """
    Dibuja EXCLUSIVAMENTE el Plano Cartesiano 2D de Gantt con cuadros [t, t+1]
    de colores distintos por proceso y signo '+' rojo al finalizar (T.F.).
    Los ejes X e Y usan spines y ticks nativos de Matplotlib con separación holgada.
    """
    fig.clear()
    fig.patch.set_facecolor("#FFFFFF")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#FFFFFF")

    # Configurar bordes nativos estilizados
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color("#C62828")
    ax.spines["left"].set_linewidth(1.6)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color("#C62828")
    ax.spines["bottom"].set_linewidth(1.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    n_procs = resultado.num_procesos
    max_time = max(1, resultado.tiempo_total)
    t_limite = max_time if paso_actual is None else min(paso_actual, max_time)
    colores = _mapa_colores(procesos)

    info_pol = INFO_TEORICA_POLITICAS.get(resultado.algoritmo, {})
    sigla = info_pol.get("nombre_corto", resultado.algoritmo)
    titulo_pol = f"RR con q = {resultado.quantum}" if resultado.algoritmo == "Round Robin (Expulsivo)" else sigla

    estado_str = (
        f" Reloj t = {t_limite} / {max_time} u.t."
        if (paso_actual is not None and t_limite < max_time)
        else f" Simulación Completada (T.F. total = {max_time} u.t.)"
    )
    ax.set_title(
        f"Política: {titulo_pol}   |   #P = {n_procs} procesos   |   Σ T.S. = {resultado.suma_rafagas} u.t.   |  {estado_str}",
        loc="left", fontsize=10.5, fontweight="bold", color="#1E293B", pad=6,
    )

    nombres = [p["nombre"] for p in procesos]
    y_map = {nom: n_procs - idx for idx, nom in enumerate(nombres)}

    # Líneas verticales punteadas de la grilla
    for t in range(1, max_time + 1):
        ax.plot([t, t], [0, n_procs + 0.65], linestyle="--", linewidth=0.75, color="#CBD5E1", zorder=1)

    # Línea indicadora del reloj actual durante la animación
    if paso_actual is not None and t_limite < max_time:
        ax.axvline(t_limite, color="#2563EB", linestyle="-", linewidth=1.4, alpha=0.6, zorder=2)

    # Dibujar cuadrados unitarios con el color único de cada proceso hasta t_limite
    alto_cuadro = 0.68 if n_procs <= 12 else (0.64 if n_procs <= 18 else 0.60)
    for t in range(t_limite):
        nom = resultado.gantt_unitario.get(t, "IDLE")
        if nom == "IDLE" or nom not in y_map:
            continue
        y_c = y_map[nom]
        c_fill, c_borde = colores.get(nom, ("#DBEAFE", "#1D4ED8"))
        sq = Rectangle(
            (t + 0.08, y_c - alto_cuadro / 2),
            0.84, alto_cuadro,
            facecolor=c_fill,
            edgecolor=c_borde,
            linewidth=1.35 if max_time <= 35 else 1.05,
            zorder=3,
            clip_on=True,
        )
        ax.add_patch(sq)

    # Dibujar el '+' rojo en T.F. si ya se alcanzó ese instante
    f_size_plus = 9.5 if n_procs <= 15 else 8.2
    for nombre, t_fin in resultado.tiempos_fin.items():
        if t_fin <= t_limite and nombre in y_map:
            y_c = y_map[nombre]
            ax.text(
                t_fin + 0.03, y_c + alto_cuadro / 2,
                "+",
                color="#D32F2F", fontsize=f_size_plus, fontweight="bold",
                ha="left", va="center", zorder=5, clip_on=True,
            )

    f_size_proc = 9.5 if n_procs <= 12 else (8.4 if n_procs <= 18 else 7.5)

    xlim_orig = (0.0, float(max_time))
    ylim_orig = (0.0, float(n_procs + 0.7))
    ax._limites_originales = (xlim_orig, ylim_orig)
    ax._max_time = max_time

    if limites_previos is not None:
        ax.set_xlim(limites_previos[0])
        ax.set_ylim(limites_previos[1])
        configurar_eje_tiempo_gantt(ax, limites_previos[0][0], limites_previos[0][1], max_time)
    else:
        ax.set_xlim(*xlim_orig)
        ax.set_ylim(*ylim_orig)
        configurar_eje_tiempo_gantt(ax, 0.0, float(max_time), max_time)

    ax.set_yticks([y_map[nom] for nom in nombres])
    ax.set_yticklabels(nombres, fontsize=f_size_proc, fontweight="bold")
    for tick_lbl, nom in zip(ax.get_yticklabels(), nombres):
        tick_lbl.set_color(colores[nom][1])
    ax.tick_params(axis="y", length=0, pad=5)
    ax.set_ylabel("Proceso", color="#C62828", fontsize=10, fontweight="bold", labelpad=8)
    fig.subplots_adjust(left=0.065, right=0.985, top=0.89, bottom=0.14)


def dibujar_apartado_cola(
    fig_cola: plt.Figure,
    procesos: List[Dict[str, Any]],
    resultado: Resultado | None,
    paso_actual: int | None = None,
    xlim_sincronizado: tuple[float, float] | None = None,
):
    """
    Dibuja en su propio apartado separado (debajo del Plano de Gantt) la
    Cola de Procesos por unidad de tiempo t = 0..T manteniendo el estilo clásico:
    eje de tiempo superior con ticks limpios y columna vertical de procesos en cada [t, t+1].
    """
    fig_cola.clear()
    fig_cola.patch.set_facecolor("#FFFFFF")
    ax = fig_cola.add_subplot(111)
    ax.set_facecolor("#F8FAFC")

    # Borde superior rojo como eje de tiempo y bordes suaves alrededor
    ax.spines["top"].set_visible(True)
    ax.spines["top"].set_color("#C62828")
    ax.spines["top"].set_linewidth(1.3)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color("#E2E8F0")
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color("#E2E8F0")
    ax.spines["right"].set_visible(True)
    ax.spines["right"].set_color("#E2E8F0")

    if resultado is None or not procesos:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(
            0.5, 0.5,
            "Apartado de Cola de Procesos por Unidad de Tiempo — Se mostrará aquí al iniciar la simulación",
            ha="center", va="center", fontsize=9.5, color="#64748B",
        )
        fig_cola.subplots_adjust(left=0.065, right=0.985, top=0.88, bottom=0.08)
        return

    n_procs = resultado.num_procesos
    max_time = max(1, resultado.tiempo_total)
    t_limite = max_time if paso_actual is None else min(paso_actual, max_time)
    colores = _mapa_colores(procesos)

    max_filas_mostrar = 6 if n_procs <= 10 else 5
    max_cola_len = max(
        2,
        min(
            max_filas_mostrar,
            max((len(col) for col in resultado.colas_por_tiempo.values()), default=1),
        ),
    )

    # Líneas divisorias verticales punteadas para cada u.t.
    for t in range(0, max_time + 1):
        ax.plot([t, t], [-max_cola_len - 0.6, 0], linestyle=":", linewidth=0.65, color="#CBD5E1", zorder=1)

    f_cpu = 8.4 if max_time <= 28 else (7.5 if max_time <= 55 else 6.8)
    f_cola = 7.6 if max_time <= 28 else (6.8 if max_time <= 55 else 6.2)

    for t in range(t_limite):
        cola_t = resultado.colas_por_tiempo.get(t, [])
        visibles = cola_t[:max_filas_mostrar]
        for idx_c, proc_nom in enumerate(visibles):
            y_txt = -0.48 - idx_c * 0.62
            if proc_nom == "IDLE":
                ax.text(
                    t + 0.5, y_txt, "-",
                    color="#94A3B8", fontsize=f_cpu, fontweight="bold",
                    ha="center", va="center", clip_on=True,
                )
            elif idx_c == 0:
                c_fill, c_borde = colores.get(proc_nom, ("#DBEAFE", "#1D4ED8"))
                pill = Rectangle(
                    (t + 0.10, y_txt - 0.24), 0.80, 0.48,
                    facecolor=c_fill, edgecolor=c_borde, linewidth=0.9, zorder=2, clip_on=True,
                )
                ax.add_patch(pill)
                ax.text(
                    t + 0.5, y_txt, proc_nom,
                    color=c_borde, fontsize=f_cpu, fontweight="bold",
                    ha="center", va="center", zorder=3, clip_on=True,
                )
            else:
                _, c_borde = colores.get(proc_nom, ("#F1F5F9", "#334155"))
                ax.text(
                    t + 0.5, y_txt, proc_nom,
                    color=c_borde, fontsize=f_cola, fontweight="bold",
                    ha="center", va="center", zorder=3, clip_on=True,
                )
        if len(cola_t) > max_filas_mostrar:
            y_mas = -0.48 - max_filas_mostrar * 0.62
            ax.text(
                t + 0.5, y_mas, f"+{len(cola_t) - max_filas_mostrar}",
                color="#64748B", fontsize=max(5.8, f_cola - 0.5),
                ha="center", va="center", clip_on=True,
            )

    xlim_orig = (0.0, float(max_time))
    ylim_orig = (-0.48 - (max_cola_len + 0.45) * 0.62, 0.0)
    ax._limites_originales = (xlim_orig, ylim_orig)
    ax._max_time = max_time

    if xlim_sincronizado is not None:
        ax.set_xlim(*xlim_sincronizado)
        configurar_eje_tiempo_cola(ax, xlim_sincronizado[0], xlim_sincronizado[1], max_time)
    else:
        ax.set_xlim(*xlim_orig)
        configurar_eje_tiempo_cola(ax, 0.0, float(max_time), max_time)
    ax.set_ylim(*ylim_orig)

    ax.set_yticks([-0.48, -1.10])
    ax.set_yticklabels(["CPU", "Cola"], color="#475569", fontsize=8.0, fontweight="bold")
    ax.tick_params(axis="y", length=0, pad=5)
    fig_cola.subplots_adjust(left=0.065, right=0.985, top=0.76, bottom=0.08)


def dibujar_panel_formulas(fig: plt.Figure, resultado: Resultado | None):
    """
    Dibuja con estilo Bento UI:
      - Izquierda: Ecuaciones paso a paso (TR, TE, ΣTR/#P, ΣTE/#P).
      - Derecha: Dos tarjetas destacadas (KPIs) con tipografía grande para TR Promedio y TE Promedio.
    """
    fig.clear()
    fig.patch.set_facecolor("#FFFFFF")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#FFFFFF")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    if resultado is None:
        ax.text(
            0.5, 0.5,
            "Las ecuaciones paso a paso (TR, TE, ΣTR/#P, ΣTE/#P)\n"
            "y las tarjetas de promedios aparecerán aquí al simular.",
            ha="center", va="center", fontsize=9.5, color="#64748B",
        )
        fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.04)
        return

    n_procs = resultado.num_procesos
    info_pol = INFO_TEORICA_POLITICAS.get(resultado.algoritmo, {})
    sigla = info_pol.get("nombre_corto", resultado.algoritmo)
    etiqueta_pol = f"RR q={resultado.quantum}" if resultado.algoritmo == "Round Robin (Expulsivo)" else sigla

    str_prom_tr = fmt_num(resultado.promedio_tr)
    str_prom_te = fmt_num(resultado.promedio_te)

    # Si hay más de 6 procesos, abreviar con puntos suspensivos para que nunca se desborde
    if n_procs <= 6:
        restas_tr = ", ".join(f"{f['fin']}-{f['llegada']}" for f in resultado.tabla)
        vals_tr = ", ".join(str(f["tr"]) for f in resultado.tabla)
        suma_str_tr = "+".join(str(f["tr"]) for f in resultado.tabla)

        restas_te = ", ".join(f"{f['tr']}-{f['rafaga']}" for f in resultado.tabla)
        vals_te = ", ".join(str(f["te"]) for f in resultado.tabla)
        suma_str_te = "+".join(str(f["te"]) for f in resultado.tabla)
    else:
        primeros = resultado.tabla[:3]
        ult = resultado.tabla[-1]
        restas_tr = ", ".join(f"{f['fin']}-{f['llegada']}" for f in primeros) + f", ..., {ult['fin']}-{ult['llegada']}"
        vals_tr = ", ".join(str(f["tr"]) for f in primeros) + f", ..., {ult['tr']}"
        suma_str_tr = "+".join(str(f["tr"]) for f in primeros) + f"+...+{ult['tr']}"

        restas_te = ", ".join(f"{f['tr']}-{f['rafaga']}" for f in primeros) + f", ..., {ult['tr']}-{ult['rafaga']}"
        vals_te = ", ".join(str(f["te"]) for f in primeros) + f", ..., {ult['te']}"
        suma_str_te = "+".join(str(f["te"]) for f in primeros) + f"+...+{ult['te']}"

    # ── Izquierda: Fórmulas paso a paso ──
    f_size_eq = 8.6 if n_procs > 12 else 9.0
    linea_tr = f"TR = TF − TLL = ({restas_tr}) = ({vals_tr})"
    linea_te = f"TE = TR − TS = ({restas_te}) = ({vals_te})"

    ax.text(0.01, 0.88, linea_tr, ha="left", va="center", fontsize=f_size_eq, color="#0F172A", family="serif")
    ax.text(0.01, 0.66, linea_te, ha="left", va="center", fontsize=f_size_eq, color="#0F172A", family="serif")

    eq_prom_tr = (
        r"$\frac{\sum TR}{\sharp P} = \frac{"
        + suma_str_tr
        + r"}{"
        + str(n_procs)
        + r"} = \frac{"
        + str(resultado.suma_tr)
        + r"}{"
        + str(n_procs)
        + r"} = "
        + str_prom_tr
        + r"$"
    )
    eq_prom_te = (
        r"$\frac{\sum TE}{\sharp P} = \frac{"
        + suma_str_te
        + r"}{"
        + str(n_procs)
        + r"} = \frac{"
        + str(resultado.suma_te)
        + r"}{"
        + str(n_procs)
        + r"} = "
        + str_prom_te
        + r"$"
    )

    ax.text(0.01, 0.38, eq_prom_tr, ha="left", va="center", fontsize=9.2, color="#0F172A")
    ax.text(0.01, 0.12, eq_prom_te, ha="left", va="center", fontsize=9.2, color="#0F172A")

    # ── Derecha: Tarjetas destacadas (KPIs Bento UI) ──
    # Tarjeta 1: TR Promedio (Azul suave con número grande)
    card_tr = FancyBboxPatch(
        (0.67, 0.52), 0.32, 0.44,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor="#EFF6FF",
        edgecolor="#BFDBFE",
        linewidth=1.2,
    )
    ax.add_patch(card_tr)
    ax.text(0.83, 0.82, "RETORNO PROM. (TR̄)", ha="center", va="center", fontsize=7.5, fontweight="bold", color="#1E40AF")
    ax.text(0.83, 0.62, f"{str_prom_tr} u.t.", ha="center", va="center", fontsize=14, fontweight="bold", color="#1D4ED8")

    # Tarjeta 2: TE Promedio (Verde suave con número grande)
    card_te = FancyBboxPatch(
        (0.67, 0.04), 0.32, 0.44,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor="#F0FDF4",
        edgecolor="#BBF7D0",
        linewidth=1.2,
    )
    ax.add_patch(card_te)
    ax.text(0.83, 0.34, "ESPERA PROM. (TĒ)", ha="center", va="center", fontsize=7.5, fontweight="bold", color="#166534")
    ax.text(0.83, 0.14, f"{str_prom_te} u.t.", ha="center", va="center", fontsize=14, fontweight="bold", color="#15803D")

    fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.04)


def exportar_hoja_completa_png(
    filepath: str,
    procesos: List[Dict[str, Any]],
    resultado: Resultado,
):
    """Genera y guarda un archivo PNG de alta resolución con el Plano de Gantt completo."""
    fig_exp = plt.figure(figsize=(12, max(5.2, resultado.num_procesos * 0.36 + 3.0)), dpi=200, facecolor="#FFFFFF")
    dibujar_plano_gantt(fig_exp, procesos, resultado, paso_actual=None)
    fig_exp.savefig(filepath, dpi=200, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(fig_exp)
