#!/usr/bin/env python3
__version__ = "1.2.0"
r"""
Social engineering wordlist generator for Kali Linux.
Generates password wordlists from social information, dictionary words, patterns,
mutations, permutations and complexity levels.

Usage examples:
  python3 selic.py --name "Juan" --color "rojo" --pattern "IV#%?CO" \
    --output wordlist.txt

Patrones Avanzados (Crunch-style):
  # -> Datos Sociales (lo que tú ingreses)
  % -> Números (0-9)
  @ -> Letras minúsculas (a-z)
  , -> Letras mayúsculas (A-Z)
  ? -> Símbolos especiales (!@#$...)
  \ -> Escape (ej: \# para un '#' literal)

If no arguments are provided, the script enters interactive mode.
"""

import argparse
import configparser
import datetime
import gc
import itertools
import os
import platform
import random
import re
import subprocess
import sys
from collections import deque
import time
import threading
try:
    import tkinter as tk
    from tkinter import simpledialog, messagebox
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

from selic_core import *
from selic_core import _combo_name, get_projected_level, show_pre_generation_summary, show_impact_comparison

DEFAULT_DICT_FILE = "wordlist.txt"
DEFAULT_OUTPUT_FILE = "passlist.txt"
DEFAULT_BASE_DIR = ""
DEFAULT_CONFIG_FILE = "selic.cfg"


def print_header():
    # Definición de colores ANSI
    C = "\033[38;5;51m" # Cian claro
    B = "\033[38;5;33m" # Azul brillante
    D = "\033[38;5;21m" # Azul oscuro
    W = "\033[0m"        # Reset (Blanco/Gris)

    banner = f"""
    {C}███████╗███████╗██╗     ██╗ ██████╗
    {C}██╔════╝██╔════╝██║     ██║██╔════╝
    {B}███████╗█████╗  ██║     ██║██║     
    {B}╚════██║██╔══╝  ██║     ██║██║     
    {D}███████║███████╗███████╗██║╚██████╗
    {D}╚══════╝╚══════╝╚══════╝╚═╝ ╚═════╝
    {W}
    {C}[+]{W} Social Engineering List Creator
    {C}[+]{W} Version: 1.2.0
    {C}[+]{W} Creador:M.A.P.A
    """
    print(banner)


def print_question(label, text):
    print("\n" + color_text(f"[{label}]", "\033[38;5;51m") + (" " + text if text else ""))


def resolve_path(base_dir, file_name):
    if not file_name:
        return None
    if os.path.isabs(file_name):
        return file_name
    if base_dir:
        return os.path.join(base_dir, file_name)
    return file_name




def parse_config_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "si", "s", "on")


def parse_config_int(value, default=None):
    if value is None:
        return default
    try:
        text = str(value).strip()
        return int(text) if text else default
    except ValueError:
        return default


def validate_length_params(min_len, max_len, count):
    """Valida parámetros de longitud."""
    errors = []
    if min_len < 1:
        errors.append("Longitud mínima debe ser al menos 1")
    if max_len < min_len:
        errors.append("Longitud máxima debe ser mayor o igual a la mínima")
    if max_len > 100:  # Límite razonable
        errors.append("Longitud máxima no puede exceder 100 caracteres")
    if count is not None and count < 1:
        errors.append("Cantidad máxima debe ser al menos 1")
    return errors


def estimate_wordlist_size(config, social_tokens):
    """Estima el tamaño aproximado de la wordlist."""
    base_count = len(social_tokens)
    if not base_count:
        return 0
    
    # Factores de variantes de caso
    case_variants = 1
    if config.get("lower") and config.get("upper"):
        case_variants = 3  # lowercase, UPPERCASE, Capitalize
    elif config.get("lower") or config.get("upper"):
        case_variants = 1
    
    # Suffixes numéricos (DEFAULT + custom + birth years + numeric parts)
    suffixes_count = len(DEFAULT_DIGIT_SUFFIXES)
    suffixes_count += len(config.get("digit_suffixes") or [])
    suffixes_count += len(config.get("birth_year") or [])
    suffixes_count += len(config.get("numeric_parts") or [])
    suffixes_count = max(1, suffixes_count)
    
    # Símbolos especiales
    specials_count = len(DEFAULT_SPECIALS) if config.get("specials") else 0
    
    # Variantes por token: caso base
    token_variants = case_variants
    
    # Añadir variantes de dígitos (token+num, pero con pérdidas por longitud)
    if config.get("digits") and suffixes_count > 0:
        token_variants += min(case_variants * suffixes_count, case_variants * 5)
    
    # Añadir variantes de especiales
    if config.get("specials") and specials_count > 0:
        token_variants += min(case_variants * specials_count, case_variants * 3)
    
    # Combinaciones digits+specials (solo si ambos activos)
    if config.get("digits") and config.get("specials") and suffixes_count > 0 and specials_count > 0:
        token_variants += min(case_variants * 2, case_variants)  # Small bonus
    
    # Leet mutations (duplica variantes aproximadamente)
    if config.get("leet"):
        token_variants = int(token_variants * 1.5)
    
    # Complejidad alta añade pocas variantes más (!, 2024, etc.)
    complexity = config.get("complexity", 2)
    if complexity >= 4:
        token_variants += min(case_variants, 2)
    
    # Permutaciones de tokens (1, 2, 3 tokens combinados)
    # Pero muchas se pierden por longitud máxima, así que usar factor conservador
    token_combinations = 1  # Tokens de 1 elemento
    if base_count > 1:
        token_combinations += min(base_count, 20)  # Tokens de 2 elementos (limitado por longitud max)
    if base_count > 10:
        token_combinations += min(base_count // 10, 3)  # Tokens de 3 elementos (muy limitado)
    
    # Patrones (Cálculo exacto para los nuevos marcadores)
    pattern_count = 0
    patterns = config.get("patterns", [])
    if patterns:
        social_size = len(social_tokens) or 10  # Fallback si no hay tokens
        MARKER_SIZES = {"#": social_size, "%": 10, "@": 26, ",": 26, "?": 30}
        for pattern in patterns:
            combos = 1
            for char in pattern:
                if char in MARKER_SIZES:
                    combos *= MARKER_SIZES[char]
            pattern_count += combos
    
    # Filtro de longitud: muchas se pierden
    max_len = config.get("max_length", 32)
    min_len = config.get("min_length", 4)
    length_penalty = 0.7 if max_len < 16 else 1.0
    
    # Cálculo final
    estimated = int(base_count * token_variants * token_combinations * length_penalty) + pattern_count
    return min(estimated, 50000000)


def load_config_file(path):
    config = configparser.ConfigParser(comment_prefixes=("#", ";"), strict=False)
    if not path:
        return config
    try:
        config.read(path, encoding="utf-8")
    except Exception:
        pass
    return config


def load_config_defaults(config_path):
    config = load_config_file(config_path)
    defaults = {}
    if config.has_section("defaults"):
        sec = config["defaults"]
        defaults = {
            "name": sec.get("name"),
            "color": sec.get("color"),
            "birth_year": parse_multi_values(sec.get("birth_year")),
            "year": parse_multi_values(sec.get("year")),
            "family_name": sec.get("family_name"),
            "family_years": parse_multi_values(sec.get("family_years")),
            "team": sec.get("team"),
            "birth_place": sec.get("birth_place"),
            "living_city": sec.get("living_city"),
            "dni": sec.get("dni"),
            "pet": sec.get("pet"),
            "singer": sec.get("singer"),
            "other": parse_multi_values(sec.get("other")),
            "dict_file": sec.get("dict_file"),
            "output_file": sec.get("output_file"),
            "base_dir": sec.get("base_dir"),
            "patterns": parse_multi_values(sec.get("patterns")),
            "hash_mode": sec.get("hash_mode", "all"),
            "min_length": parse_config_int(sec.get("min_length"), 4),
            "max_length": parse_config_int(sec.get("max_length"), 32),
            "count": parse_config_int(sec.get("count"), None),
            "lower": parse_config_bool(sec.get("lower"), True),
            "upper": parse_config_bool(sec.get("upper"), True),
            "digits": parse_config_bool(sec.get("digits"), True),
            "specials": parse_config_bool(sec.get("specials"), False),
            "leet": parse_config_bool(sec.get("leet"), True),
            "digit_suffixes": (parse_multi_values(sec.get("default_suffixes", "123, 2026, 2025")) or []) + (parse_multi_values(sec.get("extra_suffixes")) or []),
            "extra_common_passwords": parse_multi_values(sec.get("extra_common_passwords")),
            "decompose_numbers": parse_config_bool(sec.get("decompose_numbers"), False),
            "max_ram": parse_config_int(sec.get("max_ram"), 3),
            "max_template_expansion": parse_config_int(sec.get("max_template_expansion"), 100000000),
        }
    leet_mappings = {}
    if config.has_section("leet"):
        for key in config["leet"]:
            leet_mappings[key] = config["leet"][key]
    defaults["leet_mappings"] = leet_mappings or {
        "a": "4",
        "A": "4",
        "s": "$",
        "S": "$",
        "o": "0",
        "O": "0",
        "i": "1",
        "I": "1",
        "e": "3",
        "E": "3",
        "l": "1",
        "L": "1",
    }
    return defaults


def format_default_value(value):
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)


