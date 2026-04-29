#!/usr/bin/env python3
import argparse
import sys
import time
import threading
from selic_core import *

__version__ = "1.2.0"

def print_mini_logo():
    C = "\033[38;5;51m"
    B = "\033[38;5;33m"
    W = "\033[0m"
    banner = f"""
    {C}███████╗███████╗██╗     ██╗ ██████╗{W}
    {C}██╔════╝██╔════╝██║     ██║██╔════╝{W}
    {B}███████╗█████╗  ██║     ██║██║     {W}
    {B}╚════██║██╔══╝  ██║     ██║██║     {W}
    {C}███████║███████╗███████╗██║╚██████╗{W}
    {C}╚══════╝╚══════╝╚══════╝╚═╝ ╚═════╝{W}
               {B}--- m i n i  v1.2.0 ---{W}
    """
    print(banner)

def get_name_variants(name_string):
    parts = [p.strip() for p in name_string.split() if p.strip()]
    variants = set(parts)
    if len(parts) >= 2:
        # First + Last
        variants.add(f"{parts[0]}{parts[-1]}")
        # F.Last
        variants.add(f"{parts[0][0]}{parts[-1]}")
        # First.L
        variants.add(f"{parts[0]}{parts[-1][0]}")
    return variants

def parse_mini_input(user_input):
    tokens = set()
    groups = [g.strip() for g in user_input.split(',')]
    for group in groups:
        if not group:
            continue
        if ' ' in group:
            # might be a full name, extract compounds
            tokens.update(get_name_variants(group))
        # Se agrega el grupo completo; normalize_token ya se encarga de separar internamente
        tokens.add(group)
    return sorted(tokens)

