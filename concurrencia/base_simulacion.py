"""
============================================================================
 MÓDULO 2: CLASE BASE DE SIMULACIÓN DE CONCURRENCIA (TEMA CLARO)
 Autor : Jordan Oliber Soncco Machaca — UNA Puno
============================================================================

 Proporciona:
   - Interfaz en Tema Claro moderno con tonos grises y pizarra.
   - Controles corregidos y claros:
       • ▶ Iniciar / Reanudar
       • ⏸ Pausar (congela inmediatamente los hilos y los eventos)
       • 🧹 Limpiar (detiene hilos y restaura el estado inicial sin auto-iniciar)
   - Redibujado responsivo (<Configure>) para que ningún gráfico se distorsione.
   - Panel de 'Fundamento Teórico', Monitor de Semáforos y Bitácora.
============================================================================
"""

from __future__ import annotations
import queue
import threading
import time
import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, List, Tuple


TEORIA_CONCURRENCIA: Dict[str, Dict[str, str]] = {
    "Productor - Consumidor": {
        "titulo": "Problema Productor - Consumidor (Búfer Acotado)",
        "problema": (
            "Los procesos Productores generan datos y los depositan en un búfer compartido de capacidad "
            "limitada (N = 8), mientras los Consumidores extraen dichos datos. Se debe impedir escribir "
            "cuando el búfer está lleno, leer cuando está vacío y acceder simultáneamente a la misma celda."
        ),
        "semaforos": (
            "• mutex = 1 (Lock binario): Garantiza exclusión mutua al modificar el búfer.\n"
            "• empty = 8 (Semáforo contador): Cuenta espacios vacíos disponibles.\n"
            "• full  = 0 (Semáforo contador): Cuenta ítems listos para ser consumidos."
        ),
        "logica": (
            "Productor:  wait(empty) → wait(mutex) → insertar() → signal(mutex) → signal(full)\n"
            "Consumidor: wait(full)  → wait(mutex) → retirar()  → signal(mutex) → signal(empty)"
        ),
    },
    "Lectores - Escritores": {
        "titulo": "Problema de Lectores - Escritores",
        "problema": (
            "Una Base de Datos compartida es consultada por múltiples Lectores y actualizada por Escritores. "
            "Varios lectores pueden leer al mismo tiempo sin conflicto, pero cuando un Escritor accede "
            "requiere exclusividad absoluta (sin otros escritores ni lectores activos)."
        ),
        "semaforos": (
            "• wrt = 1: Semáforo de exclusión sobre el recurso compartido (Base de Datos).\n"
            "• mutex_lectores = 1: Protege el contador 'num_lectores'.\n"
            "• num_lectores = 0: Cantidad de lectores leyendo simultáneamente."
        ),
        "logica": (
            "• El 1er lector (num_lectores == 1) hace wait(wrt) bloqueando a los escritores.\n"
            "• El último lector en salir (num_lectores == 0) hace signal(wrt) liberando la BD.\n"
            "• Cada escritor ejecuta wait(wrt) → actualiza versión → signal(wrt)."
        ),
    },
    "Filósofos comensales": {
        "titulo": "Problema de los Filósofos Comensales",
        "problema": (
            "Cinco filósofos (F0..F4) alternan entre pensar y comer alrededor de una mesa con 5 tenedores "
            "(T0..T4). Para comer, cada filósofo necesita tomar los 2 tenedores adyacentes (izquierdo y derecho). "
            "Si los 5 toman su tenedor izquierdo a la vez, se produce un interbloqueo (Deadlock)."
        ),
        "semaforos": (
            "• tenedor[0..4] = [1, 1, 1, 1, 1]: Un semáforo binario por cada tenedor.\n"
            "• camarero = 4 (Semáforo contador): Permite que máximo 4 filósofos compitan por tenedores a la vez."
        ),
        "logica": (
            "Con un máximo de 4 filósofos intentando tomar 5 tenedores simultáneamente, siempre habrá al menos "
            "un filósofo que logre adquirir ambos tenedores y comer, evitando la espera circular (Deadlock)."
        ),
    },
    "Barbero dormilón": {
        "titulo": "Problema del Barbero Dormilón",
        "problema": (
            "Una barbería cuenta con 1 barbero, 1 silla de corte y 5 sillas de espera. Si no hay clientes, "
            "el barbero duerme. Al llegar un cliente, si el barbero duerme lo despierta; si está ocupado, "
            "espera en una silla libre o se retira si las 5 sillas están llenas."
        ),
        "semaforos": (
            "• clientes = 0 (Semáforo contador): Clientes esperando atención (despierta al barbero).\n"
            "• mutex = 1 (Lock): Protege el acceso a la cola de sillas de espera."
        ),
        "logica": (
            "Cliente: wait(mutex) → si (en_espera < 5): ocupa silla y signal(clientes); sino: se retira.\n"
            "Barbero: wait(clientes) → pasa al primer cliente en espera a la silla de corte → corta cabello."
        ),
    },
    "Fumadores": {
        "titulo": "Problema de los Fumadores",
        "problema": (
            "Tres fumadores requieren 3 ingredientes (Tabaco, Papel y Fósforos) para armar un cigarrillo. "
            "Cada fumador tiene cantidad infinita de un solo ingrediente. El Agente coloca 2 ingredientes "
            "al azar en la mesa y despierta únicamente al fumador que posee el 3er ingrediente."
        ),
        "semaforos": (
            "• sem_fumador[Tabaco, Papel, Fósforos] = [0, 0, 0]: Despierta al fumador con el ingrediente faltante.\n"
            "• sem_agente = 0: El agente espera hasta que el fumador activo termine de armar y fumar."
        ),
        "logica": (
            "Agente: coloca 2 ingredientes → signal(sem_fumador[faltante]) → wait(sem_agente).\n"
            "Fumador: wait(sem_fumador[propio]) → recoge la mesa, arma y fuma → signal(sem_agente)."
        ),
    },
}


