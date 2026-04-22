#!/usr/bin/env python3
__version__ = "1.2.0"
"""
Social engineering wordlist generator for Kali Linux.
Generates password wordlists from social information, dictionary words, patterns,
mutations, permutations and complexity levels.

Usage examples:
  python3 selic.py --name "Juan" --color "rojo" --birth-year 1995 \
    --dni 12345678 --min-length 8 --max-length 16 --pattern "7###C" \
    --output wordlist.txt

  python3 selic.py

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
    
    # Patrones
    pattern_count = 0
    patterns = config.get("patterns", [])
    if patterns:
        for pattern in patterns:
            hashes = pattern.count("#")
            if hashes:
                char_pool_size = 30  # Aproximado (letras + dígitos)
                pattern_count += min(char_pool_size ** hashes, 10000)
        pattern_count = min(pattern_count, 50000)
    
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
            "digit_suffixes": parse_multi_values(sec.get("digit_suffixes")),
            "decompose_numbers": parse_config_bool(sec.get("decompose_numbers"), False),
            "max_ram": parse_config_int(sec.get("max_ram"), 3),
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
    parser.add_argument("--pattern", action="append", help="Plantilla/patrón como 7###C, ###@2026, Nombre##!.")
    parser.add_argument("--digit-suffixes", action="append", help="Lista personal de sufijos numéricos separados por comas o espacios. Se agregan a los sufijos por defecto. Ej: 1234, 2025, 999")
    parser.add_argument("--hash-mode", choices=["letters", "digits", "specials", "all", "base"], default="all",
                        help="Carácter que reemplaza '#' en patrones: letters=letras, digits=números, specials=símbolos, all=todo, base=caracteres asignados.")
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
    print("Modo interactivo de SELIC")
    print("Datos objetivo — responde solo lo que conozcas.")
    print("  • Para ayuda completa: python selic.py --help")
    print("  • ENTER omite la pregunta")
    print("  • Usa skip si quieres saltar un campo")
    print("  • Separa valores con espacios o comas")
    print("--------------------------------------------------------")
    params = {}
    print_question("01", "Nombre completo / alias de la persona objetivo")
    default_name = defaults.get("name")
    if default_name is not None:
        print(f"    ENTER = omitir | predeterminado: {get_default_label(format_default_value(default_name))}")
    else:
        print("    ENTER = omitir | Ej: Marco Antonio")
    user_input = input("    > ").strip()
    params["name"] = user_input if user_input else None
    print_question("02", "Fecha(s) de nacimiento de la persona objetivo (DD/MM/YYYY, DD-MM-YYYY o solo año)")
    default_birth = defaults.get("birth_year")
    if default_birth is not None:
        print(f"    ENTER = omitir | predeterminado: {get_default_label(format_default_value(default_birth))}")
    print("    Si son varias fechas/años, sepáralas con espacios o comas.")
    print(f"    Ej: {color_text('08/04/2005', COLOR_ORANGE)}, {color_text('2010', COLOR_ORANGE)} o {color_text('2005', COLOR_ORANGE)}")
    while True:
        birth_input = input("    > ").strip()
        if not birth_input:
            params["birth_year"] = None
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
    print_question("04", "Nombre del papá/mamá u otro familiar cercano")
    default_family_name = defaults.get("family_name")
    if default_family_name is not None:
        print(f"    ENTER = omitir | predeterminado: {get_default_label(format_default_value(default_family_name))}")
    else:
        print("    (Ej: Juan, María, hermano, hermana) | ENTER = omitir")
    user_input = input("    > ").strip()
    params["family_name"] = user_input if user_input else None
    print_question("05", "Fecha(s) de nacimiento de padres o hermanos (DD/MM/YYYY, DD-MM-YYYY o solo año)")
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
    print_question("06", "DNI o documento de la persona objetivo")
    default_dni = defaults.get("dni")
    if default_dni is not None:
        print(f"    ENTER = omitir | predeterminado: {get_default_label(format_default_value(default_dni))}")
    else:
        print("    ENTER = omitir")
    while True:
        user_input = input("    > ").strip()
        if not user_input:
            params["dni"] = None
            break
        if not validate_dni(user_input):
            print(color_text(f"    [!] Error: DNI inválido. Debe ser de 6 a 12 dígitos numéricos.", COLOR_MAGENTA))
            continue
        params["dni"] = user_input
        break
    print_question("07", "Descomponer fechas en fragmentos? (s/n) [n]")
    print(color_text("    ⚠ IMPACTO ALTO: Aumenta exponencialmente las permutaciones si hay muchas fechas.", COLOR_ORANGE))
    print("    ENTER = no")
    print("    Se extraen siempre día, mes y año de fechas como 08/04/2005.")
    print("    Si no descompones, aún se usarán 08, 8, 04, 4, 2005 y 0804.")
    print("    La opción solo agrega fragmentos adicionales como 20, 05, 200, 005.")
    params["decompose_number_dates"] = yes_no_input("    > ", default="n")
    print_question("08", "Descomponer el documento de identidad en fragmentos? (s/n) [n]")
    print(color_text("    ⚠ IMPACTO MEDIO: Multiplica las palabras base extraídas del DNI.", COLOR_YELLOW))
    print("    ENTER = no")
    print("    Se aplica solo al DNI/documento")
    params["decompose_number_document"] = yes_no_input("    > ", default="n")
    params["decompose_numbers"] = params["decompose_number_dates"] or params["decompose_number_document"]
    
    print_question("08-B", "¿Generar también versiones sin tildes/acentos? (Recomendado) (s/n) [s]")
    print(color_text("    ⚠ IMPACTO ALTO: Duplica el tamaño de la base para nombres con tilde (José -> Jose).", COLOR_ORANGE))
    print("    La letra 'ñ' y 'Ñ' siempre se conservará intacta.")
    params["remove_accents_flag"] = yes_no_input("    > ", default="s")
    print_question("09", "Información adicional del objetivo")
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
    # Campos individuales no usados en interactivo (se manejan via --cli)
    params["color"] = None
    params["team"] = None
    params["birth_place"] = None
    params["living_city"] = None
    params["pet"] = None
    params["singer"] = None
    params["dict_file"] = None
    print_question("10", "Archivo de salida")
    default_output = defaults.get("output_file") or DEFAULT_OUTPUT_FILE
    print(f"    ENTER = {color_text(default_output, COLOR_GREEN)}")
    params["output_file"] = input("    > ").strip() or default_output
    print_question("11", "Directorio base para los archivos")
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
    print_question("12", "Usar plantillas/patrones con #? (s/n) [n]")
    print("    ENTER = no")
    print(f"    Ej: {color_text('7###C', COLOR_ORANGE)}, {color_text('###@2026', COLOR_ORANGE)}, {color_text('Nombre##!', COLOR_ORANGE)}")
    print("    Cada # es un marcador de posición que se reemplaza por un solo carácter.")
    print("    El patrón se completa carácter por carácter.")
    print("    No se toma un grupo de # como una palabra o fragmento entero.")
    print(f"    Ej: {color_text('7####E', COLOR_ORANGE)} => 7 + 4 caracteres + E.")
    print("    Si quieres usar un dato literal, escríbelo directamente: 7MarcoE")
    use_patterns = yes_no_input("    > ", default="n")
    patterns = []
    if use_patterns:
        print("    - Usa # para reemplazar con letras/dígitos/símbolos según la opción de hash.")
        print("    - Ejemplos: 7###C, ###@2026, Nombre##!, Password###")
        while True:
            print("    Plantilla/patrón [ENTER = terminar]:")
            patt = input("    ").strip()
            if not patt:
                break
            patterns.append(patt)
        params["patterns"] = patterns or None
        print("    Modo de # para las plantillas: letters, digits, specials, all, base")
        print(f"    - {color_text('letters', COLOR_CYAN)}: solo letras (a-z, A-Z)")
        print(f"    - {color_text('digits', COLOR_CYAN)}: solo números (0-9)")
        print(f"    - {color_text('specials', COLOR_CYAN)}: solo símbolos (!@#$%^&*_+-=)")
        print(f"    - {color_text('all', COLOR_CYAN)}: letras, números y símbolos")
        print(f"    - {color_text('base', COLOR_CYAN)}: caracteres de tus datos sociales (nombres, años, etc.)")
        print("    ENTER = all")
        params["hash_mode"] = input("    > ").strip() or "all"
    else:
        params["patterns"] = None
        params["hash_mode"] = "all"
    print_question("13", "Longitud de las contraseñas:")
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
    print_question("14", "Cantidad máxima de contraseñas")
    params["count"] = safe_int_input(f"    ENTER = {color_text('ilimitado', COLOR_GREEN)} | > ", None)
    if params["count"] is not None and params["count"] < 1:
        print(color_text("Cantidad máxima debe ser al menos 1.", COLOR_MAGENTA))
        log_error(f"Cantidad inválida: {params['count']}")
    print_question("15", "Letras")
    print("    ENTER = mezcla de mayúsculas y minúsculas")
    mixed_case = yes_no_input("    ¿Deseas usar mayúsculas y minúsculas en las combinaciones? (s/n) [s]: ", default="s")
    print()
    if mixed_case:
        params["lower"] = True
        params["upper"] = True
    else:
        params["lower"] = yes_no_input("    ¿Usar solo minúsculas? (s/n) [n]: ", default="n")
        params["upper"] = yes_no_input("    ¿Usar solo mayúsculas? (s/n) [n]: ", default="n")
        if not params["lower"] and not params["upper"]:
            print("    No se seleccionó ninguna opción de mayúsculas/minúsculas, se usará mezcla de ambas.")
            params["lower"] = True
            params["upper"] = True
    print_question("16", "Dígitos y especiales")
    print()
    print("    Las 'variaciones' son transformaciones del nombre/datos que añaden:")
    print("    • Con dígitos: nombre + números (ej: 'Marco' → 'Marco123', 'Marco2002', etc.)")
    print("    • Con símbolos: nombre + caracteres especiales (ej: 'Marco' → 'Marco!', 'Marco@', etc.)")
    print()
    default_digits = defaults.get("digits", True)
    params["digits"] = yes_no_input("    ¿Agregar variaciones CON DÍGITOS? (s/n) [s]: ", default="s" if default_digits else "n")
    print()
    default_specials = defaults.get("specials", True)
    params["specials"] = yes_no_input("    ¿Agregar variaciones CON SÍMBOLOS? (s/n) [s]: ", default="s" if default_specials else "n")
    print()
    default_separators = defaults.get("use_separators", False)
    params["use_separators"] = yes_no_input("    ¿Usar SEPARADORES (_, ., -) para unir palabras base? (s/n) [n]: ", default="s" if default_separators else "n")
    print()
    print("    Sufijos numéricos personalizados (opcional):")
    print("    ENTER = usar por defecto (123, 2023, 2024, 007)")
    print("    Si quieres otros, escríbelos separados por comas: 1234, 2025, 999")
    custom_suffixes = input("    > ").strip()
    params["digit_suffixes"] = parse_multi_values(custom_suffixes) if custom_suffixes else None
    print_question("17", "Modo leet")
    print(f"    Reemplaza letras como {color_text('a=4', COLOR_CYAN)}, {color_text('e=3', COLOR_CYAN)}, {color_text('o=0', COLOR_CYAN)}, {color_text('i=1', COLOR_CYAN)}, {color_text('s=$', COLOR_CYAN)}.")
    print("    ENTER = sí (puedes responder s/n)")
    params["leet"] = yes_no_input("    > ", default="s" if defaults.get("leet", True) else "n")
    if params["leet"]:
        print("    Max letras a reemplazar por token (1-20).")
        print("    " + color_text("⚠ IMPACTO ALTO: Valores altos multiplican drásticamente las combinaciones.", COLOR_ORANGE))
        print("    10 es suficiente para cubrir el 99.9% de contraseñas humanas complejas.")
        print(f"    ENTER = {color_text('8', COLOR_GREEN)}")
        params["max_leet_replacements"] = safe_int_input("    > ", 8, min_value=1, max_value=20)
    else:
        params["max_leet_replacements"] = 8
    print_question("18", "Complejidad:")
    print(f"    {color_text('1', COLOR_CYAN)} = solo datos básicos y poca mezcla.")
    print(f"    {color_text('2', COLOR_CYAN)} = agrega mayúsculas/minúsculas y sufijos simples.")
    print(f"    {color_text('3', COLOR_CYAN)} = agrega reversos, mutaciones y más variantes.")
    print(f"    {color_text('4', COLOR_CYAN)} = agrega símbolos y fechas adicionales.")
    print(f"    {color_text('5', COLOR_CYAN)} = mezcla máxima de tamaños, símbolos y números.")
    print(f"    {color_text('ENTER = 2', COLOR_GREEN)}")
    params["complexity"] = safe_int_input("    Nivel de complejidad 1-5 [2]: ", 2, min_value=1, max_value=5)
    print_question("19", "Nivel de Mezcla (profundidad de combinación)")
    comp = params["complexity"]
    default_mezcla = 3 if comp >= 5 else (2 if comp >= 3 else 1)
    print(f"    {color_text('1', COLOR_CYAN)} = Individual: cada palabra sola (rápido, menos contraseñas).")
    print(f"    {color_text('2', COLOR_CYAN)} = Parejas: combina 2 palabras (equilibrado).")
    print(f"    {color_text('3', COLOR_CYAN)} = Tríos: combina 3 palabras (lento, máxima cobertura).")
    print(f"    {color_text('4', COLOR_CYAN)} = Cuartetos: combina 4 palabras (extremo, fuerza bruta masiva).")
    print(f"    {color_text(f'ENTER = {default_mezcla} (recomendado para Complejidad {comp})', COLOR_GREEN)}")
    params["mezcla"] = safe_int_input(f"    Nivel de mezcla 1-4 [{default_mezcla}]: ", default_mezcla, min_value=1, max_value=4)
    
    print_question("19-B", "Nivel de Agresividad / Profundidad (Diagnóstico Automático)")
    
    # Calcular recomendación
    rec_agr = 1
    if params.get("specials") or params.get("digits"): rec_agr = 2
    if params.get("leet"): rec_agr = 3
    if params.get("complexity", 2) >= 4 or (params.get("leet") and params.get("specials")): rec_agr = 4

    print(color_text(f"    Según los ingredientes que encendiste, te diagnosticamos el Nivel {rec_agr}.", COLOR_YELLOW))
    print("    Este nivel garantiza que no se recorten tus resultados y se use todo lo que pediste.")
    print("    (Si eliges un nivel menor, se ignorarán algunos ajustes intencionalmente para ahorrar tiempo).")
    print()
    print(f"    {color_text('1', COLOR_CYAN)} = Solo alta probabilidad (Token+Número).")
    print(f"    {color_text('2', COLOR_CYAN)} = Alta prob. + Variaciones lógicas (fechas, símbolos, parejas).")
    print(f"    {color_text('3', COLOR_CYAN)} = Nivel 2 + Leet speak suave.")
    print(f"    {color_text('4', COLOR_CYAN)} = Fuerza bruta ordenada (Genera TODO ordenado de más a menos probable).")
    print(f"    {color_text(f'ENTER = {rec_agr} (Recomendado)', COLOR_GREEN)}")
    params["agresividad"] = safe_int_input(f"    Nivel de agresividad 1-4 [{rec_agr}]: ", rec_agr, min_value=1, max_value=4)

    print_question("20", "RAM máxima para deduplicación (en GB)")
    print(f"    ENTER = {color_text('3', COLOR_GREEN)} GB")
    print("    Nota: Más RAM evita lentitud al guardar diccionarios gigantes (Ej: Nivel 4).")
    print("    Si tu diccionario es pequeño (Nivel 1 o 2), usar 3GB o 10GB será igual de rápido.")
    print("    (SELIC no ocupará toda la RAM de golpe, es solo un límite máximo permitido).")
    params["max_ram"] = safe_int_input("    > ", 3, min_value=1, max_value=32)
    print("\nResumen rápido:")
    print(f"  {color_text('Salida:', COLOR_YELLOW)} {color_text(params['output_file'], COLOR_CYAN)}")
    if params.get("base_dir"):
        print(f"  {color_text('Base dir:', COLOR_YELLOW)} {color_text(params['base_dir'], COLOR_CYAN)}")
    print(f"  {color_text('Longitud mínima:', COLOR_YELLOW)} {color_text(str(params['min_length']), COLOR_GREEN)}")
    print(f"  {color_text('Longitud máxima:', COLOR_YELLOW)} {color_text(str(params['max_length']), COLOR_GREEN)}")
    if params.get("count"):
        print(f"  {color_text('Cantidad máxima:', COLOR_YELLOW)} {color_text(str(params['count']), COLOR_GREEN)}")
    else:
        print(f"  {color_text('Cantidad máxima:', COLOR_YELLOW)} {color_text('ilimitado', COLOR_GREEN)}")
    if params["patterns"]:
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
    print(f"  {color_text('Mezcla:', COLOR_YELLOW)} {color_text(str(params.get('mezcla', 'auto')), COLOR_GREEN)}")
    print(f"  {color_text('RAM dedup:', COLOR_YELLOW)} {color_text(str(params.get('max_ram', 3)) + ' GB', COLOR_GREEN)}")
    print("Pulsa ENTER si quieres continuar con la generación...")
    input("")
    return params


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
            print(color_text(f"[!] Error: El valor no puede ser menor a {min_value}.", COLOR_MAGENTA))
            continue
        if max_value is not None and value > max_value:
            print(color_text(f"[!] Error: El valor no puede ser mayor a {max_value}.", COLOR_MAGENTA))
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
        patt = simpledialog.askstring("Patrón", "Plantilla/patrón como 7###C (deja vacío para continuar):")
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


def normalize_token(value, decompose_numbers=False):
    normalized = set()
    if not value:
        return normalized
    value = str(value).strip()
    if not value:
        return normalized
    normalized.add(value)
    normalized.add(value.lower())
    normalized.add(value.upper())
    normalized.add(value.capitalize())
    normalized.add(value.replace(" ", ""))
    normalized.add(value.replace("-", ""))
    normalized.add(value.replace("_", ""))
    normalized.add(value.replace("/", ""))
    normalized.add("_".join(value.split()))

    if re.search(r"[\-/\.\\]", value):
        date_parts = [p for p in re.split(r"[\-/\.\\\s]+", value) if p]
        if date_parts and all(part.isdigit() for part in date_parts):
            normalized.add("".join(date_parts))
            for part in date_parts:
                normalized.add(part)
                if part.startswith("0"):
                    normalized.add(part.lstrip("0"))
            if len(date_parts) == 3:
                day, month, year = date_parts
                if len(day) in (1, 2) and len(month) in (1, 2) and len(year) in (2, 4):
                    day_z = day.zfill(2)
                    month_z = month.zfill(2)
                    normalized.add(day_z + month_z + year)
                    normalized.add(month_z + day_z + year)
                    normalized.add(day_z + month_z)
                    normalized.add(month_z + year)
                    normalized.add(day_z + year)
                    normalized.add(day_z + month_z)
                    normalized.add(month_z + day_z)
                    normalized.add(day.lstrip("0"))
                    normalized.add(month.lstrip("0"))
                    normalized.add(day.lstrip("0") + month.lstrip("0"))
                    normalized.add(month.lstrip("0") + day.lstrip("0"))

    for part in split_words(value):
        normalized.add(part)
        normalized.add(part.lower())
        normalized.add(part.upper())
        normalized.add(part.capitalize())
        if part.isdigit():
            if decompose_numbers:
                normalized.update(decompose_number(part))
            continue
        # Prefijos: "Marco" → "Ma", "Mar", "Marco"
        for length in range(1, min(5, len(part)) + 1):
            normalized.add(part[:length])
        # Sufijos: "Marco" → "co", "rco", "Marco"
        for length in range(1, min(5, len(part)) + 1):
            normalized.add(part[-length:])
    # Evitar tokens triviales de un solo carácter que inflan demasiado la generación.
    normalized = {token for token in normalized if len(token) > 1}
    return normalized


def apply_mutations(token, enable_leet=True, leet_mappings=None, multi_leet=False, max_leet_replacements=8):
    leet_mappings = leet_mappings or {
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
    mutated = {token}
    if enable_leet:
        # Encontrar posiciones reemplazables
        replaceable = [(idx, char) for idx, char in enumerate(token) if char in leet_mappings]
        if multi_leet and len(replaceable) > 1:
            # Generar todas las combinaciones de 1..N reemplazos (máx por defecto 8 posiciones para no explotar)
            max_positions = min(len(replaceable), max_leet_replacements)
            for count in range(1, max_positions + 1):
                for combo in itertools.combinations(replaceable[:max_positions], count):
                    chars = list(token)
                    for idx, char in combo:
                        chars[idx] = leet_mappings[char]
                    mutated.add("".join(chars))
        else:
            # Leet simple: un reemplazo a la vez
            variant = list(token)
            for idx, char in enumerate(variant):
                if char in leet_mappings:
                    copy = variant.copy()
                    copy[idx] = leet_mappings[char]
                    mutated.add("".join(copy))
    if token[::-1] != token:
        mutated.add(token[::-1])
    return mutated


def build_char_pool(hash_mode, base_tokens, options):
    pool = set()
    if hash_mode in ("letters", "all"):
        if options.get("lower") and not options.get("upper"):
            pool.update(DEFAULT_LOWER)
        elif options.get("upper") and not options.get("lower"):
            pool.update(DEFAULT_UPPER)
        else:
            pool.update(DEFAULT_LOWER + DEFAULT_UPPER)
    if hash_mode in ("digits", "all") or options.get("digits"):
        pool.update(DEFAULT_DIGITS)
    if hash_mode in ("specials", "all") or options.get("specials"):
        pool.update(DEFAULT_SPECIALS)
    if hash_mode == "base":
        for token in base_tokens:
            pool.update(token)
    if hash_mode == "all" and not pool:
        pool.update(DEFAULT_LOWER + DEFAULT_UPPER + DEFAULT_DIGITS + DEFAULT_SPECIALS)
    return sorted(pool)


def decompose_number(num_str):
    """Descompone un número en fragmentos útiles para combinaciones."""
    fragments = set()
    if not num_str or not num_str.isdigit():
        return fragments
    fragments.add(num_str)
    if len(num_str) >= 2:
        fragments.add(num_str[-2:])
        fragments.add(num_str[:2])
    if len(num_str) >= 4:
        fragments.add(num_str[-4:])
        fragments.add(num_str[:4])
    if len(num_str) == 4:
        fragments.add(num_str[2:])
    return fragments


def collect_social_tokens(params, dictionary_words, options):
    normalized = set()
    numeric_parts = set()

    def process_value(value, should_decompose):
        normalized.update(normalize_token(value, should_decompose))
        for token in normalize_token(value, should_decompose):
            if token.isdigit():
                numeric_parts.add(token)
                if should_decompose:
                    numeric_parts.update(decompose_number(token))

    for key in ("name", "color", "birth_year", "year", "family_name", "family_years", "team", "birth_place", "living_city", "dni", "pet", "singer"):
        value = params.get(key)
        if not value:
            continue
        should_decompose = (
            params.get("decompose_numbers", False) and key in ("birth_year", "year", "family_years", "dni")
        ) or (
            params.get("decompose_number_dates", False) and key in ("birth_year", "year", "family_years")
        ) or (
            params.get("decompose_number_document", False) and key == "dni"
        )
        if isinstance(value, list):
            for item in value:
                process_value(item, should_decompose)
        else:
            process_value(value, should_decompose)

    if params.get("other"):
        for extra in params["other"]:
            if extra:
                process_value(extra, False)

    for word in dictionary_words:
        normalized.add(word)
        normalized.update(normalize_token(word, False))
        if word.isdigit():
            numeric_parts.add(word)

    # Filtrar una vez tokens muy cortos para evitar explosiones combinatorias.
    normalized = {token for token in normalized if len(token) > 1}
    return sorted(normalized), sorted(numeric_parts)


def _case_variants(token, options):
    variants = set()
    if options.get("lower") and not options.get("upper"):
        variants.add(token.lower())
    elif options.get("upper") and not options.get("lower"):
        variants.add(token.upper())
    else:
        variants.update({token, token.lower(), token.upper(), token.capitalize()})
    if options.get("complexity", 2) >= 3:
        for variant in list(variants):
            if variant[::-1] != variant:
                variants.add(variant[::-1])
        # swapcase: "Marco" → "mARCO"
        variants.add(token.swapcase())
        # alternating: "Marco" → "MaRcO" (par=original, impar=invertido)
        alt = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(token))
        variants.add(alt)
    return {v for v in variants if v}


def _generate_token_variants(base, options, max_length):
    suffixes = list(DEFAULT_DIGIT_SUFFIXES)
    suffixes.extend(options.get("digit_suffixes") or [])
    birth_years = options.get("birth_year")
    if birth_years:
        if isinstance(birth_years, list):
            suffixes.extend([y for y in birth_years if y])
        else:
            suffixes.append(birth_years)
    suffixes.extend([num for num in options.get("numeric_parts", []) if num])
    specials = list(DEFAULT_SPECIALS) if options.get("specials") else []

    variants = set(_case_variants(base, options))
    multi_leet = options.get("complexity", 2) >= 3
    if options.get("leet"):
        max_leet = options.get("max_leet_replacements", 8)
        for variant in list(variants):
            variants.update(apply_mutations(variant, True, options.get("leet_mappings"), multi_leet=multi_leet, max_leet_replacements=max_leet))

    for variant in variants:
        if len(variant) <= max_length:
            yield variant

        if options.get("digits"):
            for num in suffixes:
                if not num:
                    continue
                candidate = f"{variant}{num}"
                if len(candidate) <= max_length:
                    yield candidate
                if options.get("specials"):
                    for sym in specials:
                        if len(candidate) + 1 <= max_length:
                            yield f"{candidate}{sym}"
                        if len(sym) + len(candidate) <= max_length:
                            yield f"{sym}{candidate}"

        if options.get("specials"):
            for sym in specials:
                candidate1 = f"{variant}{sym}"
                if len(candidate1) <= max_length:
                    yield candidate1
                candidate2 = f"{sym}{variant}"
                if len(candidate2) <= max_length:
                    yield candidate2

        if options.get("complexity", 2) >= 4:
            if len(variant) + 1 <= max_length:
                yield f"{variant}!"
            if len(variant) + 4 <= max_length:
                yield f"{variant}2024"

        if options.get("complexity", 2) >= 5 and options.get("digits") and options.get("specials"):
            for num in suffixes:
                if not num:
                    continue
                for sym in specials:
                    candidate = f"{variant}{num}{sym}"
                    if len(candidate) <= max_length:
                        yield candidate
                    candidate2 = f"{variant}{sym}{num}"
                    if len(candidate2) <= max_length:
                        yield candidate2
                    candidate3 = f"{sym}{variant}{num}"
                    if len(candidate3) <= max_length:
                        yield candidate3


# La función generate_combination_variants se ha movido a selic_core.py


def filter_by_length_and_complexity(candidates, min_length, max_length, options):
    cleaned = []
    for candidate in candidates:
        length = len(candidate)
        if length < min_length or length > max_length:
            continue
        cleaned.append(candidate)
    return cleaned


def _calculate_pattern_pool_size(hashes, full_pool_size):
    """Calcula el tamaño óptimo del pool para un patrón según la cantidad de #.
    Busca que pool^hashes no supere MAX_TEMPLATE_EXPANSION."""
    if hashes == 0:
        return full_pool_size
    # Encontrar el pool máximo tal que pool^hashes <= MAX_TEMPLATE_EXPANSION
    optimal = int(MAX_TEMPLATE_EXPANSION ** (1.0 / hashes))
    return min(optimal, full_pool_size)


def generate_from_patterns(patterns, char_pool, min_length, max_length, count_limit=None):
    if not patterns:
        return
    generated = 0
    for pattern in patterns:
        hashes = pattern.count("#")
        if hashes == 0:
            if min_length <= len(pattern) <= max_length:
                yield pattern
                generated += 1
                if count_limit and generated >= count_limit:
                    return
            continue
        if not char_pool:
            continue
        # Pool dinámico: ajusta el tamaño para que las combinaciones no exploten
        pool_size = _calculate_pattern_pool_size(hashes, len(char_pool))
        choices = char_pool[:pool_size]
        total_combos = pool_size ** hashes
        if total_combos > MAX_TEMPLATE_EXPANSION:
            print(color_text(
                f"⚠ Patrón '{pattern}' con {hashes} marcadores (#) generaría {total_combos:,} combinaciones. "
                f"Limitando pool a {pool_size} caracteres (~{pool_size**hashes:,} combinaciones).",
                COLOR_YELLOW
            ))
        for product in itertools.product(choices, repeat=hashes):
            candidate_chars = []
            replacement_index = 0
            for char in pattern:
                if char == "#":
                    candidate_chars.append(product[replacement_index])
                    replacement_index += 1
                else:
                    candidate_chars.append(char)
            candidate = "".join(candidate_chars)
            if min_length <= len(candidate) <= max_length:
                yield candidate
                generated += 1
                if count_limit and generated >= count_limit:
                    return
            if generated > MAX_TEMPLATE_EXPANSION:
                return


def print_live_candidate(candidate, progress_state):
    progress_state["current"] = candidate
    progress_state["generated"] = progress_state.get("generated", 0) + 1


def _format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


def _format_size(bytes_count):
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024*1024):.1f} MB"
    else:
        return f"{bytes_count / (1024*1024*1024):.2f} GB"


def show_progress(stop_event, total_estimate, progress_state, output_file):
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    base_name = os.path.basename(output_file) if output_file else DEFAULT_OUTPUT_FILE
    start_time = time.time()
    sys.stdout.write("\n\n")
    sys.stdout.flush()
    i = 0
    while not stop_event.is_set():
        current = progress_state.get("current") or "..."
        generated = progress_state.get("generated", 0)
        skipped = progress_state.get("skipped_duplicates", 0)
        elapsed = time.time() - start_time
        speed = int(generated / elapsed) if elapsed > 0 else 0
        # Estimar tamaño del archivo
        try:
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
        except OSError:
            file_size = 0
        spinner_char = spinner[i % len(spinner)]
        line1 = (f"  {color_text(spinner_char, COLOR_GREEN)} "
                 f"{color_text(f'{generated:,}', COLOR_CYAN)} generadas "
                 f"| {color_text(f'{skipped:,}', COLOR_ORANGE)} duplicados "
                 f"| {color_text(f'{speed:,}/s', COLOR_GREEN)} "
                 f"| {color_text(_format_size(file_size), COLOR_YELLOW)} "
                 f"| {color_text(_format_time(elapsed), COLOR_CYAN)}")
        line2 = (f"  {color_text('[', COLOR_YELLOW)}"
                 f"{color_text(base_name, COLOR_CYAN)}"
                 f"{color_text(']: ', COLOR_YELLOW)}"
                 f"{color_text(current[:50], COLOR_ORANGE)}")
        sys.stdout.write("\033[2A")
        sys.stdout.write("\033[2K" + line1 + "\n")
        sys.stdout.write("\033[2K" + line2 + "\n")
        sys.stdout.flush()
        i += 1
        time.sleep(0.3)
    # Guardar tiempo total en progress_state
    progress_state["elapsed"] = time.time() - start_time
    print()
    print("Generación completada.")


def stream_candidates_to_file(file_path, candidate_iterables, min_length, max_length, count_limit=None, progress_state=None, max_ram_gb=3):
    written = 0
    seen = set()
    # ~80 bytes por entrada en el set (string + overhead del set)
    max_entries = int(max_ram_gb * 1024 * 1024 * 1024 / 80)
    ram_exceeded = False
    skipped_duplicates = 0
    # Estadísticas por tipo
    stats = {"alpha": 0, "alnum": 0, "symbols": 0, "lengths": {}}
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for iterable in candidate_iterables:
                for candidate in iterable:
                    if not candidate:
                        continue
                    if len(candidate) < min_length or len(candidate) > max_length:
                        continue
                    # Deduplicación en memoria con límite de RAM
                    if candidate in seen:
                        skipped_duplicates += 1
                        continue
                    if not ram_exceeded:
                        seen.add(candidate)
                        if len(seen) >= max_entries:
                            ram_exceeded = True
                    f.write(f"{candidate}\n")
                    written += 1
                    # Estadísticas
                    clen = len(candidate)
                    stats["lengths"][clen] = stats["lengths"].get(clen, 0) + 1
                    if candidate.isalpha():
                        stats["alpha"] += 1
                    elif candidate.isalnum():
                        stats["alnum"] += 1
                    else:
                        stats["symbols"] += 1
                    if progress_state is not None:
                        print_live_candidate(candidate, progress_state)
                    if count_limit and written >= count_limit:
                        if progress_state is not None:
                            progress_state["ram_exceeded"] = ram_exceeded
                            progress_state["skipped_duplicates"] = skipped_duplicates
                        return written
    except IOError as e:
        print(f"Error al escribir el archivo de salida: {e}")
    if progress_state is not None:
        progress_state["ram_exceeded"] = ram_exceeded
        progress_state["skipped_duplicates"] = skipped_duplicates
        progress_state["stats"] = stats
    # Liberar memoria del set
    del seen
    gc.collect()
    return written


def deduplicate_file(input_file, output_file=None):
    """Elimina duplicados de un archivo. Usa Python set line-by-line para evitar
    cargar todo en RAM (el Get-Content de PowerShell cargaba todo, mismo error del OrderedDict).
    Si el set crece demasiado, cae a sort nativo del SO como último recurso."""
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_dedup{ext}"
    
    try:
        if not os.path.exists(input_file):
            print(f"Error: No se encuentra el archivo {input_file}")
            return False
        
        file_size = os.path.getsize(input_file)
        print(f"Procesando archivo: {input_file} ({file_size / (1024*1024):.1f} MB)")
        
        # Intentar dedup con Python set (line-by-line, no carga todo en RAM)
        seen = set()
        input_lines = 0
        output_lines = 0
        max_set_entries = 50_000_000  # ~4GB de RAM para el set
        set_overflow = False
        
        try:
            with open(input_file, "r", encoding="utf-8", errors="ignore") as fin, \
                 open(output_file, "w", encoding="utf-8") as fout:
                for line in fin:
                    input_lines += 1
                    stripped = line.rstrip("\n\r")
                    if not stripped:
                        continue
                    if stripped not in seen:
                        if not set_overflow:
                            seen.add(stripped)
                            if len(seen) >= max_set_entries:
                                set_overflow = True
                        fout.write(stripped + "\n")
                        output_lines += 1
        except MemoryError:
            # Si el set agotó la RAM, caer a sort nativo del SO
            del seen
            gc.collect()
            print(color_text("RAM insuficiente para dedup Python. Usando sort nativo del SO...", COLOR_YELLOW))
            return _deduplicate_file_os(input_file, output_file)
        
        del seen
        gc.collect()
        
        # Si hubo overflow del set, el archivo puede tener duplicados residuales
        # En ese caso, usar sort nativo como segunda pasada
        if set_overflow:
            print(color_text("Set de dedup lleno. Ejecutando segunda pasada con sort nativo...", COLOR_YELLOW))
            temp_file = output_file + ".tmp"
            os.replace(output_file, temp_file)
            success = _deduplicate_file_os(temp_file, output_file)
            try:
                os.remove(temp_file)
            except OSError:
                pass
            if not success:
                return False
            output_lines = sum(1 for _ in open(output_file, 'r', encoding='utf-8', errors='ignore'))
        
        duplicados = input_lines - output_lines
        print(f"\n✓ Deduplicación completada:")
        print(f"  Líneas originales: {input_lines:,}")
        print(f"  Duplicados removidos: {duplicados:,} ({100*duplicados/input_lines:.1f}%)")
        print(f"  Archivo guardado en: {output_file}")
        return True
    except Exception as e:
        print(f"Error inesperado al deduplicar: {e}")
        return False


def _deduplicate_file_os(input_file, output_file):
    """Deduplicación usando comando nativo del SO (fallback)."""
    try:
        if platform.system() == "Windows":
            cmd = f"sort \"{input_file}\" | Get-Unique | Out-File -FilePath \"{output_file}\" -Encoding UTF8"
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                ["sort", "-u", input_file, "-o", output_file],
                capture_output=True,
                text=True
            )
        if result.returncode != 0:
            print(f"Error en sort nativo: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error en sort nativo: {e}")
        return False


def build_config_from_args(args, defaults=None):
    defaults = defaults or {}
    base_dir = args.base_dir or defaults.get("base_dir") or None
    dict_file = args.dict if args.dict != DEFAULT_DICT_FILE or defaults.get("dict_file") is None else defaults.get("dict_file")
    output_file = resolve_path(base_dir, args.output or defaults.get("output_file") or DEFAULT_OUTPUT_FILE)
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
    }


def config_has_social_info(config):
    return any(config.get(key) for key in ("name", "color", "birth_year", "family_name", "family_years", "team", "birth_place", "living_city", "dni", "pet", "singer")) or config.get("other")


def run_config_wizard(config_path):
    import configparser
    print_header()
    print("=== MODO DE CONFIGURACIÓN INTERACTIVA ===")
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
        "extreme_generation_limit": config.get("extreme_generation_limit", 5000000000)
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
            pattern_candidates = generate_from_patterns(
                config.get("patterns"), char_pool,
                config["min_length"], config["max_length"], config.get("count")
            )
            candidate_iterables.append(pattern_candidates)

        if config.get("count") is None or True:
            agr = config.get("agresividad", 4)
            for t in range(1, agr + 1):
                candidate_iterables.append(generate_tiered_variants(base_tokens, options, t, config.get("count"), config["max_length"]))

        if not config.get("patterns") and not config_has_social_info(config):
            print(color_text("No se proporcionó información de ingeniería social ni patrones. Se generará contenido básico desde el diccionario.", COLOR_MAGENTA))
            candidate_iterables.append((word for word in dictionary_words))

        # Contraseñas comunes estáticas (sin combinar, solo se agregan tal cual)
        candidate_iterables.append(iter(COMMON_PASSWORDS))

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
                print(f"  Tiempo: {color_text(_format_time(elapsed), COLOR_CYAN)}")
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
