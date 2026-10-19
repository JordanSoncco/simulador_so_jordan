"""
============================================================================
 SIMULADOR DE SISTEMAS OPERATIVOS — Punto de Entrada Principal (Tema Claro)
 Autor : Jordan Oliber Soncco Machaca
 Curso : Sistemas Operativos - Grupo A
 Docente: Ing. Donia Alizandra Ruelas Acero
 Universidad Nacional del Altiplano (UNA Puno)
============================================================================

 Estructura Modular del Proyecto:
   - planificacion/ : Módulo 1 — Políticas de Planificación (FCFS, SJF, SRTF, RR)
   - concurrencia/  : Módulo 2 — Los 5 Problemas Clásicos de Concurrencia
============================================================================
"""

from __future__ import annotations
import os
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from planificacion import PanelPlanificacion
from concurrencia import PanelConcurrencia

# ─────────────────────────────────────────────────────────────
#  Configuración global en Tema Claro (Light Mode)
# ─────────────────────────────────────────────────────────────
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class SimuladorApp(ctk.CTk):
    """Ventana principal del Simulador de Sistemas Operativos."""

    def __init__(self):
        super().__init__()

        self.title("Simulador de Sistemas Operativos: Planificación y Concurrencia — Jordan Soncco | UNA Puno")
        self.geometry("1400x780")
        self.minsize(1120, 680)
        self.configure(fg_color="#EEF2F6")
        try:
            self.state("zoomed")
        except Exception:
            pass

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._crear_encabezado()
        self._crear_pestanas_principales()
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    def _crear_encabezado(self):
        header = ctk.CTkFrame(
            self, fg_color="#0F172A", corner_radius=0, height=58,
            border_width=0,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        frame_tit = ctk.CTkFrame(header, fg_color="transparent")
        frame_tit.grid(row=0, column=0, padx=16, pady=7, sticky="w")

        f_tit_top = ctk.CTkFrame(frame_tit, fg_color="transparent")
        f_tit_top.pack(anchor="w")

        ctk.CTkLabel(
            f_tit_top,
            text="SIMULADOR DE SISTEMAS OPERATIVOS — PRODUCTO UNIDAD I",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#F8FAFC",
        ).pack(side="left")

        ctk.CTkLabel(
            f_tit_top,
            text=" UNA PUNO ",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color="#1E293B",
            text_color="#38BDF8",
            corner_radius=4,
        ).pack(side="left", padx=8)

        ctk.CTkLabel(
            frame_tit,
            text="Universidad Nacional del Altiplano • Escuela Profesional de Ingeniería de Sistemas • Docente: Ing. Donia Alizandra Ruelas Acero",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#94A3B8",
        ).pack(anchor="w")

        frame_autor = ctk.CTkFrame(
            header, fg_color="#1E293B", corner_radius=8,
            border_width=1, border_color="#334155",
        )
        frame_autor.grid(row=0, column=2, padx=16, pady=8, sticky="e")

        ctk.CTkLabel(
            frame_autor,
            text="Autor: Jordan Oliber Soncco Machaca",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#F8FAFC",
        ).pack(anchor="e", padx=10, pady=(4, 0))

        ctk.CTkLabel(
            frame_autor,
            text="Grupo A • Semestre V",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#38BDF8",
        ).pack(anchor="e", padx=10, pady=(0, 4))

    def _crear_pestanas_principales(self):
        self.tabs_principales = ctk.CTkTabview(
            self,
            fg_color="#EEF2F6",
            segmented_button_fg_color="#E2E8F0",
            segmented_button_selected_color="#0F172A",
            segmented_button_selected_hover_color="#1E293B",
            segmented_button_unselected_color="#F1F5F9",
            segmented_button_unselected_hover_color="#E2E8F0",
            text_color="#FFFFFF",
            text_color_disabled="#64748B",
            corner_radius=10,
            border_width=1,
            border_color="#E2E8F0",
            command=self._actualizar_contraste_pestanas,
        )
        self.tabs_principales.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 10))

        self.tab_planificacion = self.tabs_principales.add(
            "  📊  MÓDULO 1: POLÍTICAS DE PLANIFICACIÓN DE PROCESOS  "
        )
        self.tab_concurrencia = self.tabs_principales.add(
            "  🔄  MÓDULO 2: PROBLEMAS DE CONCURRENCIA (SINCRONIZACIÓN)  "
        )
        self._actualizar_contraste_pestanas()

        carpeta_base = os.path.dirname(os.path.abspath(__file__))

        self.tab_planificacion.grid_columnconfigure(0, weight=1)
        self.tab_planificacion.grid_rowconfigure(0, weight=1)
        self.panel_planificacion = PanelPlanificacion(self.tab_planificacion, carpeta_base)
        self.panel_planificacion.grid(row=0, column=0, sticky="nsew")

        self.tab_concurrencia.grid_columnconfigure(0, weight=1)
        self.tab_concurrencia.grid_rowconfigure(0, weight=1)
        self.panel_concurrencia = PanelConcurrencia(self.tab_concurrencia)
        self.panel_concurrencia.grid(row=0, column=0, sticky="nsew")

    def _actualizar_contraste_pestanas(self):
        """Asegura que la pestaña activa tenga Dark Slate #0F172A (como Imagen 1) y la inactiva fondo sutil."""
        try:
            actual = self.tabs_principales.get()
            seg_btn = self.tabs_principales._segmented_button
            seg_btn.configure(font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
            for nombre, btn in seg_btn._buttons_dict.items():
                if nombre == actual:
                    btn.configure(
                        fg_color="#0F172A",
                        hover_color="#1E293B",
                        text_color="#FFFFFF",
                    )
                else:
                    btn.configure(
                        fg_color="#F1F5F9",
                        hover_color="#E2E8F0",
                        text_color="#475569",
                    )
        except Exception:
            pass

    def _al_cerrar(self):
        try:
            self.panel_planificacion._cancelar_animacion()
            self.panel_concurrencia.detener_todos()
        except Exception:
            pass
        plt.close("all")
        self.destroy()


if __name__ == "__main__":
    app = SimuladorApp()
    app.mainloop()
