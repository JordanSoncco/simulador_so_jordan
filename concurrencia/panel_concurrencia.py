"""
============================================================================
 MÓDULO 2: PANEL CONTENEDOR DE LOS 5 PROBLEMAS DE CONCURRENCIA (TEMA CLARO)
 Autor : Jordan Oliber Soncco Machaca — UNA Puno
============================================================================
"""

from __future__ import annotations
from typing import Dict
import customtkinter as ctk

from .base_simulacion import BaseSimulacionFrame
from .productor_consumidor import SimProductorConsumidor
from .lectores_escritores import SimLectoresEscritores
from .filosofos_comensales import SimFilosofosComensales
from .barbero_dormilon import SimBarberoDormilon
from .fumadores import SimFumadores


class PanelConcurrencia(ctk.CTkFrame):
    """Contenedor de navegación en Tema Claro para los 5 problemas de concurrencia."""

    def __init__(self, master):
        super().__init__(master, fg_color="#EEF2F6", corner_radius=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(
            self, fg_color="#FFFFFF", corner_radius=10,
            border_width=1, border_color="#CBD5E1",
        )
        nav.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))

        ctk.CTkLabel(
            nav, text="Problema:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#0F172A",
        ).pack(side="left", padx=(12, 6), pady=8)

        self.problemas_info = [
            ("▶ Problema Productor - Consumidor", SimProductorConsumidor),
            ("▶ Problema de Lectores - Escritores", SimLectoresEscritores),
            ("▶ Problema de los filósofos comensales", SimFilosofosComensales),
            ("▶ Problema del Barbero dormilón", SimBarberoDormilon),
            ("▶ Problema de los fumadores", SimFumadores),
        ]

        self.botones_nav: Dict[str, ctk.CTkButton] = {}
        self.vistas: Dict[str, BaseSimulacionFrame] = {}
        self.vista_actual: str | None = None

        self.contenedor_vista = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor_vista.grid(row=1, column=0, sticky="nsew")
        self.contenedor_vista.grid_rowconfigure(0, weight=1)
        self.contenedor_vista.grid_columnconfigure(0, weight=1)

        for titulo, clase_sim in self.problemas_info:
            btn = ctk.CTkButton(
                nav,
                text=titulo,
                height=32,
                fg_color="#F1F5F9",
                hover_color="#E2E8F0",
                text_color="#334155",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                command=lambda t=titulo: self.seleccionar_problema(t),
            )
            btn.pack(side="left", padx=4, pady=6, expand=True, fill="x")
            self.botones_nav[titulo] = btn

            instancia = clase_sim(self.contenedor_vista)
            self.vistas[titulo] = instancia

        self.seleccionar_problema(self.problemas_info[0][0])

    def seleccionar_problema(self, titulo: str):
        if self.vista_actual and self.vista_actual != titulo:
            self.vistas[self.vista_actual].pausar()
            self.vistas[self.vista_actual].grid_forget()

        for t, btn in self.botones_nav.items():
            if t == titulo:
                btn.configure(fg_color="#0F172A", text_color="#FFFFFF", hover_color="#1E293B")
            else:
                btn.configure(fg_color="#F1F5F9", text_color="#475569", hover_color="#E2E8F0")

        self.vista_actual = titulo
        self.vistas[titulo].grid(row=0, column=0, sticky="nsew")
        self.vistas[titulo]._dibujar_escena()

    def detener_todos(self):
        for vista in self.vistas.values():
            vista.detener()