def get_default_label(value):
    return color_text(str(value), COLOR_CYAN) if value is not None else color_text("omitir", COLOR_ORANGE)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generador avanzado de wordlists de ingeniería social.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--name", help="Nombre completo, nombre de pila o apellido.")
    parser.add_argument("--color", help="Color favorito.")
    parser.add_argument("--birth-year", action="append", help="Fecha de nacimiento en DD/MM/YYYY, DD-MM-YYYY o solo año. Se pueden agregar varias separadas por comas o espacios.")
    parser.add_argument("--year", action="append", help="Otra fecha importante en DD/MM/YYYY, DD-MM-YYYY o solo año. Se pueden agregar varias separadas por comas o espacios.")
    parser.add_argument("--dni", help="DNI o documento.")
    parser.add_argument("--city", help="Ciudad.")
    parser.add_argument("--pet", help="Nombre de la mascota.")
    parser.add_argument("--singer", help="Cantante o banda favorita.")
    parser.add_argument("--other", action="append", help="Otros campos genéricos. Se puede repetir.")
    parser.add_argument("--dict", default=DEFAULT_DICT_FILE, help="Archivo de diccionario base opcional (.txt). Si no existe o se omite, se genera desde datos sociales.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE, help="Archivo de salida para la wordlist.")
    parser.add_argument("--base-dir", default=DEFAULT_BASE_DIR, help="Directorio base para el diccionario y el archivo de salida.")
    parser.add_argument("--pattern", action="append", help="Plantilla personalizada. Marcadores: # (Social), % (Núm), @ (min), , (MAY), ? (Símb). Ej: IV#%?CO")
    parser.add_argument("--digit-suffixes", "--extra", action="append", help="Sufijos/Prefijos personalizados (letras, números o símbolos).")
    parser.add_argument("--hash-mode", choices=["letters", "digits", "specials", "all", "base"], default="all",
                        help="Reemplazo global de '#' si no se usan marcadores avanzados.")
    parser.add_argument("--min-length", type=int, default=4, help="Longitud mínima de las contraseñas.")
    parser.add_argument("--max-length", type=int, default=32, help="Longitud máxima de las contraseñas.")
    parser.add_argument("--count", type=int, help="Número máximo de contraseñas a generar.")
    parser.add_argument("--lower", action="store_true", help="Forzar solo minúsculas en las variaciones.")
    parser.add_argument("--upper", action="store_true", help="Forzar solo mayúsculas en las variaciones.")
    parser.add_argument("--digits", action="store_true", help="Incluir dígitos en las variaciones.")
    parser.add_argument("--specials", action="store_true", help="Incluir caracteres especiales en las variaciones.")
    parser.add_argument("--leet", dest="leet", action="store_true", help="Activar modo leet (reemplazos como a=4, e=3, o=0).")
    parser.add_argument("--no-leet", dest="leet", action="store_false", help="Desactivar modo leet.")
    parser.set_defaults(leet=True)
    parser.add_argument("--complexity", type=int, choices=[1, 2, 3, 4, 5], default=2, help="Nivel de complejidad de generación (1=básico, 5=máximo).")
    parser.add_argument("--agresividad", type=int, choices=[1, 2, 3, 4], default=4, help="Nivel de agresividad/profundidad (1=básico, 4=fuerza bruta ordenada).")
    parser.add_argument("--decompose-numbers", action="store_true", help="Descomponer números en fragmentos solo para años/documentos. El diccionario numérico no se divide.")
    parser.add_argument("--max-ram", type=int, default=3, help="RAM máxima en GB para deduplicación en memoria (default: 3).")
    parser.add_argument("--config", default=DEFAULT_CONFIG_FILE, help="Archivo de configuración externa con valores predeterminados.")
    parser.add_argument("--gui", action="store_true", help="Abrir interfaz gráfica básica si está disponible.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Forzar modo interactivo por terminal, similar a cupp -i.")
    parser.add_argument("--setup", action="store_true", help="Abrir asistente para configurar los valores predeterminados de forma interactiva.")
    parser.add_argument("--force-extreme", action="store_true", help="Forzar combinaciones extremas ignorando el límite de seguridad (puede generar archivos gigantes).")

    args = parser.parse_args()
    return args



def prompt_interactive(defaults=None):
    defaults = defaults or {}
    print_header()
    print(color_text("=== MODO INTERACTIVO DE INGENIERÍA SOCIAL ===", COLOR_CYAN))
    print(color_text("💡 Tip: Los valores entre CORCHETES [ ] son los predeterminados.", COLOR_YELLOW))
    print(color_text("   Si presionas ENTER sin escribir nada, SELIC usará lo que esté dentro de [ ].", COLOR_YELLOW))
    print(color_text("   En opciones (s/n), la letra MAYÚSCULA indica la elección automática.", COLOR_YELLOW))
    print(color_text("   (Ej: [S/n] -> ENTER es SÍ | [s/N] -> ENTER es NO).", COLOR_YELLOW))
    print("-------------------------------------------------------------------------")
    print("Datos objetivo — responde solo lo que conozcas.")
    print("  • ENTER omite la pregunta")
    print("  • Separa valores con espacios o comas")
    print("-------------------------------------------------------------------------")
    params = {}
    print_question("01", "Nombre completo / alias de la persona objetivo")
    default_name = defaults.get("name")
    if default_name is not None:
        print(f"    ENTER = usar [{color_text(default_name, COLOR_GREEN)}] | Ej: Marco Antonio")
    else:
        print("    ENTER = omitir | Ej: Marco Antonio")
    user_input = input("    > ").strip()
    params["name"] = user_input if user_input else default_name
    print_question("02", "Fecha(s) de nacimiento de la persona objetivo (DD/MM/YYYY, DD-MM-YYYY o solo año)")
    default_birth = defaults.get("birth_year")
    if default_birth is not None:
        print(f"    ENTER = usar [{color_text(str(default_birth), COLOR_GREEN)}] | Separa con comas")
    else:
        print("    ENTER = omitir | Ej: 08/04/2005, 2010")
    print("    Si son varias fechas/años, sepáralas con espacios o comas.")
    print(f"    Ej: {color_text('08/04/2005', COLOR_ORANGE)}, {color_text('2010', COLOR_ORANGE)} o {color_text('2005', COLOR_ORANGE)}")
    while True:
        birth_input = input("    > ").strip()
        if not birth_input:
            params["birth_year"] = default_birth
            break
        vals = parse_multi_values(birth_input)
        invalid_dates = [d for d in vals if not validate_date(d)]
        if invalid_dates:
            print(color_text(f"    [!] Error: Formato inválido en: {', '.join(invalid_dates)}", COLOR_MAGENTA))
            print(color_text("    Usa DD/MM/YYYY o el año. (Presiona ENTER para omitir)", COLOR_ORANGE))
            continue
        params["birth_year"] = vals
        break
    print_question("03", "Otra(s) fecha(s) importante(s) de la persona objetivo (DD/MM/YYYY, DD-MM-YYYY o solo año)")
    default_year = defaults.get("year")
    if default_year is not None:
        print(f"    ENTER = omitir | predeterminado: {get_default_label(format_default_value(default_year))}")
    print("    Si son varias fechas/años, sepáralas con espacios o comas.")
    print(f"    Ej: {color_text('14/02/2010', COLOR_ORANGE)}, {color_text('2022', COLOR_ORANGE)} o {color_text('2010', COLOR_ORANGE)}")
    while True:
        year_input = input("    > ").strip()
        if not year_input:
            params["year"] = None
            break
        vals = parse_multi_values(year_input)
        invalid_dates = [d for d in vals if not validate_date(d)]
        if invalid_dates:
            print(color_text(f"    [!] Error: Formato inválido en: {', '.join(invalid_dates)}", COLOR_MAGENTA))
            print(color_text("    Usa DD/MM/YYYY o el año. (Presiona ENTER para omitir)", COLOR_ORANGE))
            continue
        params["year"] = vals
        break

    print_question("04", "DNI o documento de identidad")
    print("    (Puedes incluir letras si el documento de tu país las usa).")
    default_dni = defaults.get("dni")
    if default_dni is not None:
        print(f"    ENTER = usar [{color_text(default_dni, COLOR_GREEN)}] | Ej: 12345678A")
    else:
        print("    ENTER = omitir | Ej: 12345678A")
    while True:
        user_input = input("    > ").strip()
        if not user_input:
            params["dni"] = default_dni
            break
        if not validate_dni(user_input):
            print(color_text(f"    [!] Error: Documento inválido (4-15 caracteres alfanuméricos).", COLOR_MAGENTA))
            continue
        params["dni"] = user_input
        break
    print_question("05", "Nombre del papá/mamá u otro familiar cercano")
    default_family_name = defaults.get("family_name")
    if default_family_name is not None:
        print(f"    ENTER = omitir | predeterminado: {get_default_label(format_default_value(default_family_name))}")
    else:
        print("    (Ej: Juan, María, hermano, hermana) | ENTER = omitir")
    user_input = input("    > ").strip()
    params["family_name"] = user_input if user_input else default_family_name
    print_question("06", "Fecha(s) de nacimiento de padres o hermanos (DD/MM/YYYY, DD-MM-YYYY o solo año)")
    default_family_years = defaults.get("family_years")
    if default_family_years is not None:
        print(f"    ENTER = omitir | predeterminado: {get_default_label(format_default_value(default_family_years))}")
    print("    Si son varias fechas/años, sepáralas con espacios o comas.")
    while True:
        family_years_input = input("    > ").strip()
        if not family_years_input:
            params["family_years"] = None
            break
        vals = parse_multi_values(family_years_input)
        invalid_dates = [d for d in vals if not validate_date(d)]
        if invalid_dates:
            print(color_text(f"    [!] Error: Formato inválido en: {', '.join(invalid_dates)}", COLOR_MAGENTA))
            print(color_text("    Usa DD/MM/YYYY o el año. (Presiona ENTER para omitir)", COLOR_ORANGE))
            continue
        params["family_years"] = vals
        break
    print_question("07", f"¿Descomponer fechas en fragmentos? [{color_text('s/N', COLOR_GREEN)}]")
    print("    Se extraen día, mes y año de fechas (08/04/2005 -> 08, 04, 2005, 0804).")
    print("    La opción agrega fragmentos adicionales como 20, 05, 200, 005.")
    params["decompose_number_dates"] = yes_no_input("    > ", default="n")
    print_question("08", f"¿Descomponer el documento de identidad en fragmentos? [{color_text('s/N', COLOR_GREEN)}]")
    print(color_text("    ⚠ IMPACTO MEDIO: Multiplica las palabras base extraídas del DNI.", COLOR_YELLOW))
    params["decompose_number_document"] = yes_no_input("    > ", default="n")
    params["decompose_numbers"] = params["decompose_number_dates"] or params["decompose_number_document"]
    print_question("09", f"¿Generar versiones sin tildes/acentos? [{color_text('S/n', COLOR_GREEN)}]")
    print(color_text("    ⚠ IMPACTO ALTO: Duplica el tamaño para nombres con tilde (José -> Jose).", COLOR_ORANGE))
    params["remove_accents_flag"] = yes_no_input("    > ", default="s")
    print_question("10", "Información adicional del objetivo")
    print("    Escribe cualquier dato relevante de la persona objetivo:")
    print(f"    {color_text('color favorito, equipo/deporte, ciudad, mascota, cantante,', COLOR_CYAN)}")
    print(f"    {color_text('empresa, hobby, apodo, nickname, universidad, etc.', COLOR_CYAN)}")
    print(f"    El orden {color_text('NO', COLOR_GREEN)} importa. Puedes separar con comas o espacios,")
    print("    o escribir uno por línea. ENTER en línea vacía = continuar.")
    others = []
    while True:
        extra = input("    > ").strip()
        if not extra:
            break
        others.extend(parse_multi_values(extra) or [])
    params["other"] = others or None
    # Lógica inteligente de mayúsculas/minúsculas en cascada (con descarte)
    print_question("11", f"¿Mezclar mayúsculas y minúsculas? [{color_text('S/n', COLOR_GREEN)}]")
    mix_case = yes_no_input("    > ", default="s")
    if mix_case:
        params["lower"] = True
        params["upper"] = True
    else:
        print_question("11-B", f"¿Usar SOLO minúsculas? [{color_text('S/n', COLOR_GREEN)}]")
        only_lower = yes_no_input("    > ", default="s")
        if only_lower:
            params["lower"] = True
            params["upper"] = False
        else:
            # Descarte inteligente para evitar lista vacía
            print(color_text("    (!) Se usarán SOLO MAYÚSCULAS por descarte.", COLOR_YELLOW))
            params["lower"] = False
            params["upper"] = True

    print_question("12", f"¿Incluir dígitos automáticos (sufijos)? [{color_text('S/n', COLOR_GREEN)}]")
    params["digits"] = yes_no_input("    > ", default="s")

    print_question("12-B", "Prefijos / Sufijos (Anclas)")
    print("    Escribe letras, números o símbolos que quieras pegar al inicio/final de CADA palabra.")
    print("    Ej: SH, PRO, !, 2025 (Separa con comas)")
    default_suf = defaults.get("digit_suffixes") or []
    print(f"    Sufijos Base Configurados: {color_text(', '.join(default_suf), COLOR_GREEN)}")
    print("    ENTER = Usar la lista Base | 'ninguno' = Borrar todos | o escribe sufijos manualmente para REEMPLAZAR la lista entera")
    extra_input = input("    > ").strip()
    if extra_input.lower() == "ninguno":
        params["digit_suffixes"] = []
    elif extra_input:
        params["digit_suffixes"] = parse_multi_values(extra_input)
    else:
        params["digit_suffixes"] = default_suf

    print_question("13", f"¿Incluir caracteres especiales? [{color_text('s/N', COLOR_GREEN)}]")
    params["specials"] = yes_no_input("    > ", default="n")

    print_question("14", f"¿Usar separadores (_, ., -) entre palabras? [{color_text('s/N', COLOR_GREEN)}]")
    params["use_separators"] = yes_no_input("    > ", default="n")

    print_question("15", f"¿Activar modo Leet Speak (a=4, e=3...)? [{color_text('s/N', COLOR_GREEN)}]")
    params["leet"] = yes_no_input("    > ", default="n")
    if params["leet"]:
        print("    ¿Límite de mutaciones Leet por palabra? (1-20) [8]")
        print("    " + color_text("    ⚠ IMPACTO ALTO: Valores altos multiplican drásticamente las combinaciones.", COLOR_ORANGE))
        print("    10 es suficiente para cubrir el 99.9% de contraseñas humanas complejas.")
        print(f"    ENTER = {color_text('8', COLOR_GREEN)}")
        params["max_leet_replacements"] = safe_int_input("    > ", 8, min_value=1, max_value=20)
    else:
        params["max_leet_replacements"] = 8
    params["color"] = None
    params["team"] = None
    params["birth_place"] = None
    params["living_city"] = None
    params["pet"] = None
    params["singer"] = None
    params["dict_file"] = None
    print_question("16", "Archivo de salida")
    default_output = defaults.get("output_file") or DEFAULT_OUTPUT_FILE
    print(f"    ENTER = {color_text(default_output, COLOR_GREEN)}")
    params["output_file"] = input("    > ").strip() or default_output
    print_question("17", "Directorio base para los archivos")
    default_base = defaults.get("base_dir")
    if default_base is not None:
        print(f"    ENTER = actual | predeterminado: {get_default_label(format_default_value(default_base))}")
    else:
        print("    ENTER = actual")
    print("    Ej: /home/kali/Documents o C:\\Users\\TuUsuario\\Documents")
    print("    Si el directorio no existe, podrás reintentar o usar el actual")
    while True:
        base_dir = input("    > ").strip()
        if not base_dir:
            params["base_dir"] = None
            break
        if os.path.isdir(base_dir):
            params["base_dir"] = base_dir
            break
        else:
            print(f"    ¡Error! El directorio '{base_dir}' no existe.")
            retry = input("    ¿Quieres reintentar (r) o usar el directorio actual (ENTER)? ").strip().lower()
            if retry != "r":
                params["base_dir"] = None
                break
                
    # Resolver path usando la nueva lógica compartida
    params["output_file"] = resolve_output_path(params["output_file"], "cli", params.get("base_dir"))
    print_question("18", f"¿Usar patrones avanzados? (#, %, @, ,, ?) [{color_text('s/N', COLOR_GREEN)}]")
    print(f"    Ejemplos: {color_text('7###C', COLOR_ORANGE)}, {color_text('###@2026', COLOR_ORANGE)}, {color_text('Nombre##!', COLOR_ORANGE)}")
    print("    Cada marcador (#, %, @, ,, ?) es un marcador de posición que se reemplaza por un solo carácter.")
    print("    El patrón se completa carácter por carácter (estilo Crunch).")
    print("    No se toma un grupo de marcadores como una palabra o fragmento entero.")
    print(f"    Ej: {color_text('7####E', COLOR_ORANGE)} => 7 + 4 caracteres + E.")
    print("    Si quieres usar un dato literal (ej: un nombre), escríbelo directamente: 7MarcoE")
    print("\n    Marcadores disponibles:")
    print(f"      {color_text('#', COLOR_CYAN)} : Datos sociales (tus nombres, años, etc.)")
    print(f"      {color_text('%', COLOR_CYAN)} : Números (0-9)")
    print(f"      {color_text('@', COLOR_CYAN)} : Letras minúsculas (a-z)")
    print(f"      {color_text(',', COLOR_CYAN)} : Letras MAYÚSCULAS (A-Z)")
    print(f"      {color_text('?', COLOR_CYAN)} : Símbolos especiales (!@#$...)")
    print(f"      {color_text('\\', COLOR_CYAN)} : Carácter literal (ej: \\# para un '#' real)")
    
    use_patterns = yes_no_input("    > ", default="n")
    patterns = []
    if use_patterns:
        print("\n    " + color_text("--- LEYENDA DE MARCADORES ---", COLOR_CYAN))
        print(f"    {color_text('#', COLOR_CYAN)} : Tus datos sociales  | {color_text('%', COLOR_CYAN)} : Números (0-9)")
        print(f"    {color_text('@', COLOR_CYAN)} : Minúsculas (a-z)    | {color_text(',', COLOR_CYAN)} : MAYÚSCULAS (A-Z)")
        print(f"    {color_text('?', COLOR_CYAN)} : Símbolos (!@#$...)  | {color_text('\\', COLOR_CYAN)} : Literal (ej: \\#)")
        print("    -----------------------------\n")
        
        while True:
            print("    Ingresa patrón [ENTER para terminar]:")
            patt = input("    > ").strip()
            if not patt:
                break
            patterns.append(patt)
        
        if patterns:
            params["patterns"] = patterns
        else:
            print(color_text("    [!] No ingresaste patrones. Continuando sin ellos...", COLOR_ORANGE))
            params["patterns"] = None
            params["hash_mode"] = "all"
    else:
        params["patterns"] = None
        params["hash_mode"] = "all"
    print_question("19", "Longitud de las contraseñas:")
    print("    - Se basa en el número de caracteres de cada contraseña generada.")
    print(f"    - Por defecto {color_text('4-32', COLOR_GREEN)} para combinar datos sociales con números y símbolos.")
    print("    - Ajusta según lo que esperes, puedes usar 1 si necesitas contraseñas muy cortas.")
    params["min_length"] = safe_int_input("    Longitud mínima [4]: ", 4)
    params["max_length"] = safe_int_input("    Longitud máxima [32]: ", 32)
    errors = validate_length_params(params["min_length"], params["max_length"], None)
    if errors:
        for error in errors:
            print(color_text(error, COLOR_MAGENTA))
        log_error(f"Errores en longitudes: {errors}")
    print_question("20", "Cantidad máxima de contraseñas")
    params["count"] = safe_int_input(f"    ENTER = {color_text('ilimitado', COLOR_GREEN)} | > ", None)
    if params["count"] is not None and params["count"] < 1:
        print(color_text("Cantidad máxima debe ser al menos 1.", COLOR_MAGENTA))
        log_error(f"Cantidad inválida: {params['count']}")

    
    print_question("21", f"Nivel de Complejidad de mutación (1-5) [{color_text('2', COLOR_GREEN)}]")
    print("    Define la profundidad de las variaciones Leet y gramaticales:")
    print(f"      {color_text('1', COLOR_CYAN)}: Básico (Solo minúsculas/mayúsculas simples)")
    print(f"      {color_text('2', COLOR_CYAN)}: Estándar (Leet común, años cortos, etc.)")
    print(f"      {color_text('3', COLOR_CYAN)}: Avanzado (Leet múltiple, variaciones de fechas)")
    print(f"      {color_text('4', COLOR_CYAN)}: Muy Alto (Combinaciones profundas de símbolos/números)")
    print(f"      {color_text('5', COLOR_CYAN)}: Extremo (Máxima mutación, wordlists gigantes)")
    ans_comp = input("    > ").strip()
    params["complexity"] = int(ans_comp) if ans_comp.isdigit() else 2

    print_question("22", f"Nivel de Mezcla (Max Combo) (1-4) [{color_text('Auto', COLOR_GREEN)}]")
    print("    Define cuántas palabras se unen para formar una sola contraseña:")
    print(f"      {color_text('1', COLOR_CYAN)}: Individual (ej: 'marco')")
    print(f"      {color_text('2', COLOR_CYAN)}: Parejas (ej: 'marco2026')")
    print(f"      {color_text('3', COLOR_CYAN)}: Tríos (ej: 'marco2026!')")
    print(f"      {color_text('4', COLOR_CYAN)}: Cuartetos (ej: 'marco2026perro!')")
    print("    ENTER = Selección automática segura según complejidad.")
    ans_mezcla = input("    > ").strip()
    params["mezcla"] = int(ans_mezcla) if ans_mezcla.isdigit() else "auto"

    # Diagnóstico de Agresividad antes de preguntar
    from selic_core import get_projected_level, _combo_name
    
    # Calculamos el combo máximo real que se usará (Lógica mejorada)
    # Comp 1 -> Mix 1 | Comp 2-3 -> Mix 2 | Comp 4 -> Mix 3 | Comp 5 -> Mix 4
    if isinstance(params["mezcla"], int):
        actual_max_combo = params["mezcla"]
    else:
        if params["complexity"] <= 1: actual_max_combo = 1
        elif params["complexity"] <= 3: actual_max_combo = 2
        else: actual_max_combo = 3
        if params["complexity"] == 5: actual_max_combo = 4

    # El diagnóstico nos da el nivel RECOMENDADO
    proj_level = get_projected_level(actual_max_combo, params)
    level_name = _combo_name(proj_level)
    
    print_question("23", f"Nivel de Agresividad / Diagnóstico [{color_text(str(proj_level), COLOR_GREEN)}]")
    print(color_text(f"    🔍 DIAGNÓSTICO: Se ha detectado que tu configuración corresponde al Nivel {proj_level} ({level_name}).", COLOR_CYAN))
    print("    Si deseas un ataque más profundo o más ligero, puedes ajustarlo aquí abajo.")
    print(f"      {color_text('1', COLOR_CYAN)}: Rápido (Solo lo más probable, muy ligero)")
    print(f"      {color_text('2', COLOR_CYAN)}: Moderado (Equilibrio entre velocidad y éxito)")
    print(f"      {color_text('3', COLOR_CYAN)}: Profundo (Ataque de ingeniería social estándar)")
    print(f"      {color_text('4', COLOR_CYAN)}: Exhaustivo (Fuerza bruta total ordenada, lento)")
    
    print(f"    ENTER = usar nivel recomendado [{color_text(str(proj_level), COLOR_GREEN)}]")
    ans_agr = input("    > ").strip()
    params["agresividad"] = int(ans_agr) if ans_agr.isdigit() else int(proj_level)

    print_question("24", "RAM máxima para deduplicación (en GB) [3]:")
    params["max_ram"] = safe_int_input("    > ", 3, min_value=1, max_value=32)
    print("\nResumen rápido:")
    print(f"  {color_text('Nombre:', COLOR_YELLOW)} {color_text(str(params.get('name') or '(vacío)'), COLOR_CYAN)}")
    print(f"  {color_text('Nacimiento:', COLOR_YELLOW)} {color_text(str(params.get('birth_year') or '(vacío)'), COLOR_CYAN)}")
    print(f"  {color_text('DNI:', COLOR_YELLOW)} {color_text(str(params.get('dni') or '(vacío)'), COLOR_CYAN)}")
    print(f"  {color_text('Otros:', COLOR_YELLOW)} {color_text(', '.join(params.get('other') or []) or '(vacío)', COLOR_CYAN)}")
    print(f"  {color_text('Salida:', COLOR_YELLOW)} {color_text(params['output_file'], COLOR_CYAN)}")
    if params.get("base_dir"):
        print(f"  {color_text('Base dir:', COLOR_YELLOW)} {color_text(params['base_dir'], COLOR_CYAN)}")
    print(f"  {color_text('Longitud mínima:', COLOR_YELLOW)} {color_text(str(params['min_length']), COLOR_GREEN)}")
    print(f"  {color_text('Longitud máxima:', COLOR_YELLOW)} {color_text(str(params['max_length']), COLOR_GREEN)}")
    if params.get("count"):
        print(f"  {color_text('Cantidad máxima:', COLOR_YELLOW)} {color_text(str(params['count']), COLOR_GREEN)}")
    else:
        print(f"  {color_text('Cantidad máxima:', COLOR_YELLOW)} {color_text('ilimitado', COLOR_GREEN)}")
    print(f"  {color_text('Sufijos:', COLOR_YELLOW)} {color_text(', '.join(params.get('digit_suffixes') or []) or '(ninguno)', COLOR_GREEN)}")
    if params.get("patterns"):
        print(f"  {color_text('Patrones:', COLOR_YELLOW)} {color_text(', '.join(params['patterns']), COLOR_ORANGE)}")
    print(f"  {color_text('Modo leet:', COLOR_YELLOW)} {color_text('Sí' if params.get('leet') else 'No', COLOR_GREEN if params.get('leet') else COLOR_ORANGE)}")
    print(f"  {color_text('Separadores:', COLOR_YELLOW)} {color_text('Sí' if params.get('use_separators') else 'No', COLOR_GREEN if params.get('use_separators') else COLOR_ORANGE)}")
    date_decompose = params.get("decompose_number_dates")
    doc_decompose = params.get("decompose_number_document")
    if date_decompose is None and doc_decompose is None:
        date_decompose = doc_decompose = params.get("decompose_numbers", False)
    print(f"  {color_text('Descomponer fechas:', COLOR_YELLOW)} {'Sí' if date_decompose else 'No'}")
    print(f"  {color_text('Descomponer documento:', COLOR_YELLOW)} {'Sí' if doc_decompose else 'No'}")
    print(f"  {color_text('Complejidad:', COLOR_YELLOW)} {color_text(str(params.get('complexity', 2)), COLOR_GREEN)}")
    print(f"  {color_text('Agresividad:', COLOR_YELLOW)} {color_text(str(params.get('agresividad', 4)), COLOR_GREEN)}")
    mezcla_val = str(params.get('mezcla', 'auto'))
    if mezcla_val == "auto":
        mezcla_val = f"Auto (Nivel {actual_max_combo})"
    print(f"  {color_text('Mezcla:', COLOR_YELLOW)} {color_text(mezcla_val, COLOR_GREEN)}")
    print(f"  {color_text('RAM dedup:', COLOR_YELLOW)} {color_text(str(params.get('max_ram', 3)) + ' GB', COLOR_GREEN)}")
    print()
    while True:
        print(f"  {color_text('ENTER', COLOR_GREEN)} = Generar  |  {color_text('R', COLOR_ORANGE)} = Reiniciar configuración")
        choice = input("  > ").strip().lower()
        if choice == "":
            return params
        elif choice == "r":
            print(color_text("\n  ♻ Reiniciando configuración (tus respuestas anteriores se mantienen como defaults)...\n", COLOR_CYAN))
            return prompt_interactive(defaults=params)
        else:
            print(color_text("  [!] Opción no válida. Pulsa ENTER para generar o escribe 'r' para reconfigurar.", COLOR_MAGENTA))


def yes_no_input(prompt, default="n"):
    while True:
        answer = input(prompt).strip().lower()
        if not answer:
            answer = default.lower()
        if answer in ("s", "si", "y", "yes", "true", "1", "n", "no", "false", "0"):
            return answer.startswith("s") or answer.startswith("y") or answer == "1"
        print(color_text("[!] Error: Por favor responde 's' (sí) o 'n' (no).", COLOR_MAGENTA))


def safe_int_input(prompt, default, min_value=None, max_value=None):
    while True:
        text = input(prompt).strip()
        if not text:
            return default
        try:
            value = int(text)
        except ValueError:
            print(color_text("[!] Error: Debes ingresar un número entero válido.", COLOR_MAGENTA))
            continue
        if min_value is not None and value < min_value:
            print(color_text(f"[!] Error: El value no puede ser menor a {min_value}.", COLOR_MAGENTA))
            continue
        if max_value is not None and value > max_value:
            print(color_text(f"[!] Error: El value no puede ser mayor a {max_value}.", COLOR_MAGENTA))
            continue
        return value


def run_gui(args):
    if not TK_AVAILABLE:
        print("Tkinter no está disponible en este entorno. Volviendo al modo CLI.")
        return None

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Social Wordlist", "Usa los cuadros de diálogo para ingresar los datos. Deja vacío lo que no quieras usar.")
    config = {
        "name": simpledialog.askstring("Nombre", "Nombre completo, nombre de pila o apellido:"),
        "color": simpledialog.askstring("Color favorito", "Color favorito:"),
        "birth_year": simpledialog.askstring("Año de nacimiento", "Año de nacimiento:"),
        "year": simpledialog.askstring("Otro año importante", "Otro año importante:"),
        "dni": simpledialog.askstring("DNI", "DNI o documento:"),
        "city": simpledialog.askstring("Ciudad", "Ciudad:"),
        "pet": simpledialog.askstring("Mascota", "Nombre de mascota:"),
        "singer": simpledialog.askstring("Cantante", "Cantante o banda favorita:"),
        "other": [],
        "dict_file": simpledialog.askstring("Diccionario", f"Archivo diccionario [{DEFAULT_DICT_FILE}]:") or DEFAULT_DICT_FILE,
        "output_file": simpledialog.askstring("Salida", f"Archivo salida [{DEFAULT_OUTPUT_FILE}]:") or DEFAULT_OUTPUT_FILE,
        "patterns": [],
        "hash_mode": simpledialog.askstring("Hash mode", "Modo de # (letters, digits, specials, all, base) [all]:") or "all",
        "min_length": safe_int_input_gui("Longitud mínima", 4),
        "max_length": safe_int_input_gui("Longitud máxima", 32),
        "count": safe_int_input_gui("Cantidad máxima de contraseñas (enter para ilimitado)", None),
        "lower": messagebox.askyesno("Minúsculas", "¿Incluir solo minúsculas?"),
        "upper": messagebox.askyesno("Mayúsculas", "¿Incluir solo mayúsculas?"),
        "digits": messagebox.askyesno("Dígitos", "¿Incluir dígitos?"),
        "specials": messagebox.askyesno("Especiales", "¿Incluir caracteres especiales?"),
        "leet": messagebox.askyesno("Modo leet", "¿Activar modo leet? (a=4, e=3, o=0)?"),
        "complexity": safe_int_input_gui("Nivel de complejidad 1-5", 2, min_value=1, max_value=5),
    }
    while True:
        extra = simpledialog.askstring("Otro dato", "Otro dato genérico (deja vacío para continuar):")
        if not extra:
            break
        config["other"].append(extra)
    while True:
        print(color_text("\n[+] Configuración de Patrones Avanzados", COLOR_CYAN))
        print(color_text("    Marcadores disponibles:", COLOR_YELLOW))
        print(f"    {color_text('#', COLOR_GREEN)} = Tus datos  {color_text('%', COLOR_GREEN)} = Números (0-9)  {color_text('@', COLOR_GREEN)} = Letras (a-z)")
        print(f"    {color_text(',', COLOR_GREEN)} = Letras (A-Z)  {color_text('?', COLOR_GREEN)} = Símbolos       {color_text('\\', COLOR_GREEN)} = Escape (ej: \\#)")
        print(color_text("    Ejemplo: IV#%?CO (Genera: IV + Dato + Núm + Símb + CO)", COLOR_CYAN))
        
        print_question("14", "Ingresa tus patrones (uno por línea, deja vacío para terminar):")
        patt = simpledialog.askstring("Patrón", "Plantilla/patrón (deja vacío para continuar):")
        if not patt:
            break
        config["patterns"].append(patt)
    root.destroy()
    config["other"] = config["other"] or None
    config["patterns"] = config["patterns"] or None
    return config


def safe_int_input_gui(prompt, default, min_value=None, max_value=None):
    try:
        text = simpledialog.askstring(prompt, prompt)
        if text is None or text.strip() == "":
            return default
        value = int(text.strip())
    except (ValueError, TypeError):
        return default
    if min_value is not None and value < min_value:
        return min_value
    if max_value is not None and value > max_value:
        return max_value
    return value


def load_dictionary(file_path):
    words = []
    if not file_path:
        return words
    if not os.path.isfile(file_path):
        return words
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                item = line.strip()
                if item:
                    words.append(item)
    except IOError:
        print(f"No se pudo leer el diccionario: {file_path}")
    return words




def build_config_from_args(args, defaults=None):
    defaults = defaults or {}
    base_dir = args.base_dir or defaults.get("base_dir") or None
    dict_file = args.dict if args.dict != DEFAULT_DICT_FILE or defaults.get("dict_file") is None else defaults.get("dict_file")
    output_file = resolve_output_path(args.output or defaults.get("output_file"), "cli", base_dir)
    return {
        "name": args.name or defaults.get("name"),
        "color": args.color or defaults.get("color"),
        "birth_year": parse_multi_values(args.birth_year) or defaults.get("birth_year"),
        "year": parse_multi_values(args.year) or defaults.get("year"),
        "dni": args.dni or defaults.get("dni"),
        "city": args.city or defaults.get("city"),
        "pet": args.pet or defaults.get("pet"),
        "singer": args.singer or defaults.get("singer"),
        "other": args.other or defaults.get("other"),
        "dict_file": resolve_path(base_dir, dict_file) if dict_file else None,
        "output_file": output_file,
        "base_dir": base_dir,
        "patterns": args.pattern or defaults.get("patterns"),
        "hash_mode": args.hash_mode or defaults.get("hash_mode", "all"),
        "min_length": args.min_length if args.min_length is not None else defaults.get("min_length", 4),
        "max_length": args.max_length if args.max_length is not None else defaults.get("max_length", 32),
        "count": args.count if args.count is not None else defaults.get("count"),
        "lower": args.lower or defaults.get("lower", False),
        "upper": args.upper or defaults.get("upper", False),
        "digits": args.digits or defaults.get("digits", False),
        "specials": args.specials or defaults.get("specials", False),
        "leet": args.leet if hasattr(args, "leet") else defaults.get("leet", True),
        "max_leet_replacements": getattr(args, "max_leet_replacements", defaults.get("max_leet_replacements", 8)),
        "digit_suffixes": parse_multi_values(args.digit_suffixes) or defaults.get("digit_suffixes"),
        "complexity": args.complexity if args.complexity is not None else defaults.get("complexity", 2),
        "agresividad": getattr(args, "agresividad", defaults.get("agresividad", 4)),
        "decompose_numbers": args.decompose_numbers or defaults.get("decompose_numbers", False),
        "max_ram": args.max_ram if args.max_ram is not None else defaults.get("max_ram", 3),
        "max_template_expansion": defaults.get("max_template_expansion", 100000000),
    }


def config_has_social_info(config):
    return any(config.get(key) for key in ("name", "color", "birth_year", "family_name", "family_years", "team", "birth_place", "living_city", "dni", "pet", "singer")) or config.get("other")


def run_config_wizard(config_path):
    import configparser
    print_header()
    print(color_text("=== MODO INTERACTIVO DE INGENIERÍA SOCIAL ===", COLOR_CYAN))
    print(color_text("💡 Tip: Presiona ENTER para usar el valor por defecto indicado en MAYÚSCULAS.", COLOR_YELLOW))
    print(color_text("   (No importa si escribes s/S o n/N, el programa lo entenderá igual).", COLOR_YELLOW))
    print("-------------------------------------------------------------------------")
    print(f"Editando archivo: {color_text(config_path, COLOR_CYAN)}")
    print("Presiona ENTER para mantener el valor actual en cualquier pregunta.\n")

    config = configparser.ConfigParser(comment_prefixes=("#", ";"), strict=False)
    if os.path.exists(config_path):
        config.read(config_path, encoding="utf-8")

    if not config.has_section("defaults"):
        config.add_section("defaults")
    if not config.has_section("leet"):
        config.add_section("leet")

    curr_out = config.get("defaults", "output_file", fallback="passlist.txt")
    print(f"Archivo de salida por defecto [Actual: {color_text(curr_out, COLOR_GREEN)}]")
    new_out = input("> ").strip()
    if new_out:
        config.set("defaults", "output_file", new_out)

    curr_ram = config.get("defaults", "max_ram", fallback="3")
    print(f"RAM máxima en GB para deduplicación [Actual: {color_text(curr_ram, COLOR_GREEN)}]")
    new_ram = input("> ").strip()
    if new_ram and new_ram.isdigit():
        config.set("defaults", "max_ram", new_ram)

    print("\n--- Mapeo Leet Speak ---")
    for letter in ['a', 'e', 'i', 'o', 's', 'l', 't', 'g']:
        curr_leet = config.get("leet", letter, fallback="")
        display_curr = curr_leet if curr_leet else 'Ninguno'
        print(f"Reemplazo para la '{color_text(letter, COLOR_YELLOW)}' [Actual: {color_text(display_curr, COLOR_GREEN)}] (ENTER=mantener, '-'=eliminar)")
        new_val = input("> ").strip()
        if new_val == "-":
            config.remove_option("leet", letter)
            config.remove_option("leet", letter.upper())
        elif new_val:
            config.set("leet", letter, new_val)
            config.set("leet", letter.upper(), new_val)

    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)
    print(f"\n{color_text('[+]', COLOR_GREEN)} ¡Configuración guardada exitosamente en {config_path}!")
    sys.exit(0)


