"""
============================================================================
 MÓDULO 2: MOTOR DE ILUSTRACIÓN VECTORIAL (PERSONAJES Y UTILERÍA)
 Autor : Jordan Oliber Soncco Machaca — UNA Puno
============================================================================

 Equivalente en Python/Tkinter a las ilustraciones SVG: todos los personajes
 y objetos se construyen con primitivas vectoriales del tk.Canvas
 (polígonos suavizados, arcos, óvalos y líneas con extremos redondeados),
 por lo que escalan sin pixelarse al redimensionar la ventana.

 Funciones principales:
   - dibujar_persona(...)  → personaje con postura, expresión y accesorios.
   - caja_3d, servidor_bd, candado, libro, laptop, tenedor, plato_espagueti,
     silla, sillon_barbero, poste_barberia, tijeras, peine, ingrediente,
     cigarrillo, mesa, burbuja_pensamiento, zzz, etiqueta, flecha_animada.
============================================================================
"""

from __future__ import annotations
import math
import tkinter as tk
from typing import Dict, Optional, Sequence, Tuple

Punto = Tuple[float, float]

# ─────────────────────────────── Utilidades de color ───────────────────────────────

def _hex_rgb(color: str) -> Tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def oscurecer(color: str, f: float = 0.72) -> str:
    r, g, b = _hex_rgb(color)
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


def aclarar(color: str, f: float = 0.45) -> str:
    r, g, b = _hex_rgb(color)
    return "#%02x%02x%02x" % (
        int(r + (255 - r) * f), int(g + (255 - g) * f), int(b + (255 - b) * f)
    )


PIELES = ("#F1C27D", "#E0AC69", "#C68642", "#FFDBAC", "#D9A27A")
ROPAS = ("#2563EB", "#16A34A", "#9333EA", "#DB2777", "#EA580C", "#0891B2", "#CA8A04", "#4F46E5")
PELOS = ("#3B2A20", "#1F2937", "#6B4423", "#A16207", "#111827")