def ask_config(options):
    options.setdefault("use_separators", False)
    options.setdefault("leet_full", False)
    options.setdefault("max_ram", 3)
    options.setdefault("remove_accents_flag", True)
    bool_to_str = lambda b: "Si" if b else "No"
    
    print(color_text("\n[ Niveles de Agresividad ]", COLOR_CYAN))
    print(color_text("  1 = Básico (Alta probabilidad, sin símbolos ni leet)", COLOR_CYAN))
    print(color_text("  2 = Intermedio (Fechas, Símbolos simples, Parejas)", COLOR_CYAN))
    print(color_text("  3 = Avanzado (Agrega Leet Speak suave)", COLOR_CYAN))
    print(color_text("  4 = Extremo (Fuerza bruta exhaustiva, TODO activo)", COLOR_CYAN))
    
    while True:
        agr_input = input(color_text(">> Elige el Nivel (1-4) [ENTER=4]: ", COLOR_GREEN)).strip()
        if not agr_input:
            options["agresividad"] = 4
            break
        if agr_input in ("1", "2", "3", "4"):
            options["agresividad"] = int(agr_input)
            break
        print(color_text("[!] Ingresa un número del 1 al 4.", COLOR_MAGENTA))

    agr = options["agresividad"]
    if agr == 1:
        options.update({"digits": True, "specials": False, "leet": False, "complexity": 2})
    elif agr == 2:
        options.update({"digits": True, "specials": True, "leet": False, "complexity": 2})
    elif agr == 3:
        options.update({"digits": True, "specials": True, "leet": True, "complexity": 3})
    elif agr == 4:
        options.update({"digits": True, "specials": True, "leet": True, "leet_full": True, "complexity": 5, "use_separators": True})

    def get_summary():
        b = bool_to_str
        parts = []
        if options.get("lower"): parts.append(f"Minusculas={b(options['lower'])}")
        if options.get("upper"): parts.append(f"Mayusculas={b(options['upper'])}")
        if options.get("digits"): parts.append(f"Numeros={b(options['digits'])}")
        if options.get("specials"): parts.append(f"Simbolos={b(options['specials'])}")
        if options.get("use_separators"): parts.append(f"Separadores={b(options['use_separators'])}")
        parts.append(f"SinTildes={b(options['remove_accents_flag'])}")
        if options.get("leet"): parts.append(f"Leet={b(options['leet'])}")
        if options.get("leet_full"): parts.append(f"LeetFull={b(options['leet_full'])}")
        parts.append(f"Complejidad={options['complexity']}")
        parts.append(f"Agresividad={options['agresividad']}")
        parts.append(f"Ram={options['max_ram']}")
        return " | ".join(parts)

    def show_help():
        b = bool_to_str
        print(color_text("\n[ Ajustes Activos para este Nivel ]", COLOR_YELLOW))
        print(color_text(f"  Minusculas={b(options.get('lower', False)):<3}  Incluir variantes en minusculas", COLOR_CYAN))
        print(color_text(f"  Mayusculas={b(options.get('upper', False)):<3}  Incluir variantes en MAYUSCULAS", COLOR_CYAN))
        print(color_text(f"  Numeros={b(options.get('digits', False)):<3}     Agregar sufijos numericos", COLOR_CYAN))
        print(color_text(f"  Simbolos={b(options.get('specials', False)):<3}    Agregar simbolos especiales", COLOR_CYAN))
        print(color_text(f"  Separadores={b(options.get('use_separators', False)):<3} Unir palabras con _, ., -", COLOR_CYAN))
        print(color_text(f"  SinTildes={b(options.get('remove_accents_flag', True)):<3}   Generar versiones sin acentos", COLOR_CYAN))
        print(color_text(f"  Leet={b(options.get('leet', False)):<3}          Reemplazar letras por numeros", COLOR_CYAN))
        print(color_text(f"  LeetFull={b(options.get('leet_full', False)):<3}      Leet agresivo: TODAS las combinaciones posibles", COLOR_CYAN))
        print(color_text(f"  Complejidad={options['complexity']}      1-5: nivel de mutaciones (reversos, swapcase...)", COLOR_CYAN))
        print(color_text(f"  Ram={options['max_ram']}              GB maximos para deduplicacion en memoria", COLOR_CYAN))
    
    show_help()
    print(color_text("\n[ Sufijos/Prefijos por Defecto ]", COLOR_YELLOW))
    print(color_text("Por defecto se usan: 123, 2026, 2025", COLOR_CYAN))
    print(color_text("Escribe los tuyos separados por coma para REEMPLAZARLOS. ¡Puedes usar letras/símbolos (ej: SH, PRO, !)!", COLOR_CYAN))
    print(color_text("Escribe 'ninguno' para no usar sufijos.", COLOR_CYAN))
    extra_anchors = input(color_text(">> Sufijos (ENTER = Mantener por defecto): ", COLOR_GREEN)).strip()
    if extra_anchors.lower() == "ninguno":
        options["digit_suffixes"] = []
    elif extra_anchors:
        options["digit_suffixes"] = parse_multi_values(extra_anchors)
    else:
        options["digit_suffixes"] = ["123", "2026", "2025"]

    print(color_text("\n[ Ajustes Extra / Sobrescritura ]", COLOR_YELLOW))
    print(color_text("Para modificar o añadir algo extra, usa CLAVE=VALOR (Ej: Simbolos=Si Ram=4)", COLOR_CYAN))
    print(color_text("💡 Tip Hacker: ¿Quieres contraseñas largas (4 palabras juntas) pero sin letras raras?", COLOR_MAGENTA))
    print(color_text("   Elige Nivel 4 y aquí escribe: Leet=No LeetFull=No", COLOR_MAGENTA))

    while True:
        config_input = input(color_text(">> Ajustes (ENTER para continuar con defaults): ", COLOR_GREEN)).strip()
        
        if not config_input:
            break
            
        # Limpieza a prueba de tontos: borrar comas y punto y comas
        clean_input = config_input.replace(",", " ").replace(";", " ")
        parts = clean_input.split()
        
        temp_options = options.copy()
        error_msg = ""
        
        for part in parts:
            if "=" not in part:
                error_msg = f"Formato incorrecto en '{part}'. Debe ser CLAVE=VALOR."
                break
                
            k, v = part.split("=", 1)
            k = k.lower().strip()
            v = v.lower().strip()
            
            valid_bools = {"si": True, "s": True, "true": True, "1": True, "yes": True, "y": True,
                           "no": False, "n": False, "false": False, "0": False}
            
            if k in ("minusculas", "lower", "l"):
                if v not in valid_bools: error_msg = f"Valor '{v}' inválido para {k}. Usa Si o No."; break
                temp_options["lower"] = valid_bools[v]
            elif k in ("mayusculas", "upper", "u"):
                if v not in valid_bools: error_msg = f"Valor '{v}' inválido para {k}. Usa Si o No."; break
                temp_options["upper"] = valid_bools[v]
            elif k in ("numeros", "digits", "d"):
                if v not in valid_bools: error_msg = f"Valor '{v}' inválido para {k}. Usa Si o No."; break
                temp_options["digits"] = valid_bools[v]
            elif k in ("simbolos", "specials", "s"):
                if v not in valid_bools: error_msg = f"Valor '{v}' inválido para {k}. Usa Si o No."; break
                temp_options["specials"] = valid_bools[v]
            elif k in ("separadores", "sep", "use_separators"):
                if v not in valid_bools: error_msg = f"Valor '{v}' inválido para {k}. Usa Si o No."; break
                temp_options["use_separators"] = valid_bools[v]
            elif k in ("sintildes", "tildes", "remove_accents"):
                if v not in valid_bools: error_msg = f"Valor '{v}' inválido para {k}. Usa Si o No."; break
                temp_options["remove_accents_flag"] = valid_bools[v]
            elif k == "leet":
                if v not in valid_bools: error_msg = f"Valor '{v}' inválido para {k}. Usa Si o No."; break
                temp_options["leet"] = valid_bools[v]
            elif k in ("leetfull", "leet_full"):
                if v not in valid_bools: error_msg = f"Valor '{v}' inválido para {k}. Usa Si o No."; break
                temp_options["leet_full"] = valid_bools[v]
            elif k in ("complejidad", "comp", "complexity"):
                if not v.isdigit():
                    error_msg = f"La Complejidad debe ser un número entero, no '{v}'."
                    break
                temp_options["complexity"] = int(v)
            elif k in ("mezcla", "mix", "combo"):
                if v == "auto":
                    temp_options["mezcla"] = "auto"
                elif v in ("1", "2", "3"):
                    temp_options["mezcla"] = int(v)
                else:
                    error_msg = f"Mezcla debe ser 1, 2, 3 o 'auto'. No '{v}'."
                    break
            elif k in ("ram", "max_ram", "memoria"):
                if not v.isdigit() or int(v) < 1:
                    error_msg = f"La RAM debe ser un número entero mayor a 0, no '{v}'."
                    break
                temp_options["max_ram"] = int(v)
            else:
                error_msg = f"Ajuste desconocido: '{k}'. Revisa los nombres permitidos."
                break
                
        if error_msg:
            print(color_text(f"[!] Error: {error_msg} Inténtalo de nuevo.", COLOR_MAGENTA))
        else:
            options.update(temp_options)
            break
            
    print(color_text(f"[*] Configuración Final: \n    {get_summary()}", COLOR_CYAN))
    sufijos = options.get("digit_suffixes", [])
    print(color_text(f"    Sufijos: {', '.join(sufijos) if sufijos else '(ninguno)'}", COLOR_CYAN))
    print()
    while True:
        print(color_text(f"  ENTER = Generar  |  R = Volver a empezar", COLOR_YELLOW))
        choice = input(color_text("  > ", COLOR_GREEN)).strip().lower()
        if choice == "":
            return options
        elif choice == "r":
            print(color_text("\n  ♻ Volviendo a empezar...\n", COLOR_CYAN))
            return ask_config()
        else:
            print(color_text("  [!] Opción no válida. Pulsa ENTER para generar o escribe 'r' para reconfigurar.", COLOR_MAGENTA))

