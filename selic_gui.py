#!/usr/bin/env python3
"""
SELIC GUI v1.2.0 - Professional Cyber-Security Tool
Interfaz Gráfica Unificada con Diagnóstico Visual de Gravedad
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import re
import ctypes
from selic_core import *
from selic_core import __version__, get_projected_level, _combo_name

class SelicGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"SELIC v{__version__} - Panel de Control Unificado")
        self.root.geometry("950x720")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(False, False)
        
        # Barra de título oscura (Windows 10/11)
        # En Linux/Wayland la barra de título la controla el gestor de ventanas/compositor.
        try:
            import sys
            if sys.platform == "win32":
                self.root.update()
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
                )
        except Exception:
            pass
        
        self.setup_styles()
        self.create_variables()
        self.create_widgets()
        self.update_diagnostic() # Inicializar diagnóstico

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        self.bg_color = "#0a0a0a"
        self.card_color = "#161616"
        self.accent_color = "#00f2ff"
        self.accent_hover = "#33f7ff"
        self.text_color = "#e0e0e0"
        self.muted_color = "#555555"
        self.green = "#00ff88"
        self.yellow = "#f2ff00"
        self.orange = "#ffaa00"
        self.red = "#ff4400"
        self.card_border = "#1e1e1e"
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background=self.card_color, relief="flat")
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=self.bg_color, foreground=self.accent_color, font=("Orbitron", 22, "bold"))
        style.configure("Sub.TLabel", background=self.card_color, foreground=self.accent_color, font=("Segoe UI", 10, "bold"))
        style.configure("TCheckbutton", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[('active', self.card_color)], foreground=[('active', self.accent_color)])
        style.configure("Horizontal.TProgressbar", thickness=12, troughcolor="#111", background=self.accent_color)
        
        # Scrollbar oscura
        style.configure("Dark.Vertical.TScrollbar",
                        background="#222", troughcolor="#0a0a0a",
                        bordercolor="#0a0a0a", arrowcolor="#555",
                        lightcolor="#0a0a0a", darkcolor="#0a0a0a")
        style.map("Dark.Vertical.TScrollbar",
                  background=[('active', '#444'), ('pressed', '#555')])

    def _dark_dialog(self, title, message, dialog_type="info", yes_no=False):
        """Diálogo personalizado dark-themed que reemplaza los messagebox del sistema."""
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.configure(bg="#0e0e0e")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()
        
        # Centrar sobre la ventana principal
        dlg.update_idletasks()
        dw, dh = 460, 340
        px = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dw // 2)
        py = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dh // 2)
        dlg.geometry(f"{dw}x{dh}+{px}+{py}")
        
        # Colores según tipo
        icon_colors = {"info": self.accent_color, "warning": self.orange, "error": self.red, "success": self.green}
        icons = {"info": "ℹ", "warning": "⚠", "error": "✕", "success": "✓"}
        color = icon_colors.get(dialog_type, self.accent_color)
        icon = icons.get(dialog_type, "ℹ")
        
        # Barra superior con color
        bar = tk.Frame(dlg, bg=color, height=3)
        bar.pack(fill="x")
        
        # Contenido
        body = tk.Frame(dlg, bg="#0e0e0e", padx=25, pady=15)
        body.pack(fill="both", expand=True)
        
        # Icono y título
        head_f = tk.Frame(body, bg="#0e0e0e")
        head_f.pack(fill="x", pady=(0, 10))
        tk.Label(head_f, text=icon, font=("Segoe UI", 20), fg=color, bg="#0e0e0e").pack(side="left", padx=(0, 10))
        tk.Label(head_f, text=title, font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#0e0e0e").pack(side="left")
        
        # Mensaje scrollable
        msg_frame = tk.Frame(body, bg="#141414", padx=12, pady=10)
        msg_frame.pack(fill="both", expand=True)
        msg_label = tk.Text(msg_frame, wrap="word", font=("Segoe UI", 9), fg="#cccccc", bg="#141414",
                           relief="flat", height=8, cursor="arrow", borderwidth=0)
        msg_label.insert("1.0", message)
        msg_label.config(state="disabled")
        msg_label.pack(fill="both", expand=True)
        
        # Botones
        btn_f = tk.Frame(body, bg="#0e0e0e")
        btn_f.pack(fill="x", pady=(12, 0))
        
        result = {"value": False}
        
        def on_yes():
            result["value"] = True
            dlg.destroy()
        def on_no():
            result["value"] = False
            dlg.destroy()
        
        if yes_no:
            no_btn = tk.Button(btn_f, text="CANCELAR", command=on_no, bg="#222", fg="#aaa",
                              font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=6, cursor="hand2")
            no_btn.pack(side="right", padx=(5, 0))
            yes_btn = tk.Button(btn_f, text="CONFIRMAR", command=on_yes, bg=color, fg="black",
                               font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=6, cursor="hand2")
            yes_btn.pack(side="right")
        else:
            ok_btn = tk.Button(btn_f, text="ENTENDIDO", command=dlg.destroy, bg=color, fg="black",
                              font=("Segoe UI", 10, "bold"), relief="flat", padx=25, pady=6, cursor="hand2")
            ok_btn.pack(side="right")
        
        dlg.wait_window()
        return result["value"]

    def create_variables(self):
        self.lower_var = tk.BooleanVar(value=True)
        self.upper_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.specials_var = tk.BooleanVar(value=False)
        self.leet_var = tk.BooleanVar(value=False)
        self.seps_var = tk.BooleanVar(value=False)
        self.accents_var = tk.BooleanVar(value=True)
        
        # Trazar cambios para diagnóstico
        for var in [self.lower_var, self.upper_var, self.digits_var, self.specials_var, self.leet_var, self.seps_var]:
            var.trace_add("write", lambda *args: self.update_diagnostic())
            
        self.progress_val = tk.DoubleVar(value=0)
        self.generated_count = tk.StringVar(value="0")
        self.diagnostic_msg = tk.StringVar(value="ANALIZANDO...")
        self.complexity_val = tk.IntVar(value=2)

    def create_widgets(self):
        # --- ESTRUCTURA PRINCIPAL (HEADER Y FOOTER FIJOS) ---
        
        # 1. HEADER (ARRIBA)
        header = ttk.Frame(self.root, padding=(30, 20, 30, 10))
        header.pack(side="top", fill="x")
        ttk.Label(header, text="SELIC", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="V1.2.0", foreground=self.muted_color, font=("Segoe UI", 10, "bold")).pack(side="left", padx=10, pady=(12, 0))
        
        tk.Button(header, text="?", command=self.show_main_help, bg="#161616", fg=self.accent_color, 
                  font=("Segoe UI", 11, "bold"), relief="flat", width=3, bd=0, cursor="hand2").pack(side="right")

        # 2. FOOTER (ABAJO)
        footer = ttk.Frame(self.root, padding=(30, 5, 30, 10))
        footer.pack(side="bottom", fill="x")
        
        self.progress_bar = ttk.Progressbar(footer, variable=self.progress_val, maximum=100, style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        info_line = ttk.Frame(footer)
        info_line.pack(fill="x")
        
        self.status_label = ttk.Label(info_line, text="SISTEMA LISTO", foreground=self.accent_color, font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="left", pady=10)
        
        self.gen_btn = tk.Button(info_line, text="⚡ GENERAR WORDLIST", command=self.start_thread,
                                bg=self.accent_color, fg="black", font=("Segoe UI", 11, "bold"),
                                relief="flat", cursor="hand2", padx=20, pady=6,
                                activebackground=self.accent_hover, activeforeground="black")
        self.gen_btn.pack(side="right", padx=10)
        self.gen_btn.bind("<Enter>", lambda e: self.gen_btn.config(bg=self.accent_hover) if self.gen_btn["state"] != "disabled" else None)
        self.gen_btn.bind("<Leave>", lambda e: self.gen_btn.config(bg=self.accent_color) if self.gen_btn["state"] != "disabled" else None)
        
        count_frame = ttk.Frame(info_line)
        count_frame.pack(side="right", padx=10)
        ttk.Label(count_frame, textvariable=self.generated_count, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Label(count_frame, text=" contraseñas", foreground=self.muted_color).pack(side="left")

        # 3. ÁREA SCROLLABLE (CENTRO)
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview, style="Dark.Vertical.TScrollbar")
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Ajustar ancho del frame interno al canvas
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Soporte para rueda del ratón
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- CONTENIDO DE LOS AJUSTES (Dentro de scrollable_frame) ---
        main_container = ttk.Frame(self.scrollable_frame, padding=(30, 0, 30, 10))
        main_container.pack(fill="both", expand=True)

        # SECCIÓN 1: DATOS (COL IZQUIERDA) Y AJUSTES (COL DERECHA)
        top_grid = ttk.Frame(main_container)
        top_grid.pack(fill="x", pady=(0, 15))
        
        # COL 1: TARGET DATA
        target_card = ttk.Frame(top_grid, style="Card.TFrame", padding=15)
        target_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ttk.Label(target_card, text="DATOS DEL OBJETIVO", style="Sub.TLabel").pack(anchor="w", pady=(0, 10))
        
        self.entries = {}
        fields = [
            ("name", "Nombre / Alias completo"),
            ("birth", "Fecha Nacimiento (DD/MM/YYYY)"),
            ("dni", "DNI / Documento Identidad"),
            ("other", "Otros datos (Hobby, Mascota...)")
        ]
        for key, label in fields:
            f = ttk.Frame(target_card, style="Card.TFrame")
            f.pack(fill="x")
            ttk.Label(f, text=label, style="Card.TLabel", foreground=self.muted_color).pack(side="left")
            
            ent = tk.Entry(target_card, bg="#222", fg="white", insertbackground=self.accent_color, 
                          relief="flat", borderwidth=5, font=("Segoe UI", 10))
            ent.pack(fill="x", pady=(2, 8))
            ent.bind("<KeyRelease>", lambda e: self.update_diagnostic())
            self.entries[key] = ent

        # COL 2: SETTINGS
        settings_card = ttk.Frame(top_grid, style="Card.TFrame", padding=15)
        settings_card.grid(row=0, column=1, sticky="nsew")
        top_grid.columnconfigure(0, weight=1)
        top_grid.columnconfigure(1, weight=1)

        ttk.Label(settings_card, text="CONFIGURACIÓN TÉCNICA", style="Sub.TLabel").pack(anchor="w", pady=(0, 10))
        
        # Grid para controles numéricos
        num_controls = ttk.Frame(settings_card, style="Card.TFrame")
        num_controls.pack(fill="x", pady=(0, 10))

        # Longitud
        ttk.Label(num_controls, text="Longitud:", style="Card.TLabel").pack(side="left")
        self.min_len_ent = tk.Spinbox(num_controls, from_=1, to=32, width=3, bg="#222", fg="white", buttonbackground="#333", relief="flat")
        self.min_len_ent.delete(0, "end"); self.min_len_ent.insert(0, "4")
        self.min_len_ent.pack(side="left", padx=5)
        ttk.Label(num_controls, text="a", style="Card.TLabel").pack(side="left")
        self.max_len_ent = tk.Spinbox(num_controls, from_=1, to=128, width=3, bg="#222", fg="white", buttonbackground="#333", relief="flat")
        self.max_len_ent.delete(0, "end"); self.max_len_ent.insert(0, "32")
        self.max_len_ent.pack(side="left", padx=5)

        # Complejidad, Sufijos y Mezcla
        adv_f = ttk.Frame(settings_card, style="Card.TFrame")
        adv_f.pack(fill="x", pady=5)
        
        # Fila Complejidad
        f_comp = ttk.Frame(adv_f, style="Card.TFrame")
        f_comp.pack(fill="x", pady=2)
        ttk.Label(f_comp, text="Complejidad:", style="Card.TLabel").pack(side="left")
        self.comp_combo = ttk.Combobox(f_comp, values=["1 (Básico)", "2 (Normal)", "3 (Alto)", "4 (Muy Alto)", "5 (Extremo)"], width=12, state="readonly")
        self.comp_combo.current(1)
        self.comp_combo.pack(side="left", padx=5)
        self.comp_combo.bind("<<ComboboxSelected>>", lambda e: self.update_diagnostic())
        tk.Button(f_comp, text="?", command=self.show_complexity_help, bg="#222", fg=self.muted_color, 
                  font=("Segoe UI", 7, "bold"), relief="flat", bd=0).pack(side="left", padx=2)

        # Fila Sufijos
        f_suf = ttk.Frame(adv_f, style="Card.TFrame")
        f_suf.pack(fill="x", pady=2)
        ttk.Label(f_suf, text="Sufijos:", style="Card.TLabel").pack(side="left")
        self.anchors_ent = tk.Entry(f_suf, bg="#222", fg=self.accent_color, insertbackground="white", 
                                   relief="flat", width=20, font=("Segoe UI", 9))
        self.anchors_ent.insert(0, "123, 2026, 2025")
        self.anchors_ent.pack(side="left", padx=5)
        self.anchors_ent.bind("<KeyRelease>", lambda e: self.update_diagnostic())
        tk.Button(f_suf, text="?", command=self.show_suffixes_help, bg="#222", fg=self.muted_color, 
                  font=("Segoe UI", 7, "bold"), relief="flat", bd=0).pack(side="left", padx=2)

        # Fila Mezcla
        f_mez = ttk.Frame(adv_f, style="Card.TFrame")
        f_mez.pack(fill="x", pady=2)
        ttk.Label(f_mez, text="Mezcla:", style="Card.TLabel").pack(side="left")
        self.mezcla_combo = ttk.Combobox(f_mez, values=["Auto", "1 (Sueltas)", "2 (Parejas)", "3 (Tríos)", "4 (Cuartetos)"], width=11, state="readonly")
        self.mezcla_combo.current(0)
        self.mezcla_combo.pack(side="left", padx=5)
        self.mezcla_combo.bind("<<ComboboxSelected>>", lambda e: self.update_diagnostic())
        tk.Button(f_mez, text="?", command=self.show_mixing_help, bg="#222", fg=self.muted_color, 
                  font=("Segoe UI", 7, "bold"), relief="flat", bd=0).pack(side="left", padx=2)

        checks = [
            ("Minúsculas", self.lower_var, "Permite usar letras minúsculas."),
            ("Mayúsculas", self.upper_var, "Permite usar letras MAYÚSCULAS."),
            ("Dígitos (0-9)", self.digits_var, "Agrega números al final o entre palabras."),
            ("Símbolos (!@#)", self.specials_var, "Agrega caracteres especiales."),
            ("Leet Speak (a=4)", self.leet_var, "Transforma letras en números (ej: 3 en lugar de E)."),
            ("Separadores (._-)", self.seps_var, "Une palabras usando puntos, guiones o barras.")
        ]
        
        for text, var, help_txt in checks:
            f = ttk.Frame(settings_card, style="Card.TFrame")
            f.pack(fill="x", pady=2)
            ttk.Checkbutton(f, text=text, variable=var, style="TCheckbutton").pack(side="left")
            tk.Button(f, text="?", command=lambda t=help_txt: self._dark_dialog("Ayuda", t),
                      bg="#222", fg=self.muted_color, font=("Segoe UI", 7, "bold"), relief="flat", bd=0).pack(side="right", padx=5)

        # SECCIÓN 2: MEDIDOR DE GRAVEDAD (TERMÓMETRO)
        diag_card = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        diag_card.pack(fill="x", pady=(0, 15))
        
        diag_header = ttk.Frame(diag_card, style="Card.TFrame")
        diag_header.pack(fill="x")
        ttk.Label(diag_header, text="ESTADO DEL ATAQUE (GRAVEDAD)", style="Sub.TLabel").pack(side="left")
        ttk.Label(diag_header, textvariable=self.diagnostic_msg, font=("Segoe UI", 10, "bold")).pack(side="right")
        
        # El Medidor de Bloques
        self.meter_frame = ttk.Frame(diag_card, style="Card.TFrame", padding=(0, 10))
        self.meter_frame.pack(fill="x")
        self.blocks = []
        for i in range(4):
            b = tk.Frame(self.meter_frame, height=20, width=180, bg="#222", relief="flat")
            b.pack(side="left", padx=2, expand=True, fill="x")
            self.blocks.append(b)

        # SECCIÓN 3: PATRONES AVANZADOS
        patt_card = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        patt_card.pack(fill="x", pady=(0, 15))
        
        p_head = ttk.Frame(patt_card, style="Card.TFrame")
        p_head.pack(fill="x")
        ttk.Label(p_head, text="PATRONES QUIRÚRGICOS", style="Sub.TLabel").pack(side="left")
        tk.Button(p_head, text="?", command=self.show_pattern_help, bg="#222", fg=self.accent_color, relief="flat", bd=0).pack(side="right")
        
        self.pattern_placeholder = "Ej: #%?#  (1 patrón por línea, vacío = sin patrones)"
        self.pattern_text = tk.Text(patt_card, height=2, bg="#000", fg="#555", 
                                   insertbackground="white", font=("Consolas", 10), relief="flat")
        self.pattern_text.pack(fill="x", pady=(5, 0), padx=10)
        self.pattern_text.insert("1.0", self.pattern_placeholder)
        self.pattern_text.bind("<FocusIn>", self._pattern_focus_in)
        self.pattern_text.bind("<FocusOut>", self._pattern_focus_out)

        # SECCIÓN 4: SALIDA DE ARCHIVO
        out_card = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        out_card.pack(fill="x", pady=(0, 15))
        
        ttk.Label(out_card, text="DESTINO DEL ARCHIVO", style="Sub.TLabel").pack(anchor="w")
        out_f = ttk.Frame(out_card, style="Card.TFrame")
        out_f.pack(fill="x", pady=5)
        
        os.makedirs("wordlists", exist_ok=True)
        self.output_path_var = tk.StringVar(value=os.path.abspath(os.path.join("wordlists", "passlist_gui.txt")))
        
        # Primero el botón Buscador para que no sea empujado
        tk.Button(out_f, text="Buscador", command=self.browse_output, bg="#222", fg=self.accent_color,
                  relief="flat", font=("Segoe UI", 9), padx=10).pack(side="right", padx=5)

        self.output_entry = tk.Entry(out_f, textvariable=self.output_path_var, bg="#000", fg="#aaa", 
                                    relief="flat", font=("Segoe UI", 9))
        self.output_entry.pack(side="left", fill="x", expand=True, pady=5, padx=10)

    def update_diagnostic(self, *args):
        # 1. Obtener parámetros actuales de la UI
        try:
            config = self.get_params()
            
            # 2. Calcular tokens sociales (el motor real lo hace así)
            social_tokens, numeric_parts = collect_social_tokens(config, [], config)
            config["numeric_parts"] = numeric_parts
            
            # 3. Obtener el nivel proyectado del cerebro de SELIC
            actual_max_combo = config["mezcla"] if isinstance(config["mezcla"], int) else (1 if config["complexity"] == 1 else (2 if config["complexity"] <= 3 else 3))
            level = get_projected_level(actual_max_combo, config)
            
            # Limpiar nivel de strings si vienen con texto
            if isinstance(level, str):
                level = int(re.search(r'\d+', level).group())
            
            level_name = _combo_name(level)
        except:
            level = 1
            level_name = "Social Lite (Básico)"

        # 4. Actualizar bloques visuales
        colors = [self.green, self.yellow, self.orange, self.red]
        for i in range(4):
            if i < level:
                self.blocks[i].configure(bg=colors[level-1])
            else:
                self.blocks[i].configure(bg="#222")
        
        self.diagnostic_msg.set(f"NIVEL {level}: {level_name.upper()}")
        self.diagnostic_color = colors[level-1]
        self.complexity_val.set(level)

    def show_main_help(self):
        msg = ("SELIC v1.2.0 - Guía de Uso\n\n"
               "1. DATOS: Ingresa todo lo que sepas del objetivo. A más datos, más precisión.\n"
               "2. AJUSTES: Elige qué transformaciones aplicar. \n"
               "3. MEDIDOR: Observa los bloques. Si llega al ROJO, la wordlist será enorme pero muy efectiva.\n"
               "4. GENERAR: Elige la ruta y espera a que el sistema termine.")
        self._dark_dialog("Ayuda SELIC", msg)

    def _on_canvas_configure(self, event):
        # Ajustar el ancho del frame interno para que coincida con el canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Scroll con la rueda del ratón
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def show_complexity_help(self):
        msg = ("NIVELES DE COMPLEJIDAD\n\n"
               "1: Básico. Solo variaciones simples.\n"
               "2: Normal. Incluye símbolos dobles (!!, @@).\n"
               "3: Alto. Leet Speak multi-carácter, reversos y mayúsculas alternas.\n"
               "4: Muy Alto. Añade sufijos automáticos como '!2024'.\n"
               "5: Extremo. Cruces exhaustivos entre símbolos y números.")
        self._dark_dialog("Ayuda: Complejidad", msg)

    def show_suffixes_help(self):
        msg = ("SUFIJOS PERSONALIZADOS\n\n"
               "Escribe palabras, letras o números separados por coma.\n"
               "Se pegarán al principio y al final de cada contraseña.\n"
               "Ejemplo: SH, 2025, !\n\n"
               "Escribe 'ninguno' o deja el campo vacío si NO quieres usar sufijos.")
        self._dark_dialog("Ayuda: Sufijos", msg)

    def show_mixing_help(self):
        msg = ("NIVELES DE MEZCLA (PROFUNDIDAD)\n\n"
               "1: Palabras sueltas.\n"
               "2: Parejas de palabras (Ej: NombreApellido).\n"
               "3: Tríos de palabras (Ej: NombreApellidoHobby).\n"
               "4: Cuartetos (¡Cuidado! Generación muy pesada).\n\n"
               "Auto: El sistema elige según la complejidad seleccionada.")
        self._dark_dialog("Ayuda: Mezcla", msg)

    def show_pattern_help(self):
        msg = ("GUÍA DE PATRONES (Estilo Crunch)\n\n"
               "Cada marcador = 1 posición de carácter:\n"
               "  #  → 1 carácter del pool social (tus datos)\n"
               "  %  → 1 número (0-9)\n"
               "  @  → 1 letra minúscula (a-z)\n"
               "  ,   → 1 letra MAYÚSCULA (A-Z)\n"
               "  ?   → 1 símbolo especial (!@#$...)\n\n"
               "TEXTO FIJO: Todo lo que NO sea un marcador\n"
               "se mantiene literal en la contraseña.\n"
               "  Ej: IV%%%CO → IV000CO, IV001CO... IV999CO\n"
               "  Ej: V#9 → Va9, Vb9, Vc9...\n\n"
               "MÚLTIPLES PATRONES: Escribe 1 patrón por\n"
               "línea (presiona Enter para separar).\n\n"
               "ESCAPE: Si quieres usar un marcador como\n"
               "texto fijo, ponle \\ delante.\n"
               "  Ej: precio\\?%%%  → precio?000... precio?999\n"
               "  (El \\? se trata como '?' literal, no como símbolo)")
        self._dark_dialog("Patrones", msg)

    def _pattern_focus_in(self, event):
        """Cuando el usuario hace clic en el campo de patrones, quitar el placeholder."""
        content = self.pattern_text.get("1.0", "end").strip()
        if content == self.pattern_placeholder:
            self.pattern_text.delete("1.0", "end")
            self.pattern_text.config(fg=self.accent_color)

    def _pattern_focus_out(self, event):
        """Si el campo queda vacío, restaurar el placeholder gris."""
        content = self.pattern_text.get("1.0", "end").strip()
        if not content:
            self.pattern_text.config(fg="#555")
            self.pattern_text.insert("1.0", self.pattern_placeholder)

    def _get_real_patterns(self):
        """Obtener patrones reales, ignorando el placeholder."""
        content = self.pattern_text.get("1.0", "end").strip()
        if content == self.pattern_placeholder or not content:
            return []
        return [p.strip() for p in content.splitlines() if p.strip()]

    def validate_patterns(self, patterns):
        """Valida los patrones ingresados. Retorna (ok, mensaje_error)."""
        valid_markers = {"#", "%", "@", ",", "?"}
        for i, pattern in enumerate(patterns, 1):
            if not pattern:
                continue
            # Verificar que tenga al menos 1 marcador
            has_marker = False
            j = 0
            while j < len(pattern):
                ch = pattern[j]
                if ch == "\\" and j + 1 < len(pattern):
                    j += 2  # Saltar escape
                    continue
                if ch in valid_markers:
                    has_marker = True
                    break
                j += 1
            if not has_marker:
                return False, (f"Patrón #{i} '{pattern}' no tiene ningún marcador (#, %, @, ,, ?).\n"
                               "Si quieres texto fijo, no necesitas un patrón.\n"
                               "¿Quizás quisiste usar un marcador?")
        return True, ""

    def browse_output(self):
        os.makedirs("wordlists", exist_ok=True)
        f = filedialog.asksaveasfilename(defaultextension=".txt", 
                                        initialfile="passlist_gui.txt",
                                        initialdir=os.path.abspath("wordlists"),
                                        title="Seleccionar destino de la wordlist")
        if f:
            self.output_path_var.set(f)

    def start_thread(self):
        # Construir resumen de configuración antes de generar
        try:
            config = self.get_params()
        except Exception as e:
            self._dark_dialog("Error", f"Error al leer configuración:\n{e}", "error")
            return

        raw_output = self.output_path_var.get()
        output_file = resolve_output_path(raw_output, "gui")
        self.output_path_var.set(output_file)
        if not output_file:
            self._dark_dialog("Atención", "Por favor, elige un destino para el archivo.", "warning")
            return

        # Validar patrones
        if config.get("patterns"):
            ok, err_msg = self.validate_patterns(config["patterns"])
            if not ok:
                self._dark_dialog("Patrón Inválido", err_msg, "warning")
                return

        # Construir texto de resumen
        si_no = lambda v: "Sí" if v else "No"
        sufijos = config.get("digit_suffixes", [])
        patrones = config.get("patterns", [])

        summary = "RESUMEN DE CONFIGURACIÓN\n"
        summary += "=" * 35 + "\n\n"
        summary += f"Nombre:  {config.get('name') or '(vacío)'}\n"
        summary += f"Nacimiento:  {', '.join(config.get('birth_year') or []) or '(vacío)'}\n"
        summary += f"DNI:  {config.get('dni') or '(vacío)'}\n"
        summary += f"Otros:  {', '.join(config.get('other') or []) or '(vacío)'}\n\n"

        summary += f"Minúsculas:  {si_no(config.get('lower'))}\n"
        summary += f"Mayúsculas:  {si_no(config.get('upper'))}\n"
        summary += f"Dígitos:  {si_no(config.get('digits'))}\n"
        summary += f"Especiales:  {si_no(config.get('specials'))}\n"
        summary += f"Leet Speak:  {si_no(config.get('leet'))}\n"
        summary += f"Separadores:  {si_no(config.get('use_separators'))}\n\n"

        summary += f"Sufijos:  {', '.join(sufijos) if sufijos else '(ninguno)'}\n"
        summary += f"Patrones:  {', '.join(patrones) if patrones else '(ninguno)'}\n\n"

        summary += f"Complejidad:  {config.get('complexity', 2)}\n"
        mezcla_val = config.get('mezcla', 'auto')
        if mezcla_val == "auto":
            comp = config.get("complexity", 2)
            if comp <= 1: actual = 1
            elif comp <= 3: actual = 2
            elif comp == 4: actual = 3
            else: actual = 4
            mezcla_val = f"Auto (Nivel {actual})"
        
        summary += f"Mezcla:  {mezcla_val}\n"
        summary += f"Longitud:  {config.get('min_length', 4)} - {config.get('max_length', 32)}\n"
        summary += f"Salida:  {output_file}\n\n"

        summary += "¿Deseas continuar con la generación?"

        if not self._dark_dialog("Confirmar Generación", summary, "info", yes_no=True):
            return

        self.gen_btn.config(state="disabled", text="GENERANDO...", bg="#333")
        threading.Thread(target=self.run_generation, daemon=True).start()

    def run_generation(self):
        try:
            config = self.get_params()
            output_file = self.output_path_var.get()

            self.status_label.config(text="SISTEMA EN EJECUCIÓN...")
            
            # Recolección
            options = config.copy()
            social_tokens, numeric_parts = collect_social_tokens(config, [], options)
            options["numeric_parts"] = numeric_parts
            char_pool = build_char_pool("base", social_tokens, options)
            
            # Estimación real
            total_est = estimate_wordlist_size(config, social_tokens)
            
            candidate_iterables = []
            if config["patterns"]:
                p_iter = generate_from_patterns(config["patterns"], char_pool, config["min_length"], config["max_length"])
                candidate_iterables.append(p_iter)
            
            # Si no hay patrones, usar generador normal por capas
            if not candidate_iterables:
                 p_iter = generate_tiered_variants(social_tokens, options, tier=1) # Usar tier según agresividad
                 candidate_iterables.append(p_iter)

            progress_state = {"generated": 0, "current": ""}
            
            def update_ui():
                while threading.main_thread().is_alive() and self.gen_btn["state"] == "disabled":
                    gen = progress_state.get("generated", 0)
                    self.generated_count.set(f"{gen:,}")
                    if total_est > 0:
                        prog = min(100, (gen / total_est) * 100)
                        self.progress_val.set(prog)
                    time.sleep(0.3)

            threading.Thread(target=update_ui, daemon=True).start()
            written = stream_candidates_to_file(output_file, candidate_iterables, config["min_length"], config["max_length"], progress_state=progress_state)
            
            self._dark_dialog("SELIC", f"¡Wordlist Generada con éxito!\n\nTotal: {written:,} items\nArchivo: {os.path.basename(output_file)}", "success")
        except Exception as e:
            self._dark_dialog("Error del Motor", f"Ocurrió un fallo: {str(e)}", "error")
        finally:
            self.reset_ui()

    def get_params(self):
        # Procesar Complejidad (Extraer número de '2 (Normal)')
        comp_str = self.comp_combo.get()
        complexity = int(re.search(r'\d+', comp_str).group()) if comp_str else 2
        
        # Procesar Mezcla
        mez_str = self.mezcla_combo.get()
        if mez_str == "Auto":
            mezcla = "auto"
        else:
            mezcla = int(re.search(r'\d+', mez_str).group())

        return {
            "name": self.entries["name"].get(),
            "birth_year": parse_multi_values(self.entries["birth"].get()),
            "dni": self.entries["dni"].get(),
            "other": parse_multi_values(self.entries["other"].get()),
            "patterns": self._get_real_patterns(),
            "lower": self.lower_var.get(),
            "upper": self.upper_var.get(),
            "digits": self.digits_var.get(),
            "specials": self.specials_var.get(),
            "use_separators": self.seps_var.get(),
            "leet": self.leet_var.get(),
            "complexity": complexity,
            "mezcla": mezcla,
            "digit_suffixes": [] if self.anchors_ent.get().strip().lower() in ["", "ninguno"] else parse_multi_values(self.anchors_ent.get()),
            "min_length": int(self.min_len_ent.get()),
            "max_length": int(self.max_len_ent.get()),
            "remove_accents_flag": True,
            "agresividad": 4
        }

    def reset_ui(self):
        self.gen_btn.config(state="normal", text="⚡ GENERAR WORDLIST", bg=self.accent_color)
        self.status_label.config(text="SISTEMA LISTO")
        self.progress_val.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    # Centrar en pantalla
    w, h = 950, 720
    x = (root.winfo_screenwidth()/2) - (w/2)
    y = (root.winfo_screenheight()/2) - (h/2)
    root.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
    SelicGUI(root)
    root.mainloop()