def paleta_por_nombre(nombre: str) -> Tuple[str, str, str]:
    """Devuelve (piel, ropa, pelo) estables según el nombre del actor."""
    hsh = sum(ord(ch) * (i + 3) for i, ch in enumerate(nombre))
    return PIELES[hsh % len(PIELES)], ROPAS[hsh % len(ROPAS)], PELOS[(hsh // 3) % len(PELOS)]


# ─────────────────────────────── Primitivas básicas ───────────────────────────────

def rect_redondeado(c: tk.Canvas, x1, y1, x2, y2, r, **kw):
    r = max(0.0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [
        x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
        x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
    ]
    return c.create_polygon(pts, smooth=True, **kw)


def etiqueta(c: tk.Canvas, x, y, texto, bg="#F1F5F9", fg="#0F172A", borde=None,
             font=("Segoe UI", 8, "bold"), pad_x=6, pad_y=2, anchor="center"):
    """Píldora de texto con fondo redondeado (badge)."""
    tid = c.create_text(x, y, text=texto, font=font, fill=fg, anchor=anchor)
    bb = c.bbox(tid)
    if bb:
        rid = rect_redondeado(
            c, bb[0] - pad_x, bb[1] - pad_y, bb[2] + pad_x, bb[3] + pad_y, 8,
            fill=bg, outline=borde or bg, width=1,
        )
        c.tag_raise(tid, rid)
    return tid


def flecha_animada(c: tk.Canvas, p0: Punto, p1: Punto, color: str, frame: int = 0,
                   curva: float = 0.18, ancho: float = 2.2):
    """Flecha curva punteada con desplazamiento animado (sensación de flujo)."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    cx, cy = mx - dy * curva, my + dx * curva
    c.create_line(
        p0[0], p0[1], cx, cy, p1[0], p1[1], smooth=True, fill=color, width=ancho,
        dash=(6, 4), dashoffset=-(frame * 3) % 10, arrow=tk.LAST, arrowshape=(10, 12, 4),
    )


def paquetes_en_linea(c: tk.Canvas, p0: Punto, p1: Punto, color: str, frame: int,
                      n: int = 3, tam: float = 4.0):
    """Pequeños paquetes de datos que viajan de p0 a p1."""
    for k in range(n):
        t = ((frame * 0.09) + k / n) % 1.0
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        c.create_rectangle(x - tam, y - tam, x + tam, y + tam, fill=color, outline=oscurecer(color), width=1)


# ─────────────────────────────── Personaje vectorial ───────────────────────────────

# Posición de las manos (relativa al centro de la cabeza, en unidades de escala)
POSES: Dict[str, Tuple[Punto, Punto]] = {
    "reposo": ((-19, 44), (19, 44)),
    "cargar": ((-6, 31), (14, 31)),
    "extender": ((16, 26), (30, 30)),
    "arriba": ((-25, -6), (25, -6)),
    "menton": ((-18, 44), (3, 10)),
    "leer": ((-9, 31), (11, 31)),
    "teclear": ((-6, 40), (16, 40)),
    "fumar": ((-18, 44), (7, 7)),
    "saludar": ((-19, 44), (26, -4)),
}


def mano(c: tk.Canvas, p: Punto, s: float, piel: str):
    c.create_oval(p[0] - 4.5 * s, p[1] - 4.5 * s, p[0] + 4.5 * s, p[1] + 4.5 * s,
                  fill=piel, outline=oscurecer(piel, 0.78))


def dibujar_persona(
    c: tk.Canvas, x: float, y: float, s: float = 1.0, *,
    piel: str = "#F1C27D", ropa: str = "#2563EB", pantalon: str = "#334155",
    pelo: Optional[str] = "#3B2A20", accesorio: Optional[str] = None,
    ojos: str = "abiertos", boca: str = "sonrisa", pose: str = "reposo",
    direccion: int = 1, piernas: Optional[str] = "pie",
    manos: Optional[Sequence[Punto]] = None, delantal: bool = False,
    capa: Optional[str] = None, extra: Sequence[str] = (),
) -> Dict[str, object]:
    """
    Dibuja un personaje vectorial. (x, y) = centro de la cabeza.
    piernas: "pie" (de pie), "sentado" o None (busto).
    accesorio: casco, gorra, gafas, auriculares, sombrero, barba, bigote.
    extra: elementos adicionales en el torso: "corbata", "pajarita".
    Devuelve un diccionario con la geometría (cabeza, manos, cadera...).
    """
    d = 1 if direccion >= 0 else -1
    hr = 13 * s
    sy = y + hr + 3 * s           # línea de hombros
    hip = sy + 34 * s             # cadera
    out_ropa = oscurecer(ropa)
    out_piel = oscurecer(piel, 0.78)
    zapato = "#1F2937"

    # ── Piernas ──
    if piernas == "pie":
        for k, dx in enumerate((-6, 6)):
            col = pantalon if k else oscurecer(pantalon, 0.85)
            x_pie = x + dx * 1.1 * s
            c.create_line(x + dx * s, hip - 4 * s, x_pie, hip + 28 * s,
                          fill=col, width=9 * s, capstyle=tk.ROUND)
            c.create_oval(x_pie - 5 * s + d * 2 * s, hip + 26 * s,
                          x_pie + 6 * s + d * 3 * s, hip + 33 * s, fill=zapato, outline="")
    elif piernas == "sentado":
        for k, off in enumerate((-3, 3)):
            col = pantalon if k else oscurecer(pantalon, 0.85)
            kx = x + d * 24 * s + off * s
            c.create_line(x - d * 2 * s + off * s, hip - 4 * s, kx, hip - 4 * s,
                          fill=col, width=10 * s, capstyle=tk.ROUND)
            c.create_line(kx, hip - 4 * s, kx + d * 2 * s, hip + 22 * s,
                          fill=col, width=8 * s, capstyle=tk.ROUND)
            c.create_oval(kx - 4 * s + d * 3 * s, hip + 20 * s,
                          kx + 7 * s + d * 4 * s, hip + 27 * s, fill=zapato, outline="")

    # ── Cuello y torso ──
    c.create_rectangle(x - 4 * s, y + hr - 3 * s, x + 4 * s, sy + 3 * s, fill=piel, outline="")
    rect_redondeado(c, x - 16 * s, sy, x + 16 * s, hip + 2 * s, 8 * s,
                    fill=ropa, outline=out_ropa, width=1.2)
    c.create_polygon(x - 5 * s, sy, x + 5 * s, sy, x, sy + 6 * s, fill=piel, outline="")

    if delantal:
        rect_redondeado(c, x - 12 * s, sy + 8 * s, x + 12 * s, hip + 6 * s, 4 * s,
                        fill="#F8FAFC", outline="#CBD5E1", width=1)
        c.create_line(x - 10 * s, sy + 9 * s, x - 6 * s, sy + 1 * s, fill="#CBD5E1", width=1.5 * s)
        c.create_line(x + 10 * s, sy + 9 * s, x + 6 * s, sy + 1 * s, fill="#CBD5E1", width=1.5 * s)
        c.create_rectangle(x - 6 * s, sy + 18 * s, x + 6 * s, sy + 25 * s, outline="#CBD5E1")
    if "corbata" in extra:
        c.create_polygon(x - 2.5 * s, sy + 5 * s, x + 2.5 * s, sy + 5 * s, x + 4 * s, sy + 20 * s,
                         x, sy + 24 * s, x - 4 * s, sy + 20 * s, fill="#DC2626", outline="#991B1B")
    if "pajarita" in extra:
        c.create_polygon(x, sy + 4 * s, x - 7 * s, sy + 1 * s, x - 7 * s, sy + 8 * s,
                         fill="#111827", outline="")
        c.create_polygon(x, sy + 4 * s, x + 7 * s, sy + 1 * s, x + 7 * s, sy + 8 * s,
                         fill="#111827", outline="")

    # ── Cabeza ──
    hx = x
    for sg in (-1, 1):
        c.create_oval(hx + sg * hr - 3 * s, y - 3 * s, hx + sg * hr + 3 * s, y + 4 * s,
                      fill=piel, outline=out_piel)
    c.create_oval(hx - hr, y - hr, hx + hr, y + hr, fill=piel, outline=out_piel, width=1.2)

    if pelo and accesorio not in ("casco", "gorra", "sombrero"):
        c.create_arc(hx - hr - 1, y - hr - 2 * s, hx + hr + 1, y + hr, start=8, extent=164,
                     style=tk.CHORD, fill=pelo, outline=pelo)

    if accesorio == "barba":
        barba = pelo or "#9CA3AF"
        c.create_polygon(
            hx - hr + 1 * s, y + 1 * s, hx - hr + 3 * s, y + hr + 4 * s, hx, y + hr + 10 * s,
            hx + hr - 3 * s, y + hr + 4 * s, hx + hr - 1 * s, y + 1 * s,
            hx + 6 * s, y + 4 * s, hx - 6 * s, y + 4 * s,
            smooth=True, fill=barba, outline=oscurecer(barba, 0.8),
        )

    # Ojos
    ex, eyy = hx + d * 1.5 * s, y - 1 * s
    for sx_ in (-4.5, 4.5):
        px = ex + sx_ * s
        if ojos == "cerrados":
            c.create_arc(px - 2.6 * s, eyy - 2 * s, px + 2.6 * s, eyy + 2.2 * s, start=200,
                         extent=140, style=tk.ARC, outline="#1F2937", width=max(1, 1.4 * s))
        elif ojos == "felices":
            c.create_arc(px - 2.6 * s, eyy - 1 * s, px + 2.6 * s, eyy + 3.5 * s, start=20,
                         extent=140, style=tk.ARC, outline="#1F2937", width=max(1, 1.4 * s))
        elif ojos == "sorpresa":
            c.create_oval(px - 2.8 * s, eyy - 2.8 * s, px + 2.8 * s, eyy + 2.8 * s,
                          fill="#FFFFFF", outline="#1F2937")
            c.create_oval(px - 1.3 * s, eyy - 1.3 * s, px + 1.3 * s, eyy + 1.3 * s,
                          fill="#1F2937", outline="")
        else:
            c.create_oval(px - 1.8 * s, eyy - 1.8 * s, px + 1.8 * s, eyy + 1.8 * s,
                          fill="#1F2937", outline="")
            c.create_oval(px - 0.4 * s + d * 0.6 * s, eyy - 1.2 * s, px + 0.6 * s + d * 0.6 * s,
                          eyy - 0.2 * s, fill="#FFFFFF", outline="")

    # Nariz
    c.create_arc(hx + d * 1.5 * s - 2 * s, y + 0.5 * s, hx + d * 1.5 * s + 2 * s, y + 4 * s,
                 start=200 if d > 0 else -20, extent=140, style=tk.ARC, outline=out_piel,
                 width=max(1, 1.1 * s))

    # Mejillas
    if ojos == "felices" or boca == "sonrisa":
        for sg in (-1, 1):
            c.create_oval(hx + sg * 7.5 * s - 2 * s, y + 3 * s, hx + sg * 7.5 * s + 2 * s,
                          y + 6 * s, fill="#FCA5A5", outline="")

    # Boca
    mx_, my_ = hx + d * 1.5 * s, y + 6.5 * s
    if boca == "abierta":
        c.create_oval(mx_ - 2.6 * s, my_ - 1.5 * s, mx_ + 2.6 * s, my_ + 3.5 * s,
                      fill="#7F1D1D", outline="")
    elif boca == "triste":
        c.create_arc(mx_ - 4 * s, my_, mx_ + 4 * s, my_ + 6 * s, start=20, extent=140,
                     style=tk.ARC, outline="#7F1D1D", width=max(1, 1.4 * s))
    elif boca == "neutral":
        c.create_line(mx_ - 3 * s, my_ + 0.5 * s, mx_ + 3 * s, my_ + 0.5 * s,
                      fill="#7F1D1D", width=max(1, 1.3 * s))
    else:
        c.create_arc(mx_ - 4.5 * s, my_ - 4 * s, mx_ + 4.5 * s, my_ + 2.5 * s, start=200,
                     extent=140, style=tk.ARC, outline="#7F1D1D", width=max(1, 1.4 * s))

    # Accesorios de cabeza
    if accesorio == "bigote":
        col_b = oscurecer(pelo or "#3B2A20", 0.8)
        c.create_polygon(
            mx_ - 7 * s, my_ - 0.5 * s, mx_, my_ - 3 * s, mx_ + 7 * s, my_ - 0.5 * s,
            mx_ + 3 * s, my_ + 0.5 * s, mx_, my_ - 1 * s, mx_ - 3 * s, my_ + 0.5 * s,
            smooth=True, fill=col_b, outline=col_b,
        )
    elif accesorio == "gafas":
        for sx_ in (-4.5, 4.5):
            px = ex + sx_ * s
            c.create_oval(px - 3.9 * s, eyy - 3.6 * s, px + 3.9 * s, eyy + 3.6 * s,
                          outline="#1F2937", width=max(1, 1.3 * s))
        c.create_line(ex - 0.6 * s, eyy, ex + 0.6 * s, eyy, fill="#1F2937", width=max(1, 1.3 * s))
    elif accesorio in ("casco", "gorra"):
        col = "#FACC15" if accesorio == "casco" else "#1E3A8A"
        c.create_arc(hx - hr - 1.5 * s, y - hr - 5 * s, hx + hr + 1.5 * s, y + hr - 5 * s,
                     start=0, extent=180, style=tk.CHORD, fill=col, outline=oscurecer(col))
        if accesorio == "casco":
            rect_redondeado(c, hx - hr - 4 * s, y - 6.5 * s, hx + hr + 4 * s, y - 3 * s, 1.5 * s,
                            fill=col, outline=oscurecer(col))
            c.create_line(hx, y - hr - 5 * s, hx, y - 6.5 * s, fill=oscurecer(col), width=2 * s)
        else:
            c.create_polygon(hx, y - 6.5 * s, hx + d * (hr + 10 * s), y - 6 * s,
                             hx + d * (hr + 10 * s), y - 3 * s, hx, y - 3 * s,
                             smooth=True, fill=oscurecer(col, 0.8), outline="")
    elif accesorio == "sombrero":
        c.create_oval(hx - hr - 7 * s, y - hr - 1 * s, hx + hr + 7 * s, y - hr + 6 * s,
                      fill="#1F2937", outline="#111827")
        rect_redondeado(c, hx - hr + 2 * s, y - hr - 12 * s, hx + hr - 2 * s, y - hr + 3 * s,
                        5 * s, fill="#1F2937", outline="#111827")
        c.create_rectangle(hx - hr + 2 * s, y - hr - 2 * s, hx + hr - 2 * s, y - hr + 1 * s,
                           fill="#B45309", outline="")
    elif accesorio == "auriculares":
        c.create_arc(hx - hr - 2 * s, y - hr - 3 * s, hx + hr + 2 * s, y + hr, start=10,
                     extent=160, style=tk.ARC, outline="#334155", width=2.5 * s)
        for sg in (-1, 1):
            rect_redondeado(c, hx + sg * hr - 3 * s, y - 5 * s, hx + sg * hr + 3 * s, y + 5 * s,
                            2 * s, fill="#334155", outline="#1E293B")

    # ── Brazos y manos (o capa protectora) ──
    hombro_i = (x - 15 * s, sy + 5 * s)
    hombro_d = (x + 15 * s, sy + 5 * s)
    if capa:
        c.create_polygon(x - 6 * s, sy - 1 * s, x + 6 * s, sy - 1 * s, x + 25 * s, hip + 10 * s,
                         x - 25 * s, hip + 10 * s, fill=capa, outline=oscurecer(capa), width=1)
        mano_i, mano_d = hombro_i, hombro_d
    elif manos is None and pose == "cruzados":
        rect_redondeado(c, x - 18 * s, sy + 13 * s, x + 18 * s, sy + 22 * s, 4 * s,
                        fill=ropa, outline=out_ropa)
        mano_i, mano_d = (x - 9 * s, sy + 17.5 * s), (x + 9 * s, sy + 17.5 * s)
        mano(c, mano_i, s * 0.9, piel)
        mano(c, mano_d, s * 0.9, piel)
    else:
        if manos is None:
            offs = POSES.get(pose, POSES["reposo"])
            pts = [(x + d * ox * s, y + oy * s) for ox, oy in offs]
        else:
            pts = list(manos)
        pts.sort(key=lambda p: p[0])
        mano_i, mano_d = pts[0], pts[1]
        for hombro, mn, sg in ((hombro_i, mano_i, -1), (hombro_d, mano_d, 1)):
            mx = (hombro[0] + mn[0]) / 2 + sg * 6 * s
            my = (hombro[1] + mn[1]) / 2 + 4 * s
            c.create_line(hombro[0], hombro[1], mx, my, mn[0], mn[1], fill=ropa, width=7 * s,
                          capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True)
            mano(c, mn, s, piel)

    return {
        "cabeza": (hx, y), "r": hr, "manos": (mano_i, mano_d),
        "hombros": sy, "cadera": hip,
        "boca": (mx_, my_),
    }


# ─────────────────────────────── Utilería / Props ───────────────────────────────

def caja_3d(c: tk.Canvas, x, y, t, texto: str = "", subtexto: str = "",
            color: str = "#D9A066", resaltar: Optional[str] = None):
    """Caja de cartón isométrica. (x, y) = centro de la cara frontal; t = semilado."""
    dpt = t * 0.5
    out = resaltar or oscurecer(color, 0.6)
    c.create_polygon(x - t, y - t, x - t + dpt, y - t - dpt, x + t + dpt, y - t - dpt, x + t, y - t,
                     fill=aclarar(color, 0.3), outline=out)
    c.create_polygon(x + t, y - t, x + t + dpt, y - t - dpt, x + t + dpt, y + t - dpt, x + t, y + t,
                     fill=oscurecer(color, 0.8), outline=out)
    c.create_rectangle(x - t, y - t, x + t, y + t, fill=color, outline=out,
                       width=2 if resaltar else 1)
    # Cinta adhesiva
    c.create_rectangle(x - t * 0.18, y - t, x + t * 0.18, y - t * 0.35, fill="#F5DEB3", outline="")
    c.create_polygon(x - t * 0.18, y - t, x - t * 0.18 + dpt, y - t - dpt,
                     x + t * 0.18 + dpt, y - t - dpt, x + t * 0.18, y - t, fill="#F5DEB3", outline="")
    if texto:
        c.create_text(x, y + (0 if not subtexto else -t * 0.05), text=texto,
                      font=("Segoe UI", max(7, int(t * 0.55)), "bold"), fill="#3F2A14")
    if subtexto:
        c.create_text(x, y + t * 0.62, text=subtexto, font=("Segoe UI", max(6, int(t * 0.34)), "bold"),
                      fill="#5B3A1A")


def servidor_bd(c: tk.Canvas, cx, cy, w, h, color_led: str, frame: int = 0,
                cuerpo: str = "#E2E8F0"):
    """Pila de 3 cilindros de base de datos con LEDs parpadeantes."""
    uh = h / 3.0
    e = min(w * 0.30, uh * 0.55)
    top = cy - h / 2
    for k in (2, 1, 0):
        y_top = top + k * uh + e / 2
        y_bot = top + (k + 1) * uh - e / 2 + (e / 2 if k == 2 else 0)
        col = cuerpo
        c.create_oval(cx - w / 2, y_bot - e / 2, cx + w / 2, y_bot + e / 2,
                      fill=oscurecer(col, 0.85), outline="#64748B", width=1.5)
        c.create_rectangle(cx - w / 2, y_top, cx + w / 2, y_bot, fill=col, outline="")
        c.create_line(cx - w / 2, y_top, cx - w / 2, y_bot, fill="#64748B", width=1.5)
        c.create_line(cx + w / 2, y_top, cx + w / 2, y_bot, fill="#64748B", width=1.5)
        c.create_oval(cx - w / 2, y_top - e / 2, cx + w / 2, y_top + e / 2,
                      fill=aclarar(col, 0.5), outline="#64748B", width=1.5)
        # Brillo lateral
        c.create_rectangle(cx - w / 2 + w * 0.08, y_top + e * 0.3, cx - w / 2 + w * 0.14,
                           y_bot - e * 0.1, fill="#FFFFFF", outline="")
        # LEDs y ranuras
        ly = (y_top + y_bot) / 2 + e * 0.2
        for j in range(3):
            encendido = (frame + k * 2 + j) % 4 != 0
            led = color_led if encendido else oscurecer(color_led, 0.55)
            lx = cx - w * 0.30 + j * w * 0.11
            c.create_oval(lx - 3, ly - 3, lx + 3, ly + 3, fill=led, outline=oscurecer(led, 0.7))
        for j in range(3):
            c.create_line(cx + w * 0.02, ly - 4 + j * 4, cx + w * 0.36, ly - 4 + j * 4,
                          fill="#94A3B8", width=1.5)


def candado(c: tk.Canvas, x, y, s: float, cerrado: bool, color: str):
    dx = 0 if cerrado else 5 * s
    dy = 0 if cerrado else -5 * s
    c.create_arc(x - 6 * s + dx, y - 12 * s + dy, x + 6 * s + dx, y + 4 * s + dy, start=0,
                 extent=180, style=tk.ARC, outline="#475569", width=3 * s)
    if cerrado:
        c.create_line(x - 6 * s, y - 4 * s, x - 6 * s, y, fill="#475569", width=3 * s)
        c.create_line(x + 6 * s, y - 4 * s, x + 6 * s, y, fill="#475569", width=3 * s)
    else:
        c.create_line(x + 6 * s + dx, y - 4 * s + dy, x + 6 * s + dx, y, fill="#475569", width=3 * s)
    rect_redondeado(c, x - 9 * s, y - 1 * s, x + 9 * s, y + 12 * s, 3 * s,
                    fill=color, outline=oscurecer(color))
    c.create_oval(x - 2 * s, y + 2.5 * s, x + 2 * s, y + 6.5 * s, fill="#1F2937", outline="")
    c.create_line(x, y + 6 * s, x, y + 9.5 * s, fill="#1F2937", width=1.6 * s)


def libro(c: tk.Canvas, x, y, s: float, color: str = "#2563EB", abierto: bool = True):
    if not abierto:
        rect_redondeado(c, x - 9 * s, y - 11 * s, x + 9 * s, y + 9 * s, 2 * s,
                        fill=color, outline=oscurecer(color))
        c.create_rectangle(x - 9 * s, y + 5 * s, x + 9 * s, y + 9 * s, fill="#F8FAFC", outline="")
        c.create_line(x - 5 * s, y - 5 * s, x + 5 * s, y - 5 * s, fill="#FFFFFF", width=1.5 * s)
        return
    c.create_polygon(x, y - 6 * s, x - 16 * s, y - 10 * s, x - 16 * s, y + 7 * s, x, y + 10 * s,
                     x + 16 * s, y + 7 * s, x + 16 * s, y - 10 * s, fill=color, outline=oscurecer(color))
    c.create_polygon(x, y - 7 * s, x - 14 * s, y - 10 * s, x - 14 * s, y + 4 * s, x, y + 7 * s,
                     fill="#FFFFFF", outline="#CBD5E1")
    c.create_polygon(x, y - 7 * s, x + 14 * s, y - 10 * s, x + 14 * s, y + 4 * s, x, y + 7 * s,
                     fill="#F8FAFC", outline="#CBD5E1")
    for k in range(3):
        yy = y - 5 * s + k * 3.5 * s
        c.create_line(x - 12 * s, yy - 2 * s, x - 2 * s, yy, fill="#94A3B8")
        c.create_line(x + 2 * s, yy, x + 12 * s, yy - 2 * s, fill="#94A3B8")


def periodico(c: tk.Canvas, x, y, s: float):
    c.create_polygon(x - 15 * s, y - 12 * s, x + 15 * s, y - 13 * s, x + 14 * s, y + 9 * s,
                     x - 14 * s, y + 10 * s, fill="#F1F5F9", outline="#94A3B8")
    c.create_line(x, y - 12 * s, x, y + 9 * s, fill="#CBD5E1")
    c.create_rectangle(x - 12 * s, y - 9 * s, x - 3 * s, y - 4 * s, fill="#CBD5E1", outline="")
    for k in range(3):
        yy = y - 1 * s + k * 3 * s
        c.create_line(x - 12 * s, yy, x - 2 * s, yy, fill="#94A3B8")
        c.create_line(x + 2 * s, yy - 6 * s, x + 12 * s, yy - 6 * s, fill="#94A3B8")


def laptop(c: tk.Canvas, x, y, s: float, activo: bool, frame: int = 0, color_codigo: str = "#F87171"):
    """(x, y) = centro del borde inferior de la pantalla."""
    rect_redondeado(c, x - 17 * s, y - 24 * s, x + 17 * s, y, 3 * s, fill="#334155", outline="#1E293B")
    c.create_rectangle(x - 14 * s, y - 21 * s, x + 14 * s, y - 3 * s,
                       fill="#0F172A" if activo else "#475569", outline="")
    if activo:
        n = 1 + frame % 5
        for k in range(n):
            largo = (8 + (k * 7 + frame) % 14) * s
            c.create_line(x - 12 * s, y - 18 * s + k * 3.2 * s, x - 12 * s + largo, y - 18 * s + k * 3.2 * s,
                          fill=color_codigo if k % 2 == 0 else "#86EFAC", width=1.6 * s)
    c.create_polygon(x - 19 * s, y, x + 19 * s, y, x + 23 * s, y + 6 * s, x - 23 * s, y + 6 * s,
                     fill="#94A3B8", outline="#64748B")


def tenedor(c: tk.Canvas, x, y, ang_deg: float, s: float, color: str = "#CBD5E1",
            resaltar: Optional[str] = None):
    """Tenedor metálico de 3 puntas centrado en (x, y) apuntando hacia ang_deg."""
    a = math.radians(ang_deg)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    L = 26 * s
    p0 = (x - ux * L / 2, y - uy * L / 2)
    p1 = (x + ux * L * 0.12, y + uy * L * 0.12)
    base = (x + ux * L * 0.18, y + uy * L * 0.18)
    borde = resaltar or "#475569"
    c.create_line(p0[0], p0[1], p1[0], p1[1], fill=borde, width=4.5 * s, capstyle=tk.ROUND)
    c.create_line(p0[0], p0[1], p1[0], p1[1], fill=color, width=2.6 * s, capstyle=tk.ROUND)
    c.create_line(base[0] - px * 4 * s, base[1] - py * 4 * s, base[0] + px * 4 * s, base[1] + py * 4 * s,
                  fill=borde, width=2.6 * s, capstyle=tk.ROUND)
    for k in (-3.5, 0, 3.5):
        bx, by = base[0] + px * k * s, base[1] + py * k * s
        tx, ty = bx + ux * L * 0.34, by + uy * L * 0.34
        c.create_line(bx, by, tx, ty, fill=borde, width=1.8 * s, capstyle=tk.ROUND)


def plato_espagueti(c: tk.Canvas, x, y, r: float, lleno: bool = True, frame: int = 0):
    c.create_oval(x - r, y - r * 0.62, x + r, y + r * 0.62, fill="#FFFFFF", outline="#CBD5E1", width=1.5)
    c.create_oval(x - r * 0.72, y - r * 0.44, x + r * 0.72, y + r * 0.44, fill="#F8FAFC", outline="#E2E8F0")
    if not lleno:
        return
    rr = r * 0.55
    for k in range(5):
        fase = k * 1.3 + frame * 0.15
        pts = []
        for j in range(7):
            t = j / 6.0
            pts += [x - rr + 2 * rr * t, y - rr * 0.35 + k * rr * 0.17 + math.sin(t * 9 + fase) * rr * 0.12]
        c.create_line(*pts, smooth=True, fill="#EAB308" if k % 2 else "#FACC15", width=max(1.5, r * 0.08))
    c.create_oval(x - rr * 0.35, y - rr * 0.32, x + rr * 0.35, y + rr * 0.12, fill="#DC2626", outline="")
    c.create_oval(x - rr * 0.18, y - rr * 0.22, x + rr * 0.14, y + rr * 0.02, fill="#7C2D12", outline="")


def burbuja_pensamiento(c: tk.Canvas, x, y, texto: str, s: float = 1.0, origen: Optional[Punto] = None,
                        color_texto: str = "#334155"):
    circ = [(-14, 0, 10), (-4, -6, 12), (9, -4, 11), (14, 4, 9), (2, 6, 10), (-10, 6, 9)]
    for dx, dy, r in circ:
        c.create_oval(x + (dx - r) * s - 1.5, y + (dy - r) * s - 1.5, x + (dx + r) * s + 1.5,
                      y + (dy + r) * s + 1.5, fill="#94A3B8", outline="")
    for dx, dy, r in circ:
        c.create_oval(x + (dx - r) * s, y + (dy - r) * s, x + (dx + r) * s, y + (dy + r) * s,
                      fill="#FFFFFF", outline="")
    if origen:
        for k, rad in ((0.55, 3.5), (0.8, 2.2)):
            bx = x + (origen[0] - x) * k
            by = y + (origen[1] - y) * k
            c.create_oval(bx - rad * s, by - rad * s, bx + rad * s, by + rad * s, fill="#FFFFFF",
                          outline="#94A3B8")
    c.create_text(x, y + 1 * s, text=texto, font=("Segoe UI", max(7, int(9 * s)), "bold"), fill=color_texto)


def globo_dialogo(c: tk.Canvas, x, y, texto: str, color: str = "#DC2626", s: float = 1.0):
    tid = c.create_text(x, y, text=texto, font=("Segoe UI", max(7, int(8 * s)), "bold"), fill=color)
    bb = c.bbox(tid)
    if bb:
        rid = rect_redondeado(c, bb[0] - 6, bb[1] - 3, bb[2] + 6, bb[3] + 3, 7,
                              fill="#FFFFFF", outline=color, width=1.5)
        pico = c.create_polygon(x - 4, bb[3] + 2, x + 4, bb[3] + 2, x - 2, bb[3] + 9,
                                fill="#FFFFFF", outline=color)
        c.tag_raise(rid, pico)
        c.tag_raise(tid, rid)


def zzz(c: tk.Canvas, x, y, frame: int, s: float = 1.0):
    for k in range(3):
        fase = (frame + k * 2) % 6
        c.create_text(x + k * 8 * s, y - k * 10 * s - fase * 1.5 * s, text="Z",
                      font=("Segoe UI", int((8 + k * 3) * s) + 1, "bold"), fill="#6366F1")


def silla(c: tk.Canvas, x, y, s: float, direccion: int = 1, color: str = "#2563EB"):
    """Silla de perfil. (x, y) = centro superior del asiento. Respaldo opuesto a la dirección."""
    d = 1 if direccion >= 0 else -1
    out = oscurecer(color)
    bx = x - d * 15 * s
    for lx in (x - 12 * s, x + 12 * s):
        c.create_line(lx, y + 3 * s, lx, y + 26 * s, fill="#475569", width=2.5 * s)
    rect_redondeado(c, bx - 3 * s, y - 32 * s, bx + 3 * s, y + 4 * s, 2.5 * s, fill=color, outline=out)
    rect_redondeado(c, x - 16 * s, y - 2 * s, x + 16 * s, y + 5 * s, 3 * s, fill=color, outline=out)


def sillon_barbero(c: tk.Canvas, x, y, s: float, direccion: int = 1, y_piso: Optional[float] = None):
    d = 1 if direccion >= 0 else -1
    y_piso = y_piso if y_piso is not None else y + 34 * s
    rojo = "#B91C1C"
    c.create_rectangle(x - 3 * s, y + 6 * s, x + 3 * s, y_piso - 4 * s, fill="#CBD5E1", outline="#94A3B8")
    c.create_oval(x - 18 * s, y_piso - 7 * s, x + 18 * s, y_piso + 1 * s, fill="#CBD5E1", outline="#94A3B8")
    bx = x - d * 17 * s
    rect_redondeado(c, bx - 5 * s, y - 40 * s, bx + 5 * s, y + 6 * s, 4 * s, fill=rojo, outline="#7F1D1D")
    rect_redondeado(c, bx - 6 * s, y - 52 * s, bx + 6 * s, y - 40 * s, 4 * s, fill="#1F2937", outline="#111827")
    rect_redondeado(c, x - 20 * s, y - 3 * s, x + 20 * s, y + 7 * s, 4 * s, fill=rojo, outline="#7F1D1D")
    c.create_line(x - 12 * s, y - 12 * s, x + 14 * s, y - 12 * s, fill="#CBD5E1", width=3 * s, capstyle=tk.ROUND)
    c.create_line(x + d * 26 * s, y + 18 * s, x + d * 38 * s, y + 18 * s, fill="#94A3B8", width=3 * s,
                  capstyle=tk.ROUND)


def poste_barberia(c: tk.Canvas, x, y1, y2, w: float, frame: int = 0):
    rect_redondeado(c, x - w / 2, y1, x + w / 2, y2, w / 2.5, fill="#FFFFFF", outline="#94A3B8")
    paso = 14.0
    alto = y2 - y1
    for k in range(int(alto / paso) + 3):
        yb = y1 + ((k * paso + frame * 2.5) % (alto + paso)) - paso / 2
        col = "#DC2626" if k % 2 == 0 else "#2563EB"
        pts = [(x - w / 2 + 1, yb), (x + w / 2 - 1, yb - 7), (x + w / 2 - 1, yb - 2), (x - w / 2 + 1, yb + 5)]
        flat = []
        for px, py in pts:
            flat += [px, max(y1 + 2, min(y2 - 2, py))]
        c.create_polygon(flat, fill=col, outline="")
    c.create_oval(x - w / 2 - 2, y1 - 6, x + w / 2 + 2, y1 + 2, fill="#CBD5E1", outline="#94A3B8")
    c.create_oval(x - w / 2 + 1, y1 - 12, x + w / 2 - 1, y1 - 3, fill="#FDE68A", outline="#CA8A04")
    c.create_oval(x - w / 2 - 2, y2 - 2, x + w / 2 + 2, y2 + 6, fill="#CBD5E1", outline="#94A3B8")


def tijeras(c: tk.Canvas, x, y, s: float, abiertas: bool, ang: float = -35):
    apertura = 22 if abiertas else 5
    for sg in (-1, 1):
        a = math.radians(ang + sg * apertura)
        tx, ty = x + math.cos(a) * 15 * s, y + math.sin(a) * 15 * s
        c.create_line(x, y, tx, ty, fill="#64748B", width=2.6 * s, capstyle=tk.ROUND)
        c.create_line(x, y, tx, ty, fill="#E2E8F0", width=1.2 * s, capstyle=tk.ROUND)
        a2 = math.radians(ang + 180 - sg * apertura)
        hx, hy = x + math.cos(a2) * 7 * s, y + math.sin(a2) * 7 * s
        c.create_oval(hx - 3.5 * s, hy - 3.5 * s, hx + 3.5 * s, hy + 3.5 * s, outline="#DC2626", width=2 * s)
    c.create_oval(x - 1.5 * s, y - 1.5 * s, x + 1.5 * s, y + 1.5 * s, fill="#334155", outline="")


def peine(c: tk.Canvas, x, y, s: float):
    c.create_rectangle(x - 9 * s, y - 2.5 * s, x + 9 * s, y + 0.5 * s, fill="#1F2937", outline="")
    for k in range(9):
        xx = x - 8 * s + k * 2 * s
        c.create_line(xx, y + 0.5 * s, xx, y + 4.5 * s, fill="#1F2937", width=1)


def ingrediente(c: tk.Canvas, nombre: str, x, y, s: float):
    """Iconos vectoriales: Tabaco (hojas), Papel (pliegos) y Fósforos (caja + cerillas)."""
    if nombre == "Tabaco":
        for off, col in ((-4, "#92400E"), (3, "#65A30D")):
            c.create_polygon(
                x - 13 * s, y + off * s * 0.6, x - 4 * s, y - 7 * s + off * s, x + 9 * s, y - 5 * s + off * s,
                x + 14 * s, y + off * s * 0.6, x + 9 * s, y + 5 * s + off * s, x - 4 * s, y + 7 * s + off * s,
                smooth=True, fill=col, outline=oscurecer(col, 0.7),
            )
            c.create_line(x - 12 * s, y + off * s * 0.6, x + 13 * s, y + off * s * 0.6,
                          fill=aclarar(col, 0.4), width=1.2)
    elif nombre == "Papel":
        c.create_polygon(x - 12 * s, y - 8 * s, x + 10 * s, y - 11 * s, x + 13 * s, y + 6 * s,
                         x - 9 * s, y + 9 * s, fill="#F1F5F9", outline="#94A3B8")
        c.create_polygon(x - 13 * s, y - 6 * s, x + 11 * s, y - 7 * s, x + 12 * s, y + 9 * s,
                         x - 12 * s, y + 10 * s, fill="#FFFFFF", outline="#94A3B8")
        c.create_line(x - 12 * s, y + 2 * s, x + 12 * s, y + 1 * s, fill="#CBD5E1", dash=(2, 2))
    else:  # Fósforos
        rect_redondeado(c, x - 13 * s, y - 6 * s, x + 9 * s, y + 9 * s, 2 * s, fill="#DC2626", outline="#7F1D1D")
        c.create_rectangle(x - 13 * s, y - 1 * s, x + 9 * s, y + 3 * s, fill="#FACC15", outline="")
        for k in range(3):
            bx = x + 4 * s + k * 3.5 * s
            c.create_line(bx, y - 2 * s, bx + 4 * s, y - 14 * s, fill="#F5DEB3", width=2 * s)
            c.create_oval(bx + 2.3 * s, y - 17 * s, bx + 6.3 * s, y - 12.5 * s, fill="#B91C1C", outline="")


def cigarrillo(c: tk.Canvas, x, y, s: float, direccion: int, frame: int = 0):
    """Cigarrillo encendido sostenido en (x, y), con brasa y humo animado."""
    d = 1 if direccion >= 0 else -1
    x2, y2 = x + d * 16 * s, y - 3 * s
    c.create_line(x, y, x + d * 5 * s, y - 1 * s, fill="#F59E0B", width=3.6 * s, capstyle=tk.ROUND)
    c.create_line(x + d * 5 * s, y - 1 * s, x2, y2, fill="#FFFFFF", width=3.6 * s, capstyle=tk.ROUND)
    c.create_line(x + d * 5 * s, y - 2.8 * s, x2, y2 - 1.8 * s, fill="#E2E8F0", width=1)
    brillo = "#F97316" if frame % 2 == 0 else "#EF4444"
    c.create_oval(x2 - 2.6 * s, y2 - 2.6 * s, x2 + 2.6 * s, y2 + 2.6 * s, fill=brillo, outline="#B91C1C")
    for k in range(4):
        t = ((frame + k * 2.5) % 10) / 10.0
        px = x2 + d * 3 * s + math.sin(t * 6 + k) * 4 * s
        py = y2 - 5 * s - t * 34 * s
        rad = (2.5 + t * 6) * s
        tono = "#E2E8F0" if t < 0.6 else "#F1F5F9"
        c.create_oval(px - rad, py - rad, px + rad, py + rad, fill=tono, outline="#CBD5E1")


def mesa(c: tk.Canvas, x1, y, x2, s: float, alto_patas: float, color: str = "#B7794A"):
    out = oscurecer(color, 0.65)
    for lx in (x1 + 10 * s, x2 - 10 * s):
        c.create_rectangle(lx - 3 * s, y + 6 * s, lx + 3 * s, y + alto_patas, fill=oscurecer(color, 0.8), outline=out)
    rect_redondeado(c, x1, y, x2, y + 8 * s, 3 * s, fill=color, outline=out)
    c.create_line(x1 + 6 * s, y + 2 * s, x2 - 6 * s, y + 2 * s, fill=aclarar(color, 0.35), width=1)


def reloj_pared(c: tk.Canvas, x, y, r: float, frame: int = 0):
    c.create_oval(x - r, y - r, x + r, y + r, fill="#FFFFFF", outline="#475569", width=2)
    for k in range(12):
        a = math.radians(k * 30)
        c.create_line(x + math.cos(a) * r * 0.78, y + math.sin(a) * r * 0.78, x + math.cos(a) * r * 0.92,
                      y + math.sin(a) * r * 0.92, fill="#94A3B8")
    a_m = math.radians(-90 + frame * 18)
    a_h = math.radians(-90 + frame * 1.5)
    c.create_line(x, y, x + math.cos(a_h) * r * 0.5, y + math.sin(a_h) * r * 0.5, fill="#0F172A", width=2.5)
    c.create_line(x, y, x + math.cos(a_m) * r * 0.78, y + math.sin(a_m) * r * 0.78, fill="#DC2626", width=1.5)
