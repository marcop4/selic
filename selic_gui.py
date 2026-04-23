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
from selic_core import *
from selic_core import __version__, get_projected_level, _combo_name

class SelicGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"SELIC v{__version__} - Panel de Control Unificado")
        self.root.geometry("900x780")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(False, False)
        
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
        self.text_color = "#e0e0e0"
        self.muted_color = "#666666"
        self.green = "#00ff88"
        self.yellow = "#f2ff00"
        self.orange = "#ffaa00"
        self.red = "#ff4400"
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background=self.card_color, relief="flat")
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=self.bg_color, foreground=self.accent_color, font=("Orbitron", 22, "bold"))
        style.configure("Sub.TLabel", background=self.card_color, foreground=self.accent_color, font=("Segoe UI", 10, "bold"))
        style.configure("TCheckbutton", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[('active', self.card_color)], foreground=[('active', self.accent_color)])
        style.configure("Horizontal.TProgressbar", thickness=10, troughcolor="#111", background=self.accent_color)

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
        # Header
        header = ttk.Frame(self.root, padding=(30, 20, 30, 10))
        header.pack(fill="x")
        ttk.Label(header, text="SELIC", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="V1.2.0", foreground=self.muted_color, font=("Segoe UI", 10, "bold")).pack(side="left", padx=10, pady=(12, 0))
        
        tk.Button(header, text="?", command=self.show_main_help, bg="#161616", fg=self.accent_color, 
                  font=("Segoe UI", 11, "bold"), relief="flat", width=3, bd=0, cursor="hand2").pack(side="right")

        main_container = ttk.Frame(self.root, padding=(30, 0, 30, 10))
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

        # Complejidad y Mezcla (Nuevos)
        adv_f = ttk.Frame(settings_card, style="Card.TFrame")
        adv_f.pack(fill="x", pady=5)
        
        ttk.Label(adv_f, text="Complejidad:", style="Card.TLabel").pack(side="left")
        self.comp_combo = ttk.Combobox(adv_f, values=["1 (Básico)", "2 (Normal)", "3 (Alto)", "4 (Muy Alto)", "5 (Extremo)"], width=12, state="readonly")
        self.comp_combo.current(1)
        self.comp_combo.pack(side="left", padx=5)
        self.comp_combo.bind("<<ComboboxSelected>>", lambda e: self.update_diagnostic())

        ttk.Label(adv_f, text="Anclas:", style="Card.TLabel").pack(side="left", padx=(10, 0))
        self.anchors_ent = tk.Entry(adv_f, bg="#222", fg=self.accent_color, insertbackground="white", 
                                   relief="flat", width=15, font=("Segoe UI", 9))
        self.anchors_ent.pack(side="left", padx=5)
        self.anchors_ent.bind("<KeyRelease>", lambda e: self.update_diagnostic())

        ttk.Label(adv_f, text="Mezcla:", style="Card.TLabel").pack(side="left", padx=(10, 0))
        self.mezcla_combo = ttk.Combobox(adv_f, values=["Auto", "1 (Sueltas)", "2 (Parejas)", "3 (Tríos)", "4 (Cuartetos)"], width=11, state="readonly")
        self.mezcla_combo.current(0)
        self.mezcla_combo.pack(side="left", padx=5)
        self.mezcla_combo.bind("<<ComboboxSelected>>", lambda e: self.update_diagnostic())

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
            tk.Button(f, text="?", command=lambda t=help_txt: messagebox.showinfo("Ayuda", t),
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
        
        self.pattern_text = tk.Text(patt_card, height=2, bg="#000", fg=self.accent_color, 
                                   insertbackground="white", font=("Consolas", 10), relief="flat")
        self.pattern_text.pack(fill="x", pady=(5, 0), padx=10)
        self.pattern_text.insert("1.0", "#%?#")

        # SECCIÓN 4: SALIDA DE ARCHIVO
        out_card = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        out_card.pack(fill="x", pady=(0, 15))
        
        ttk.Label(out_card, text="DESTINO DEL ARCHIVO", style="Sub.TLabel").pack(anchor="w")
        out_f = ttk.Frame(out_card, style="Card.TFrame")
        out_f.pack(fill="x", pady=5)
        
        self.output_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "selic_wordlist.txt"))
        self.output_entry = tk.Entry(out_f, textvariable=self.output_path_var, bg="#000", fg="#aaa", 
                                    relief="flat", font=("Segoe UI", 9))
        self.output_entry.pack(side="left", fill="x", expand=True, pady=5, padx=10)
        
        tk.Button(out_f, text="Buscador", command=self.browse_output, bg="#222", fg=self.accent_color,
                  relief="flat", font=("Segoe UI", 9)).pack(side="right", padx=(15, 0))

        # FOOTER
        footer = ttk.Frame(self.root, padding=(30, 10, 30, 20))
        footer.pack(side="bottom", fill="x")
        
        self.progress_bar = ttk.Progressbar(footer, variable=self.progress_val, maximum=100, style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        info_line = ttk.Frame(footer)
        info_line.pack(fill="x")
        self.status_label = ttk.Label(info_line, text="SISTEMA LISTO", foreground=self.accent_color, font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="left")
        
        self.gen_btn = tk.Button(footer, text="GENERAR WORDLIST", command=self.start_thread,
                                bg=self.accent_color, fg="black", font=("Segoe UI", 12, "bold"),
                                relief="flat", cursor="hand2")
        self.gen_btn.pack(side="right", padx=40, pady=12)
        
        count_frame = ttk.Frame(info_line)
        count_frame.pack(side="right", padx=20)
        ttk.Label(count_frame, textvariable=self.generated_count, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Label(count_frame, text=" contraseñas", foreground=self.muted_color).pack(side="left")

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
        messagebox.showinfo("Ayuda SELIC", msg)

    def show_pattern_help(self):
        msg = ("GUÍA DE PATRONES QUIRÚRGICOS\n\n"
               "Crea estructuras fijas usando marcadores:\n"
               "# -> Datos del objetivo\n"
               "% -> Números (0-9)\n"
               "@ -> Letras minúsculas\n"
               ", -> Letras MAYÚSCULAS\n"
               "? -> Símbolos especiales\n\n"
               "Ejemplo: #%?2023 -> Nombre + Número + Símbolo + 2023")
        messagebox.showinfo("Patrones", msg)

    def browse_output(self):
        f = filedialog.asksaveasfilename(defaultextension=".txt", 
                                        initialfile="selic_wordlist.txt",
                                        title="Seleccionar destino de la wordlist")
        if f:
            self.output_path_var.set(f)

    def start_thread(self):
        self.gen_btn.config(state="disabled", text="GENERANDO...", bg="#333")
        threading.Thread(target=self.run_generation, daemon=True).start()

    def run_generation(self):
        try:
            config = self.get_params()
            output_file = self.output_path_var.get()
            
            if not output_file:
                messagebox.showwarning("Atención", "Por favor, elige un destino para el archivo.")
                self.reset_ui()
                return

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
            
            messagebox.showinfo("SELIC", f"¡Wordlist Generada con éxito!\n\nTotal: {written:,} items\nArchivo: {os.path.basename(output_file)}")
        except Exception as e:
            messagebox.showerror("Error del Motor", f"Ocurrió un fallo: {str(e)}")
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
            "patterns": [p.strip() for p in self.pattern_text.get("1.0", "end").splitlines() if p.strip()],
            "lower": self.lower_var.get(),
            "upper": self.upper_var.get(),
            "digits": self.digits_var.get(),
            "specials": self.specials_var.get(),
            "use_separators": self.seps_var.get(),
            "leet": self.leet_var.get(),
            "complexity": complexity,
            "mezcla": mezcla,
            "digit_suffixes": parse_multi_values(self.anchors_ent.get()),
            "min_length": int(self.min_len_ent.get()),
            "max_length": int(self.max_len_ent.get()),
            "remove_accents_flag": True,
            "agresividad": 4
        }

    def reset_ui(self):
        self.gen_btn.config(state="normal", text="GENERAR WORDLIST", bg=self.accent_color)
        self.status_label.config(text="SISTEMA LISTO")
        self.progress_val.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    # Centrar en pantalla
    w, h = 900, 780
    x = (root.winfo_screenwidth()/2) - (w/2)
    y = (root.winfo_screenheight()/2) - (h/2)
    root.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
    SelicGUI(root)
    root.mainloop()
