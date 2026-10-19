"""
============================================================================
 5. PROBLEMA DE LOS FUMADORES
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


class SimFumadores(BaseSimulacionFrame):
    INGREDIENTES = ("Tabaco", "Papel", "Fósforos")

    def __init__(self, master):
        super().__init__(master, "Fumadores")
        self.mesa_ingredientes: List[str] = []
        self.fumador_activo: str | None = None
        self.destinatario_actual: str | None = None
        self.conteo_fuma = {"Tabaco": 0, "Papel": 0, "Fósforos": 0}
        self._configurar_indicadores_semaforos([
            ("mesa", "Ingredientes en la Mesa", "Mesa vacía"),
            ("agente", "Semáforo del Agente", "Listo"),
            ("fum_activo", "Fumador en Sección Crítica", "Ninguno"),
            ("c_tabaco", "Fumador con Tabaco (∞)", "0 cigarrillos"),
            ("c_papel", "Fumador con Papel (∞)", "0 cigarrillos"),
            ("c_fosforos", "Fumador con Fósforos (∞)", "0 cigarrillos"),
        ])
        self._dibujar_escena()

    def _reset_estado_visual(self):
        self.mesa_ingredientes.clear()
        self.fumador_activo = None
        self.destinatario_actual = None
        for k in self.conteo_fuma:
            self.conteo_fuma[k] = 0
        self._actualizar_ui()
        self._dibujar_escena()

    def _iniciar_hilos(self, my_sim_id: int):
        self.sem_fumador = {ing: threading.Semaphore(0) for ing in self.INGREDIENTES}
        self.sem_agente = threading.Semaphore(0)
        self._agregar_log("Iniciando Agente y los 3 Fumadores (Tabaco, Papel, Fósforos).")
        for ing_propio in self.INGREDIENTES:
            threading.Thread(target=self._hilo_fumador, args=(ing_propio, my_sim_id), daemon=True).start()
        threading.Thread(target=self._hilo_agente, args=(my_sim_id,), daemon=True).start()

    def _desbloquear_semaforos(self):
        for s in getattr(self, "sem_fumador", {}).values():
            try:
                s.release()
            except Exception:
                pass
        ag = getattr(self, "sem_agente", None)
        if ag:
            try:
                ag.release()
            except Exception:
                pass

    def _hilo_agente(self, my_sim_id: int):
        while self._esperar_si_pausado(my_sim_id):
            faltante = random.choice(self.INGREDIENTES)
            par_mesa = [ing for ing in self.INGREDIENTES if ing != faltante]
            self._emitir(my_sim_id, "agente_coloca", (par_mesa, faltante))
            if not self._dormir_hilo(0.75, my_sim_id):
                break
            self.sem_fumador[faltante].release()
            self.sem_agente.acquire()
            if not self._esperar_si_pausado(my_sim_id):
                break
            if not self._dormir_hilo(0.45, my_sim_id):
                break

    def _hilo_fumador(self, ing_propio: str, my_sim_id: int):
        while self._esperar_si_pausado(my_sim_id):
            self.sem_fumador[ing_propio].acquire()
            if not self._esperar_si_pausado(my_sim_id):
                break
            self.conteo_fuma[ing_propio] += 1
            self._emitir(my_sim_id, "fumador_fuma", (ing_propio, self.conteo_fuma[ing_propio]))
            if not self._dormir_hilo(1.3, my_sim_id):
                break
            self._emitir(my_sim_id, "fumador_termina", ing_propio)
            self.sem_agente.release()

    def _actualizar_ui(self):
        mesa_txt = " + ".join(self.mesa_ingredientes) if self.mesa_ingredientes else "Vacía"
        self._actualizar_indicador("mesa", mesa_txt, "#B45309")
        self._actualizar_indicador(
            "agente",
            "0 (Esperando fumador)" if self.fumador_activo or self.mesa_ingredientes else "1 (Listo)",
            "#1E40AF",
        )
        self._actualizar_indicador(
            "fum_activo",
            f"Fumador ({self.fumador_activo})" if self.fumador_activo else "Ninguno",
            "#15803D" if self.fumador_activo else "#64748B",
        )
        self._actualizar_indicador("c_tabaco", f"{self.conteo_fuma['Tabaco']} cigarrillos", "#0F172A")
        self._actualizar_indicador("c_papel", f"{self.conteo_fuma['Papel']} cigarrillos", "#0F172A")
        self._actualizar_indicador("c_fosforos", f"{self.conteo_fuma['Fósforos']} cigarrillos", "#0F172A")

    def _procesar_evento(self, tipo: str, datos: Any):
        if tipo == "agente_coloca":
            par_mesa, faltante = datos
            self.mesa_ingredientes = par_mesa
            self.fumador_activo = None
            self.destinatario_actual = faltante
            self.lbl_status_banner.configure(
                text=f"Agente colocó [{par_mesa[0]} + {par_mesa[1]}] en la mesa → Despierta al Fumador con [{faltante}]",
                text_color="#B45309",
            )
            self._agregar_log(f"Agente colocó {par_mesa[0]} + {par_mesa[1]} → signal(sem_{faltante.lower()}).")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "fumador_fuma":
            ing_propio, total_c = datos
            par = list(self.mesa_ingredientes)
            self.mesa_ingredientes.clear()
            self.fumador_activo = ing_propio
            self.destinatario_actual = None
            self.lbl_status_banner.configure(
                text=f"Fumador con [{ing_propio}] recogió la mesa, armó su cigarrillo #{total_c} y está FUMANDO.",
                text_color="#15803D",
            )
            self._agregar_log(f"Fumador({ing_propio}) tomó {par} → armó y fuma cigarrillo #{total_c}.")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "fumador_termina":
            ing_propio = datos
            self.fumador_activo = None
            self.destinatario_actual = None
            self._agregar_log(f"Fumador({ing_propio}) terminó de fumar → ejecuta signal(agente).")
            self._actualizar_ui()
            self._dibujar_escena()

    def _dibujar_escena(self):
        c = self.canvas
        c.delete("all")
        w = max(580, c.winfo_width())
        h = max(300, c.winfo_height())
        f = getattr(self, "anim_frame", 0)
        cx = w * 0.50
        s = max(0.6, min(0.9, h / 390))
        y_t = h * 0.33
        mw = min(190, w * 0.28)
        y_piso = h - 40

        c.create_rectangle(0, y_piso, w, h, fill="#F1F5F9", outline="")
        c.create_line(0, y_piso, w, y_piso, fill="#CBD5E1", width=2)
        c.create_text(cx, 14, text="MESA DEL AGENTE", font=("Segoe UI", 11, "bold"), fill="#0F172A")

        # ── Agente (sombrero y traje) colocando 2 ingredientes ──
        tiene_ing = len(self.mesa_ingredientes) > 0
        pos_ing = [(cx - mw * 0.45, y_t - 10 * s), (cx + mw * 0.45, y_t - 10 * s)]
        manos_ag = [(pos_ing[0][0] + 16 * s, y_t - 3 * s), (pos_ing[1][0] - 16 * s, y_t - 3 * s)] if tiene_ing else None
        head_ag = y_t - 36 * s
        gp.dibujar_persona(c, cx, head_ag, s, piel="#FFDBAC", ropa="#1F2937", accesorio="sombrero",
                           ojos="abiertos", boca="sonrisa" if tiene_ing else "neutral",
                           pose="reposo", manos=manos_ag, piernas=None, extra=("corbata",))
        gp.etiqueta(c, cx + 52 * s, head_ag - 6 * s, "Agente", bg="#0F172A", fg="#FFFFFF", font=("Segoe UI", 8, "bold"))
        gp.mesa(c, cx - mw, y_t, cx + mw, s, alto_patas=50 * s,
                color="#D97706" if tiene_ing else "#B7794A")
        if tiene_ing:
            for (ix, iy), nombre in zip(pos_ing, self.mesa_ingredientes):
                gp.ingrediente(c, nombre, ix, iy, s * 1.1)
                gp.etiqueta(c, ix, y_t + 20 * s, nombre, bg="#FEF3C7", fg="#92400E", font=("Segoe UI", 8, "bold"))
        else:
            c.create_text(cx, y_t + 20 * s, text="Mesa vacía (fumador en turno o preparando ronda)",
                          font=("Segoe UI", 8), fill="#64748B")

        # ── Los 3 fumadores ──
        posiciones_x = [w * 0.17, w * 0.50, w * 0.83]
        dirs = [1, 1, -1]
        ropas = ["#16A34A", "#0891B2", "#9333EA"]
        s2 = max(0.55, min(0.95, (y_piso - (y_t + 50 * s) - 34) / 82))
        for idx, ing in enumerate(self.INGREDIENTES):
            fx = posiciones_x[idx]
            d = dirs[idx]
            fumando = self.fumador_activo == ing
            llamado = self.destinatario_actual == ing
            head = y_piso - 82 * s2
            piel = gp.PIELES[(idx + 1) % len(gp.PIELES)]

            # Mesita auxiliar con su ingrediente infinito
            stx = fx - d * 42 * s2
            gp.mesa(c, stx - 17 * s2, y_piso - 30 * s2, stx + 17 * s2, s2, alto_patas=30 * s2, color="#A16207")
            gp.ingrediente(c, ing, stx, y_piso - 41 * s2, s2 * 0.85)
            c.create_text(stx + 16 * s2, y_piso - 52 * s2, text="∞", font=("Segoe UI", 11, "bold"), fill="#B45309")

            if fumando:
                kw = dict(pose="fumar", ojos="felices", boca="sonrisa")
                est_txt, col = "ARMANDO Y FUMANDO", "#15803D"
            elif llamado:
                kw = dict(pose="arriba", ojos="sorpresa", boca="abierta")
                est_txt, col = "¡DESPERTADO POR AGENTE!", "#CA8A04"
            else:
                kw = dict(pose="cruzados", ojos="abiertos", boca="neutral")
                est_txt, col = "Esperando ingredientes...", "#64748B"

            gp.dibujar_persona(c, fx, head, s2, piel=piel, ropa=ropas[idx], pelo=gp.PELOS[idx], direccion=d, **kw)
            if fumando:
                mano_f = (fx + d * 7 * s2, head + 7 * s2)
                gp.cigarrillo(c, mano_f[0] + d * 2 * s2, mano_f[1] - 1 * s2, s2, d, f)
                gp.mano(c, mano_f, s2, piel)

            y_est = head - 13 * s2 - 14
            gp.etiqueta(c, fx, y_est, est_txt, bg=gp.aclarar(col, 0.85), fg=col, font=("Segoe UI", 7, "bold"))
            if fumando or llamado:
                origen = (cx + (idx - 1) * mw * 0.55, y_t + 10 * s)
                gp.flecha_animada(c, origen, (fx, y_est - 10), col, f, curva=0.08)

            gp.etiqueta(c, max(90, min(w - 90, fx)), y_piso + 16,
                        f"Fumador {idx + 1} · {ing} (∞) · {self.conteo_fuma[ing]} cigarrillos",
                        bg="#FFFFFF", fg="#1E293B", borde="#CBD5E1", font=("Segoe UI", 7, "bold"))
