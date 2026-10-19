"""
============================================================================
 2. PROBLEMA DE LECTORES - ESCRITORES
 Autor : Jordan Oliber Soncco Machaca — UNA Puno
============================================================================
"""

from __future__ import annotations
import re
import math
import random
import threading
import tkinter as tk
from typing import Any, List
from .base_simulacion import BaseSimulacionFrame
from . import graficos_personajes as gp


class SimLectoresEscritores(BaseSimulacionFrame):
    def __init__(self, master):
        super().__init__(master, "Lectores - Escritores")
        self.version_bd = 0
        self.lectores_activos: List[str] = []
        self.escritor_activo: str | None = None
        self.total_lecturas = 0
        self.total_escrituras = 0
        self.estados = {
            "L1": "Inactivo", "L2": "Inactivo", "L3": "Inactivo",
            "E1": "Inactivo", "E2": "Inactivo",
        }
        self._configurar_indicadores_semaforos([
            ("wrt", "Semáforo wrt (Recurso BD)", "1 (Disponible)"),
            ("mutex_l", "Semáforo mutex_lectores", "1 (Libre)"),
            ("num_l", "Contador num_lectores", "0 activos"),
            ("version", "Versión Actual de BD", "v0"),
            ("tot_lec", "Total Operaciones Lectura", "0"),
            ("tot_esc", "Total Operaciones Escritura", "0"),
        ])
        self._dibujar_escena()

    def _reset_estado_visual(self):
        self.version_bd = 0
        self.lectores_activos.clear()
        self.escritor_activo = None
        self.total_lecturas = 0
        self.total_escrituras = 0
        for k in self.estados:
            self.estados[k] = "Inactivo"
        self._actualizar_ui()
        self._dibujar_escena()

    def _iniciar_hilos(self, my_sim_id: int):
        self.num_lectores = 0
        self.mutex_lectores = threading.Lock()
        self.wrt = threading.Lock()
        self._agregar_log("Iniciando Base de Datos compartida (wrt=1, mutex_lectores=1, num_lectores=0).")
        for l_name in ("L1", "L2", "L3"):
            threading.Thread(target=self._hilo_lector, args=(l_name, my_sim_id), daemon=True).start()
        for e_name in ("E1", "E2"):
            threading.Thread(target=self._hilo_escritor, args=(e_name, my_sim_id), daemon=True).start()

    def _desbloquear_semaforos(self):
        for lk in (getattr(self, "wrt", None), getattr(self, "mutex_lectores", None)):
            if lk and lk.locked():
                try:
                    lk.release()
                except Exception:
                    pass

    def _hilo_lector(self, nombre: str, my_sim_id: int):
        while self._esperar_si_pausado(my_sim_id):
            if not self._dormir_hilo(random.uniform(0.6, 1.5), my_sim_id):
                break
            self._emitir(my_sim_id, "estado", (nombre, "Esperando acceso..."))
            with self.mutex_lectores:
                if not self._activo(my_sim_id):
                    break
                self.num_lectores += 1
                primero = self.num_lectores == 1
                if primero:
                    self.wrt.acquire()
                self._emitir(my_sim_id, "lector_entra", (nombre, primero, self.num_lectores))

            if not self._dormir_hilo(random.uniform(1.1, 1.9), my_sim_id):
                break

            with self.mutex_lectores:
                if not self._activo(my_sim_id):
                    break
                self.num_lectores = max(0, self.num_lectores - 1)
                ultimo = self.num_lectores == 0
                if ultimo:
                    try:
                        self.wrt.release()
                    except RuntimeError:
                        pass
                self.total_lecturas += 1
                self._emitir(my_sim_id, "lector_sale", (nombre, ultimo, self.num_lectores, self.total_lecturas))

    def _hilo_escritor(self, nombre: str, my_sim_id: int):
        while self._esperar_si_pausado(my_sim_id):
            if not self._dormir_hilo(random.uniform(1.4, 2.4), my_sim_id):
                break
            self._emitir(my_sim_id, "estado", (nombre, "Esperando wrt exclusivo..."))
            self.wrt.acquire()
            if not self._esperar_si_pausado(my_sim_id):
                try:
                    self.wrt.release()
                except RuntimeError:
                    pass
                break
            self.version_bd += 1
            self._emitir(my_sim_id, "escritor_entra", (nombre, self.version_bd))
            if not self._dormir_hilo(1.2, my_sim_id):
                try:
                    self.wrt.release()
                except RuntimeError:
                    pass
                break
            self.total_escrituras += 1
            self._emitir(my_sim_id, "escritor_sale", (nombre, self.version_bd, self.total_escrituras))
            try:
                self.wrt.release()
            except RuntimeError:
                pass

    def _actualizar_ui(self):
        if self.escritor_activo:
            self._actualizar_indicador("wrt", f"0 (Exclusivo: {self.escritor_activo})", "#B91C1C")
        elif self.lectores_activos:
            self._actualizar_indicador("wrt", "0 (Retenido por Lectores)", "#15803D")
        else:
            self._actualizar_indicador("wrt", "1 (Disponible)", "#1E40AF")

        self._actualizar_indicador("mutex_l", "1 (Libre)", "#15803D")
        self._actualizar_indicador("num_l", f"{len(self.lectores_activos)} activos", "#15803D")
        self._actualizar_indicador("version", f"v{self.version_bd}", "#0F172A")
        self._actualizar_indicador("tot_lec", str(self.total_lecturas), "#1E40AF")
        self._actualizar_indicador("tot_esc", str(self.total_escrituras), "#B91C1C")

    def _procesar_evento(self, tipo: str, datos: Any):
        if tipo == "estado":
            actor, est = datos
            self.estados[actor] = est
            self._dibujar_escena()
        elif tipo == "lector_entra":
            nombre, primero, n_lec = datos
            if nombre not in self.lectores_activos:
                self.lectores_activos.append(nombre)
            self.estados[nombre] = "LEYENDO BD"
            msg_extra = " (1er lector → bloqueó wrt)" if primero else " (lectura simultánea)"
            self.lbl_status_banner.configure(
                text=f"{nombre} leyendo simultáneamente (Lectores activos: {len(self.lectores_activos)}){msg_extra}",
                text_color="#15803D",
            )
            self._agregar_log(f"{nombre} entra a leer (num_lectores={n_lec}){msg_extra}.")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "lector_sale":
            nombre, ultimo, n_lec, _tot_l = datos
            if nombre in self.lectores_activos:
                self.lectores_activos.remove(nombre)
            self.estados[nombre] = "Inactivo"
            msg_extra = " (Último lector → liberó signal(wrt))" if ultimo else ""
            self._agregar_log(f"{nombre} sale de leer (num_lectores={n_lec}){msg_extra}.")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "escritor_entra":
            nombre, ver = datos
            self.escritor_activo = nombre
            self.estados[nombre] = f"ESCRIBIENDO v{ver}"
            self.lbl_status_banner.configure(
                text=f"{nombre} adquirió wait(wrt) en EXCLUSIÓN MUTUA → Escribiendo versión v{ver}",
                text_color="#B91C1C",
            )
            self._agregar_log(f"{nombre} adquiere wait(wrt) exclusivo → Escribiendo v{ver}.")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "escritor_sale":
            nombre, ver, _tot_e = datos
            self.escritor_activo = None
            self.estados[nombre] = "Inactivo"
            self.lbl_status_banner.configure(
                text=f"{nombre} finalizó escritura v{ver} y liberó signal(wrt).",
                text_color="#1E40AF",
            )
            self._agregar_log(f"{nombre} libera signal(wrt) tras guardar v{ver}.")
            self._actualizar_ui()
            self._dibujar_escena()

    def _dibujar_escena(self):
        c = self.canvas
        c.delete("all")
        w = max(580, c.winfo_width())
        h = max(300, c.winfo_height())
        f = getattr(self, "anim_frame", 0)

        cx, cy = w * 0.50, h * 0.50
        bd_w, bd_h = min(110, w * 0.16), min(160, h * 0.48)

        if self.escritor_activo:
            led, col_modo = "#EF4444", "#DC2626"
            modo_txt = f"ESCRITURA EXCLUSIVA ({self.escritor_activo})"
        elif self.lectores_activos:
            led, col_modo = "#22C55E", "#16A34A"
            modo_txt = f"LECTURA COMPARTIDA ({', '.join(self.lectores_activos)})"
        else:
            led, col_modo = "#3B82F6", "#475569"
            modo_txt = "RECURSO LIBRE (wrt = 1)"

        # ── Servidor central de Base de Datos ──
        c.create_oval(cx - bd_w * 0.95, cy - bd_h * 0.62, cx + bd_w * 0.95, cy + bd_h * 0.62,
                      fill=gp.aclarar(col_modo, 0.9), outline="")
        c.create_text(cx, cy - bd_h / 2 - 30, text="BASE DE DATOS COMPARTIDA",
                      font=("Segoe UI", 11, "bold"), fill="#0F172A")
        gp.servidor_bd(c, cx, cy, bd_w, bd_h, led, f)
        bloqueada = bool(self.escritor_activo or self.lectores_activos)
        gp.candado(c, cx + bd_w / 2 + 18, cy - bd_h / 2 + 6, 1.1, cerrado=bloqueada,
                   color="#DC2626" if self.escritor_activo else ("#16A34A" if self.lectores_activos else "#94A3B8"))
        gp.etiqueta(c, cx, cy + bd_h / 2 + 18, f"Versión v{self.version_bd}", bg="#0F172A", fg="#FFFFFF",
                    font=("Segoe UI", 10, "bold"))
        c.create_text(cx, cy + bd_h / 2 + 40, text=modo_txt, font=("Segoe UI", 9, "bold"), fill=col_modo)

        s = max(0.6, min(0.85, h / 400))
        colores_libro = {"L1": "#2563EB", "L2": "#9333EA", "L3": "#0891B2"}

        # ── Lectores (con gafas y libro) a la izquierda ──
        lx = w * 0.13
        for idx, l_name in enumerate(("L1", "L2", "L3")):
            ly = h * (0.13 + idx * 0.32)
            est = self.estados[l_name]
            leyendo = l_name in self.lectores_activos
            esperando = "Esperando" in est
            piel, ropa, pelo = gp.paleta_por_nombre(l_name + "lector")
            if leyendo:
                pose, ojos, boca = "leer", "abiertos", "sonrisa"
                bg_l, fg_l = "#DCFCE7", "#15803D"
            elif esperando:
                pose, ojos, boca = "cruzados", "abiertos", "triste"
                bg_l, fg_l = "#FEF3C7", "#B45309"
            else:
                pose, ojos, boca = "reposo", "abiertos", "neutral"
                bg_l, fg_l = "#F1F5F9", "#475569"
            geo = gp.dibujar_persona(c, lx, ly, s, piel=piel, ropa=ropa, pelo=pelo, accesorio="gafas",
                                     ojos=ojos, boca=boca, pose=pose, direccion=1, piernas=None)
            mi, md = geo["manos"]
            if leyendo:
                bx, by = (mi[0] + md[0]) / 2, (mi[1] + md[1]) / 2 - 4 * s
                gp.libro(c, bx, by, s, colores_libro[l_name], abierto=True)
                gp.mano(c, mi, s, piel)
                gp.mano(c, md, s, piel)
                origen = (cx - bd_w / 2, cy)
                destino = (bx + 16 * s, by)
                c.create_line(origen[0], origen[1], destino[0], destino[1], fill="#86EFAC", width=2, dash=(4, 3))
                gp.paquetes_en_linea(c, origen, destino, "#22C55E", f)
            elif esperando:
                if self.escritor_activo:
                    gp.globo_dialogo(c, lx + 52 * s, ly - 16 * s, "⏳ BD bloqueada", color="#B45309", s=s)
            else:
                gp.libro(c, md[0], md[1] - 7 * s, s * 0.7, colores_libro[l_name], abierto=False)
            gp.etiqueta(c, lx, geo["cadera"] + 10, f"Lector {l_name} · {est}", bg=bg_l, fg=fg_l,
                        font=("Segoe UI", 7, "bold"))

        # ── Escritores (auriculares y laptop) a la derecha ──
        ex = w * 0.87
        for idx, e_name in enumerate(("E1", "E2")):
            ey = h * (0.20 + idx * 0.42)
            est = self.estados[e_name]
            escribiendo = self.escritor_activo == e_name
            esperando = "Esperando" in est
            piel, ropa, pelo = gp.paleta_por_nombre(e_name + "escritor")
            manos_tec = [(ex - 10 * s, ey + 47 * s), (ex + 10 * s, ey + 47 * s)]
            if escribiendo:
                kw = dict(manos=manos_tec, ojos="abiertos", boca="sonrisa")
                bg_l, fg_l = "#FEE2E2", "#B91C1C"
            elif esperando:
                kw = dict(pose="cruzados", ojos="abiertos", boca="triste")
                bg_l, fg_l = "#FEF3C7", "#B45309"
            else:
                kw = dict(pose="reposo", ojos="abiertos", boca="neutral")
                bg_l, fg_l = "#F1F5F9", "#475569"
            geo = gp.dibujar_persona(c, ex, ey, s, piel=piel, ropa=ropa, pelo=pelo, accesorio="auriculares",
                                     direccion=-1, piernas=None, **kw)
            # Escritorio + laptop delante del personaje
            c.create_rectangle(ex - 34 * s, ey + 50 * s, ex + 34 * s, ey + 55 * s, fill="#A16207", outline="#713F12")
            gp.laptop(c, ex, ey + 44 * s, s * 0.9, activo=escribiendo, frame=f)
            if escribiendo:
                for p in manos_tec:
                    gp.mano(c, p, s, piel)
                origen = (ex - 22 * s, ey + 30 * s)
                destino = (cx + bd_w / 2, cy)
                c.create_line(origen[0], origen[1], destino[0], destino[1], fill="#FCA5A5", width=2.5)
                gp.paquetes_en_linea(c, origen, destino, "#EF4444", f)
            elif esperando:
                gp.globo_dialogo(c, ex - 46 * s, ey - 18 * s, "Esperando wrt", color="#B45309", s=s)
            gp.etiqueta(c, max(70, min(w - 70, ex)), ey + 66 * s, f"Escritor {e_name} · {est}",
                        bg=bg_l, fg=fg_l, font=("Segoe UI", 7, "bold"))
