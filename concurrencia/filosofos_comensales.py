"""
============================================================================
 3. PROBLEMA DE LOS FILÓSOFOS COMENSALES
 Autor : Jordan Oliber Soncco Machaca — UNA Puno
============================================================================
"""

from __future__ import annotations
import re
import math
import random
import threading
from typing import Any, List
from .base_simulacion import BaseSimulacionFrame
from . import graficos_personajes as gp


class SimFilosofosComensales(BaseSimulacionFrame):
    N = 5

    def __init__(self, master):
        super().__init__(master, "Filósofos comensales")
        self.estados = ["Pensando"] * self.N
        self.comidas = [0] * self.N
        self.dueno_tenedor: List[int | None] = [None] * self.N
        self.camarero_disp = 4
        self._configurar_indicadores_semaforos([
            ("camarero", "Semáforo Camarero (Anti-Deadlock)", "4 / 4 disponibles"),
            ("comiendo", "Filósofos Comiendo Ahora", "Ninguno"),
            ("tenedores", "Tenedores Libres (T0..T4)", "5 / 5 libres"),
            ("comidas_1", "Comidas (F0, F1, F2)", "F0:0 | F1:0 | F2:0"),
            ("comidas_2", "Comidas (F3, F4)", "F3:0 | F4:0"),
            ("total_com", "Total Raciones Comidas", "0"),
        ])
        self._dibujar_escena()

    def _reset_estado_visual(self):
        self.estados = ["Pensando"] * self.N
        self.comidas = [0] * self.N
        self.dueno_tenedor = [None] * self.N
        self.camarero_disp = 4
        self._actualizar_ui()
        self._dibujar_escena()

    def _iniciar_hilos(self, my_sim_id: int):
        self.tenedores = [threading.Lock() for _ in range(self.N)]
        self.camarero = threading.Semaphore(self.N - 1)
        self._agregar_log("Iniciando mesa con 5 filósofos, 5 tenedores y semáforo camarero=4.")
        for i in range(self.N):
            threading.Thread(target=self._hilo_filosofo, args=(i, my_sim_id), daemon=True).start()

    def _desbloquear_semaforos(self):
        cam = getattr(self, "camarero", None)
        if cam:
            for _ in range(self.N):
                try:
                    cam.release()
                except Exception:
                    pass
        for t in getattr(self, "tenedores", []):
            if t.locked():
                try:
                    t.release()
                except Exception:
                    pass

    def _hilo_filosofo(self, i: int, my_sim_id: int):
        izq = i
        der = (i + 1) % self.N
        while self._esperar_si_pausado(my_sim_id):
            self._emitir(my_sim_id, "pensar", i)
            if not self._dormir_hilo(random.uniform(1.0, 1.9), my_sim_id):
                break

            self._emitir(my_sim_id, "hambriento", i)
            self.camarero.acquire()
            if not self._esperar_si_pausado(my_sim_id):
                self.camarero.release()
                break

            self.tenedores[izq].acquire()
            self._emitir(my_sim_id, "tomo_tenedor", (i, izq))
            if not self._dormir_hilo(0.2, my_sim_id):
                self.tenedores[izq].release()
                self.camarero.release()
                break

            self.tenedores[der].acquire()
            self._emitir(my_sim_id, "comer", (i, izq, der))
            if not self._dormir_hilo(random.uniform(1.1, 1.8), my_sim_id):
                self.tenedores[der].release()
                self.tenedores[izq].release()
                self.camarero.release()
                break

            self.tenedores[der].release()
            self.tenedores[izq].release()
            self.camarero.release()
            self._emitir(my_sim_id, "terminar_comer", (i, izq, der))

    def _actualizar_ui(self):
        comiendo_ahora = [f"F{i}" for i, e in enumerate(self.estados) if e == "Comiendo"]
        libres = sum(1 for d in self.dueno_tenedor if d is None)
        self._actualizar_indicador("camarero", f"{self.camarero_disp} / 4 libres", "#1E40AF")
        self._actualizar_indicador(
            "comiendo", ", ".join(comiendo_ahora) if comiendo_ahora else "Ninguno", "#15803D"
        )
        self._actualizar_indicador("tenedores", f"{libres} / 5 libres", "#B45309")
        self._actualizar_indicador(
            "comidas_1", f"F0:{self.comidas[0]} | F1:{self.comidas[1]} | F2:{self.comidas[2]}", "#0F172A"
        )
        self._actualizar_indicador(
            "comidas_2", f"F3:{self.comidas[3]} | F4:{self.comidas[4]}", "#0F172A"
        )
        self._actualizar_indicador("total_com", str(sum(self.comidas)), "#334155")

    def _procesar_evento(self, tipo: str, datos: Any):
        if tipo == "pensar":
            i = datos
            self.estados[i] = "Pensando"
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "hambriento":
            i = datos
            self.estados[i] = "Hambriento"
            self._agregar_log(f"F{i} tiene hambre → solicita wait(camarero).")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "tomo_tenedor":
            i, izq = datos
            self.dueno_tenedor[izq] = i
            self.camarero_disp = max(0, self.camarero_disp - 1)
            self._dibujar_escena()
        elif tipo == "comer":
            i, izq, der = datos
            self.dueno_tenedor[izq] = i
            self.dueno_tenedor[der] = i
            self.estados[i] = "Comiendo"
            self.comidas[i] += 1
            self.lbl_status_banner.configure(
                text=f"Filósofo F{i} adquirió tenedores T{izq} y T{der} → COMIENDO (Comidas de F{i}: {self.comidas[i]})",
                text_color="#15803D",
            )
            self._agregar_log(f"F{i} adquirió T{izq} y T{der} → COMIENDO (ración #{self.comidas[i]}).")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "terminar_comer":
            i, izq, der = datos
            if self.dueno_tenedor[izq] == i:
                self.dueno_tenedor[izq] = None
            if self.dueno_tenedor[der] == i:
                self.dueno_tenedor[der] = None
            self.estados[i] = "Pensando"
            self.camarero_disp = min(4, self.camarero_disp + 1)
            self._agregar_log(f"F{i} liberó T{der}, T{izq} y signal(camarero) → vuelve a pensar.")
            self._actualizar_ui()
            self._dibujar_escena()

    def _dibujar_escena(self):
        c = self.canvas
        c.delete("all")
        w = max(580, c.winfo_width())
        h = max(310, c.winfo_height())
        f = getattr(self, "anim_frame", 0)
        cx, cy = w * 0.50, h * 0.53
        r_mesa = min(w, h) * 0.27
        ex_x = 1.25  # mesa ovalada (más ancha que alta)
        s = max(0.6, min(0.9, min(w, h) / 400))
        s_t = max(0.6, r_mesa / 105)

        def punto(a: float, k: float):
            return cx + k * r_mesa * ex_x * math.cos(a), cy + k * r_mesa * math.sin(a)

        ang_f = [math.radians(-90 + i * 72) for i in range(self.N)]
        ang_t = [math.radians(-90 + i * 72 - 36) for i in range(self.N)]

        # ── Mesa de madera con mantel ──
        c.create_oval(cx - r_mesa * ex_x + 5, cy - r_mesa + 9, cx + r_mesa * ex_x + 5, cy + r_mesa + 9,
                      fill="#E2E8F0", outline="")
        c.create_oval(cx - r_mesa * ex_x, cy - r_mesa, cx + r_mesa * ex_x, cy + r_mesa,
                      fill="#C08552", outline="#7C4A22", width=3)
        c.create_oval(cx - r_mesa * ex_x * 0.9, cy - r_mesa * 0.9, cx + r_mesa * ex_x * 0.9, cy + r_mesa * 0.9,
                      fill="#FDF6EC", outline="#D6B48C")
        gp.plato_espagueti(c, cx, cy, r_mesa * 0.32, True, f)

        # Platos individuales
        for i, a in enumerate(ang_f):
            px, py = punto(a, 0.64)
            gp.plato_espagueti(c, px, py, r_mesa * 0.17, self.estados[i] == "Comiendo", f)

        # Tenedores libres sobre la mesa (los ocupados se dibujan en las manos)
        pos_ten = []
        for i, a in enumerate(ang_t):
            tx, ty = punto(a, 0.64)
            pos_ten.append((tx, ty))
            if self.dueno_tenedor[i] is None:
                gp.tenedor(c, tx, ty, math.degrees(a), s_t)
            else:
                c.create_oval(tx - 9 * s_t, ty - 6 * s_t, tx + 9 * s_t, ty + 6 * s_t,
                              outline="#D6B48C", dash=(2, 2))
            c.create_text(tx + 12 * s_t * math.cos(a + 1.57), ty + 12 * s_t * math.sin(a + 1.57),
                          text=f"T{i}", font=("Consolas", 7, "bold"), fill="#92400E")

        # ── Filósofos ──
        pensamientos = ("¿Ser?", "∞", "Logos", "π", "Ética")
        for i, a in enumerate(ang_f):
            rr = 1.0 + 24 * s / r_mesa
            px, py = punto(a, rr)
            hy = py - 20 * s
            est = self.estados[i]
            piel = gp.PIELES[i % len(gp.PIELES)]
            ropa = ("#7C3AED", "#0E7490", "#B45309", "#BE123C", "#15803D")[i]
            pelo = ("#9CA3AF", "#E5E7EB", "#6B7280", "#D1D5DB", "#A8A29E")[i]
            izq, der = i, (i + 1) % self.N
            plato = punto(a, 0.64)
            kw = {}
            tenedores_mano = []  # (indice_tenedor, punto_mano)
            if est == "Comiendo":
                perp = (-math.sin(a), math.cos(a))
                m1 = (plato[0] + perp[0] * r_mesa * 0.2 - math.cos(a) * 4, plato[1] + perp[1] * r_mesa * 0.2 + 6 * s)
                m2 = (plato[0] - perp[0] * r_mesa * 0.2 - math.cos(a) * 4, plato[1] - perp[1] * r_mesa * 0.2 + 6 * s)
                kw = dict(manos=[m1, m2], ojos="felices", boca="abierta" if f % 2 else "sonrisa")
                tenedores_mano = [(izq, m1), (der, m2)]
                bg_l, fg_l = "#DCFCE7", "#15803D"
            elif est == "Hambriento":
                pecho = (px, py)
                m1 = (pecho[0] + (pos_ten[izq][0] - pecho[0]) * 0.72, pecho[1] + (pos_ten[izq][1] - pecho[1]) * 0.72)
                m2 = (pecho[0] + (pos_ten[der][0] - pecho[0]) * 0.72, pecho[1] + (pos_ten[der][1] - pecho[1]) * 0.72)
                kw = dict(manos=[m1, m2], ojos="sorpresa", boca="abierta")
                if self.dueno_tenedor[izq] == i:
                    tenedores_mano.append((izq, m1))
                if self.dueno_tenedor[der] == i:
                    tenedores_mano.append((der, m2))
                bg_l, fg_l = "#FEF9C3", "#A16207"
            else:
                kw = dict(pose="menton", ojos="abiertos", boca="neutral")
                bg_l, fg_l = "#F1F5F9", "#475569"

            geo = gp.dibujar_persona(c, px, hy, s, piel=piel, ropa=ropa, pelo=pelo, accesorio="barba",
                                     direccion=1 if math.cos(a) <= 0.05 else -1, piernas=None, **kw)

            for t_idx, m in tenedores_mano:
                ang_m = math.degrees(math.atan2(plato[1] - m[1], plato[0] - m[0])) if est == "Comiendo" \
                    else math.degrees(math.atan2(m[1] - py, m[0] - px))
                gp.tenedor(c, m[0] + 6 * s * math.cos(math.radians(ang_m)),
                           m[1] + 6 * s * math.sin(math.radians(ang_m)), ang_m, s_t * 0.9, resaltar="#15803D")
                gp.mano(c, m, s, piel)

            hx, hyc = geo["cabeza"]
            if est == "Comiendo":
                bx, by = geo["boca"]
                c.create_line(plato[0], plato[1], (plato[0] + bx) / 2 + math.sin(f) * 4, (plato[1] + by) / 2,
                              bx, by + 1, smooth=True, fill="#EAB308", width=2)
            elif est == "Hambriento":
                gp.globo_dialogo(c, hx + 20 * s, hyc - 24 * s, "¡Hambre!", color="#CA8A04", s=s)
            else:
                sg = 1 if math.cos(a) >= -0.05 else -1
                gp.burbuja_pensamiento(c, hx + sg * 36 * s, hyc - 22 * s, pensamientos[i], s * 0.85,
                                       origen=(hx + sg * 10 * s, hyc - 10 * s))

            texto = f"F{i} · {est} · comió {self.comidas[i]}"
            if math.sin(a) < -0.5:
                gp.etiqueta(c, px, hy - 13 * s - 22, texto, bg=bg_l, fg=fg_l, font=("Segoe UI", 7, "bold"))
            else:
                gp.etiqueta(c, px, geo["cadera"] + 10, texto, bg=bg_l, fg=fg_l, font=("Segoe UI", 7, "bold"))

        # ── Camarero (semáforo anti-deadlock) con su bandeja de permisos ──
        s_c = s * 0.8
        wx = max(46, w * 0.07)
        wy = h - 26 - 82 * s_c
        bandeja = (wx + 24 * s_c, wy + 26 * s_c)
        gp.dibujar_persona(c, wx, wy, s_c, piel="#E0AC69", ropa="#FFFFFF", pantalon="#111827", pelo="#111827",
                           ojos="abiertos", boca="sonrisa", manos=[(wx - 19 * s_c, wy + 44 * s_c), bandeja],
                           extra=("pajarita",))
        c.create_oval(bandeja[0] - 20 * s_c, bandeja[1] - 6 * s_c, bandeja[0] + 20 * s_c, bandeja[1] + 2 * s_c,
                      fill="#CBD5E1", outline="#64748B")
        for k in range(4):
            col = "#22C55E" if k < self.camarero_disp else "#E2E8F0"
            tx = bandeja[0] - 12 * s_c + k * 8 * s_c
            c.create_oval(tx - 3 * s_c, bandeja[1] - 10 * s_c, tx + 3 * s_c, bandeja[1] - 4 * s_c,
                          fill=col, outline="#475569")
        gp.etiqueta(c, wx + 14, h - 12, f"Camarero: {self.camarero_disp}/4 permisos", bg="#EFF6FF", fg="#1E40AF",
                    font=("Segoe UI", 7, "bold"))