class BaseSimulacionFrame(ctk.CTkFrame):
    """Estructura visual y de control común para las 5 simulaciones de concurrencia."""

    def __init__(self, master, clave_teoria: str):
        super().__init__(master, fg_color="#EEF2F6", corner_radius=0)
        self.clave_teoria = clave_teoria

        # Identificador de sesión para descartar hilos antiguos al limpiar
        self.sim_id = 0
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.running = False
        self.events: queue.Queue[Tuple[int, str, Any]] = queue.Queue()
        self.t_inicio_sim = time.monotonic()
        # Fotograma de animación para los personajes vectoriales (humo, Zzz, tijeras, LEDs...)
        self.anim_frame = 0

        self.grid_columnconfigure(0, weight=3, uniform="main_cols")
        self.grid_columnconfigure(1, weight=2, uniform="main_cols")
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._crear_barra_controles()
        self._crear_area_principal()
        self.after(60, self._loop_eventos)
        self.after(200, self._loop_animacion)

    def _loop_animacion(self):
        """Avanza la animación de los personajes solo si la simulación corre y es visible."""
        try:
            if self.running and self.pause_event.is_set() and self.canvas.winfo_ismapped():
                self.anim_frame += 1
                self._dibujar_escena()
        except tk.TclError:
            return
        if self.winfo_exists():
            self.after(200, self._loop_animacion)

    # ── Barra superior con botones claros: Iniciar/Reanudar, Pausar, Limpiar ──
    def _crear_barra_controles(self):
        barra = ctk.CTkFrame(
            self, fg_color="#FFFFFF", corner_radius=10,
            border_width=1, border_color="#CBD5E1", height=50,
        )
        barra.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 6))
        barra.pack_propagate(False)

        info = TEORIA_CONCURRENCIA[self.clave_teoria]
        ctk.CTkLabel(
            barra,
            text=info["titulo"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#0F172A",
        ).pack(side="left", padx=(14, 10), pady=10)

        self.badge_estado = ctk.CTkLabel(
            barra,
            text=" ● LISTO ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#DCFCE7",
            text_color="#166534",
            corner_radius=6,
        )
        self.badge_estado.pack(side="left", padx=4, pady=10)

        frame_ctrl = ctk.CTkFrame(barra, fg_color="transparent")
        frame_ctrl.pack(side="right", padx=12, pady=8)

        # Iniciar (Verde Esmeralda Suave)
        self.btn_iniciar = ctk.CTkButton(
            frame_ctrl, text="▶ Iniciar", width=105, height=30,
            fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534",
            border_width=1, border_color="#86EFAC",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.iniciar_o_reanudar,
        )
        self.btn_iniciar.pack(side="left", padx=3)

        # Pausar (Ámbar Suave)
        self.btn_pausar = ctk.CTkButton(
            frame_ctrl, text="⏸ Pausar", width=95, height=30,
            fg_color="#FEF3C7", hover_color="#FDE68A", text_color="#92400E",
            border_width=1, border_color="#FCD34D",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.pausar,
        )
        self.btn_pausar.pack(side="left", padx=3)

        # Limpiar (Pizarra Neutro)
        self.btn_limpiar = ctk.CTkButton(
            frame_ctrl, text="🧹 Limpiar", width=95, height=30,
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#334155",
            border_width=1, border_color="#CBD5E1",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.limpiar,
        )
        self.btn_limpiar.pack(side="left", padx=3)

        ctk.CTkLabel(
            frame_ctrl, text="Velocidad:", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#475569",
        ).pack(side="left", padx=(10, 4))

        self.lbl_vel = ctk.CTkLabel(
            frame_ctrl, text="1.0x", width=36,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#0F172A",
        )
        self.lbl_vel.pack(side="right", padx=(2, 4))

        self.slider_vel = ctk.CTkSlider(
            frame_ctrl, from_=0.25, to=2.5, number_of_steps=9, width=95,
            fg_color="#E2E8F0", progress_color="#2563EB",
            button_color="#2563EB", button_hover_color="#1D4ED8",
            command=self._on_vel_change,
        )
        self.slider_vel.set(1.0)
        self.slider_vel.pack(side="right", padx=2)

    def _on_vel_change(self, val):
        self.lbl_vel.configure(text=f"{float(val):.2f}x")

    def get_speed(self) -> float:
        try:
            return max(0.25, float(self.slider_vel.get()))
        except Exception:
            return 1.0

    # ── Área central: Lienzo + Fundamento Teórico (Izq) y Semáforos + Bitácora (Der) ──
    def _crear_area_principal(self):
        col_izq = ctk.CTkFrame(self, fg_color="transparent")
        col_izq.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))
        col_izq.grid_rowconfigure(0, weight=1)
        col_izq.grid_rowconfigure(1, weight=0)
        col_izq.grid_columnconfigure(0, weight=1)

        # ── SECCIÓN 1: ESPACIO DE SIMULACIÓN (Lienzo interactivo con Personajes) ──
        frame_canvas = ctk.CTkFrame(
            col_izq, fg_color="#FFFFFF", corner_radius=10,
            border_width=1.5, border_color="#94A3B8",
        )
        frame_canvas.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        frame_canvas.grid_rowconfigure(1, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)

        banner_frame = ctk.CTkFrame(
            frame_canvas, fg_color="#EFF6FF", corner_radius=6,
            border_width=1, border_color="#BFDBFE", height=28,
        )
        banner_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 4))
        banner_frame.pack_propagate(False)

        ctk.CTkLabel(
            banner_frame,
            text="🎯 ESPACIO DE SIMULACIÓN",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#1E3A8A",
        ).pack(side="left", padx=8, pady=3)

        self.lbl_status_banner = ctk.CTkLabel(
            banner_frame,
            text="│ Presiona '▶ Iniciar' para comenzar.",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#475569",
            anchor="w",
        )
        self.lbl_status_banner.pack(side="left", fill="x", expand=True, padx=(4, 8), pady=3)

        # Lienzo 100% INTACTO para respetar los gráficos vectoriales y personajes
        self.canvas = tk.Canvas(
            frame_canvas, bg="#FFFFFF", highlightthickness=0, width=720, height=340
        )
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=8, pady=(2, 8))
        self.canvas.bind("<Configure>", lambda _e: self._dibujar_escena())

        # ── SECCIÓN 2: ESPACIO DE INFORMACIÓN · Fundamento Teórico (Ámbar Académico) ──
        teoria = TEORIA_CONCURRENCIA[self.clave_teoria]
        frame_teoria = ctk.CTkFrame(
            col_izq, fg_color="#FFFBEB", corner_radius=10,
            border_width=1, border_color="#FDE68A", height=152,
        )
        frame_teoria.grid(row=1, column=0, sticky="ew")
        frame_teoria.pack_propagate(False)

        header_teoria = ctk.CTkFrame(frame_teoria, fg_color="#FEF3C7", corner_radius=6, height=26)
        header_teoria.pack(fill="x", padx=6, pady=(6, 3))
        header_teoria.pack_propagate(False)

        ctk.CTkLabel(
            header_teoria,
            text="📘 Fundamento Teórico del Problema",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#92400E",
        ).pack(side="left", padx=8, pady=2)

        texto_teoria = (
            f"• Descripción: {teoria['problema']}\n"
            f"{teoria['semaforos']}\n"
            f"• Sincronización: {teoria['logica']}"
        )
        self.txt_teoria = ctk.CTkTextbox(
            frame_teoria, height=112, fg_color="#FEFCE8", text_color="#78350F",
            border_width=1, border_color="#FDE68A",
            font=ctk.CTkFont(family="Segoe UI", size=11), wrap="word",
        )
        self.txt_teoria.pack(fill="x", padx=6, pady=(2, 6))
        self.txt_teoria.insert("1.0", texto_teoria)
        self.txt_teoria.configure(state="disabled")

        # Columna derecha: Semáforos + Bitácora
        col_der = ctk.CTkFrame(self, fg_color="transparent")
        col_der.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))
        col_der.grid_rowconfigure(0, weight=0)
        col_der.grid_rowconfigure(1, weight=1)
        col_der.grid_columnconfigure(0, weight=1)

        # ── SECCIÓN 3: ESPACIO DE INFORMACIÓN · Semáforos y Métricas en Vivo ──
        self.frame_semaforos = ctk.CTkFrame(
            col_der, fg_color="#FFFFFF", corner_radius=10,
            border_width=1, border_color="#BFDBFE",
        )
        self.frame_semaforos.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        header_sem = ctk.CTkFrame(self.frame_semaforos, fg_color="#EFF6FF", corner_radius=6, height=28)
        header_sem.pack(fill="x", padx=6, pady=(6, 4))
        header_sem.pack_propagate(False)

        ctk.CTkLabel(
            header_sem,
            text="🚦 Estado de Semáforos y Métricas en Vivo",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#1E3A8A",
        ).pack(side="left", padx=8, pady=3)

        self.grid_sem = ctk.CTkFrame(self.frame_semaforos, fg_color="transparent")
        self.grid_sem.pack(fill="x", padx=6, pady=(0, 6))
        self.sem_labels: Dict[str, ctk.CTkLabel] = {}

        # ── SECCIÓN 4: ESPACIO DE INFORMACIÓN · Bitácora de Sincronización (Consola Terminal Dark) ──
        frame_log = ctk.CTkFrame(
            col_der, fg_color="#1E293B", corner_radius=10,
            border_width=1, border_color="#334155",
        )
        frame_log.grid(row=1, column=0, sticky="nsew")
        frame_log.grid_rowconfigure(1, weight=1)
        frame_log.grid_columnconfigure(0, weight=1)

        header_log = ctk.CTkFrame(frame_log, fg_color="#0F172A", corner_radius=6, height=30)
        header_log.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 4))
        header_log.pack_propagate(False)

        ctk.CTkLabel(
            header_log,
            text="📟 Bitácora de Sincronización (Eventos P/V)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#F8FAFC",
        ).pack(side="left", padx=8, pady=4)

        ctk.CTkButton(
            header_log, text="Borrar bitácora", width=95, height=22,
            fg_color="#334155", hover_color="#475569", text_color="#F8FAFC",
            border_width=1, border_color="#475569",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), command=self._limpiar_log,
        ).pack(side="right", padx=6, pady=4)

        self.txt_log = ctk.CTkTextbox(
            frame_log, fg_color="#0F172A", text_color="#A7F3D0",
            border_width=0,
            font=ctk.CTkFont(family="Consolas", size=10), wrap="word",
        )
        self.txt_log.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.txt_log.configure(state="disabled")

    def _configurar_indicadores_semaforos(self, items: List[Tuple[str, str, str]]):
        for w in self.grid_sem.winfo_children():
            w.destroy()
        self.sem_labels.clear()

        for idx, (clave, titulo, val_ini) in enumerate(items):
            r, c = divmod(idx, 2)
            self.grid_sem.grid_columnconfigure(c, weight=1, uniform="sem_cols")
            card = ctk.CTkFrame(
                self.grid_sem, fg_color="#F8FAFC", corner_radius=6,
                border_width=1, border_color="#CBD5E1", height=46,
            )
            card.grid(row=r, column=c, sticky="ew", padx=3, pady=3)
            card.pack_propagate(False)

            ctk.CTkLabel(
                card, text=titulo, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#64748B"
            ).pack(anchor="w", padx=8, pady=(3, 0))

            lbl_val = ctk.CTkLabel(
                card, text=val_ini,
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color="#0F172A",
            )
            lbl_val.pack(anchor="w", padx=8, pady=(0, 3))
            self.sem_labels[clave] = lbl_val

    def _actualizar_indicador(self, clave: str, valor: str, color: str = "#0F172A"):
        if clave in self.sem_labels:
            self.sem_labels[clave].configure(text=valor, text_color=color)

    def _agregar_log(self, mensaje: str):
        elapsed = time.monotonic() - self.t_inicio_sim
        linea = f"[{elapsed:05.1f}s] {mensaje}\n"
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", linea)
        num_lines = int(self.txt_log.index("end-1c").split(".")[0])
        if num_lines > 120:
            self.txt_log.delete("1.0", f"{num_lines - 120}.0")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _limpiar_log(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    # ── Métodos seguros para hilos con soporte real de PAUSA y LIMPIAR ──
    def _activo(self, my_sim_id: int) -> bool:
        return not self.stop_event.is_set() and my_sim_id == self.sim_id

    def _esperar_si_pausado(self, my_sim_id: int) -> bool:
        """Bloquea el hilo mientras esté en pausa. Devuelve False si se detuvo/limpió."""
        while not self.pause_event.is_set():
            if self.stop_event.is_set() or my_sim_id != self.sim_id:
                return False
            time.sleep(0.04)
        return self._activo(my_sim_id)

    def _dormir_hilo(self, segundos_base: float, my_sim_id: int) -> bool:
        """
        Duerme el hilo respetando la velocidad y congelando el conteo de tiempo
        mientras el botón Pausar esté activo.
        """
        restante = segundos_base / self.get_speed()
        paso = 0.04
        while restante > 0:
            if not self._esperar_si_pausado(my_sim_id):
                return False
            t0 = time.monotonic()
            time.sleep(min(paso, restante))
            if self.pause_event.is_set():
                restante -= (time.monotonic() - t0)
        return self._esperar_si_pausado(my_sim_id)

    def _emitir(self, my_sim_id: int, tipo: str, datos: Any):
        if self._activo(my_sim_id):
            self.events.put((my_sim_id, tipo, datos))

    # ── Acciones de los 3 botones: Iniciar/Continuar, Pausar, Limpiar ──
    def iniciar_o_reanudar(self):
        if not self.running:
            self.sim_id += 1
            self.running = True
            self.stop_event.clear()
            self.pause_event.set()
            self.t_inicio_sim = time.monotonic()
            self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534", border_color="#86EFAC")
            self.badge_estado.configure(text=" ● EN EJECUCIÓN ", fg_color="#059669", text_color="#FFFFFF")
            self._iniciar_hilos(self.sim_id)
        elif not self.pause_event.is_set():
            self.pause_event.set()
            self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534", border_color="#86EFAC")
            self.badge_estado.configure(text=" ● EN EJECUCIÓN ", fg_color="#059669", text_color="#FFFFFF")
            self.lbl_status_banner.configure(text="Simulación activa en tiempo real.", text_color="#166534")
            self._agregar_log("▶ Simulación continuada.")

    def pausar(self):
        if self.running and self.pause_event.is_set():
            self.pause_event.clear()
            self.btn_iniciar.configure(text="▶ Continuar", fg_color="#FEF3C7", hover_color="#FDE68A", text_color="#92400E", border_color="#FCD34D")
            self.badge_estado.configure(text=" ⏸ PAUSADO ", fg_color="#FEF3C7", text_color="#92400E")
            self.lbl_status_banner.configure(
                text="⏸ Simulación en pausa — Presiona '▶ Continuar' para seguir o '🧹 Limpiar' para reiniciar.",
                text_color="#92400E",
            )
            self._agregar_log("⏸ Simulación pausada.")

    def limpiar(self):
        """
        Detiene todos los hilos, vacía la cola de eventos, limpia la bitácora
        y restaura el estado visual inicial SIN auto-iniciar.
        """
        self.sim_id += 1
        self.running = False
        self.stop_event.set()
        self.pause_event.set()
        self._desbloquear_semaforos()

        while not self.events.empty():
            try:
                self.events.get_nowait()
            except queue.Empty:
                break

        self._limpiar_log()
        self._reset_estado_visual()
        self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534", border_color="#86EFAC")
        self.badge_estado.configure(text=" ● LISTO ", fg_color="#DCFCE7", text_color="#166534")
        self.lbl_status_banner.configure(
            text="Estado limpio. Presiona '▶ Iniciar' cuando desees arrancar la simulación.",
            text_color="#334155",
        )

    def detener(self):
        """Método auxiliar al cerrar la aplicación."""
        self.sim_id += 1
        self.running = False
        self.stop_event.set()
        self.pause_event.set()
        self._desbloquear_semaforos()

    def _loop_eventos(self):
        # Si está en pausa, NO procesar nuevos eventos visuales hasta que se reanude
        if self.running and self.pause_event.is_set():
            try:
                while True:
                    ev_sim_id, tipo, datos = self.events.get_nowait()
                    if ev_sim_id == self.sim_id:
                        self._procesar_evento(tipo, datos)
            except queue.Empty:
                pass
        if self.winfo_exists():
            self.after(60, self._loop_eventos)

    # Métodos a sobrescribir en las 5 subclases
    def _iniciar_hilos(self, my_sim_id: int):
        pass

    def _desbloquear_semaforos(self):
        pass

    def _reset_estado_visual(self):
        pass

    def _procesar_evento(self, tipo: str, datos: Any):
        pass

    def _dibujar_escena(self):
        pass
