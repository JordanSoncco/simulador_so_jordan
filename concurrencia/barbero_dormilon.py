"""
============================================================================
 4. PROBLEMA DEL BARBERO DORMILÓN
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


class SimBarberoDormilon(BaseSimulacionFrame):
    NUM_SILLAS = 5

    def __init__(self, master):
        super().__init__(master, "Barbero dormilón")
        self.cola_espera: List[str] = []
        self.cliente_en_silla: str | None = None
        self.estado_barbero = "DURMIENDO"
        self.atendidos = 0
        self.retirados = 0
        self.ultimo_evento_puerta = "Sin llegadas aún"
        self._configurar_indicadores_semaforos([
            ("barbero", "Estado del Barbero", "DURMIENDO"),
            ("clientes_sem", "Semáforo clientes (En espera)", "0 esperando"),
            ("sillas_lib", "Sillas de Espera Libres", f"{self.NUM_SILLAS} / {self.NUM_SILLAS}"),
            ("mutex", "Semáforo mutex (Sala)", "1 (Libre)"),
            ("atendidos", "Clientes Atendidos", "0"),
            ("retirados", "Clientes Retirados (Sala llena)", "0"),
        ])
        self._dibujar_escena()

    def _reset_estado_visual(self):
        self.cola_espera.clear()
        self.cliente_en_silla = None
        self.estado_barbero = "DURMIENDO"
        self.atendidos = 0
        self.retirados = 0
        self.ultimo_evento_puerta = "Sin llegadas aún"
        self._actualizar_ui()
        self._dibujar_escena()

    def _iniciar_hilos(self, my_sim_id: int):
        self.sem_clientes = threading.Semaphore(0)
        self.mutex_sala = threading.Lock()
        self.cola_interna: List[str] = []
        self._agregar_log(f"Abriendo barbería con {self.NUM_SILLAS} sillas de espera (clientes=0, mutex=1).")
        threading.Thread(target=self._hilo_barbero, args=(my_sim_id,), daemon=True).start()
        threading.Thread(target=self._hilo_llegada_clientes, args=(my_sim_id,), daemon=True).start()

    def _desbloquear_semaforos(self):
        sem = getattr(self, "sem_clientes", None)
        if sem:
            try:
                sem.release()
            except Exception:
                pass

    def _hilo_llegada_clientes(self, my_sim_id: int):
        contador = 0
        while self._esperar_si_pausado(my_sim_id):
            if not self._dormir_hilo(random.uniform(0.75, 1.5), my_sim_id):
                break
            contador += 1
            c_nom = f"C{contador}"
            with self.mutex_sala:
                if not self._activo(my_sim_id):
                    break
                if len(self.cola_interna) < self.NUM_SILLAS:
                    self.cola_interna.append(c_nom)
                    copia_cola = list(self.cola_interna)
                    self._emitir(my_sim_id, "cliente_entra", (c_nom, copia_cola))
                    self.sem_clientes.release()
                else:
                    self.retirados += 1
                    self._emitir(my_sim_id, "cliente_se_va", (c_nom, self.retirados))

    def _hilo_barbero(self, my_sim_id: int):
        while self._esperar_si_pausado(my_sim_id):
            with self.mutex_sala:
                if not self._activo(my_sim_id):
                    break
                if not self.cola_interna:
                    self._emitir(my_sim_id, "barbero_duerme", None)
            self.sem_clientes.acquire()
            if not self._esperar_si_pausado(my_sim_id):
                break
            with self.mutex_sala:
                if not self._activo(my_sim_id) or not self.cola_interna:
                    continue
                cliente = self.cola_interna.pop(0)
                copia_cola = list(self.cola_interna)
            self._emitir(my_sim_id, "barbero_corta", (cliente, copia_cola))
            if not self._dormir_hilo(1.5, my_sim_id):
                break
            self.atendidos += 1
            self._emitir(my_sim_id, "corte_terminado", (cliente, self.atendidos))

    def _actualizar_ui(self):
        n_esp = len(self.cola_espera)
        libres = self.NUM_SILLAS - n_esp
        self._actualizar_indicador(
            "barbero", self.estado_barbero,
            "#15803D" if "CORTANDO" in self.estado_barbero else "#B45309",
        )
        self._actualizar_indicador("clientes_sem", f"{n_esp} esperando", "#1E40AF")
        self._actualizar_indicador("sillas_lib", f"{libres} / {self.NUM_SILLAS}", "#0F172A")
        self._actualizar_indicador("mutex", "1 (Libre)", "#15803D")
        self._actualizar_indicador("atendidos", str(self.atendidos), "#15803D")
        self._actualizar_indicador("retirados", str(self.retirados), "#B91C1C")

    def _procesar_evento(self, tipo: str, datos: Any):
        if tipo == "barbero_duerme":
            self.cliente_en_silla = None
            self.estado_barbero = "DURMIENDO"
            self.lbl_status_banner.configure(
                text="Sala de espera vacía (clientes = 0) → El Barbero duerme en wait(clientes).",
                text_color="#B45309",
            )
            self._agregar_log("Barbero: cola vacía → se duerme en wait(clientes).")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "cliente_entra":
            c_nom, cola = datos
            self.cola_espera = cola
            self.ultimo_evento_puerta = f"Entró {c_nom} y tomó silla ({len(cola)}/5)"
            self._agregar_log(f"Llega {c_nom}: ocupa silla ({len(cola)}/{self.NUM_SILLAS}) → signal(clientes).")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "cliente_se_va":
            c_nom, _tot_ret = datos
            self.ultimo_evento_puerta = f"{c_nom} se retiró (Sala llena 5/5)"
            self.lbl_status_banner.configure(
                text=f"Llegó {c_nom} pero las 5 sillas están ocupadas → Se retira.",
                text_color="#B91C1C",
            )
            self._agregar_log(f"Llega {c_nom}: Sala llena (5/5) → {c_nom} se marcha.")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "barbero_corta":
            c_nom, cola = datos
            self.cliente_en_silla = c_nom
            self.cola_espera = cola
            self.estado_barbero = f"CORTANDO a {c_nom}"
            self.lbl_status_banner.configure(
                text=f"Barbero atendiendo a {c_nom} en su silla | En sala de espera: {len(cola)}/{self.NUM_SILLAS}",
                text_color="#15803D",
            )
            self._agregar_log(f"Barbero pasa a {c_nom} a la silla principal y comienza el corte.")
            self._actualizar_ui()
            self._dibujar_escena()
        elif tipo == "corte_terminado":
            c_nom, tot_at = datos
            self.cliente_en_silla = None
            self._agregar_log(f"Barbero terminó el corte de {c_nom} (Total atendidos: {tot_at}).")
            self._actualizar_ui()
            self._dibujar_escena()

    def _dibujar_escena(self):
        c = self.canvas
        c.delete("all")
        w = max(580, c.winfo_width())
        h = max(300, c.winfo_height())
        f = getattr(self, "anim_frame", 0)
        s = max(0.6, min(0.9, h / 390))
        y_piso = h - 50

        # ═════════════ Zona 1: Sala de espera ═════════════
        sx1, sx2 = w * 0.02, w * 0.56
        scx = (sx1 + sx2) / 2
        gp.rect_redondeado(c, sx1, 6, sx2, h - 6, 10, fill="#FFFBEB", outline="#E2E8F0", width=1.5)
        c.create_rectangle(sx1 + 1, y_piso, sx2 - 1, h - 8, fill="#E7D3B5", outline="")
        xx = sx1 + 20
        while xx < sx2 - 4:
            c.create_line(xx, y_piso, xx, h - 8, fill="#D6BC94")
            xx += 30
        c.create_line(sx1 + 1, y_piso, sx2 - 1, y_piso, fill="#B08D57", width=2)
        c.create_text(scx, 22, text=f"SALA DE ESPERA ({len(self.cola_espera)} / {self.NUM_SILLAS} sillas ocupadas)",
                      font=("Segoe UI", 11, "bold"), fill="#0F172A")

        # Decoración: reloj de pared y cuadro
        gp.reloj_pared(c, sx2 - 32, 60, 16, f)
        qx1, qy1 = sx1 + 70, 42
        c.create_rectangle(qx1, qy1, qx1 + 60, qy1 + 38, fill="#BAE6FD", outline="#92400E", width=3)
        c.create_polygon(qx1 + 2, qy1 + 36, qx1 + 22, qy1 + 14, qx1 + 36, qy1 + 30, qx1 + 46, qy1 + 20,
                         qx1 + 58, qy1 + 36, fill="#4D7C0F", outline="")
        c.create_oval(qx1 + 42, qy1 + 5, qx1 + 52, qy1 + 15, fill="#FACC15", outline="")

        # Puerta de entrada
        dx1 = sx1 + 8
        dx2 = dx1 + 38 * s
        dy1 = y_piso - 96 * s
        c.create_rectangle(dx1, dy1, dx2, y_piso, fill="#92400E", outline="#78350F", width=2)
        c.create_rectangle(dx1 + 6 * s, dy1 + 8 * s, dx2 - 6 * s, dy1 + 34 * s, fill="#BFDBFE", outline="#78350F")
        c.create_oval(dx2 - 9 * s, y_piso - 50 * s, dx2 - 4 * s, y_piso - 45 * s, fill="#FACC15", outline="")
        if "se retiró" in self.ultimo_evento_puerta:
            sm = s * 0.7
            gp.dibujar_persona(c, dx2 + 14 * sm, y_piso - 82 * sm, sm, ropa="#64748B", ojos="abiertos",
                               boca="triste", pose="reposo", direccion=-1)
            gp.globo_dialogo(c, dx2 + 30 * sm, y_piso - 82 * sm - 26, "¡Lleno! Me voy", color="#DC2626", s=s)
        elif "Entró" in self.ultimo_evento_puerta:
            gp.globo_dialogo(c, (dx1 + dx2) / 2 + 10, dy1 - 14, "¡Bienvenido!", color="#15803D", s=s)

        # 5 sillas con clientes sentados
        x0 = dx2 + 18 * s
        paso = (sx2 - 12 - x0) / self.NUM_SILLAS
        seat_y = y_piso - 26 * s
        for i in range(self.NUM_SILLAS):
            chx = x0 + paso * (i + 0.5) - 6 * s
            ocupada = i < len(self.cola_espera)
            gp.silla(c, chx, seat_y, s, 1, "#0EA5E9" if ocupada else "#94A3B8")
            if ocupada:
                nom = self.cola_espera[i]
                piel, ropa, pelo = gp.paleta_por_nombre(nom)
                head_y = seat_y - 48 * s
                num = int(re.sub(r"\D", "", nom) or 0)
                leer = num % 2 == 1
                geo = gp.dibujar_persona(c, chx - 2 * s, head_y, s, piel=piel, ropa=ropa, pelo=pelo,
                                         ojos="abiertos", boca="neutral", pose="leer" if leer else "reposo",
                                         direccion=1, piernas="sentado")
                if leer:
                    mi, md = geo["manos"]
                    gp.periodico(c, (mi[0] + md[0]) / 2, (mi[1] + md[1]) / 2 - 4 * s, s * 0.85)
                gp.etiqueta(c, chx, head_y - 13 * s - 10, nom, bg=gp.aclarar(ropa, 0.8), fg=gp.oscurecer(ropa, 0.7),
                            font=("Segoe UI", 8, "bold"))
            c.create_text(chx, y_piso + 11, text=f"Silla {i + 1}", font=("Segoe UI", 7, "bold"), fill="#78716C")

        gp.etiqueta(c, scx, h - 20, f"Recepción: {self.ultimo_evento_puerta}", bg="#FFFFFF", fg="#0F172A",
                    borde="#CBD5E1", font=("Segoe UI", 8, "bold"))

        # ═════════════ Zona 2: Barbería ═════════════
        bx1, bx2 = w * 0.58, w * 0.98
        bcx = (bx1 + bx2) / 2
        cortando = self.cliente_en_silla is not None
        gp.rect_redondeado(c, bx1, 6, bx2, h - 6, 10, fill="#EFF6FF", outline="#E2E8F0", width=1.5)
        # Piso ajedrezado clásico de barbería
        tile = 14
        fila = 0
        yy = y_piso
        while yy < h - 8:
            xx = bx1 + 1
            col_i = fila % 2
            while xx < bx2 - 1:
                if col_i % 2 == 0:
                    c.create_rectangle(xx, yy, min(xx + tile, bx2 - 1), min(yy + tile, h - 8),
                                       fill="#1F2937", outline="")
                xx += tile
                col_i += 1
            yy += tile
            fila += 1
        c.create_line(bx1 + 1, y_piso, bx2 - 1, y_piso, fill="#64748B", width=2)
        c.create_text(bcx, 22, text="BARBERÍA · SILLA DEL BARBERO", font=("Segoe UI", 11, "bold"), fill="#0F172A")
        if cortando:
            gp.etiqueta(c, bcx, 42, f"✂ CORTANDO a {self.cliente_en_silla}", bg="#DCFCE7", fg="#15803D",
                        font=("Segoe UI", 9, "bold"))
        else:
            gp.etiqueta(c, bcx, 42, "Zz DURMIENDO (clientes = 0)", bg="#FEF3C7", fg="#B45309",
                        font=("Segoe UI", 9, "bold"))

        # Espejo y poste
        my1, my2 = 58, 58 + h * 0.20
        gp.rect_redondeado(c, bx1 + 18, my1, bx2 - 44, my2, 8, fill="#DBEAFE", outline="#94A3B8", width=3)
        c.create_line(bx1 + 30, my2 - 10, bx1 + 50, my1 + 10, fill="#FFFFFF", width=3)
        c.create_line(bx1 + 44, my2 - 8, bx1 + 60, my1 + 18, fill="#FFFFFF", width=2)
        gp.poste_barberia(c, bx2 - 20, 70, y_piso - 30, 14, f if cortando else 0)

        ch_x = bcx - 4
        seat_y_ch = y_piso - 28 * s
        gp.sillon_barbero(c, ch_x, seat_y_ch, s, 1, y_piso=y_piso - 2)
        piel_b, pelo_b = "#E0AC69", "#1F2937"
        if cortando:
            nom = self.cliente_en_silla
            piel, ropa, pelo = gp.paleta_por_nombre(nom)
            head_c = seat_y_ch - 48 * s
            gp.dibujar_persona(c, ch_x, head_c, s, piel=piel, ropa=ropa, pelo=pelo, ojos="felices", boca="sonrisa",
                               direccion=1, piernas="sentado", capa="#E0F2FE")
            gp.etiqueta(c, ch_x + 30 * s, head_c - 24 * s, nom, bg=gp.aclarar(ropa, 0.8),
                        fg=gp.oscurecer(ropa, 0.7), font=("Segoe UI", 8, "bold"))
            # Mechones de cabello cayendo
            for k in range(6):
                cy_m = head_c + 10 * s + ((f * 5 + k * 9) % max(1, int(44 * s)))
                cx_m = ch_x + (k - 2.5) * 6 * s
                c.create_line(cx_m, cy_m, cx_m + 3 * s, cy_m + 3 * s, fill=pelo, width=2)
            # Barbero de pie detrás del cliente con tijeras y peine
            sb = s * 1.12
            bxb = ch_x - 36 * s
            head_b = y_piso - 2 - 82 * sb
            mano_tij = (ch_x - 2 * s, head_c - 17 * s)
            mano_pei = (ch_x - 15 * s, head_c - 2 * s)
            gp.dibujar_persona(c, bxb, head_b, sb, piel=piel_b, ropa="#0F172A", pelo=pelo_b, accesorio="bigote",
                               ojos="abiertos", boca="sonrisa", direccion=1, manos=[mano_pei, mano_tij],
                               delantal=True)
            gp.tijeras(c, mano_tij[0] + 7 * s, mano_tij[1] - 3 * s, s, abiertas=(f % 2 == 0))
            gp.peine(c, mano_pei[0] + 8 * s, mano_pei[1] - 4 * s, s * 0.8)
            gp.mano(c, mano_tij, sb, piel_b)
        else:
            head_b = seat_y_ch - 48 * s
            gp.dibujar_persona(c, ch_x, head_b, s, piel=piel_b, ropa="#0F172A", pelo=pelo_b, accesorio="bigote",
                               ojos="cerrados", boca="neutral", pose="cruzados", direccion=1, piernas="sentado",
                               delantal=True)
            gp.zzz(c, ch_x + 16 * s, head_b - 18 * s, f, s)

        gp.etiqueta(c, bcx, h - 20, f"Atendidos: {self.atendidos}   |   Se fueron: {self.retirados}",
                    bg="#FFFFFF", fg="#1E293B", borde="#CBD5E1", font=("Segoe UI", 9, "bold"))