def main():
    parser = argparse.ArgumentParser(description="SELIC mini - Generador rápido")
    parser.add_argument("-p", "--pattern", help="Patrón avanzado (ej: #%?CO)")
    args = parser.parse_args()

    print_mini_logo()
    
    print(color_text("Instrucciones: Escribe los datos clave de la persona separados por comas.", COLOR_CYAN))
    print(color_text("Ejemplo: Juan Jose Diaz Rojas, 19/04/2002, rojo, unsm, batman", COLOR_YELLOW))
    print()
    while True:
        user_input = input(color_text(">> Ingrese datos del objetivo: ", COLOR_GREEN)).strip()
        if user_input:
            break
        print(color_text("[!] Error: No puedes dejar esto vacío. Escribe al menos un dato.", COLOR_MAGENTA))
        
    print()
    while True:
        min_len_input = input(color_text(">> Longitud mínima [4]: ", COLOR_GREEN)).strip()
        if not min_len_input:
            min_length = 4
            break
        if min_len_input.isdigit() and int(min_len_input) > 0:
            min_length = int(min_len_input)
            break
        print(color_text("[!] Error: La longitud debe ser un número mayor a 0.", COLOR_MAGENTA))
    
    while True:
        max_len_input = input(color_text(">> Longitud máxima (ENTER = sin límite): ", COLOR_GREEN)).strip()
        if not max_len_input:
            max_length = 999
            break
        if max_len_input.isdigit() and int(max_len_input) >= min_length:
            max_length = int(max_len_input)
            break
        print(color_text(f"[!] Error: Debe ser un número mayor o igual a {min_length}.", COLOR_MAGENTA))
    print()
    
    # Soporte de Patrones
    pattern = args.pattern
    if not pattern:
        print(color_text("\n[ Patrones Avanzados ]", COLOR_YELLOW))
        print(color_text("  Marcadores disponibles:", COLOR_CYAN))
        print(color_text("    # : Datos sociales (Nombres, DNI, Años...)", COLOR_GREEN))
        print(color_text("    % : Números (0-9)", COLOR_GREEN))
        print(color_text("    @ : Letras minúsculas (a-z)", COLOR_GREEN))
        print(color_text("    , : Letras MAYÚSCULAS (A-Z)", COLOR_GREEN))
        print(color_text("    ? : Símbolos especiales (!@#$...)", COLOR_GREEN))
        print(color_text("    \\ : Carácter literal (ej: \\# para un '#' real)", COLOR_GREEN))
        print(color_text("\n>> ¿Desea usar patrones avanzados? (Ej: #%?2026 | ENTER = No)", COLOR_CYAN))
        pattern = input(color_text("   > ", COLOR_GREEN)).strip()
    
    options_patterns = [pattern] if pattern else []

    raw_tokens = parse_mini_input(user_input)
    
    options = {
        "lower": True,
        "upper": True,
        "digits": True,
        "specials": False,
        "leet": True,
        "max_leet_replacements": 8,
        "complexity": 2,
        "leet_mappings": {
            "a": "4", "A": "4", "s": "$", "S": "$", "o": "0", "O": "0",
            "i": "1", "I": "1", "e": "3", "E": "3", "l": "1", "L": "1",
        },
        "digit_suffixes": [],
        "numeric_parts": [],
        "allow_extreme_generation": False,
        "extreme_generation_limit": 5000000000,
        "patterns": options_patterns
    }
    
    options = ask_config(options)

    # Process numeric parts for digits
    numeric_parts = []
    base_tokens = set()
    use_seps = options.get("use_separators", False)
    for token in raw_tokens:
        base_tokens.update(normalize_token(token, False, True, use_seps))
        for t in normalize_token(token, False, True, use_seps):
            if t.isdigit():
                numeric_parts.append(t)
    
    options["numeric_parts"] = sorted(set(numeric_parts))
    base_tokens = sorted({t for t in base_tokens if len(t) > 1})

    print(color_text(f"[*] Base de palabras identificadas: {len(base_tokens)}", COLOR_CYAN))
    
    # Si el usuario fijó mezcla manualmente, usarla directamente
    mezcla_setting = options.get("mezcla", "auto")
    if isinstance(mezcla_setting, int) and mezcla_setting in (1, 2, 3):
        force_max_combo = mezcla_setting
        show_pre_generation_summary(len(base_tokens), force_max_combo, options, interactive=True)
    else:
        force_max_combo = check_and_prompt_limits(len(base_tokens), options, interactive=True)
    
    print(color_text("[*] Generando...", COLOR_YELLOW))
    
    start_time = time.time()
    candidate_iterables = []
    
    # Inyectar Patrones si existen
    char_pool = build_char_pool("all", base_tokens, options)
    if options.get("patterns"):
        candidate_iterables.append(generate_from_patterns(
            options["patterns"], char_pool, min_length, max_length
        ))

    agr = options.get("agresividad", 4)
    if agr == 4:
        for t in range(1, 5):
            candidate_iterables.append(generate_tiered_variants(base_tokens, options, t, count_limit=None, max_length=max_length))
    else:
        for t in range(1, agr + 1):
            candidate_iterables.append(generate_tiered_variants(base_tokens, options, t, count_limit=None, max_length=max_length))
    
    output_file = "mini_output.txt"
    
    stop_event = threading.Event()
    progress_state = {"current": None, "generated": 0}
    progress_thread = threading.Thread(target=show_progress, args=(stop_event, "calculando...", progress_state, output_file))
    progress_thread.daemon = True
    progress_thread.start()
    
    try:
        written = stream_candidates_to_file(
            output_file,
            candidate_iterables,
            min_length=min_length,
            max_length=max_length,
            count_limit=None,
            progress_state=progress_state,
            max_ram_gb=options.get("max_ram", 3),
            show_live=True
        )
    except KeyboardInterrupt:
        stop_event.set()
        progress_thread.join()
        print(color_text("\n[!] Generación cancelada por el usuario.", COLOR_MAGENTA))
        sys.exit(1)
    
    stop_event.set()
    progress_thread.join()
    
    elapsed = time.time() - start_time
    print(color_text(f"✓ Generadas {written:,} variantes en {elapsed:.2f} segundos.", COLOR_GREEN))
    print(color_text(f"✓ Guardado en {output_file}", COLOR_GREEN))

if __name__ == "__main__":
    main()
