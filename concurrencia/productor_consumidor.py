"""
============================================================================
 1. PROBLEMA PRODUCTOR - CONSUMIDOR (Búfer Acotado Circular)
 Autor : Jordan Oliber Soncco Machaca — UNA Puno
============================================================================
"""

from __future__ import annotations
import re
import math
import random
import threading
from typing import Any, List, Tuple
from .base_simulacion import BaseSimulacionFrame
from . import graficos_personajes as gp


class SimProductorConsumidor(BaseSimulacionFrame):
    CAPACIDAD = 8

    def __init__(self, master):
        super().__init__(master, "Productor - Consumidor")
        self.buffer: List[Tuple[int, str] | None] = [None] * self.CAPACIDAD
        self.idx_in = 0
        self.idx_out = 0
        self.total_prod = 0
        self.total_cons = 0
        self.celda_activa: int | None = None
        self.tipo_activo = ""
        self.estado_actores = {
            "P1": "Listo",
            "P2": "Listo",
            "C1": "Listo",
            "C2": "Listo",
        }
        self._configurar_indicadores_semaforos([
            ("mutex", "Semáforo mutex (Exclusión)", "1 (Libre)"),
            ("empty", "Semáforo empty (Vacíos)", f"{self.CAPACIDAD} / {self.CAPACIDAD}"),
            ("full", "Semáforo full (Llenos)", f"0 / {self.CAPACIDAD}"),
            ("punteros", "Punteros Circular (IN / OUT)", "IN=0 | OUT=0"),
            ("producidos", "Total Ítems Producidos", "0"),
            ("consumidos", "Total Ítems Consumidos", "0"),
        ])
        self._dibujar_escena()

    def _reset_estado_visual(self):
        self.buffer = [None] * self.CAPACIDAD
        self.idx_in = 0
        self.idx_out = 0
        self.total_prod = 0
        self.total_cons = 0
        self.celda_activa = None
        self.tipo_activo = ""
        for k in self.estado_actores:
            self.estado_actores[k] = "Listo"
        self._actualizar_semaforos_ui("Libre")
        self._dibujar_escena()

    def _iniciar_hilos(self, my_sim_id: int):
        self.empty = threading.Semaphore(self.CAPACIDAD)
        self.full = threading.Semaphore(0)
        self.mutex = threading.Lock()
        self._agregar_log(f"Iniciando con búfer circular N={self.CAPACIDAD} (empty=8, full=0, mutex=1).")
        for p_name in ("P1", "P2"):
            threading.Thread(target=self._hilo_productor, args=(p_name, my_sim_id), daemon=True).start()
        for c_name in ("C1", "C2"):
            threading.Thread(target=self._hilo_consumidor, args=(c_name, my_sim_id), daemon=True).start()

    def _desbloquear_semaforos(self):
        for sem in (getattr(self, "empty", None), getattr(self, "full", None)):
            if sem:
                for _ in range(4):
                    try:
                        sem.release()
                    except Exception:
                        pass

    def _hilo_productor(self, nombre: str, my_sim_id: int):
        while self._esperar_si_pausado(my_sim_id):
            self._emitir(my_sim_id, "actor", (nombre, "Esperando empty..."))
            self.empty.acquire()
            if not self._esperar_si_pausado(my_sim_id):
                self.empty.release()
                break
            valor = random.randint(10, 99)
            self._emitir(my_sim_id, "actor", (nombre, f"En sección crítica ({valor})"))
            with self.mutex:
                if not self._activo(my_sim_id):
                    break
                pos = self.idx_in
                self.idx_in = (self.idx_in + 1) % self.CAPACIDAD
                self.buffer[pos] = (valor, nombre)
                self.total_prod += 1
                self._emitir(my_sim_id, "producir", (nombre, pos, valor, self.idx_in, self.idx_out, self.total_prod))
                if not self._dormir_hilo(0.35, my_sim_id):
                    break
            self.full.release()
            self._emitir(my_sim_id, "actor", (nombre, "En reposo"))
            if not self._dormir_hilo(random.uniform(0.9, 1.6), my_sim_id):
                break

    def _hilo_consumidor(self, nombre: str, my_sim_id: int):
        while self._esperar_si_pausado(my_sim_id):
            self._emitir(my_sim_id, "actor", (nombre, "Esperando full..."))
            self.full.acquire()
            if not self._esperar_si_pausado(my_sim_id):
                self.full.release()
                break
            self._emitir(my_sim_id, "actor", (nombre, "En sección crítica..."))
            with self.mutex:
                if not self._activo(my_sim_id):
                    break
                pos = self.idx_out
                item = self.buffer[pos]
                self.buffer[pos] = None
                self.idx_out = (self.idx_out + 1) % self.CAPACIDAD
                self.total_cons += 1
                valor = item[0] if item else 0
                self._emitir(my_sim_id, "consumir", (nombre, pos, valor, self.idx_in, self.idx_out, self.total_cons))
                if not self._dormir_hilo(0.35, my_sim_id):
                    break
            self.empty.release()
            self._emitir(my_sim_id, "actor", (nombre, f"Procesó dato {valor}"))
            if not self._dormir_hilo(random.uniform(1.1, 1.8), my_sim_id):
                break

    def _actualizar_semaforos_ui(self, estado_mutex: str):
        ocupados = sum(1 for x in self.buffer if x is not None)
        libres = self.CAPACIDAD - ocupados
        self._actualizar_indicador(
            "mutex",
            "0 (Ocupado)" if estado_mutex != "Libre" else "1 (Libre)",
            "#B91C1C" if estado_mutex != "Libre" else "#15803D",
        )
        self._actualizar_indicador("empty", f"{libres} / {self.CAPACIDAD}", "#1E40AF")
        self._actualizar_indicador("full", f"{ocupados} / {self.CAPACIDAD}", "#B45309")
        self._actualizar_indicador("punteros", f"IN={self.idx_in} | OUT={self.idx_out}", "#0F172A")
        self._actualizar_indicador("producidos", str(self.total_prod), "#15803D")
        self._actualizar_indicador("consumidos", str(self.total_cons), "#1E40AF")

    def _procesar_evento(self, tipo: str, datos: Any):
        if tipo == "actor":
            actor, est = datos
            self.estado_actores[actor] = est
            self.celda_activa = None
            self._actualizar_semaforos_ui("Libre")
            self._dibujar_escena()
        elif tipo == "producir":
            nombre, pos, valor, _in, _out, _tot = datos
            self.estado_actores[nombre] = f"Insertó [{valor}] en #{pos}"
            self.celda_activa = pos
            self.tipo_activo = "prod"
            self.lbl_status_banner.configure(
                text=f"{nombre} ejecutó wait(empty) y wait(mutex) → Insertó [{valor}] en celda [{pos}] → signal(full)",
                text_color="#15803D",
            )
            self._agregar_log(f"{nombre}: wait(empty) → wait(mutex) → buffer[{pos}]={valor} → signal(mutex) → signal(full)")
            self._actualizar_semaforos_ui(nombre)
            self._dibujar_escena()
        elif tipo == "consumir":
            nombre, pos, valor, _in, _out, _tot = datos
            self.estado_actores[nombre] = f"Retiró [{valor}] de #{pos}"
            self.celda_activa = pos
            self.tipo_activo = "cons"
            self.lbl_status_banner.configure(
                text=f"{nombre} ejecutó wait(full) y wait(mutex) → Retiró [{valor}] de celda [{pos}] → signal(empty)",
                text_color="#1E40AF",
            )
            self._agregar_log(f"{nombre}: wait(full) → wait(mutex) → leyó buffer[{pos}]={valor} → signal(mutex) → signal(empty)")
            self._actualizar_semaforos_ui(nombre)
            self._dibujar_escena()

    def _dibujar_escena(self):
        c = self.canvas
        c.delete("all")
        w = max(580, c.winfo_width())
        h = max(300, c.winfo_height())
        f = getattr(self, "anim_frame", 0)

        # ── Fondo de fábrica (piso) y título ──
        y_piso = h - 44
        c.create_rectangle(0, y_piso, w, h, fill="#F1F5F9", outline="")
        c.create_line(0, y_piso, w, y_piso, fill="#CBD5E1", width=2)
        c.create_text(
            w / 2, 16, text="FÁBRICA · BÚFER ACOTADO CIRCULAR (N = 8)",
            font=("Segoe UI", 11, "bold"), fill="#1E293B",
        )
        ocupados = sum(1 for x in self.buffer if x is not None)

        # ── Geometría de la cinta transportadora ──
        espacio = 8
        ancho_celda = min(74, (w - 70 - (self.CAPACIDAD - 1) * espacio) / self.CAPACIDAD)
        total_w = self.CAPACIDAD * ancho_celda + (self.CAPACIDAD - 1) * espacio
        x_ini = (w - total_w) / 2
        y_buf = h * 0.57
        alto = min(56, h * 0.17)
        y1, y2 = y_buf - alto / 2, y_buf + alto / 2

        def centro_celda(i: int) -> float:
            return x_ini + i * (ancho_celda + espacio) + ancho_celda / 2

        # Patas, banda y rodillos animados
        for lx in (x_ini + 10, x_ini + total_w / 2, x_ini + total_w - 10):
            c.create_rectangle(lx - 4, y2 + 8, lx + 4, y_piso, fill="#94A3B8", outline="#64748B")
        gp.rect_redondeado(c, x_ini - 14, y1 - 8, x_ini + total_w + 14, y2 + 8, 10,
                           fill="#475569", outline="#334155", width=2)
        n_rod = self.CAPACIDAD + 1
        for k in range(n_rod):
            rx = x_ini - 6 + k * (total_w + 12) / (n_rod - 1)
            ry = y2 + 15
            c.create_oval(rx - 6, ry - 6, rx + 6, ry + 6, fill="#CBD5E1", outline="#475569", width=1.5)
            a = math.radians(f * 25 + k * 40)
            c.create_line(rx - 5 * math.cos(a), ry - 5 * math.sin(a), rx + 5 * math.cos(a),
                          ry + 5 * math.sin(a), fill="#475569", width=1.5)

        # Celdas con cajas 3D
        col_act = "#16A34A" if self.tipo_activo == "prod" else "#2563EB"
        for i in range(self.CAPACIDAD):
            x1 = x_ini + i * (ancho_celda + espacio)
            x2 = x1 + ancho_celda
            cxs = (x1 + x2) / 2
            item = self.buffer[i]
            activo = i == self.celda_activa
            gp.rect_redondeado(
                c, x1, y1, x2, y2, 6, fill="#F8FAFC" if item is None else "#E2E8F0",
                outline=col_act if activo else "#94A3B8", width=3 if activo else 1.2,
            )
            c.create_text(x1 + 5, y1 + 3, anchor="nw", text=f"[{i}]",
                          font=("Consolas", 7, "bold"), fill="#64748B")
            if item is not None:
                val, autor = item
                t = min(17, ancho_celda * 0.27, alto * 0.3)
                gp.caja_3d(
                    c, cxs - t * 0.2, y_buf + t * 0.25 + 2, t, texto=str(val), subtexto=autor,
                    color="#D9A066" if autor == "P1" else "#C9874E",
                    resaltar=col_act if activo else None,
                )
            else:
                c.create_text(cxs, y_buf + 4, text="vacía", font=("Segoe UI", 8), fill="#94A3B8")

            if i == self.idx_in or i == self.idx_out:
                if i == self.idx_in and i == self.idx_out:
                    txt, col = "IN / OUT", "#334155"
                elif i == self.idx_in:
                    txt, col = "IN (Prod)", "#15803D"
                else:
                    txt, col = "OUT (Cons)", "#1D4ED8"
                c.create_polygon(cxs, y2 + 24, cxs - 6, y2 + 33, cxs + 6, y2 + 33, fill=col, outline="")
                gp.etiqueta(c, cxs, y2 + 43, txt, bg=gp.aclarar(col, 0.85), fg=col, font=("Segoe UI", 7, "bold"))

        # ── Candado del mutex (centro superior) ──
        en_seccion = any("sección" in e for e in self.estado_actores.values()) or self.celda_activa is not None
        gp.candado(c, w / 2, 44, 1.2, cerrado=en_seccion, color="#DC2626" if en_seccion else "#16A34A")
        gp.etiqueta(c, w / 2, 70, "mutex = 0 (ocupado)" if en_seccion else "mutex = 1 (libre)",
                    bg="#FEE2E2" if en_seccion else "#DCFCE7",
                    fg="#B91C1C" if en_seccion else "#15803D", font=("Segoe UI", 7, "bold"))

        # ── Personajes: Productores (casco) y Consumidores (gorra) ──
        y_pies = y1 - 34
        s = max(0.55, min(1.0, (y_pies - 28) / 82))
        y_cab = y_pies - 82 * s
        actores = [("P1", w * 0.09, "prod"), ("P2", w * 0.25, "prod"),
                   ("C1", w * 0.75, "cons"), ("C2", w * 0.91, "cons")]
        for clave, x, rol in actores:
            est = self.estado_actores[clave]
            m = re.search(r"[\[\(](\d+)[\]\)]", est)
            valor = m.group(1) if m else ""
            d = 1 if rol == "prod" else -1
            ropa = "#EA580C" if rol == "prod" else "#2563EB"
            acc = "casco" if rol == "prod" else "gorra"
            col_rol = "#16A34A" if rol == "prod" else "#2563EB"
            piel = "#F1C27D" if clave.endswith("1") else "#E0AC69"
            pose, ojos, boca = "reposo", "abiertos", "neutral"
            caja, globo, flecha = None, None, None
            bg_lbl, fg_lbl = "#F1F5F9", "#475569"

            if "sección" in est:
                bg_lbl, fg_lbl = gp.aclarar(col_rol, 0.85), col_rol
                if rol == "prod":
                    pose, boca, caja = "cargar", "sonrisa", valor or "?"
                else:
                    pose, boca = "extender", "sonrisa"
            elif "Insertó" in est:
                pose, boca, flecha = "extender", "sonrisa", "a_celda"
                bg_lbl, fg_lbl = "#DCFCE7", "#15803D"
            elif "Retiró" in est:
                pose, boca, caja, flecha = "cargar", "sonrisa", valor, "desde_celda"
                bg_lbl, fg_lbl = "#DBEAFE", "#1D4ED8"
            elif "Esperando" in est:
                pose = "cruzados"
                bg_lbl, fg_lbl = "#FEF3C7", "#B45309"
                if rol == "prod" and ocupados >= self.CAPACIDAD:
                    boca, globo = "triste", "¡Búfer lleno!"
                elif rol == "cons" and ocupados == 0:
                    boca, globo = "triste", "¡Búfer vacío!"
            elif "reposo" in est or "Procesó" in est:
                ojos, boca = "felices", "sonrisa"

            geo = gp.dibujar_persona(
                c, x, y_cab, s, piel=piel, ropa=ropa,
                pantalon="#1E3A8A" if rol == "prod" else "#334155",
                accesorio=acc, ojos=ojos, boca=boca, pose=pose, direccion=d,
            )
            mi, md = geo["manos"]
            if caja:
                bx, by = (mi[0] + md[0]) / 2, (mi[1] + md[1]) / 2 - 2 * s
                gp.caja_3d(c, bx, by, 10 * s, texto=str(caja), color="#D9A066")
                gp.mano(c, mi, s, piel)
                gp.mano(c, md, s, piel)
            if "Procesó" in est:
                gp.caja_3d(c, x + d * 26 * s, y_pies - 8 * s, 7 * s, texto="✓", color="#BBF7D0")
            if globo:
                gp.globo_dialogo(c, x, y_cab - 13 * s - 14, globo, color="#DC2626", s=s)

            if flecha and self.celda_activa is not None and self.tipo_activo == rol:
                cel = (centro_celda(self.celda_activa), y1 - 4)
                frente = md if d > 0 else mi
                if flecha == "a_celda":
                    gp.flecha_animada(c, frente, cel, col_rol, f)
                else:
                    gp.flecha_animada(c, cel, (frente[0], frente[1] - 6 * s), col_rol, f)

            corto = est if len(est) <= 22 else est[:21] + "…"
            x_lbl = max(62, min(w - 62, x))
            gp.etiqueta(c, x_lbl, y_pies + 9, f"{clave} · {corto}", bg=bg_lbl, fg=fg_lbl,
                        font=("Segoe UI", 7, "bold"))

        # ── Barra de ocupación inferior ──
        by1 = h - 32
        c.create_rectangle(x_ini, by1, x_ini + total_w, by1 + 20, fill="#FFFFFF", outline="#CBD5E1")
        if ocupados > 0:
            fill_w = (ocupados / self.CAPACIDAD) * total_w
            c.create_rectangle(x_ini, by1, x_ini + fill_w, by1 + 20, fill="#93C5FD", outline="")
        c.create_text(
            w / 2, by1 + 10,
            text=f"Ocupación del Búfer: {ocupados} / {self.CAPACIDAD}   |   Vacíos (empty) = {self.CAPACIDAD - ocupados}   |   Llenos (full) = {ocupados}",
            font=("Segoe UI", 9, "bold"), fill="#0F172A",
        )