def main():
    args = parse_args()
    config_path = args.config if hasattr(args, "config") else DEFAULT_CONFIG_FILE
    if args.setup:
        run_config_wizard(config_path)

    config_defaults = load_config_defaults(config_path)

    if args.gui:
        gui_config = run_gui(args)
        config = gui_config if gui_config is not None else build_config_from_args(args, config_defaults)
    elif args.interactive or len(sys.argv) == 1:
        config = prompt_interactive(config_defaults)
    else:
        config = build_config_from_args(args, config_defaults)

    config["leet_mappings"] = config_defaults.get("leet_mappings")

    if config.get("min_length") is None:
        config["min_length"] = 1
    if config.get("max_length") is None:
        config["max_length"] = 16
    if config["max_length"] < config["min_length"]:
        config["max_length"] = config["min_length"]

    dictionary_words = load_dictionary(config.get("dict_file"))
    options = {
        "lower": config.get("lower"),
        "upper": config.get("upper"),
        "digits": config.get("digits"),
        "specials": config.get("specials"),
        "leet": config.get("leet", True),
        "max_leet_replacements": config.get("max_leet_replacements", 8),
        "complexity": config.get("complexity", 2),
        "birth_year": config.get("birth_year"),
        "leet_mappings": config.get("leet_mappings"),
        "force_extreme": getattr(args, "force_extreme", False),
        "remove_accents_flag": config.get("remove_accents_flag", True),
        "use_separators": config.get("use_separators", False),
        "allow_extreme_generation": config.get("allow_extreme_generation", False),
        "extreme_generation_limit": config.get("extreme_generation_limit", 5000000000),
        "max_template_expansion": config.get("max_template_expansion", 100000000)
    }
    base_tokens, numeric_parts = collect_social_tokens(config, dictionary_words, options)
    options["numeric_parts"] = numeric_parts
    char_pool = build_char_pool(config.get("hash_mode", "all"), base_tokens, options)

    print(color_text(f"[*] Base de palabras identificadas: {len(base_tokens)}", COLOR_CYAN))
    
    is_interactive = args.interactive or len(sys.argv) == 1
    # Si el usuario fijó mezcla manualmente, usarla directamente
    mezcla_setting = config.get("mezcla", "auto")
    if isinstance(mezcla_setting, int) and mezcla_setting in (1, 2, 3):
        force_max_combo = mezcla_setting
        show_pre_generation_summary(len(base_tokens), force_max_combo, options, is_interactive)
    else:
        force_max_combo = check_and_prompt_limits(len(base_tokens), options, is_interactive)

    stop_event = threading.Event()
    total_estimate = "calculando..."
    progress_state = {"current": None, "generated": 0}
    print("Presiona Ctrl+C en cualquier momento para cancelar la generación y guardar lo generado hasta ese punto.")
    
    progress_thread = threading.Thread(target=show_progress, args=(stop_event, total_estimate, progress_state, config.get("output_file", DEFAULT_OUTPUT_FILE)))
    progress_thread.daemon = True
    progress_thread.start()
    output_file = config.get("output_file", DEFAULT_OUTPUT_FILE)
    candidate_iterables = []
    try:
    if config.get("patterns"):
        # Modo Quirúrgico: Patrones
        # Usamos "all" para que el marcador # incluya mutaciones (Leet, Caps, etc) si están activas
        pattern_pool = build_char_pool("all", base_tokens, options)
        pattern_candidates = generate_from_patterns(
            config.get("patterns"), pattern_pool,
            config["min_length"], config["max_length"], config.get("count"),
            max_expansion=options.get("max_template_expansion")
        )
        candidate_iterables.append(pattern_candidates)
    else:
        # Modo Automático: Capas (Tier 1-4)
        agr = config.get("agresividad", 4)
        for t in range(1, agr + 1):
            candidate_iterables.append(generate_tiered_variants(base_tokens, options, t, config.get("count"), config["max_length"]))

        if not config.get("patterns") and not config_has_social_info(config):
            print(color_text("No se proporcionó información de ingeniería social ni patrones. Se generará contenido básico desde el diccionario.", COLOR_MAGENTA))
            candidate_iterables.append((word for word in dictionary_words))

        # Contraseñas comunes estáticas (sin combinar, solo se agregan tal cual)
        common_pwds = list(COMMON_PASSWORDS)
        if config.get("extra_common_passwords"):
            common_pwds.extend(config["extra_common_passwords"])
        candidate_iterables.append(iter(common_pwds))

        max_ram = config.get("max_ram", 3)
        written = stream_candidates_to_file(
            output_file,
            candidate_iterables,
            config["min_length"],
            config["max_length"],
            config.get("count"),
            progress_state,
            max_ram_gb=max_ram,
        )

        stop_event.set()
        progress_thread.join()

        if written == 0:
            print(color_text("No se generaron contraseñas con los parámetros actuales. Ajusta el rango, patrones o datos ingresados.", COLOR_MAGENTA))
        else:
            skipped = progress_state.get("skipped_duplicates", 0)
            ram_exceeded = progress_state.get("ram_exceeded", False)
            print(f"Wordlist guardada en: {output_file} ({written:,} líneas, {skipped:,} duplicados eliminados en memoria)")
            # Estadísticas finales
            stats = progress_state.get("stats", {})
            elapsed = progress_state.get("elapsed", 0)
            if stats and written > 0:
                alpha = stats.get("alpha", 0)
                alnum = stats.get("alnum", 0)
                symbols = stats.get("symbols", 0)
                lengths = stats.get("lengths", {})
                avg_len = sum(k * v for k, v in lengths.items()) / written if lengths else 0
                min_len = min(lengths.keys()) if lengths else 0
                max_len_actual = max(lengths.keys()) if lengths else 0
                print(f"\n{color_text('📊 Estadísticas:', COLOR_CYAN)}")
                print(f"  Total únicas: {color_text(f'{written:,}', COLOR_GREEN)}")
                print(f"  Duplicados eliminados: {color_text(f'{skipped:,}', COLOR_ORANGE)}")
                print(f"  Tiempo: {color_text(format_time(elapsed), COLOR_CYAN)}")
                print(f"  Longitud promedio: {color_text(f'{avg_len:.1f}', COLOR_GREEN)} chars (rango: {min_len}-{max_len_actual})")
                pct_a = 100 * alpha / written
                pct_an = 100 * alnum / written
                pct_s = 100 * symbols / written
                print(f"  Solo letras: {pct_a:.0f}%  |  Alfanumérica: {pct_an:.0f}%  |  Con símbolos: {pct_s:.0f}%")
            # Si se excedió la RAM, auto-deduplicar los overflow restantes
            if ram_exceeded:
                print(color_text(f"⚠ Se excedió el límite de RAM ({max_ram} GB). Auto-deduplicando posibles duplicados restantes...", COLOR_YELLOW))
                if deduplicate_file(output_file):
                    print("✓ Deduplicación automática completada. Cero duplicados, cero datos perdidos.")
                else:
                    print("⚠ La deduplicación falló, pero la wordlist original se conservó.")
            else:
                print(color_text("✓ Deduplicación completa en memoria. Sin duplicados.", COLOR_GREEN))
    except KeyboardInterrupt:
        stop_event.set()
        progress_thread.join()
        print("\nGeneración cancelada por el usuario.")
        generated = progress_state.get('generated', 0)
        print(f"Se guardaron {generated:,} líneas parciales en {output_file}.")
        ram_exceeded = progress_state.get("ram_exceeded", False)
        if generated > 0 and ram_exceeded:
            print("Auto-deduplicando...")
            if deduplicate_file(output_file):
                print("✓ Deduplicación completada.")


if __name__ == "__main__":
    main()
