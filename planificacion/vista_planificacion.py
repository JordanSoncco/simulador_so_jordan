"""
============================================================================
 MÓDULO 1: VISTA INTERACTIVA DE PLANIFICACIÓN DE PROCESOS (TEMA CLARO)
 Autor : Jordan Oliber Soncco Machaca — UNA Puno
============================================================================

 Características:
   - Tema Claro moderno con tonos grises/pizarra sin contaminación visual.
   - Interactividad al agregar procesos (se grafican en vivo en el plano).
   - Simulación interactiva paso a paso en el tiempo (Iniciar/Reanudar,
     Pausar, Resultado Completo, Limpiar y control de Velocidad).
   - Separación total entre el Plano de Gantt (arriba) y el Cuadro de
     Resultados + Fórmulas (abajo).
   - Leyenda de abreviaturas siempre visible y pestaña de Fundamento Teórico.
============================================================================
"""

from __future__ import annotations
import os
from tkinter import messagebox, ttk, filedialog
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .algoritmos import ejecutar, comparar_todos, ALGORITMOS, INFO_TEORICA_POLITICAS, Resultado
from .graficador_gantt import (
    fmt_num,
    dibujar_plano_vacio_o_previa,
    dibujar_plano_gantt,
    dibujar_apartado_cola,
    dibujar_panel_formulas,
    configurar_eje_tiempo_gantt,
    configurar_eje_tiempo_cola,
    PALETA_PROCESOS,
)



class PanelPlanificacion(ctk.CTkFrame):
    """Módulo 1: Simulador interactivo de Políticas de Planificación."""

    def __init__(self, master, carpeta_base: str):
        super().__init__(master, fg_color="#EEF2F6", corner_radius=0)
        self.carpeta_base = carpeta_base

        self.procesos: list[dict] = []
        self.contador_procesos = 0
        self.ultimo_resultado: Resultado | None = None

        # Estado de la animación interactiva paso a paso
        self.anim_corriendo = False
        self.anim_pausada = False
        self.paso_actual = 0
        self.after_id: str | None = None

        # Estado de la herramienta de Lupa (Zoom) y Traslado (Pan)
        self.modo_interaccion: str | None = None   # None, "lupa", "mover"
        self.limites_zoom_actual: tuple | None = None
        self._drag_inicio: tuple | None = None
        self._drag_limites_ini: tuple | None = None
        self._rect_lupa: Rectangle | None = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._configurar_estilo_tablas()
        self._crear_panel_izquierdo()
        self._crear_panel_derecho()

    def _configurar_estilo_tablas(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Estilo para la tabla de Entrada (Azul Pizarra Suave)
        style.configure(
            "Entrada.Treeview",
            background="#FFFFFF",
            foreground="#1E293B",
            fieldbackground="#FFFFFF",
            rowheight=24,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Entrada.Treeview.Heading",
            background="#DBEAFE",
            foreground="#1E3A8A",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Entrada.Treeview",
            background=[("selected", "#EFF6FF")],
            foreground=[("selected", "#1D4ED8")],
        )

        # Estilo para la tabla de Resultados (Verde Esmeralda Suave)
        style.configure(
            "Resultados.Treeview",
            background="#FFFFFF",
            foreground="#1E293B",
            fieldbackground="#FFFFFF",
            rowheight=24,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Resultados.Treeview.Heading",
            background="#D1FAE5",
            foreground="#065F46",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Resultados.Treeview",
            background=[("selected", "#ECFDF5")],
            foreground=[("selected", "#059669")],
        )

        # Estilo para las barras de scroll discretas del Plano de Gantt (Tema Claro Bento)
        style.configure(
            "Gantt.Horizontal.TScrollbar",
            gripcount=0,
            background="#CBD5E1",
            darkcolor="#CBD5E1",
            lightcolor="#CBD5E1",
            troughcolor="#F8FAFC",
            bordercolor="#E2E8F0",
            arrowcolor="#64748B",
            arrowsize=10,
            width=10,
        )
        style.map(
            "Gantt.Horizontal.TScrollbar",
            background=[("active", "#94A3B8"), ("pressed", "#64748B")],
            arrowcolor=[("active", "#1E293B")],
        )

        style.configure(
            "Gantt.Vertical.TScrollbar",
            gripcount=0,
            background="#CBD5E1",
            darkcolor="#CBD5E1",
            lightcolor="#CBD5E1",
            troughcolor="#F8FAFC",
            bordercolor="#E2E8F0",
            arrowcolor="#64748B",
            arrowsize=10,
            width=10,
        )
        style.map(
            "Gantt.Vertical.TScrollbar",
            background=[("active", "#94A3B8"), ("pressed", "#64748B")],
            arrowcolor=[("active", "#1E293B")],
        )

    # ═══════════════════════════════════════════════════════════
    #  PANEL IZQUIERDO: BENTO UI SIN SCROLL VERTICAL
    # ═══════════════════════════════════════════════════════════
    def _crear_panel_izquierdo(self):
        """
        Panel izquierdo compacto diseñado para encajar el 100% de los controles
        sin necesidad de scroll vertical en cualquier resolución estándar.
        """
        panel = ctk.CTkFrame(
            self, width=356, corner_radius=10,
            fg_color="#FFFFFF", border_width=1.5, border_color="#BFDBFE",
        )
        panel.grid(row=0, column=0, sticky="nswe", padx=(6, 6), pady=(4, 4))
        panel.grid_propagate(False)
        panel.pack_propagate(False)

        # Encabezado distintivo de la Zona de Entrada y Configuración
        header_izq = ctk.CTkFrame(panel, fg_color="#1E3A8A", corner_radius=8, height=34)
        header_izq.pack(fill="x", padx=8, pady=(8, 4))
        header_izq.pack_propagate(False)

        ctk.CTkLabel(
            header_izq, text="📥 ENTRADA Y CONFIGURACIÓN",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=10, pady=4)

        ctk.CTkLabel(
            header_izq, text="MÓDULO 1",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color="#1D4ED8", text_color="#BFDBFE", corner_radius=4,
        ).pack(side="right", padx=8, pady=5)

        # Atributos de compatibilidad (resumen trasladado a la cabecera del Plano de Gantt)
        self.lbl_info_num_proc = None
        self.lbl_info_suma_ts = None
        self.lbl_info_tipo_pol = None

        # ── 1. Formulario Compacto de Ingreso de Procesos ──
        frame_form = ctk.CTkFrame(panel, fg_color="transparent")
        frame_form.pack(fill="x", padx=10, pady=(2, 0))

        # Fila A: Nombre del Proceso
        ctk.CTkLabel(
            frame_form, text="Nombre del Proceso:",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#1E3A8A",
        ).pack(anchor="w", pady=(0, 1))
        self.entry_nombre = ctk.CTkEntry(
            frame_form, placeholder_text="Ej: P0 (automático)", height=26,
            fg_color="#F8FAFC", border_color="#CBD5E1", text_color="#0F172A",
            font=ctk.CTkFont(family="Segoe UI", size=10),
        )
        self.entry_nombre.pack(fill="x", pady=(0, 3))

        # Fila B: T.LL y T.S. LADO A LADO en 2 columnas
        frame_tiempos = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_tiempos.pack(fill="x", pady=(0, 3))
        frame_tiempos.grid_columnconfigure((0, 1), weight=1, uniform="tiempos")

        # Columna 1: T.LL
        f_tll = ctk.CTkFrame(frame_tiempos, fg_color="transparent")
        f_tll.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ctk.CTkLabel(
            f_tll, text="Tiempo Llegada (T.LL):",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color="#334155",
        ).pack(anchor="w")
        self.entry_llegada = ctk.CTkEntry(
            f_tll, placeholder_text="≥ 0 (Ej: 0)", height=26,
            fg_color="#F8FAFC", border_color="#CBD5E1", text_color="#0F172A",
            font=ctk.CTkFont(family="Segoe UI", size=10),
        )
        self.entry_llegada.pack(fill="x", pady=(1, 0))

        # Columna 2: T.S.
        f_ts = ctk.CTkFrame(frame_tiempos, fg_color="transparent")
        f_ts.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        ctk.CTkLabel(
            f_ts, text="Tiempo Servicio (T.S.):",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color="#334155",
        ).pack(anchor="w")
        self.entry_rafaga = ctk.CTkEntry(
            f_ts, placeholder_text="> 0 (Ej: 6)", height=26,
            fg_color="#F8FAFC", border_color="#CBD5E1", text_color="#0F172A",
            font=ctk.CTkFont(family="Segoe UI", size=10),
        )
        self.entry_rafaga.pack(fill="x", pady=(1, 0))
        self.entry_rafaga.bind("<Return>", lambda _e: self._agregar_proceso())

        # Fila C: Botones (Agregar en Azul Primario, Quitar en Coral Suave, Vaciar en Outline)
        frame_btns = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_btns.pack(fill="x", pady=(0, 3))
        frame_btns.grid_columnconfigure((0, 1, 2), weight=1, uniform="btns_cola")

        # Primario Único: + Agregar (Azul vibrante)
        ctk.CTkButton(
            frame_btns, text="➕ Agregar", height=26,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF",
            command=self._agregar_proceso,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 2))

        # Destructivo: - Quitar (Rojo coral suave con texto rojo)
        ctk.CTkButton(
            frame_btns, text="➖ Quitar", height=26,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#FEE2E2", hover_color="#FECACA", text_color="#DC2626",
            border_width=1, border_color="#FECACA",
            command=self._eliminar_seleccionado,
        ).grid(row=0, column=1, sticky="ew", padx=2)

        # Secundario outline: Vaciar
        ctk.CTkButton(
            frame_btns, text="🗑 Vaciar", height=26,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#334155",
            border_width=1, border_color="#CBD5E1",
            command=self._vaciar_cola,
        ).grid(row=0, column=2, sticky="ew", padx=(2, 0))

        # Fila D: Botón Cargar TXT tipo Outline Secundario
        ctk.CTkButton(
            frame_form, text="📂  Cargar desde archivos TXT", height=26,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#1E293B",
            border_width=1, border_color="#CBD5E1",
            command=self._cargar_desde_archivo,
        ).pack(fill="x", pady=(1, 1))

        ctk.CTkLabel(
            frame_form,
            text="Formato: Nombre, T.LL, T.S.  (Ej: P0, 0, 5)",
            font=ctk.CTkFont(family="Segoe UI", size=8, slant="italic"),
            text_color="#64748B",
        ).pack(anchor="w", pady=(0, 2))

        # ── 2. Tabla de Procesos en Cola (Columnas limpias Proceso, T.LL, T.S.) ──
        self.lbl_titulo_cola = ctk.CTkLabel(
            panel, text="Cola de Entrada (#P = 0):",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#1E3A8A",
        )
        self.lbl_titulo_cola.pack(anchor="w", padx=12, pady=(0, 1))

        frame_tabla = ctk.CTkFrame(
            panel, fg_color="#FFFFFF", height=120,
            border_width=1, border_color="#BFDBFE", corner_radius=6,
        )
        frame_tabla.pack(fill="x", padx=10, pady=(0, 4))
        frame_tabla.pack_propagate(False)

        columnas = ("nombre", "llegada", "rafaga")
        self.tree_cola = ttk.Treeview(
            frame_tabla, columns=columnas, show="headings", style="Entrada.Treeview"
        )
        self.tree_cola.heading("nombre", text="Proceso")
        self.tree_cola.heading("llegada", text="T.LL")
        self.tree_cola.heading("rafaga", text="T.S.")

        self.tree_cola.column("nombre", anchor="center", width=95, minwidth=60)
        self.tree_cola.column("llegada", anchor="center", width=85, minwidth=50)
        self.tree_cola.column("rafaga", anchor="center", width=85, minwidth=50)

        sb_cola = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree_cola.yview)
        self.tree_cola.configure(yscrollcommand=sb_cola.set)
        self.tree_cola.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb_cola.pack(side="right", fill="y")

        # ── 3. Política de Planificación y Quantum LADO A LADO ──
        card_pol = ctk.CTkFrame(
            panel, fg_color="#F8FAFF", corner_radius=8,
            border_width=1, border_color="#BFDBFE",
        )
        card_pol.pack(fill="x", padx=10, pady=(2, 4))

        frame_pol_q = ctk.CTkFrame(card_pol, fg_color="transparent")
        frame_pol_q.pack(fill="x", padx=6, pady=4)
        frame_pol_q.grid_columnconfigure(0, weight=3)
        frame_pol_q.grid_columnconfigure(1, weight=1)

        f_pol = ctk.CTkFrame(frame_pol_q, fg_color="transparent")
        f_pol.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ctk.CTkLabel(
            f_pol, text="Política:",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color="#1E3A8A",
        ).pack(anchor="w")

        self.combo_algo = ctk.CTkComboBox(
            f_pol,
            values=list(ALGORITMOS.keys()),
            state="readonly",
            height=26,
            fg_color="#FFFFFF",
            border_color="#BFDBFE",
            button_color="#DBEAFE",
            button_hover_color="#BFDBFE",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#0F172A",
            text_color="#0F172A",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            command=self._on_algo_change,
        )
        self.combo_algo.set("FCFS")
        self.combo_algo.pack(fill="x", pady=(1, 0))

        f_q = ctk.CTkFrame(frame_pol_q, fg_color="transparent")
        f_q.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        self.label_quantum = ctk.CTkLabel(
            f_q, text="Quantum (q):",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color="#1E3A8A",
        )
        self.label_quantum.pack(anchor="w")

        self.entry_quantum = ctk.CTkEntry(
            f_q, height=26, placeholder_text="2",
            fg_color="#FFFFFF", border_color="#BFDBFE", text_color="#0F172A",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
        )
        self.entry_quantum.pack(fill="x", pady=(1, 0))
        self.entry_quantum.insert(0, "2")
        self._toggle_quantum()

        # ── 4. Botones de Acción Final (Siempre visibles al pie) ──
        # Comparar las 4 Políticas (Dark Slate #0F172A - Elegante y distinguido)
        self.btn_comparar = ctk.CTkButton(
            panel, text="📊  Comparar las 4 Políticas", height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#0F172A", hover_color="#1E293B", text_color="#FFFFFF",
            command=self._comparar_algoritmos,
        )
        self.btn_comparar.pack(fill="x", padx=10, pady=(2, 3))

        # Secundario Outline: Exportar Plano en Imagen (PNG)
        ctk.CTkButton(
            panel, text="💾  Exportar Plano en Imagen (PNG)", height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#334155",
            border_width=1, border_color="#CBD5E1",
            command=self._exportar_png,
        ).pack(fill="x", padx=10, pady=(0, 6))

    # ═══════════════════════════════════════════════════════════
    #  PANEL DERECHO: BENTO UI LIGHT MODE (GANTT Y COLA INTACTOS)
    # ═══════════════════════════════════════════════════════════
    def _crear_panel_derecho(self):
        self.panel_der = ctk.CTkFrame(
            self, corner_radius=10, fg_color="#FFFFFF",
            border_width=1, border_color="#E2E8F0",
        )
        self.panel_der.grid(row=0, column=1, sticky="nswe", padx=(0, 6), pady=6)
        self.panel_der.grid_rowconfigure(0, weight=0)   # Barra interactiva + métricas
        self.panel_der.grid_rowconfigure(1, weight=0)   # Leyenda de abreviaturas
        self.panel_der.grid_rowconfigure(2, weight=1)   # Sub-pestañas
        self.panel_der.grid_columnconfigure(0, weight=1)

        # ── 1. Barra Superior de Controles de Simulación (Colores Semánticos Intuitivos) ──
        barra_ctrl = ctk.CTkFrame(
            self.panel_der, fg_color="#F8FAFC", corner_radius=8,
            border_width=1, border_color="#E2E8F0", height=42,
        )
        barra_ctrl.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        barra_ctrl.pack_propagate(False)

        f_botones = ctk.CTkFrame(barra_ctrl, fg_color="transparent")
        f_botones.pack(side="right", padx=8, pady=5)

        # Iniciar (Verde Esmeralda Suave de alta legibilidad)
        self.btn_iniciar = ctk.CTkButton(
            f_botones, text="▶ Iniciar", width=80, height=28,
            fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534",
            border_width=1, border_color="#86EFAC",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.iniciar_o_reanudar_simulacion,
        )
        self.btn_iniciar.pack(side="left", padx=2)

        # Pausar (Ámbar Suave)
        self.btn_pausar = ctk.CTkButton(
            f_botones, text="⏸ Pausar", width=76, height=28,
            fg_color="#FEF3C7", hover_color="#FDE68A", text_color="#92400E",
            border_width=1, border_color="#FCD34D",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.pausar_simulacion,
        )
        self.btn_pausar.pack(side="left", padx=2)

        # Completo (Índigo Suave)
        self.btn_completo = ctk.CTkButton(
            f_botones, text="⏭ Completo", width=86, height=28,
            fg_color="#E0E7FF", hover_color="#C7D2FE", text_color="#3730A3",
            border_width=1, border_color="#A5B4FC",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.mostrar_resultado_completo,
        )
        self.btn_completo.pack(side="left", padx=2)

        # Limpiar (Pizarra Neutro)
        self.btn_limpiar_sim = ctk.CTkButton(
            f_botones, text="🧹 Limpiar", width=76, height=28,
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#334155",
            border_width=1, border_color="#CBD5E1",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=self.limpiar_simulacion,
        )
        self.btn_limpiar_sim.pack(side="left", padx=2)

        ctk.CTkLabel(
            f_botones, text="Velocidad:", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#475569",
        ).pack(side="left", padx=(6, 2))

        self.slider_vel = ctk.CTkSlider(
            f_botones, from_=0.5, to=3.0, number_of_steps=5, width=68,
            fg_color="#E2E8F0", progress_color="#2563EB",
            button_color="#2563EB", button_hover_color="#1D4ED8",
            command=self._on_vel_change,
        )
        self.slider_vel.set(1.5)
        self.slider_vel.pack(side="left", padx=2)

        self.lbl_vel_valor = ctk.CTkLabel(
            f_botones, text="1.5x", width=30,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#0F172A",
        )
        self.lbl_vel_valor.pack(side="left", padx=(1, 2))

        # A la izquierda: Badge de estado y texto conciso sin recortarse
        self.badge_estado = ctk.CTkLabel(
            barra_ctrl, text=" ● EN ESPERA ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#F1F5F9", text_color="#475569", corner_radius=6,
        )
        self.badge_estado.pack(side="left", padx=(8, 6), pady=6)

        self.lbl_cpu_vivo = ctk.CTkLabel(
            barra_ctrl,
            text="Agrega procesos y presiona '▶ Iniciar' para simular.",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#1E293B",
            anchor="w",
        )
        self.lbl_cpu_vivo.pack(side="left", fill="x", expand=True, padx=4, pady=6)

        # ── 2. Barra de Leyenda de Abreviaturas (Tono Ámbar Académico de Consulta Rápida) ──
        barra_leyenda = ctk.CTkFrame(
            self.panel_der, fg_color="#FFFBEB", corner_radius=6,
            border_width=1, border_color="#FDE68A", height=28,
        )
        barra_leyenda.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 4))
        barra_leyenda.pack_propagate(False)

        texto_leyenda = (
            "📌 Leyenda:  "
            "#P = Cant. Procesos │ "
            "T.LL = Tiempo Llegada │ "
            "T.S. = Tiempo Servicio (Ráfaga) │ "
            "T.F. = Tiempo Finalización (+) │ "
            "T.R. = Retorno (TF−TLL) │ "
            "T.E. = Espera (TR−TS) │ "
            "q = Quantum"
        )
        ctk.CTkLabel(
            barra_leyenda, text=texto_leyenda,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#92400E",
        ).pack(padx=8, pady=3, anchor="w")

        # ── 3. Sub-pestañas Bento UI con Dark Slate (#0F172A) en activa ──
        self.subtabs = ctk.CTkTabview(
            self.panel_der,
            fg_color="#FFFFFF",
            segmented_button_fg_color="#E2E8F0",
            segmented_button_selected_color="#0F172A",
            segmented_button_selected_hover_color="#1E293B",
            segmented_button_unselected_color="#F1F5F9",
            segmented_button_unselected_hover_color="#E2E8F0",
            text_color="#FFFFFF",
            text_color_disabled="#64748B",
            corner_radius=8,
            border_width=1,
            border_color="#CBD5E1",
            command=self._actualizar_contraste_subtabs,
        )
        self.subtabs.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))

        self.tab_sim = self.subtabs.add(
            "  📊  Plano de Gantt, Cola de Procesos y Cuadro de Resultados  "
        )
        self.tab_teoria = self.subtabs.add(
            "  📘  Fundamento Teórico y Traza de Ejecución  "
        )
        self._actualizar_contraste_subtabs()

        self.tab_sim.grid_rowconfigure(0, weight=4)   # Sección 1: Plano de Gantt
        self.tab_sim.grid_rowconfigure(1, weight=2)   # Sección 2: Apartado Cola de Procesos
        self.tab_sim.grid_rowconfigure(2, weight=3)   # Sección 3: Cuadro + Fórmulas
        self.tab_sim.grid_columnconfigure(0, weight=1)

        # ── SECCIÓN 1: ZONA DE SIMULACIÓN · Tarjeta Enmarcada del Plano de Gantt ──
        frame_plano = ctk.CTkFrame(
            self.tab_sim, fg_color="#FFFFFF", corner_radius=10,
            border_width=1.5, border_color="#94A3B8",
        )
        frame_plano.grid(row=0, column=0, sticky="nsew", padx=6, pady=(3, 2))
        frame_plano.grid_rowconfigure(0, weight=0)
        frame_plano.grid_rowconfigure(1, weight=1)
        frame_plano.grid_rowconfigure(2, weight=0)
        frame_plano.grid_columnconfigure(0, weight=1)
        frame_plano.grid_columnconfigure(1, weight=0)

        barra_zoom = ctk.CTkFrame(
            frame_plano, fg_color="#F1F5F9", corner_radius=6,
            border_width=1, border_color="#CBD5E1", height=30,
        )
        barra_zoom.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=(4, 2))
        barra_zoom.pack_propagate(False)

        # Barra de herramientas de Zoom estilizada tipo Bento Outline
        f_tools = ctk.CTkFrame(barra_zoom, fg_color="transparent")
        f_tools.pack(side="right", padx=6, pady=2)

        self.btn_lupa = ctk.CTkButton(
            f_tools, text="🔍 Lupa (Zoom)", width=104, height=24,
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#1E293B",
            border_width=1, border_color="#CBD5E1",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._toggle_modo_lupa,
        )
        self.btn_lupa.pack(side="left", padx=2)

        self.btn_mover = ctk.CTkButton(
            f_tools, text="✋ Mover", width=84, height=24,
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#1E293B",
            border_width=1, border_color="#CBD5E1",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._toggle_modo_mover,
        )
        self.btn_mover.pack(side="left", padx=2)

        ctk.CTkButton(
            f_tools, text="➕ Zoom +", width=70, height=24,
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#1E293B",
            border_width=1, border_color="#CBD5E1",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=lambda: self._aplicar_zoom_factor(0.78),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            f_tools, text="➖ Zoom -", width=70, height=24,
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#1E293B",
            border_width=1, border_color="#CBD5E1",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=lambda: self._aplicar_zoom_factor(1.28),
        ).pack(side="left", padx=2)

        self.btn_vista_completa = ctk.CTkButton(
            f_tools, text="🏠 Vista Completa", width=118, height=24,
            fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#0F172A",
            border_width=1, border_color="#CBD5E1",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            command=self._restablecer_vista_gantt,
        )
        self.btn_vista_completa.pack(side="left", padx=(4, 2))

        self.lbl_ayuda_zoom = ctk.CTkLabel(
            barra_zoom,
            text="🎯 ESPACIO DE SIMULACIÓN │ Plano de Gantt (Barras de scroll, Shift+Rueda o Clic Derecho)",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#1E3A8A",
            anchor="w",
        )
        self.lbl_ayuda_zoom.pack(side="left", fill="x", expand=True, padx=8, pady=2)

        # Lienzo del Plano de Gantt INTACTO
        self.fig_gantt = plt.figure(figsize=(9.2, 2.5), dpi=100, facecolor="#FFFFFF")
        self.canvas_gantt = FigureCanvasTkAgg(self.fig_gantt, master=frame_plano)
        self.canvas_gantt.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=(4, 1), pady=(0, 0))

        # Scrollbar Vertical del Plano de Gantt (Derecha)
        self.sb_gantt_v = ttk.Scrollbar(
            frame_plano, orient="vertical", style="Gantt.Vertical.TScrollbar", command=self._on_scroll_v
        )
        self.sb_gantt_v.grid(row=1, column=1, sticky="ns", padx=(1, 4), pady=(0, 0))

        # Scrollbar Horizontal del Plano de Gantt (Inferior)
        self.sb_gantt_h = ttk.Scrollbar(
            frame_plano, orient="horizontal", style="Gantt.Horizontal.TScrollbar", command=self._on_scroll_h
        )
        self.sb_gantt_h.grid(row=2, column=0, sticky="ew", padx=(4, 1), pady=(1, 3))

        # Conectar eventos de interacción con el ratón
        self.canvas_gantt.mpl_connect("scroll_event", self._on_gantt_scroll)
        self.canvas_gantt.mpl_connect("button_press_event", self._on_gantt_press)
        self.canvas_gantt.mpl_connect("motion_notify_event", self._on_gantt_motion)
        self.canvas_gantt.mpl_connect("button_release_event", self._on_gantt_release)
        self.canvas_gantt.get_tk_widget().bind("<Shift-MouseWheel>", self._on_tk_shift_mousewheel)

        # ── SECCIÓN 2: ZONA DE SIMULACIÓN · Tarjeta Enmarcada de la Cola de Procesos ──
        frame_cola_sec = ctk.CTkFrame(
            self.tab_sim, fg_color="#FFFFFF", corner_radius=10,
            border_width=1.5, border_color="#94A3B8",
        )
        frame_cola_sec.grid(row=1, column=0, sticky="nsew", padx=6, pady=2)
        frame_cola_sec.grid_rowconfigure(0, weight=0)
        frame_cola_sec.grid_rowconfigure(1, weight=1)
        frame_cola_sec.grid_columnconfigure(0, weight=1)

        f_header_cola = ctk.CTkFrame(frame_cola_sec, fg_color="#F1F5F9", corner_radius=6, height=24)
        f_header_cola.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 1))
        f_header_cola.pack_propagate(False)

        ctk.CTkLabel(
            f_header_cola,
            text="🎯 ESPACIO DE SIMULACIÓN │ Cola de Procesos por Unidad de Tiempo (Fila sup: CPU │ Filas inf: En Espera)",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#1E3A8A",
        ).pack(side="left", padx=8, pady=2)

        # Lienzo de la Cola INTACTO
        self.fig_cola = plt.figure(figsize=(9.2, 1.15), dpi=100, facecolor="#FFFFFF")
        self.canvas_cola = FigureCanvasTkAgg(self.fig_cola, master=frame_cola_sec)
        self.canvas_cola.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 2))

        # ── SECCIÓN 3: ZONA DE INFORMACIÓN Y RESULTADOS (Cuadro Esmeralda y Fórmulas Índigo) ──
        frame_inferior = ctk.CTkFrame(self.tab_sim, fg_color="transparent")
        frame_inferior.grid(row=2, column=0, sticky="nsew", padx=6, pady=(2, 4))
        frame_inferior.grid_columnconfigure(0, weight=5, uniform="inf_cols")
        frame_inferior.grid_columnconfigure(1, weight=6, uniform="inf_cols")
        frame_inferior.grid_rowconfigure(0, weight=1)

        frame_cuadro = ctk.CTkFrame(
            frame_inferior, fg_color="#FFFFFF", corner_radius=10,
            border_width=1.5, border_color="#A7F3D0",
        )
        frame_cuadro.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        frame_cuadro.grid_rowconfigure(1, weight=1)
        frame_cuadro.grid_columnconfigure(0, weight=1)

        f_header_cuadro = ctk.CTkFrame(frame_cuadro, fg_color="#ECFDF5", corner_radius=6, height=26)
        f_header_cuadro.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=(5, 3))
        f_header_cuadro.pack_propagate(False)

        self.lbl_titulo_cuadro = ctk.CTkLabel(
            f_header_cuadro,
            text="📊 RESULTADOS │ Cuadro de Métricas por Proceso (#P = 0)",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#065F46",
        )
        self.lbl_titulo_cuadro.pack(side="left", padx=8, pady=2)

        cols_res = ("nombre", "tll", "ts", "tf", "tr", "te")
        self.tree_resultados = ttk.Treeview(
            frame_cuadro, columns=cols_res, show="headings", style="Resultados.Treeview", height=4
        )
        for col_id, texto_h, w_col in [
            ("nombre", "Proceso", 70),
            ("tll", "T.LL", 55),
            ("ts", "T.S.", 55),
            ("tf", "T.F.", 55),
            ("tr", "T.R.", 55),
            ("te", "T.E.", 55),
        ]:
            self.tree_resultados.heading(col_id, text=texto_h)
            self.tree_resultados.column(col_id, anchor="center", width=w_col, minwidth=45)

        sb_res = ttk.Scrollbar(frame_cuadro, orient="vertical", command=self.tree_resultados.yview)
        self.tree_resultados.configure(yscrollcommand=sb_res.set)
        self.tree_resultados.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 4))
        sb_res.grid(row=1, column=1, sticky="ns", padx=(0, 6), pady=(0, 4))

        # Derecha: Fórmulas Matemáticas Paso a Paso y Tarjetas KPIs Bento
        frame_math = ctk.CTkFrame(
            frame_inferior, fg_color="#FFFFFF", corner_radius=10,
            border_width=1.5, border_color="#C7D2FE",
        )
        frame_math.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        frame_math.grid_rowconfigure(1, weight=1)
        frame_math.grid_columnconfigure(0, weight=1)

        f_header_math = ctk.CTkFrame(frame_math, fg_color="#EEF2FF", corner_radius=6, height=26)
        f_header_math.grid(row=0, column=0, sticky="ew", padx=6, pady=(5, 3))
        f_header_math.pack_propagate(False)

        ctk.CTkLabel(
            f_header_math,
            text="📐 ANÁLISIS │ Ecuaciones Paso a Paso y Promedios (TR̄ y TĒ)",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#3730A3",
        ).pack(side="left", padx=8, pady=2)

        self.fig_math = plt.figure(figsize=(5.5, 1.85), dpi=100, facecolor="#FFFFFF")
        self.canvas_math = FigureCanvasTkAgg(self.fig_math, master=frame_math)
        self.canvas_math.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

        # Configurar Tab 2: Fundamento Teórico + Traza
        self.tab_teoria.grid_rowconfigure(0, weight=0)
        self.tab_teoria.grid_rowconfigure(1, weight=1)
        self.tab_teoria.grid_columnconfigure(0, weight=1)

        f_teo = ctk.CTkFrame(
            self.tab_teoria, fg_color="#FFFBEB", corner_radius=8,
            border_width=1.5, border_color="#FDE68A",
        )
        f_teo.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            f_teo, text="📘 Fundamento Teórico del Algoritmo",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#92400E",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.txt_teoria = ctk.CTkTextbox(
            f_teo, height=145, fg_color="#FEFCE8", text_color="#78350F",
            border_width=1, border_color="#FDE68A",
            font=ctk.CTkFont(size=12), wrap="word",
        )
        self.txt_teoria.pack(fill="x", padx=10, pady=(0, 8))

        f_traza = ctk.CTkFrame(
            self.tab_teoria, fg_color="#FFFFFF", corner_radius=8,
            border_width=1.5, border_color="#CBD5E1",
        )
        f_traza.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        f_traza.grid_rowconfigure(1, weight=1)
        f_traza.grid_columnconfigure(0, weight=1)

        header_traza = ctk.CTkFrame(f_traza, fg_color="#1E293B", corner_radius=6, height=30)
        header_traza.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            header_traza, text="⏱️ Consola de Ejecución Cronológica y Cola de Listos",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#F8FAFC",
        ).pack(side="left", padx=10, pady=4)

        self.txt_traza = ctk.CTkTextbox(
            f_traza, fg_color="#0F172A", text_color="#A7F3D0",
            border_width=1, border_color="#1E293B",
            font=ctk.CTkFont(family="Consolas", size=11), wrap="word",
        )
        self.txt_traza.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # Inicializar vistas limpias
        self._redibujar_vista_previa()
        dibujar_panel_formulas(self.fig_math, None)
        self.canvas_math.draw()
        self._actualizar_fundamento_teorico("FCFS")

    # ═══════════════════════════════════════════════════════════
    #  HERRAMIENTAS DE LUPA (ZOOM), MOVER (TRASLADO) CON LÍMITES ESTRICTOS
    # ═══════════════════════════════════════════════════════════
    def _on_vel_change(self, val):
        try:
            self.lbl_vel_valor.configure(text=f"{float(val):.1f}x")
        except Exception:
            pass

    def _actualizar_contraste_subtabs(self):
        """Garantiza que la sub-pestaña activa tenga texto blanco con Dark Slate #0F172A (como Imagen 1) y la inactiva texto oscuro legible."""
        try:
            actual = self.subtabs.get()
            seg_btn = self.subtabs._segmented_button
            seg_btn.configure(font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"))
            for nombre, btn in seg_btn._buttons_dict.items():
                if nombre == actual:
                    btn.configure(fg_color="#0F172A", hover_color="#1E293B", text_color="#FFFFFF")
                else:
                    btn.configure(fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#475569")
        except Exception:
            pass

    def _obtener_ax_gantt(self):
        return self.fig_gantt.axes[0] if self.fig_gantt.axes else None

    def _obtener_ax_cola(self):
        return self.fig_cola.axes[0] if self.fig_cola.axes else None

    def _restringir_y_aplicar_limites(self, nx0: float, nx1: float, ny0: float, ny1: float):
        """
        Aplica límites estrictos de Zoom In, Zoom Out (máximo 100% original) y
        tope de desplazamiento (Pan) para que el gráfico jamás se deforme ni se salga de sus bordes.
        Además sincroniza el eje X del apartado de la Cola de Procesos.
        """
        ax = self._obtener_ax_gantt()
        if ax is None:
            return

        if hasattr(ax, "_limites_originales"):
            (xmin_orig, xmax_orig), (ymin_orig, ymax_orig) = ax._limites_originales
        else:
            xmin_orig, xmax_orig = ax.get_xlim()
            ymin_orig, ymax_orig = ax.get_ylim()

        w_orig = max(1.0, xmax_orig - xmin_orig)
        h_orig = max(1.0, ymax_orig - ymin_orig)

        # 1. Restringir ancho y alto entre el mínimo (Zoom In máx) y el 100% original (Zoom Out máx)
        min_w = min(w_orig, 6.0)
        min_h = min(h_orig, 3.0)
        w = max(min_w, min(w_orig, nx1 - nx0))
        h = max(min_h, min(h_orig, ny1 - ny0))

        # 2. Sujetar dentro de los bordes originales [xmin_orig, xmax_orig] y [ymin_orig, ymax_orig]
        cx = (nx0 + nx1) / 2.0
        cy = (ny0 + ny1) / 2.0
        x0 = cx - w / 2.0
        x1 = cx + w / 2.0
        y0 = cy - h / 2.0
        y1 = cy + h / 2.0

        if x0 < xmin_orig:
            x0 = xmin_orig
            x1 = xmin_orig + w
        if x1 > xmax_orig:
            x1 = xmax_orig
            x0 = xmax_orig - w

        if y0 < ymin_orig:
            y0 = ymin_orig
            y1 = ymin_orig + h
        if y1 > ymax_orig:
            y1 = ymax_orig
            y0 = ymax_orig - h

        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)

        # Actualizar dinámicamente los números del eje X según el nivel de zoom y desplazamiento
        max_time = getattr(ax, "_max_time", int(round(xmax_orig)))
        configurar_eje_tiempo_gantt(ax, x0, x1, max_time)

        # Si está en el 100% original, limpiar limites_zoom_actual; de lo contrario guardarlo
        if abs(w - w_orig) < 1e-4 and abs(h - h_orig) < 1e-4:
            self.limites_zoom_actual = None
        else:
            self.limites_zoom_actual = ((x0, x1), (y0, y1))

        self.canvas_gantt.draw_idle()

        # Actualizar dinámicamente las barras de scroll horizontal y vertical del Plano
        self._actualizar_scrollbars_gantt()

        # Sincronizar horizontalmente el apartado separado de la Cola de Procesos
        ax_c = self._obtener_ax_cola()
        if ax_c is not None and self.ultimo_resultado is not None:
            ax_c.set_xlim(x0, x1)
            configurar_eje_tiempo_cola(ax_c, x0, x1, max_time)
            self.canvas_cola.draw_idle()

    def _actualizar_encabezado_gantt(self):
        """Actualiza la cabecera del Plano de Gantt según el modo de interacción activo."""
        if getattr(self, "lbl_ayuda_zoom", None) is None:
            return
        if self.modo_interaccion == "lupa":
            self.lbl_ayuda_zoom.configure(
                text="🔍 Modo LUPA activo: Arrastra un rectángulo sobre el plano para acercar esa región.",
                text_color="#0F172A",
            )
        elif self.modo_interaccion == "mover":
            self.lbl_ayuda_zoom.configure(
                text="✋ Modo MOVER activo: Arrastra el plano dentro de sus bordes para desplazarte.",
                text_color="#0F172A",
            )
        else:
            self.lbl_ayuda_zoom.configure(
                text="📐 Plano de Gantt │ Barras de scroll, Shift+Rueda o Clic Derecho para zoom",
                text_color="#475569",
            )

    def _toggle_modo_lupa(self):
        if self.modo_interaccion == "lupa":
            self.modo_interaccion = None
            self.btn_lupa.configure(
                fg_color="#F8FAFC", text_color="#1E293B", hover_color="#F1F5F9", border_color="#CBD5E1"
            )
            self.canvas_gantt.get_tk_widget().configure(cursor="")
            self._actualizar_encabezado_gantt()
        else:
            self.modo_interaccion = "lupa"
            self.btn_lupa.configure(
                fg_color="#0F172A", text_color="#FFFFFF", hover_color="#1E293B", border_color="#0F172A"
            )
            self.btn_mover.configure(
                fg_color="#F8FAFC", text_color="#1E293B", hover_color="#F1F5F9", border_color="#CBD5E1"
            )
            self.canvas_gantt.get_tk_widget().configure(cursor="crosshair")
            self._actualizar_encabezado_gantt()

    def _toggle_modo_mover(self):
        if self.modo_interaccion == "mover":
            self.modo_interaccion = None
            self.btn_mover.configure(
                fg_color="#F8FAFC", text_color="#1E293B", hover_color="#F1F5F9", border_color="#CBD5E1"
            )
            self.canvas_gantt.get_tk_widget().configure(cursor="")
            self._actualizar_encabezado_gantt()
        else:
            self.modo_interaccion = "mover"
            self.btn_mover.configure(
                fg_color="#0F172A", text_color="#FFFFFF", hover_color="#1E293B", border_color="#0F172A"
            )
            self.btn_lupa.configure(
                fg_color="#F8FAFC", text_color="#1E293B", hover_color="#F1F5F9", border_color="#CBD5E1"
            )
            self.canvas_gantt.get_tk_widget().configure(cursor="fleur")
            self._actualizar_encabezado_gantt()

    def _aplicar_zoom_factor(self, factor: float, centro_x: float | None = None, centro_y: float | None = None):
        ax = self._obtener_ax_gantt()
        if ax is None:
            return
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        cx = (x0 + x1) / 2.0 if centro_x is None else centro_x
        cy = (y0 + y1) / 2.0 if centro_y is None else centro_y

        nuevo_w = (x1 - x0) * factor
        nuevo_h = (y1 - y0) * factor

        rx = (cx - x0) / (x1 - x0) if (x1 - x0) != 0 else 0.5
        ry = (cy - y0) / (y1 - y0) if (y1 - y0) != 0 else 0.5

        nx0 = cx - rx * nuevo_w
        nx1 = nx0 + nuevo_w
        ny0 = cy - ry * nuevo_h
        ny1 = ny0 + nuevo_h

        self._restringir_y_aplicar_limites(nx0, nx1, ny0, ny1)

    def _restablecer_vista_gantt(self):
        """Restablece el zoom al 100%, devuelve los scrollbars al inicio y desactiva lupa/mover."""
        self.limites_zoom_actual = None
        self.modo_interaccion = None
        self.btn_lupa.configure(
            fg_color="#F8FAFC", text_color="#1E293B", hover_color="#F1F5F9", border_color="#CBD5E1"
        )
        self.btn_mover.configure(
            fg_color="#F8FAFC", text_color="#1E293B", hover_color="#F1F5F9", border_color="#CBD5E1"
        )
        self.canvas_gantt.get_tk_widget().configure(cursor="")
        self._actualizar_encabezado_gantt()
        ax = self._obtener_ax_gantt()
        if ax is not None and hasattr(ax, "_limites_originales"):
            (xmin_orig, xmax_orig), (ymin_orig, ymax_orig) = ax._limites_originales
            self._restringir_y_aplicar_limites(xmin_orig, xmax_orig, ymin_orig, ymax_orig)
        else:
            self._actualizar_scrollbars_gantt()

    def _on_gantt_scroll(self, event):
        """
        Rueda del ratón:
          - Shift + Rueda: Desplazamiento horizontal rápido por la línea de tiempo.
          - Rueda normal : Acercar / Alejar (Zoom in / Zoom out) centrado en el cursor.
        """
        if event.inaxes is None:
            return

        is_shift = False
        if event.key and "shift" in event.key.lower():
            is_shift = True
        elif event.guiEvent and getattr(event.guiEvent, "state", 0) & 0x0001:
            is_shift = True

        if is_shift:
            ax = self._obtener_ax_gantt()
            if ax is not None:
                x0, x1 = ax.get_xlim()
                y0, y1 = ax.get_ylim()
                w = x1 - x0
                delta = (w * 0.10) if (event.button == "down" or (hasattr(event, "step") and event.step < 0)) else -(w * 0.10)
                self._restringir_y_aplicar_limites(x0 + delta, x1 + delta, y0, y1)
            return

        factor = 0.80 if event.button == "up" else 1.25
        self._aplicar_zoom_factor(factor, centro_x=event.xdata, centro_y=event.ydata)

    def _on_tk_shift_mousewheel(self, event):
        """Atajo nativo para Shift + Rueda del ratón en Windows."""
        ax = self._obtener_ax_gantt()
        if ax is None:
            return
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        w = x1 - x0
        delta = -(w * 0.10) if event.delta > 0 else (w * 0.10)
        self._restringir_y_aplicar_limites(x0 + delta, x1 + delta, y0, y1)

    def _on_gantt_press(self, event):
        """
        Presión del ratón:
          - Clic Derecho (3) o Botón Central (2): Arrastre (panning) inmediato sin cambiar de herramienta.
          - Clic Izquierdo (1) en modo 'mover' : Arrastre tradicional.
          - Clic Izquierdo (1) en modo 'lupa'  : Selección de rectángulo para zoom.
        """
        ax = self._obtener_ax_gantt()
        if ax is None or event.inaxes != ax or event.xdata is None or event.ydata is None:
            return

        if event.button in (2, 3) or (event.button == 1 and self.modo_interaccion == "mover"):
            self._drag_inicio = (event.x, event.y)
            self._drag_limites_ini = (ax.get_xlim(), ax.get_ylim())
            self._drag_boton = event.button
            self.canvas_gantt.get_tk_widget().configure(cursor="fleur")
        elif event.button == 1 and self.modo_interaccion == "lupa":
            self._drag_inicio = (event.xdata, event.ydata)
            self._drag_boton = 1
            if self._rect_lupa is not None:
                try:
                    self._rect_lupa.remove()
                except Exception:
                    pass
            self._rect_lupa = Rectangle(
                (event.xdata, event.ydata), 0, 0,
                facecolor="#3B82F6", alpha=0.18,
                edgecolor="#1D4ED8", linestyle="--", linewidth=1.5, zorder=10,
            )
            ax.add_patch(self._rect_lupa)
            self.canvas_gantt.draw_idle()

    def _on_gantt_motion(self, event):
        if self._drag_inicio is None:
            return
        ax = self._obtener_ax_gantt()
        if ax is None:
            return

        if self._drag_limites_ini is not None:
            (x0, x1), (y0, y1) = self._drag_limites_ini
            bbox = ax.bbox
            if bbox.width > 0 and bbox.height > 0:
                dx = (event.x - self._drag_inicio[0]) * (x1 - x0) / bbox.width
                dy = (event.y - self._drag_inicio[1]) * (y1 - y0) / bbox.height
                self._restringir_y_aplicar_limites(x0 - dx, x1 - dx, y0 - dy, y1 - dy)
        elif self.modo_interaccion == "lupa" and getattr(self, "_drag_boton", None) == 1 and self._rect_lupa is not None and event.xdata is not None and event.ydata is not None:
            x_ini, y_ini = self._drag_inicio
            x_min = min(x_ini, event.xdata)
            y_min = min(y_ini, event.ydata)
            w = abs(event.xdata - x_ini)
            h = abs(event.ydata - y_ini)
            self._rect_lupa.set_xy((x_min, y_min))
            self._rect_lupa.set_width(w)
            self._rect_lupa.set_height(h)
            self.canvas_gantt.draw_idle()

    def _on_gantt_release(self, event):
        if self._drag_inicio is None:
            return
        ax = self._obtener_ax_gantt()

        if self._drag_limites_ini is not None:
            self._drag_inicio = None
            self._drag_limites_ini = None
            self._drag_boton = None
            if self.modo_interaccion == "lupa":
                self.canvas_gantt.get_tk_widget().configure(cursor="crosshair")
            elif self.modo_interaccion == "mover":
                self.canvas_gantt.get_tk_widget().configure(cursor="fleur")
            else:
                self.canvas_gantt.get_tk_widget().configure(cursor="")
            return

        if self.modo_interaccion == "lupa" and ax is not None and getattr(self, "_drag_boton", None) == 1:
            x_ini, y_ini = self._drag_inicio
            if self._rect_lupa is not None:
                try:
                    self._rect_lupa.remove()
                except Exception:
                    pass
                self._rect_lupa = None

            if event.xdata is not None and event.ydata is not None:
                x0, x1 = sorted([x_ini, event.xdata])
                y0, y1 = sorted([y_ini, event.ydata])
                if (x1 - x0) >= 0.8 and (y1 - y0) >= 0.6:
                    self._restringir_y_aplicar_limites(x0, x1, y0, y1)
                else:
                    self.canvas_gantt.draw_idle()

        self._drag_inicio = None
        self._drag_limites_ini = None
        self._drag_boton = None

    def _actualizar_scrollbars_gantt(self):
        """Actualiza la posición y tamaño del control deslizante de los scrollbars según el zoom actual."""
        ax = self._obtener_ax_gantt()
        if ax is None:
            return

        if hasattr(ax, "_limites_originales"):
            (xmin_orig, xmax_orig), (ymin_orig, ymax_orig) = ax._limites_originales
        else:
            xmin_orig, xmax_orig = ax.get_xlim()
            ymin_orig, ymax_orig = ax.get_ylim()

        w_orig = max(1.0, xmax_orig - xmin_orig)
        h_orig = max(1.0, ymax_orig - ymin_orig)
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()

        # Horizontal: de 0.0 (inicio del tiempo) a 1.0 (final del tiempo)
        first_x = max(0.0, min(1.0, (x0 - xmin_orig) / w_orig))
        last_x = max(0.0, min(1.0, (x1 - xmin_orig) / w_orig))
        if hasattr(self, "sb_gantt_h"):
            self.sb_gantt_h.set(first_x, last_x)

        # Vertical: 0.0 arriba (procesos superiores P0...) y 1.0 abajo (procesos inferiores Pn)
        first_y = max(0.0, min(1.0, (ymax_orig - y1) / h_orig))
        last_y = max(0.0, min(1.0, (ymax_orig - y0) / h_orig))
        if hasattr(self, "sb_gantt_v"):
            self.sb_gantt_v.set(first_y, last_y)

    def _on_scroll_h(self, *args):
        """Maneja el desplazamiento horizontal del Plano de Gantt desde el scrollbar inferior."""
        ax = self._obtener_ax_gantt()
        if ax is None:
            return
        if hasattr(ax, "_limites_originales"):
            (xmin_orig, xmax_orig), _ = ax._limites_originales
        else:
            xmin_orig, xmax_orig = ax.get_xlim()

        w_orig = max(1.0, xmax_orig - xmin_orig)
        x0, x1 = ax.get_xlim()
        w = x1 - x0

        if args[0] == "moveto":
            fraction = float(args[1])
            new_x0 = xmin_orig + fraction * w_orig
            new_x1 = new_x0 + w
        elif args[0] == "scroll":
            count = int(args[1])
            step = (0.5 * w) if (len(args) > 2 and args[2] == "pages") else (0.1 * w)
            new_x0 = x0 + count * step
            new_x1 = new_x0 + w
        else:
            return

        y0, y1 = ax.get_ylim()
        self._restringir_y_aplicar_limites(new_x0, new_x1, y0, y1)

    def _on_scroll_v(self, *args):
        """Maneja el desplazamiento vertical del Plano de Gantt desde el scrollbar derecho."""
        ax = self._obtener_ax_gantt()
        if ax is None:
            return
        if hasattr(ax, "_limites_originales"):
            _, (ymin_orig, ymax_orig) = ax._limites_originales
        else:
            _, (ymin_orig, ymax_orig) = (0, ax.get_ylim())

        h_orig = max(1.0, ymax_orig - ymin_orig)
        y0, y1 = ax.get_ylim()
        h = y1 - y0

        if args[0] == "moveto":
            fraction = float(args[1])
            new_y1 = ymax_orig - fraction * h_orig
            new_y0 = new_y1 - h
        elif args[0] == "scroll":
            count = int(args[1])
            step = (0.5 * h) if (len(args) > 2 and args[2] == "pages") else (0.15 * h)
            new_y0 = y0 - count * step
            new_y1 = new_y0 + h
        else:
            return

        x0, x1 = ax.get_xlim()
        self._restringir_y_aplicar_limites(x0, x1, new_y0, new_y1)

    # ═══════════════════════════════════════════════════════════
    #  GESTIÓN DE PROCESOS Y ACTUALIZACIÓN EN VIVO DEL PLANO
    # ═══════════════════════════════════════════════════════════
    def _on_algo_change(self, _=None):
        self._toggle_quantum()
        algo = self.combo_algo.get()
        self._actualizar_encabezado_gantt()
        self._actualizar_fundamento_teorico(algo, self.ultimo_resultado)
        if not self.anim_corriendo and self.ultimo_resultado is None:
            self._redibujar_vista_previa()

    def _toggle_quantum(self):
        if self.combo_algo.get() == "Round Robin (Expulsivo)":
            self.label_quantum.configure(text_color="#1E293B")
            self.entry_quantum.configure(state="normal")
        else:
            self.label_quantum.configure(text_color="#94A3B8")
            self.entry_quantum.configure(state="disabled")

    def _actualizar_contadores_y_previa(self):
        self._cancelar_animacion()
        self.ultimo_resultado = None
        self.limites_zoom_actual = None
        self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#0F172A")
        n = len(self.procesos)
        suma_ts = sum(int(p["rafaga"]) for p in self.procesos)

        self.lbl_titulo_cola.configure(text=f"Cola de Entrada (#P = {n}):")
        self.lbl_titulo_cuadro.configure(text=f"📋 Cuadro de Resultados por Proceso (#P = {n})")

        for item in self.tree_cola.get_children():
            self.tree_cola.delete(item)
        for idx, p in enumerate(self.procesos, start=1):
            _c_fill, c_borde = PALETA_PROCESOS[(idx - 1) % len(PALETA_PROCESOS)]
            self.tree_cola.tag_configure(p["nombre"], foreground=c_borde)
            self.tree_cola.insert(
                "", "end", values=(f"● {p['nombre']}", p["llegada"], p["rafaga"]), tags=(p["nombre"],)
            )

        # Poblar el cuadro inferior con los datos de entrada (T.F., T.R., T.E. pendientes "--")
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        for idx, p in enumerate(self.procesos):
            _c_fill, c_borde = PALETA_PROCESOS[idx % len(PALETA_PROCESOS)]
            self.tree_resultados.tag_configure(p["nombre"], foreground=c_borde)
            self.tree_resultados.insert(
                "", "end", values=(f"● {p['nombre']}", p["llegada"], p["rafaga"], "--", "--", "--"), tags=(p["nombre"],)
            )

        self._redibujar_vista_previa()
        dibujar_panel_formulas(self.fig_math, None)
        self.canvas_math.draw()
        self._actualizar_encabezado_gantt()

        if n > 0:
            self.badge_estado.configure(text=" ● LISTO ", fg_color="#DCFCE7", text_color="#166534")
            self.lbl_cpu_vivo.configure(
                text=f"#P = {n} procesos (Σ T.S. = {suma_ts} u.t.). Presiona '▶ Iniciar' o '⏭ Completo'."
            )
        else:
            self.badge_estado.configure(text=" ● EN ESPERA ", fg_color="#F1F5F9", text_color="#475569")
            self.lbl_cpu_vivo.configure(
                text="Agrega procesos y presiona '▶ Iniciar' para simular."
            )

    def _redibujar_vista_previa(self):
        dibujar_plano_vacio_o_previa(self.fig_gantt, self.procesos, self.combo_algo.get())
        self.canvas_gantt.draw()
        dibujar_apartado_cola(self.fig_cola, self.procesos, None)
        self.canvas_cola.draw()
        self._actualizar_scrollbars_gantt()

    def _agregar_proceso(self):
        nombre = self.entry_nombre.get().strip()
        llegada = self.entry_llegada.get().strip()
        rafaga = self.entry_rafaga.get().strip()

        if not nombre:
            while any(p["nombre"] == f"P{self.contador_procesos}" for p in self.procesos):
                self.contador_procesos += 1
            nombre = f"P{self.contador_procesos}"
            self.contador_procesos += 1

        if any(p["nombre"] == nombre for p in self.procesos):
            messagebox.showerror("Error", f"Ya existe un proceso llamado '{nombre}'.")
            return

        try:
            llegada_int = int(llegada)
            if llegada_int < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El Tiempo de Llegada (T.LL) debe ser un entero ≥ 0.")
            return

        try:
            rafaga_int = int(rafaga)
            if rafaga_int <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El Tiempo de Servicio (T.S.) debe ser un entero > 0.")
            return

        self.procesos.append({"nombre": nombre, "llegada": llegada_int, "rafaga": rafaga_int})
        self._actualizar_contadores_y_previa()

        self.entry_nombre.delete(0, "end")
        self.entry_llegada.delete(0, "end")
        self.entry_rafaga.delete(0, "end")
        self.entry_nombre.focus()

    def _eliminar_seleccionado(self):
        seleccion = self.tree_cola.selection()
        if not seleccion:
            messagebox.showinfo("Aviso", "Selecciona un proceso de la Cola de Entrada para quitarlo.")
            return
        nombres_a_quitar = set()
        for item_id in seleccion:
            vals = self.tree_cola.item(item_id, "values")
            if vals and len(vals) >= 1:
                nom = str(vals[0]).replace("●", "").strip()
                if nom:
                    nombres_a_quitar.add(nom)
        self.procesos = [p for p in self.procesos if p["nombre"] not in nombres_a_quitar]
        self._actualizar_contadores_y_previa()

    def _vaciar_cola(self):
        self.procesos.clear()
        self.contador_procesos = 0
        self._actualizar_contadores_y_previa()
        self._actualizar_fundamento_teorico(self.combo_algo.get(), None)

    def _mostrar_guia_y_seleccionar_archivo(self):
        """Muestra una ventana modal con el formato de archivo requerido antes de abrir el explorador."""
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Formato de Archivo TXT Admitido — Planificación de Procesos")
        dialogo.geometry("540x440")
        dialogo.resizable(False, False)
        dialogo.configure(fg_color="#FFFFFF")
        dialogo.transient(self.winfo_toplevel())
        dialogo.grab_set()

        # Centrar diálogo respecto a la ventana principal
        try:
            x = self.winfo_toplevel().winfo_x() + 200
            y = self.winfo_toplevel().winfo_y() + 120
            dialogo.geometry(f"+{x}+{y}")
        except Exception:
            pass

        # Encabezado
        frame_head = ctk.CTkFrame(dialogo, fg_color="#F8FAFC", corner_radius=0, height=52)
        frame_head.pack(fill="x")
        ctk.CTkLabel(
            frame_head,
            text="📄  Formato Requerido para Cargar Procesos (.txt)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1E293B",
        ).pack(side="left", padx=16, pady=12)

        body = ctk.CTkFrame(dialogo, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=12)

        ctk.CTkLabel(
            body,
            text="Para que el simulador reconozca los procesos, cada línea del archivo\n"
                 "debe contener los siguientes 3 campos en orden:",
            font=ctk.CTkFont(size=12),
            text_color="#334155",
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        # Cuadro de sintaxis
        frame_sintaxis = ctk.CTkFrame(
            body, fg_color="#EFF6FF", border_width=1, border_color="#BFDBFE", corner_radius=6
        )
        frame_sintaxis.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            frame_sintaxis,
            text="Estructura:  Nombre_Proceso,  Tiempo_Llegada,  Tiempo_Servicio\n"
                 "            (PID)           (T.LL ≥ 0)       (T.S. > 0)",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#1D4ED8",
            justify="left",
        ).pack(padx=12, pady=8, anchor="w")

        # Puntos clave
        puntos = (
            "• Separadores válidos: Coma (,), punto y coma (;), espacio o tabulación.\n"
            "• Líneas de comentario: Aquellas que comiencen con '#' serán ignoradas.\n"
            "• T.LL: Tiempo de llegada (entero mayor o igual a 0).\n"
            "• T.S.: Tiempo de servicio / ráfaga de CPU (entero mayor a 0)."
        )
        ctk.CTkLabel(
            body, text=puntos, font=ctk.CTkFont(size=11), text_color="#475569", justify="left"
        ).pack(anchor="w", pady=(0, 8))

        # Ejemplo en caja de código
        ctk.CTkLabel(
            body, text="Ejemplo válido de contenido del archivo .txt:",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#334155"
        ).pack(anchor="w")

        txt_ejemplo = (
            "# Archivo de ejemplo con 4 procesos\n"
            "P0, 0, 7\n"
            "P1, 2, 4\n"
            "P2, 4, 1\n"
            "P3, 5, 4"
        )
        caja_ej = ctk.CTkTextbox(body, height=75, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#F8FAFC", border_width=1, border_color="#CBD5E1")
        caja_ej.pack(fill="x", pady=(3, 12))
        caja_ej.insert("1.0", txt_ejemplo)
        caja_ej.configure(state="disabled")

        # Botones inferiores
        frame_acciones = ctk.CTkFrame(dialogo, fg_color="#F8FAFC", height=50, corner_radius=0)
        frame_acciones.pack(fill="x", side="bottom")

        def _al_elegir():
            dialogo.destroy()
            self._procesar_archivo_seleccionado()

        ctk.CTkButton(
            frame_acciones,
            text="📂  Seleccionar archivo .txt...",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB", hover_color="#1D4ED8", text_color="#FFFFFF",
            width=210, height=32,
            command=_al_elegir,
        ).pack(side="right", padx=16, pady=8)

        ctk.CTkButton(
            frame_acciones,
            text="Cancelar",
            font=ctk.CTkFont(size=12),
            fg_color="#E2E8F0", hover_color="#CBD5E1", text_color="#334155",
            width=90, height=32,
            command=dialogo.destroy,
        ).pack(side="right", padx=6, pady=8)

    def _cargar_desde_archivo(self):
        """Muestra el formato admitido y permite al usuario elegir su archivo .txt."""
        self._mostrar_guia_y_seleccionar_archivo()

    def _procesar_archivo_seleccionado(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de procesos (.txt)",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
            initialdir=self.carpeta_base,
        )
        if not filepath:
            return

        errores = []
        procesos_cargados = 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for num_linea, linea in enumerate(f, start=1):
                    linea = linea.strip()
                    if not linea or linea.startswith("#"):
                        continue
                    if "," in linea:
                        partes = [p.strip() for p in linea.split(",")]
                    elif ";" in linea:
                        partes = [p.strip() for p in linea.split(";")]
                    elif "\t" in linea:
                        partes = [p.strip() for p in linea.split("\t")]
                    else:
                        partes = linea.split()

                    if len(partes) < 3:
                        errores.append(f"Línea {num_linea}: formato incompleto (esperaba Nombre, T.LL, T.S.)")
                        continue

                    nombre = partes[0]
                    try:
                        llegada = int(partes[1])
                        rafaga = int(partes[2])
                    except ValueError:
                        errores.append(f"Línea {num_linea}: T.LL o T.S. no son enteros válidos")
                        continue

                    if llegada < 0 or rafaga <= 0:
                        errores.append(f"Línea {num_linea}: T.LL debe ser ≥ 0 y T.S. > 0")
                        continue

                    if any(p["nombre"] == nombre for p in self.procesos):
                        errores.append(f"Línea {num_linea}: proceso '{nombre}' ya existe en la cola")
                        continue

                    self.procesos.append({"nombre": nombre, "llegada": llegada, "rafaga": rafaga})
                    procesos_cargados += 1
        except Exception as e:
            messagebox.showerror("Error de lectura", f"No se pudo leer el archivo:\n{e}")
            return

        self._actualizar_contadores_y_previa()
        msg = f"✅ {procesos_cargados} proceso(s) cargado(s) exitosamente.\nTotal en cola (#P) = {len(self.procesos)}."
        if errores:
            msg += f"\n\n⚠ {len(errores)} aviso(s):\n" + "\n".join(errores[:6])
        messagebox.showinfo("Carga de Archivo TXT", msg)

    # ═══════════════════════════════════════════════════════════
    #  SIMULACIÓN INTERACTIVA PASO A PASO (INICIAR/CONTINUAR / PAUSAR / COMPLETO / LIMPIAR)
    # ═══════════════════════════════════════════════════════════
    def _calcular_resultado_actual(self) -> Resultado | None:
        if not self.procesos:
            messagebox.showwarning("Aviso", "No hay procesos en la cola. Agrega o carga procesos primero.")
            return None

        algo = self.combo_algo.get()
        quantum = 2
        if algo == "Round Robin (Expulsivo)":
            try:
                quantum = int(self.entry_quantum.get().strip())
                if quantum <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "El Quantum (q) debe ser un entero > 0.")
                return None

        try:
            return ejecutar(algo, self.procesos, quantum)
        except Exception as e:
            messagebox.showerror("Error en Simulación", str(e))
            return None

    def iniciar_o_reanudar_simulacion(self):
        """Inicia la simulación paso a paso desde t=0 o la continúa si estaba en pausa."""
        if self.anim_corriendo and self.anim_pausada:
            self.anim_pausada = False
            self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534", border_color="#86EFAC")
            self.badge_estado.configure(text=" ● EJECUTANDO ", fg_color="#059669", text_color="#FFFFFF")
            self._actualizar_encabezado_gantt()
            self._avanzar_paso_animacion()
            return

        resultado = self._calcular_resultado_actual()
        if resultado is None:
            return

        self._cancelar_animacion()
        self.ultimo_resultado = resultado
        self.anim_corriendo = True
        self.anim_pausada = False
        self.paso_actual = 0

        self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534", border_color="#86EFAC")
        self.badge_estado.configure(text=" ● EJECUTANDO ", fg_color="#059669", text_color="#FFFFFF")
        self._actualizar_encabezado_gantt()
        self._actualizar_fundamento_teorico(self.combo_algo.get(), resultado)
        self._avanzar_paso_animacion()

    def pausar_simulacion(self):
        """Pausa inmediatamente el avance del reloj y cambia el botón Iniciar a Continuar."""
        if self.anim_corriendo and not self.anim_pausada:
            self.anim_pausada = True
            if self.after_id is not None:
                try:
                    self.after_cancel(self.after_id)
                except Exception:
                    pass
                self.after_id = None
            self.btn_iniciar.configure(text="▶ Continuar", fg_color="#FEF3C7", hover_color="#FDE68A", text_color="#92400E", border_color="#FCD34D")
            self.badge_estado.configure(text=" ⏸ PAUSADO ", fg_color="#FEF3C7", text_color="#92400E")
            self._actualizar_encabezado_gantt()
            self.lbl_cpu_vivo.configure(
                text=f"Pausado en t = {self.paso_actual} u.t. Presiona '▶ Continuar' para seguir."
            )

    def mostrar_resultado_completo(self):
        """Muestra de forma inmediata el plano completo, la cola, la tabla y las fórmulas finales."""
        resultado = self._calcular_resultado_actual()
        if resultado is None:
            return
        self._cancelar_animacion()
        self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534", border_color="#86EFAC")
        self.ultimo_resultado = resultado
        self.paso_actual = resultado.tiempo_total
        self._renderizar_estado_paso(resultado, resultado.tiempo_total, finalizado=True)
        self._actualizar_encabezado_gantt()
        self._actualizar_fundamento_teorico(self.combo_algo.get(), resultado)

    def limpiar_simulacion(self):
        """
        Detiene cualquier animación activa y limpia el plano, la cola y el cuadro
        regresándolos al estado inicial de vista previa SIN auto-iniciar.
        """
        self._cancelar_animacion()
        self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#DCFCE7", hover_color="#BBF7D0", text_color="#166534", border_color="#86EFAC")
        self.ultimo_resultado = None
        self.limites_zoom_actual = None
        self.paso_actual = 0

        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)
        for idx, p in enumerate(self.procesos):
            _c_fill, c_borde = PALETA_PROCESOS[idx % len(PALETA_PROCESOS)]
            self.tree_resultados.tag_configure(p["nombre"], foreground=c_borde)
            self.tree_resultados.insert(
                "", "end", values=(f"● {p['nombre']}", p["llegada"], p["rafaga"], "--", "--", "--"), tags=(p["nombre"],)
            )

        self._redibujar_vista_previa()
        dibujar_panel_formulas(self.fig_math, None)
        self.canvas_math.draw()
        self._actualizar_encabezado_gantt()

        n = len(self.procesos)
        self.badge_estado.configure(
            text=" ● LISTO " if n > 0 else " ● EN ESPERA ",
            fg_color="#DCFCE7" if n > 0 else "#F1F5F9",
            text_color="#166534" if n > 0 else "#475569",
        )
        self.lbl_cpu_vivo.configure(
            text="Simulación limpia. Presiona '▶ Iniciar' cuando desees ejecutarla."
        )

    def _cancelar_animacion(self):
        self.anim_corriendo = False
        self.anim_pausada = False
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def _avanzar_paso_animacion(self):
        if not self.anim_corriendo or self.anim_pausada or self.ultimo_resultado is None:
            return

        res = self.ultimo_resultado
        self.paso_actual += 1

        if self.paso_actual >= res.tiempo_total:
            self.paso_actual = res.tiempo_total
            self.anim_corriendo = False
            self.btn_iniciar.configure(text="▶ Iniciar", fg_color="#F8FAFC", hover_color="#F1F5F9", text_color="#0F172A")
            self._renderizar_estado_paso(res, self.paso_actual, finalizado=True)
            return

        self._renderizar_estado_paso(res, self.paso_actual, finalizado=False)

        vel = max(0.5, float(self.slider_vel.get()))
        delay_ms = int(420 / vel)
        self.after_id = self.after(delay_ms, self._avanzar_paso_animacion)

    def _renderizar_estado_paso(self, res: Resultado, t_actual: int, finalizado: bool):
        dibujar_plano_gantt(
            self.fig_gantt,
            self.procesos,
            res,
            paso_actual=None if finalizado else t_actual,
            limites_previos=self.limites_zoom_actual,
        )
        self.canvas_gantt.draw()
        self._actualizar_scrollbars_gantt()

        xlim_sync = self.limites_zoom_actual[0] if self.limites_zoom_actual is not None else None
        dibujar_apartado_cola(
            self.fig_cola,
            self.procesos,
            res,
            paso_actual=None if finalizado else t_actual,
            xlim_sincronizado=xlim_sync,
        )
        self.canvas_cola.draw()

        # Actualizar el Cuadro de Resultados mostrando los valores de los procesos que ya finalizaron en <= t_actual
        for item in self.tree_resultados.get_children():
            self.tree_resultados.delete(item)

        for idx_f, fila in enumerate(res.tabla):
            _c_fill, c_borde = PALETA_PROCESOS[idx_f % len(PALETA_PROCESOS)]
            self.tree_resultados.tag_configure(fila["nombre"], foreground=c_borde)
            if finalizado or fila["fin"] <= t_actual:
                vals = (f"● {fila['nombre']}", fila["llegada"], fila["rafaga"], fila["fin"], fila["tr"], fila["te"])
            else:
                vals = (f"● {fila['nombre']}", fila["llegada"], fila["rafaga"], "...", "...", "...")
            self.tree_resultados.insert("", "end", values=vals, tags=(fila["nombre"],))

        self._actualizar_encabezado_gantt()

        if finalizado:
            dibujar_panel_formulas(self.fig_math, res)
            self.canvas_math.draw()
            self.badge_estado.configure(text=" SIMULACIÓN COMPLETADA ", fg_color="#059669", text_color="#FFFFFF")
            self.lbl_cpu_vivo.configure(
                text=f"Completado (#P = {res.num_procesos})  │  TR̄ = {fmt_num(res.promedio_tr)}  │  TĒ = {fmt_num(res.promedio_te)}"
            )
        else:
            self.badge_estado.configure(text=" ● EJECUTANDO ", fg_color="#059669", text_color="#FFFFFF")
            t_prev = max(0, t_actual - 1)
            cola_t = res.colas_por_tiempo.get(t_prev, ["IDLE"])
            en_cpu = cola_t[0]
            espera_lista = cola_t[1:]
            if not espera_lista:
                en_espera = "Vacía"
            elif len(espera_lista) <= 4:
                en_espera = ", ".join(espera_lista)
            else:
                en_espera = ", ".join(espera_lista[:4]) + f", ... (+{len(espera_lista) - 4})"
            self.lbl_cpu_vivo.configure(
                text=f"Reloj t = {t_actual}/{res.tiempo_total} u.t.  │  CPU: {en_cpu}  │  Cola: [{en_espera}]"
            )

    # ═══════════════════════════════════════════════════════════
    #  FUNDAMENTO TEÓRICO, COMPARACIÓN Y EXPORTACIÓN
    # ═══════════════════════════════════════════════════════════
    def _actualizar_fundamento_teorico(self, algo: str, resultado: Resultado | None = None):
        info = INFO_TEORICA_POLITICAS.get(algo, {})
        texto = (
            f"• Política: {info.get('nombre_completo', algo)}\n"
            f"• Clasificación: {info.get('tipo', '')}\n"
            f"• Criterio de Selección: {info.get('criterio', '')}\n"
            f"• Ventajas: {info.get('ventajas', '')}\n"
            f"• Desventajas: {info.get('desventajas', '')}\n"
            f"• Fórmulas: {info.get('formulas', '')}"
        )
        self.txt_teoria.configure(state="normal")
        self.txt_teoria.delete("1.0", "end")
        self.txt_teoria.insert("1.0", texto)
        self.txt_teoria.configure(state="disabled")

        self.txt_traza.configure(state="normal")
        self.txt_traza.delete("1.0", "end")
        if resultado is None:
            self.txt_traza.insert(
                "1.0",
                "Inicia la simulación para consultar aquí el registro cronológico instante por instante.",
            )
        else:
            lineas = [f"═══ REGISTRO CRONOLÓGICO — {resultado.algoritmo} (#P = {resultado.num_procesos}) ═══\n"]
            for paso in resultado.traza:
                lineas.append(f"• {paso}")
            self.txt_traza.insert("1.0", "\n".join(lineas))
        self.txt_traza.configure(state="disabled")

    def _comparar_algoritmos(self):
        if not self.procesos:
            messagebox.showwarning("Aviso", "No hay procesos en la cola para comparar.")
            return

        quantum = 2
        try:
            q_str = self.entry_quantum.get().strip()
            if q_str:
                quantum = max(1, int(q_str))
        except ValueError:
            pass

        resultados = comparar_todos(self.procesos, quantum)

        win = ctk.CTkToplevel(self)
        win.title(f"Comparativa de las 4 Políticas (#P = {len(self.procesos)} procesos)")
        win.geometry("760x380")
        win.configure(fg_color="#F4F5F7")
        win.attributes("-topmost", True)

        frame = ctk.CTkFrame(
            win, fg_color="#FFFFFF", corner_radius=10,
            border_width=1, border_color="#CBD5E1",
        )
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            frame,
            text=f"📊 Comparativa de las 4 Políticas de Planificación (#P = {len(self.procesos)} procesos)",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#1E293B",
        ).pack(pady=(12, 4))

        mejor_algo = min(resultados.items(), key=lambda kv: kv[1].promedio_te)[0]
        ctk.CTkLabel(
            frame,
            text=f"🏆 Menor Tiempo de Espera Promedio (TĒ): {mejor_algo}",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#15803D",
        ).pack(pady=(0, 10))

        headers = ctk.CTkFrame(frame, fg_color="#E2E8F0", corner_radius=6)
        headers.pack(fill="x", padx=14, pady=4)
        cols = [
            ("Política de Planificación", 220, "w"),
            ("#P", 60, "center"),
            ("Σ T.R.", 80, "center"),
            ("Promedio TR̄", 120, "center"),
            ("Σ T.E.", 80, "center"),
            ("Promedio TĒ", 120, "center"),
        ]
        for th, wh, anc in cols:
            ctk.CTkLabel(
                headers, text=th, width=wh, anchor=anc,
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#0F172A",
            ).pack(side="left", padx=6, pady=6)

        for algo, res in resultados.items():
            es_mejor = algo == mejor_algo
            row = ctk.CTkFrame(
                frame,
                fg_color="#DCFCE7" if es_mejor else "#F8FAFC",
                corner_radius=6,
                border_width=1,
                border_color="#86EFAC" if es_mejor else "#E2E8F0",
            )
            row.pack(fill="x", padx=14, pady=3)
            nom = f"{algo} (q={quantum})" if "Round Robin" in algo else algo
            for val, wc, anc in [
                (nom, 220, "w"),
                (str(res.num_procesos), 60, "center"),
                (str(res.suma_tr), 80, "center"),
                (fmt_num(res.promedio_tr), 120, "center"),
                (str(res.suma_te), 80, "center"),
                (fmt_num(res.promedio_te), 120, "center"),
            ]:
                ctk.CTkLabel(
                    row, text=val, width=wc, anchor=anc,
                    font=ctk.CTkFont(size=12, weight="bold" if es_mejor else "normal"),
                    text_color="#166534" if es_mejor else "#1E293B",
                ).pack(side="left", padx=6, pady=7)

    def _exportar_png(self):
        if self.ultimo_resultado is None:
            messagebox.showwarning("Aviso", "Primero ejecuta una simulación para exportar el plano.")
            return
        filepath = filedialog.asksaveasfilename(
            title="Guardar Plano de Gantt como Imagen PNG",
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png")],
            initialfile=f"plano_{self.ultimo_resultado.algoritmo.split()[0].lower()}.png",
            initialdir=self.carpeta_base,
        )
        if not filepath:
            return
        try:
            self.fig_gantt.savefig(filepath, dpi=220, bbox_inches="tight", facecolor="#FFFFFF")
            messagebox.showinfo("Exportación Exitosa", f"✅ Imagen guardada en:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e))
