# SELIC Core - Motor de Generación Heurística v1.2.0
# Parte del proyecto SELIC (Social Engineering Wordlist Generator)
__version__ = "1.2.0"

import re
import os
import gc
import itertools
import platform
import subprocess
import sys
import time
import shutil
from datetime import datetime

# --- Compatibilidad multiplataforma: forzar UTF-8 en Windows/Mac/Linux ---
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass  # Python < 3.7 o entorno sin reconfigure

DEFAULT_SPECIALS = "!@#$%^&*_+-="
DEFAULT_DIGITS = "0123456789"
DEFAULT_DIGIT_SUFFIXES = ["123", "2023", "2024", "007"]
DEFAULT_LOWER = "abcdefghijklmnñopqrstuvwxyz"
DEFAULT_UPPER = DEFAULT_LOWER.upper()
COLOR_BLUE = "\033[38;5;33m"
COLOR_CYAN = "\033[38;5;51m"
COLOR_GREEN = "\033[38;5;82m"
COLOR_YELLOW = "\033[38;5;226m"
COLOR_ORANGE = "\033[38;5;208m"
COLOR_MAGENTA = "\033[38;5;201m"
COLOR_RESET = "\033[0m"
MAX_TEMPLATE_EXPANSION = 100000000

COMMON_PASSWORDS = [
    "123456", "12345678", "123456789", "1234567890", "password", "contraseña",
    "qwerty", "abc123", "111111", "123123", "admin", "letmein", "welcome",
    "monkey", "master", "dragon", "login", "princess", "football", "shadow",
    "sunshine", "trustno1", "iloveyou", "batman", "access", "hello", "charlie",
    "donald", "password1", "qwerty123", "654321", "555555", "lovely", "7777777",
    "888888", "000000", "1q2w3e", "1q2w3e4r", "q1w2e3r4", "123qwe", "zxcvbnm",
    "asdfghjkl", "1qaz2wsx", "password123", "admin123", "root", "toor",
    "pass", "test", "guest", "changeme", "fuckyou", "jordan", "thomas",
]

def color_text(text, color_code):
    if not sys.stdout.isatty():
        return text
    return f"{color_code}{text}\033[0m"

def split_words(value):
    tokens = set()
    if not value:
        return tokens
    value = str(value).strip()
    for chunk in re.split(r"[\s,_\-\/\.]+", value):
        if not chunk:
            continue
        tokens.add(chunk)
        camel_parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", chunk)
        for part in camel_parts:
            if part:
                tokens.add(part)
    return tokens

def parse_multi_values(value):
    if value is None:
        return None
    if isinstance(value, list):
        items = []
        for part in value:
            if part:
                items.extend([item.strip() for item in re.split(r"[\s,]+", part) if item.strip()])
        return items or None
    text = str(value).strip()
    if not text:
        return None
    items = [item.strip() for item in re.split(r"[\s,]+", text) if item.strip()]
    return items or None

def validate_date(date_str):
    if not date_str:
        return False
    if re.match(r"^\d{4}$", date_str):
        year = int(date_str)
        return 1900 <= year <= 2100
    match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", date_str)
    if match:
        day, month, year = map(int, match.groups())
        if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100):
            return False
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return day <= days_in_month[month - 1]
    return False

def validate_dni(dni_str):
    if not dni_str:
        return True
    # Ahora permite letras y números, de 4 a 15 caracteres (soporte internacional)
    if not re.match(r"^[a-zA-Z0-9]{4,15}$", dni_str):
        return False
    return True

def log_error(message):
    try:
        with open("selic_errors.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - ERROR: {message}\n")
    except:
        pass

def remove_accents(text):
    if not text:
        return text
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
        'Ä': 'A', 'Ë': 'E', 'Ï': 'I', 'Ö': 'O', 'Ü': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    res = text
    for k, v in replacements.items():
        res = res.replace(k, v)
    return res

def normalize_token(value, decompose_numbers=False, remove_accents_flag=True, use_separators=True):
    normalized = set()
    if not value:
        return normalized
    value = str(value).strip()
    if not value:
        return normalized
    values_to_process = [value]
    if remove_accents_flag:
        clean_val = remove_accents(value)
        if clean_val != value:
            values_to_process.append(clean_val)

    for val in values_to_process:
        if " " not in val:
            normalized.add(val)
            normalized.add(val.lower())
            normalized.add(val.upper())
            normalized.add(val.capitalize())
            
        normalized.add(val.replace(" ", ""))
        normalized.add(val.replace("-", ""))
        normalized.add(val.replace("_", ""))
        normalized.add(val.replace("/", ""))
        if use_separators:
            parts = val.split()
            normalized.add("_".join(parts))
            normalized.add(".".join(parts))
            normalized.add("-".join(parts))
            if len(parts) >= 2:
                # Iniciales con separador (Ej: J.Diaz, Diaz.J)
                for sep in [".", "_", "-"]:
                    normalized.add(f"{parts[0][0]}{sep}{parts[-1]}")
                    normalized.add(f"{parts[0]}{sep}{parts[-1][0]}")

        if re.search(r"[\-/\.\\]", val):
            date_parts = [p for p in re.split(r"[\-/\.\\\s]+", val) if p]
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
                            year_2 = year[-2:] if len(year) >= 2 else year
                            # Largos
                            normalized.add(day_z + month_z + year)
                            normalized.add(month_z + day_z + year)
                            normalized.add(day_z + month_z)
                            normalized.add(month_z + year)
                            normalized.add(day_z + year)
                            normalized.add(month_z + day_z)
                            # Cortos (DDMMYY)
                            normalized.add(day_z + month_z + year_2)
                            normalized.add(month_z + day_z + year_2)
                            normalized.add(day_z + year_2)
                            normalized.add(month_z + year_2)
                            
                            normalized.add(day.lstrip("0"))
                            normalized.add(month.lstrip("0"))
                            normalized.add(day.lstrip("0") + month.lstrip("0"))
                            normalized.add(month.lstrip("0") + day.lstrip("0"))

        for part in split_words(val):
            normalized.add(part)
            normalized.add(part.lower())
            normalized.add(part.upper())
            normalized.add(part.capitalize())
            if part.isdigit():
                if decompose_numbers:
                    normalized.update(decompose_number(part))
                continue
            for length in range(1, min(5, len(part)) + 1):
                normalized.add(part[:length])
            for length in range(1, min(5, len(part)) + 1):
                normalized.add(part[-length:])
    normalized = {token for token in normalized if len(token) > 1 and " " not in token}
    if not use_separators:
        normalized = {token for token in normalized if not re.search(r"[\-/\._\\]", token)}
    return normalized

def apply_mutations(token, enable_leet=True, leet_mappings=None, multi_leet=False, max_leet_replacements=8, leet_full=False):
    leet_mappings = leet_mappings or {
        "a": "4", "A": "4", "s": "$", "S": "$", "o": "0", "O": "0",
        "i": "1", "I": "1", "e": "3", "E": "3", "l": "1", "L": "1",
    }
    mutated = {token}
    if enable_leet:
        replaceable = [(idx, char) for idx, char in enumerate(token) if char in leet_mappings]
        if multi_leet and len(replaceable) > 1:
            max_positions = min(len(replaceable), max_leet_replacements)
            if leet_full:
                counts_to_do = set(range(1, max_positions + 1))
            else:
                counts_to_do = {1}
                if max_positions >= 2: counts_to_do.add(2)
                if max_positions >= 3: counts_to_do.add(max_positions)
            for count in counts_to_do:
                for combo in itertools.combinations(replaceable[:max_positions], count):
                    chars = list(token)
                    for idx, char in combo:
                        chars[idx] = leet_mappings[char]
                    mutated.add("".join(chars))
        else:
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
        remove_acc = options.get("remove_accents_flag", True)
        use_seps = options.get("use_separators", False)
        normalized.update(normalize_token(value, should_decompose, remove_acc, use_seps))
        for token in normalize_token(value, should_decompose, remove_acc, use_seps):
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
        remove_acc = options.get("remove_accents_flag", True)
        normalized.add(word)
        normalized.update(normalize_token(word, False, remove_acc))
        if word.isdigit():
            numeric_parts.add(word)

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
        variants.add(token.swapcase())
        alt = "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(token))
        variants.add(alt)
    return {v for v in variants if v}

def _generate_token_variants(base, options, max_length):
    suffixes = list(DEFAULT_DIGIT_SUFFIXES)
    custom_digits = options.get("digit_suffixes") or []
    suffixes.extend([re.sub(r"[\-/\._\\\s]", "", str(d)) for d in custom_digits if d])
    birth_years = options.get("birth_year")
    if birth_years:
        if isinstance(birth_years, list):
            suffixes.extend([re.sub(r"[\-/\._\\\s]", "", str(y)) for y in birth_years if y])
        else:
            suffixes.append(re.sub(r"[\-/\._\\\s]", "", str(birth_years)))
    suffixes.extend([num for num in options.get("numeric_parts", []) if num])
    specials = list(DEFAULT_SPECIALS) if options.get("specials") else []

    variants = set(_case_variants(base, options))
    multi_leet = options.get("complexity", 2) >= 3
    if options.get("leet"):
        max_leet = options.get("max_leet_replacements", 8)
        leet_full = options.get("leet_full", False)
        for variant in list(variants):
            variants.update(apply_mutations(variant, True, options.get("leet_mappings"), multi_leet=multi_leet, max_leet_replacements=max_leet, leet_full=leet_full))

    for variant in variants:
        if len(variant) <= max_length:
            yield variant

        if options.get("digits"):
            for num in suffixes:
                if not num:
                    continue
                candidate = f"{variant}{num}"
                candidate_pre = f"{num}{variant}"
                if len(candidate) <= max_length:
                    yield candidate
                if len(candidate_pre) <= max_length:
                    yield candidate_pre
                
                # Símbolos dobles si complejidad >= 2
                if options.get("complexity", 2) >= 2 and options.get("specials"):
                    for sym in specials:
                        if sym in ["!", "@", "."]:
                            c_dbl = f"{variant}{sym}{sym}"
                            if len(c_dbl) <= max_length:
                                yield c_dbl
                
                if options.get("specials"):
                    for sym in specials:
                        if len(candidate) + len(sym) <= max_length:
                            yield f"{candidate}{sym}"
                            yield f"{sym}{candidate}"
                        if len(candidate_pre) + len(sym) <= max_length:
                            yield f"{candidate_pre}{sym}"
                            yield f"{sym}{candidate_pre}"

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
                    candidate2 = f"{variant}{sym}{num}"
                    if len(candidate2) <= max_length:
                        yield candidate2
                    candidate4 = f"{num}{sym}{variant}"
                    if len(candidate4) <= max_length:
                        yield candidate4

def estimate_passwords(num_tokens, max_combo, options):
    """Estima cuántas contraseñas se generarán según los parámetros actuales."""
    if num_tokens == 0:
        return 0
    # Variantes de caso por token
    case_mult = 4  # original, lower, upper, capitalize
    comp = options.get("complexity", 2)
    if comp >= 3:
        case_mult = 7  # + reversos, swapcase, alternating

    # Leet Speak
    leet_mult = 1
    if options.get("leet"):
        if options.get("leet_full"):
            leet_mult = 30
        elif comp >= 3:
            leet_mult = 15  # promedio realista
        else:
            leet_mult = 3

    # El pool real de trabajo es el número de tokens mutados por caso y leet
    effective_n = num_tokens * case_mult * leet_mult
    
    # Permutaciones base según profundidad de mezcla usando el pool real
    base_perms = 0
    for length in range(1, max_combo + 1):
        perm = 1
        for i in range(length):
            perm *= (effective_n - i) if (effective_n - i) > 0 else 1
        base_perms += perm

    estimated = base_perms
    
    # Sufijos numéricos
    suffix_count = len(DEFAULT_DIGIT_SUFFIXES) + len(options.get("numeric_parts", []))
    digit_mult = 1
    if options.get("digits"):
        digit_mult = 1 + suffix_count * 2  # post + pre

    # Símbolos: variant+sym, sym+variant, más cruces con dígitos
    sym_count = len(DEFAULT_SPECIALS) if options.get("specials") else 0
    sym_mult = 1
    if sym_count > 0:
        sym_mult = 1 + sym_count * 2  # post + pre

    estimated_with_suffixes = estimated * digit_mult * sym_mult
    # Deduplicación real (observada) elimina ~40-50% de duplicados en cruces complejos
    dedup_factor = 0.6 if estimated_with_suffixes > 10000 else 0.85
    
    # Ajuste drástico para Niveles Heurísticos (1, 2, 3)
    # Los niveles heurísticos intencionalmente NO cruzan números y símbolos con las parejas.
    agr = options.get("agresividad", 4)
    # Al final, si es un nivel heurístico o manual de baja profundidad, aplicamos factor de escala
    # para no asustar al usuario con el producto cartesiano teórico.
    if agr < 4 or max_combo <= 2:
        # Los niveles 1, 2 y 3 son heurísticos. Tras auditoría real, 
        # el factor 0.10 es el más cercano a la realidad para evitar sobre-estimaciones.
        dedup_factor *= 0.10

    estimated_final = int(estimated_with_suffixes * dedup_factor)
    return max(estimated_final, base_perms)

def estimate_wordlist_size(options, social_tokens):
    """Alias para la GUI: Calcula el estimado de contraseñas."""
    # Calcular mezcla según complejidad si es auto
    max_combo = options.get("mezcla")
    if not isinstance(max_combo, int):
        comp = options.get("complexity", 2)
        max_combo = 1 if comp == 1 else (2 if comp <= 3 else 3)
    
    return estimate_passwords(len(social_tokens), max_combo, options)

def _format_estimate(n):
    """Formatea un número grande de forma legible."""
    if n < 1_000:
        return f"{n:,}"
    elif n < 1_000_000:
        return f"~{n/1_000:.0f} mil"
    elif n < 1_000_000_000:
        return f"~{n/1_000_000:.0f} millones"
    else:
        return f"~{n/1_000_000_000:.1f} billones"

def get_projected_level(max_combo, options):
    """Determina a qué nivel heurístico (int) equivalen los ajustes manuales."""
    comp = options.get("complexity", 2)
    leet = options.get("leet", False)
    specials = options.get("specials", False)
    
    if max_combo >= 3 or comp >= 4:
        return 4
    if leet or comp >= 3:
        return 3
    if specials or max_combo >= 2:
        return 2
    return 1

def _combo_name(level):
    """Devuelve el nombre legible de un nivel de agresividad."""
    names = {
        1: "Social Lite (Básico)",
        2: "Social Medium (Intermedio)",
        3: "Social Deep (Avanzado)",
        4: "Social Extreme (Exhaustivo)"
    }
    return names.get(level, f"Nivel {level}")

def show_impact_comparison(num_tokens, max_combo, options):
    """Muestra una tabla comparativa de cómo cada opción afecta la generación."""
    current_est = estimate_passwords(num_tokens, max_combo, options)
    
    print(color_text("  ¿Qué pasa si cambio...?", COLOR_CYAN))
    print(color_text("  ─────────────────────────────────────────────", COLOR_CYAN))
    
    # Comparar niveles de mezcla
    for lvl in (1, 2, 3, 4):
        opts_copy = dict(options)
        e = estimate_passwords(num_tokens, lvl, opts_copy)
        if lvl == max_combo:
            marker = color_text(" ◄ actual", COLOR_GREEN)
        else:
            ratio = e / current_est if current_est > 0 else 0
            if ratio > 1:
                marker = color_text(f"  (×{ratio:.0f} más)", COLOR_ORANGE)
            else:
                marker = color_text(f"  (×{ratio:.2f} menos)", COLOR_GREEN)
        print(color_text(f"    Mezcla={lvl} ({_combo_name(lvl)}): ", COLOR_YELLOW) + color_text(f"{_format_estimate(e)}", COLOR_CYAN) + marker)
    
    print()
    
    # Comparar toggle de Simbolos
    if options.get("specials"):
        opts_no_sym = dict(options, specials=False)
        e_no_sym = estimate_passwords(num_tokens, max_combo, opts_no_sym)
        ratio = e_no_sym / current_est if current_est > 0 else 0
        print(color_text(f"    Simbolos=No:    {_format_estimate(e_no_sym)}", COLOR_YELLOW) + color_text(f"  (×{ratio:.2f} menos)", COLOR_GREEN))
    else:
        opts_yes_sym = dict(options, specials=True)
        e_yes_sym = estimate_passwords(num_tokens, max_combo, opts_yes_sym)
        ratio = e_yes_sym / current_est if current_est > 0 else 0
        print(color_text(f"    Simbolos=Si:    {_format_estimate(e_yes_sym)}", COLOR_YELLOW) + color_text(f"  (×{ratio:.0f} más)", COLOR_ORANGE))
    
    # Comparar toggle de Leet
    if options.get("leet"):
        opts_no_leet = dict(options, leet=False)
        e_no_leet = estimate_passwords(num_tokens, max_combo, opts_no_leet)
        ratio = e_no_leet / current_est if current_est > 0 else 0
        print(color_text(f"    Leet=No:        {_format_estimate(e_no_leet)}", COLOR_YELLOW) + color_text(f"  (×{ratio:.2f} menos)", COLOR_GREEN))
    else:
        opts_yes_leet = dict(options, leet=True)
        e_yes_leet = estimate_passwords(num_tokens, max_combo, opts_yes_leet)
        ratio = e_yes_leet / current_est if current_est > 0 else 0
        print(color_text(f"    Leet=Si:        {_format_estimate(e_yes_leet)}", COLOR_YELLOW) + color_text(f"  (×{ratio:.0f} más)", COLOR_ORANGE))
    
    # Comparar toggle de Numeros
    if options.get("digits"):
        opts_no_dig = dict(options, digits=False)
        e_no_dig = estimate_passwords(num_tokens, max_combo, opts_no_dig)
        ratio = e_no_dig / current_est if current_est > 0 else 0
        print(color_text(f"    Numeros=No:     {_format_estimate(e_no_dig)}", COLOR_YELLOW) + color_text(f"  (×{ratio:.2f} menos)", COLOR_GREEN))
    else:
        opts_yes_dig = dict(options, digits=True)
        e_yes_dig = estimate_passwords(num_tokens, max_combo, opts_yes_dig)
        ratio = e_yes_dig / current_est if current_est > 0 else 0
        print(color_text(f"    Numeros=Si:     {_format_estimate(e_yes_dig)}", COLOR_YELLOW) + color_text(f"  (×{ratio:.0f} más)", COLOR_ORANGE))
    
    # Escenario mínimo: todo apagado
    opts_min = dict(options, specials=False, leet=False, digits=False)
    e_min = estimate_passwords(num_tokens, 1, opts_min)
    print(color_text(f"    Todo mínimo:    {_format_estimate(e_min)}", COLOR_YELLOW) + color_text("  (solo palabras base)", COLOR_GREEN))
    
    print()

def show_pre_generation_summary(num_tokens, max_combo, options, interactive):
    """Muestra un resumen claro de lo que va a pasar ANTES de generar."""
    est = estimate_passwords(num_tokens, max_combo, options)
    # Estimación de peso: ~18 bytes por contraseña es un promedio seguro (letras+números+newline)
    gb_est = est * 18 / (1024**3)
    time_est_mins = est / (500_000 * 60)
    if time_est_mins < 1: time_est_mins = 1

    print(color_text("\n╔══════════════════════════════════════════════════════╗", COLOR_CYAN))
    print(color_text("║           RESUMEN PRE-GENERACIÓN                    ║", COLOR_CYAN))
    print(color_text("╚══════════════════════════════════════════════════════╝", COLOR_CYAN))
    print(color_text(f"  Palabras base:    {num_tokens}", COLOR_YELLOW))
    print(color_text(f"  Mezcla:           {max_combo} → {_combo_name(max_combo)}", COLOR_YELLOW))
    sym_str = "Si" if options.get("specials") else "No"
    leet_str = "Si" if options.get("leet") else "No"
    dig_str = "Si" if options.get("digits") else "No"
    print(color_text(f"  Simbolos={sym_str} | Leet={leet_str} | Numeros={dig_str}", COLOR_YELLOW))
    print(color_text(f"  Estimación:       {_format_estimate(est)} contraseñas", COLOR_CYAN))
    print(color_text(f"  Peso estimado:    ~{max(gb_est, 0.01):.2f} GB", COLOR_YELLOW))
    
    # Sensor de Espacio en Disco
    try:
        total, used, free = shutil.disk_usage(".")
        free_gb = free / (1024**3)
        if gb_est > free_gb:
            print(color_text(f"  ⚠ AVISO DE ESPACIO: {free_gb:.2f} GB libres. El archivo podría no caber.", COLOR_ORANGE))
        else:
            print(color_text(f"  Espacio en disco: {free_gb:.2f} GB disponibles (OK)", COLOR_GREEN))
    except:
        pass

    print(color_text(f"  Tiempo estimado:  ~{int(time_est_mins)} min", COLOR_YELLOW))
    print(color_text(f"  Nivel proyectado: {get_projected_level(max_combo, options)}", COLOR_CYAN))
    print()

    # Mostrar panel comparativo
    show_impact_comparison(num_tokens, max_combo, options)

    return est

def check_and_prompt_limits(num_tokens, options, interactive):
    """Calcula el nivel de mezcla según complejidad y permite al usuario ajustarlo."""
    comp = options.get("complexity", 2)
    agr = options.get("agresividad", 0) # Si existe, usar agresividad como guía primaria
    
    # Nivel de mezcla recomendado
    if agr >= 4 or comp >= 5:
        recommended = 4 # En Nivel 4, se permiten hasta 4
    elif agr >= 2 or comp >= 3:
        recommended = 2 # Niveles 2 y 3 mezclan parejas explícitamente
    else:
        recommended = 1 # Nivel 1 solo usa individuales

    max_combo = recommended

    # Mostrar resumen y permitir ajuste
    est = show_pre_generation_summary(num_tokens, max_combo, options, interactive)

    if interactive:
        # Usar el límite configurado o 5 mil millones por defecto
        limit_val = options.get("extreme_generation_limit", 5_000_000_000)
        if est > limit_val:
            print(color_text("☢ PELIGRO: GENERACIÓN EXTREMA DETECTADA ☢", COLOR_RED))
            print(color_text(f"  Esta configuración generará {_format_estimate(est)} contraseñas.", COLOR_RED))
            print(color_text("  Podría llenar tu disco duro o tardar DÍAS en terminar.", COLOR_RED))
            
            # Freno de Seguridad con Desafío
            if not options.get("allow_extreme_generation", False):
                print(color_text("\n[!] BLOQUEO DE SEGURIDAD ACTIVO", COLOR_RED))
                print(color_text(f"    Has superado el límite de seguridad de {_format_estimate(limit_val)}.", COLOR_YELLOW))
                print(color_text("    Si realmente sabes lo que haces, tienes tres opciones:", COLOR_CYAN))
                print(color_text("    1. Escribe 'ACEPTO EL RIESGO' para continuar esta vez.", COLOR_WHITE))
                print(color_text("    2. Cambia 'allow_extreme_generation = true' en selic.cfg para siempre.", COLOR_WHITE))
                print(color_text(f"    3. Aumenta 'extreme_generation_limit' en selic.cfg para subir este umbral.", COLOR_WHITE))
                
                confirm = input(color_text("\n>> [Escribe la frase o ENTER para volver a Mezcla segura]: ", COLOR_CYAN)).strip()
                
                # Ignorar espacios y mayúsculas para no ser frustrante
            max_combo = int(resp)
            print(color_text(f"  ✓ Mezcla ajustada a: {max_combo} ({_combo_name(max_combo)})", COLOR_GREEN))
            # Re-mostrar estimación actualizada
            new_est = estimate_passwords(num_tokens, max_combo, options)
            print(color_text(f"  Nueva estimación: {_format_estimate(new_est)} contraseñas", COLOR_CYAN))
        else:
            print(color_text(f"  ✓ Continuando con Mezcla={max_combo}", COLOR_GREEN))
    
    print(color_text("Presiona Ctrl+C en cualquier momento para cancelar.\n", COLOR_YELLOW))
    return max_combo

def generate_tiered_variants(tokens, options, tier, count_limit=None, max_length=16):
    """Genera combinaciones enfocadas usando heurísticas según el nivel de agresividad (Tier)."""
    tokens = [t for t in tokens if t]
    if not tokens:
        return

    # Ingredientes
    suffixes = list(DEFAULT_DIGIT_SUFFIXES)
    custom_digits = options.get("digit_suffixes") or []
    suffixes.extend([re.sub(r"[\-/\._\\\s]", "", str(d)) for d in custom_digits if d])
    birth_years = options.get("birth_year")
    if birth_years:
        if isinstance(birth_years, list):
            suffixes.extend([re.sub(r"[\-/\._\\\s]", "", str(y)) for y in birth_years if y])
        else:
            suffixes.append(re.sub(r"[\-/\._\\\s]", "", str(birth_years)))
    suffixes.extend([num for num in options.get("numeric_parts", []) if num])
    # Filtrar vacíos
    suffixes = list(set([s for s in suffixes if s]))
    
    specials = list(DEFAULT_SPECIALS) if options.get("specials") else []
    use_digits = options.get("digits", True)
    if not use_digits:
        suffixes = []
    
    specials = DEFAULT_SPECIALS if options.get("specials") else []

    # Generar variantes base de los tokens (sin Leet)
    base_variants = set()
    for t in tokens:
        base_variants.update(_case_variants(t, options))
    
    # Preparar tokens con Leet para Tiers >= 3
    leet_variants = set()
    multi_leet = options.get("complexity", 2) >= 3
    if options.get("leet") and tier >= 3:
        max_leet = options.get("max_leet_replacements", 8)
        leet_full = options.get("leet_full", False)
        for v in base_variants:
            leet_variants.update(apply_mutations(v, True, options.get("leet_mappings"), multi_leet=multi_leet, max_leet_replacements=max_leet, leet_full=leet_full))
            
    working_tokens = list(leet_variants if tier >= 3 else base_variants)
    yielded = 0

    def limit_reached():
        return count_limit is not None and yielded >= count_limit

    # Nivel 1: Básico (Solo Token + Números, Altamente probable)
    if tier == 1:
        for t in working_tokens:
            if len(t) <= max_length:
                yield t; yielded += 1
                if limit_reached(): return
            if use_digits:
                for num in suffixes:
                    c1, c2 = f"{t}{num}", f"{num}{t}"
                    if len(c1) <= max_length:
                        yield c1; yielded += 1
                        if limit_reached(): return
                    if len(c2) <= max_length:
                        yield c2; yielded += 1
                        if limit_reached(): return

    # Nivel 2: Variaciones Lógicas (Envolturas, Símbolos, Parejas)
    elif tier == 2:
        for t in working_tokens:
            if specials:
                for sym in specials:
                    c1, c2 = f"{t}{sym}", f"{sym}{t}"
                    if len(c1) <= max_length:
                        yield c1; yielded += 1
                        if limit_reached(): return
                    if len(c2) <= max_length:
                        yield c2; yielded += 1
                        if limit_reached(): return
                        # Símbolos dobles (Ej: marco!!)
                        if sym in ["!", "@", "."]:
                            c_dbl = f"{t}{sym}{sym}"
                            if len(c_dbl) <= max_length:
                                yield c_dbl; yielded += 1
                                if limit_reached(): return
                    if use_digits:
                        for num in suffixes:
                            c3, c4, c5 = f"{t}{num}{sym}", f"{t}{sym}{num}", f"{sym}{t}{num}"
                            if len(c3) <= max_length:
                                yield c3; yielded += 1
                                if limit_reached(): return
                            if len(c4) <= max_length:
                                yield c4; yielded += 1
                                if limit_reached(): return
                            if len(c5) <= max_length:
                                yield c5; yielded += 1
                                if limit_reached(): return
        
        # Envoltura de números (ej. 04segu1988)
        if use_digits:
            for t in working_tokens:
                for num1 in suffixes:
                    for num2 in suffixes:
                        if num1 != num2:
                            c = f"{num1}{t}{num2}"
                            if len(c) <= max_length:
                                yield c; yielded += 1
                                if limit_reached(): return
                            
        # Redundancia (Ej: marcomarco)
        for t in working_tokens:
            if len(t) > 2:
                c_red = f"{t}{t}"
                if len(c_red) <= max_length:
                    yield c_red; yielded += 1
                    if limit_reached(): return
                    
        # Parejas
        for t1, t2 in itertools.permutations(working_tokens, 2):
            c = f"{t1}{t2}"
            if len(c) <= max_length:
                yield c; yielded += 1
                if limit_reached(): return
            if specials:
                for sym in specials:
                    c2, c3, c_pre = f"{t1}{sym}{t2}", f"{t1}{t2}{sym}", f"{sym}{t1}{t2}"
                    if len(c2) <= max_length:
                        yield c2; yielded += 1
                        if limit_reached(): return
                    if len(c3) <= max_length:
                        yield c3; yielded += 1
                        if limit_reached(): return
                    if len(c_pre) <= max_length:
                        yield c_pre; yielded += 1
                        if limit_reached(): return
            if use_digits:
                # Sufijos comunes + sufijos específicos del objetivo
                target_suffixes = (suffixes[:10] if suffixes else [])
                for num in (["123", "2024", "2025"] + target_suffixes):
                    c4 = f"{t1}{t2}{num}"
                    if len(c4) <= max_length:
                        yield c4; yielded += 1
                        if limit_reached(): return
                        # [NUEVO] Word+Word+Number+Symbol (Ej: DiazRojas2024@)
                        if specials:
                            for s in ["!", "@", ".", "#"]:
                                c5 = f"{c4}{s}"
                                if len(c5) <= max_length:
                                    yield f"{s}{c4}"
                                    yield c5; yielded += 2
                                    if limit_reached(): return

    # Nivel 3: Leet Speak Común y Parejas con Leet
    elif tier == 3:
        for t in working_tokens:
            if len(t) <= max_length:
                yield t; yielded += 1
                if limit_reached(): return
            if use_digits:
                for num in suffixes:
                    c1, c2 = f"{t}{num}", f"{num}{t}"
                    if len(c1) <= max_length:
                        yield c1; yielded += 1
                        if limit_reached(): return
                    if len(c2) <= max_length:
                        yield c2; yielded += 1
                        if limit_reached(): return
            if specials:
                for sym in specials:
                    c1, c2 = f"{t}{sym}", f"{sym}{t}"
                    if len(c1) <= max_length:
                        yield c1; yielded += 1
                        if limit_reached(): return
                    if len(c2) <= max_length:
                        yield c2; yielded += 1
                        if limit_reached(): return
                    # Símbolos dobles
                    if sym in ["!", "@", "."]:
                        c_dbl = f"{t}{sym}{sym}"
                        if len(c_dbl) <= max_length:
                            yield c_dbl; yielded += 1
                            if limit_reached(): return
                    if use_digits:
                        for num in suffixes:
                            c3 = f"{t}{num}{sym}"
                            if len(c3) <= max_length:
                                yield c3; yielded += 1
                                if limit_reached(): return
        # Redundancia
        for t in working_tokens:
            if len(t) > 2:
                c_red = f"{t}{t}"
                if len(c_red) <= max_length:
                    yield c_red; yielded += 1
                    if limit_reached(): return
        
        for t1, t2 in itertools.permutations(working_tokens, 2):
            c = f"{t1}{t2}"
            if len(c) <= max_length:
                yield c; yielded += 1
                if limit_reached(): return
            if specials:
                for sym in specials:
                    c2, c3, c_pre = f"{t1}{sym}{t2}", f"{t1}{t2}{sym}", f"{sym}{t1}{t2}"
                    if len(c2) <= max_length:
                        yield c2; yielded += 1
                        if limit_reached(): return
                    if len(c3) <= max_length:
                        yield c3; yielded += 1
                        if limit_reached(): return
                    if len(c_pre) <= max_length:
                        yield c_pre; yielded += 1
                        if limit_reached(): return
            if use_digits:
                target_suffixes = (suffixes[:10] if suffixes else [])
                for num in (["123", "2024", "2025"] + target_suffixes):
                    c4 = f"{t1}{t2}{num}"
                    if len(c4) <= max_length:
                        yield c4; yielded += 1
                        if limit_reached(): return
                        if specials:
                            for s in ["!", "@", ".", "#"]:
                                c5 = f"{c4}{s}"
                                if len(c5) <= max_length:
                                    yield f"{s}{c4}"
                                    yield c5; yielded += 2
                                    if limit_reached(): return

    # Nivel 4: Fuerza Bruta Dirigida Completa
    elif tier >= 4:
        for candidate in generate_combination_variants(tokens, options, count_limit, max_length):
            yield candidate
            yielded += 1
            if limit_reached(): return

def generate_combination_variants(tokens, options, count_limit=None, max_length=16, force_max_combo=None):
    tokens = [t for t in tokens if t]
    if not tokens:
        return
    num_tokens = len(tokens)
    if force_max_combo is not None:
        max_combo = force_max_combo
    else:

        if num_tokens > 80:
            max_combo = 1
        elif num_tokens > 30:
            max_combo = 2
        else:
            max_combo = min(3, num_tokens)
    separators = [""]
    if options.get("use_separators", False) and options.get("complexity", 2) >= 3:
        separators.extend(["_", ".", "-"])

    yielded = 0
    # Redundancia en modo manual (Ej: adminadmin)
    if options.get("complexity", 2) >= 2:
        for t in tokens:
            if len(t) > 2:
                for candidate in _generate_token_variants(f"{t}{t}", options, max_length):
                    yield candidate; yielded += 1
                    if count_limit and yielded >= count_limit: return

    for length in range(1, max_combo + 1):
        for subset in itertools.permutations(tokens, length):
            for sep in separators:
                if length == 1 and sep != "":
                    continue
                base_candidate = sep.join(subset)
                if len(base_candidate) > max_length:
                    continue
                for candidate in _generate_token_variants(base_candidate, options, max_length):
                    yield candidate
                    yielded += 1
                    if count_limit and yielded >= count_limit:
                        return

def _calculate_pattern_pool_size(hashes, full_pool_size, max_expansion=None):
    if max_expansion is None:
        max_expansion = MAX_TEMPLATE_EXPANSION
    if hashes == 0:
        return full_pool_size
    optimal = int(max_expansion ** (1.0 / hashes))
    return min(optimal, full_pool_size)

def generate_from_patterns(patterns, char_pool, min_length, max_length, count_limit=None, max_expansion=None):
    if max_expansion is None:
        max_expansion = MAX_TEMPLATE_EXPANSION
    if not patterns:
        return
    
    # Definición de bolsas de caracteres para cada marcador
    MARKER_POOLS = {
        "#": char_pool,         # Social (Tus datos)
        "%": DEFAULT_DIGITS,    # Números
        "@": DEFAULT_LOWER,     # Minúsculas
        ",": DEFAULT_UPPER,     # Mayúsculas
        "?": DEFAULT_SPECIALS   # Símbolos
    }
    
    generated = 0
    for pattern in patterns:
        # Analizar el patrón para separar literales de marcadores (soportando escape \)
        segments = []
        pattern_markers = []
        i = 0
        while i < len(pattern):
            char = pattern[i]
            if char == "\\" and i + 1 < len(pattern):
                # Es un escape, el siguiente caracter es literal
                segments.append({"type": "literal", "value": pattern[i+1]})
                i += 2
            elif char in MARKER_POOLS:
                # Es un marcador
                segments.append({"type": "marker", "value": char})
                pattern_markers.append(char)
                i += 1
            else:
                # Es un caracter literal normal
                segments.append({"type": "literal", "value": char})
                i += 1
        
        if not pattern_markers:
            # Reconstruir literal si hubo escapes
            literal_val = "".join(s["value"] for s in segments)
            if min_length <= len(literal_val) <= max_length:
                yield literal_val
                generated += 1
                if count_limit and generated >= count_limit:
                    return
            continue

        # Calcular combinaciones totales
        total_combos = 1
        for m in pattern_markers:
            total_combos *= len(MARKER_POOLS[m])

        # Si excede el límite, truncamos proporcionalmente las bolsas
        current_pools = []
        if total_combos > max_expansion:
            reduction_factor = (max_expansion / total_combos) ** (1.0 / len(pattern_markers))
            for m in pattern_markers:
                full_pool = MARKER_POOLS[m]
                new_size = max(1, int(len(full_pool) * reduction_factor))
                current_pools.append(full_pool[:new_size])
            
            print(color_text(
                f"⚠ Patrón '{pattern}' generaría {total_combos:,} combinaciones.\n"
                f"  Limitando proporcionalmente para no exceder {max_expansion:,}.",
                COLOR_ORANGE
            ))
        else:
            for m in pattern_markers:
                current_pools.append(MARKER_POOLS[m])

        # Generar el producto cartesiano
        for combination in itertools.product(*current_pools):
            candidate_chars = []
            comb_idx = 0
            for seg in segments:
                if seg["type"] == "marker":
                    candidate_chars.append(combination[comb_idx])
                    comb_idx += 1
                else:
                    candidate_chars.append(seg["value"])
            
            candidate = "".join(candidate_chars)
            if min_length <= len(candidate) <= max_length:
                yield candidate
                generated += 1
                if count_limit and generated >= count_limit:
                    return
            if generated > max_expansion:
                return

def print_live_candidate(candidate, progress_state):
    progress_state["current"] = candidate
    progress_state["generated"] = progress_state.get("generated", 0) + 1

def format_time(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"

def format_size(bytes_count):
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
    base_name = os.path.basename(output_file) if output_file else "passlist.txt"
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
        
        eta_str = "--"
        if isinstance(total_estimate, (int, float)) and total_estimate > 0 and speed > 0:
            remaining = total_estimate - generated
            if remaining > 0:
                eta_seconds = remaining / speed
                eta_str = format_time(eta_seconds)
            else:
                eta_str = "0s"

        # Estimar tamaño del archivo
        try:
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
        except OSError:
            file_size = 0
        spinner_char = spinner[i % len(spinner)]
        line1 = (f"  {color_text(spinner_char, COLOR_GREEN)} "
                 f"{color_text(f'{generated:,}', COLOR_CYAN)} generadas "
                 f"| {color_text(f'{speed:,}/s', COLOR_GREEN)} "
                 f"| {color_text(f'ETA: {eta_str}', COLOR_ORANGE)} "
                 f"| {color_text(format_size(file_size), COLOR_YELLOW)} "
                 f"| {color_text(format_time(elapsed), COLOR_CYAN)}")
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
    progress_state["elapsed"] = time.time() - start_time
    print()
    print("Generación completada.")

def stream_candidates_to_file(file_path, candidate_iterables, min_length, max_length, count_limit=None, progress_state=None, max_ram_gb=3, show_live=True):
    written = 0
    seen = set()
    max_entries = int(max_ram_gb * 1024 * 1024 * 1024 / 80)
    ram_exceeded = False
    skipped_duplicates = 0
    stats = {"alpha": 0, "alnum": 0, "symbols": 0, "lengths": {}}
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for iterable in candidate_iterables:
                for candidate in iterable:
                    if not candidate:
                        continue
                    if len(candidate) < min_length or len(candidate) > max_length:
                        continue
                    if candidate in seen:
                        skipped_duplicates += 1
                        continue
                    if not ram_exceeded:
                        seen.add(candidate)
                        if len(seen) >= max_entries:
                            ram_exceeded = True
                    f.write(f"{candidate}\n")
                    written += 1
                    
                    # [SENSOR DE SEGURIDAD DE DISCO REAL-TIME]
                    if written % 500_000 == 0:
                        try:
                            _, _, free = shutil.disk_usage(".")
                            if free < 5 * 1024 * 1024 * 1024:  # Menos de 5 GB
                                print(color_text("\n\n☢ ¡FRENO DE PÁNICO! ESPACIO EN DISCO INSUFICIENTE (Límite 5GB) ☢", COLOR_RED))
                                print(color_text("  La generación se ha detenido para evitar el colapso del sistema.", COLOR_YELLOW))
                                print(color_text(f"  Contraseñas guardadas hasta ahora: {written:,}", COLOR_CYAN))
                                break
                        except: pass

                    clen = len(candidate)
                    stats["lengths"][clen] = stats["lengths"].get(clen, 0) + 1
                    if candidate.isalpha():
                        stats["alpha"] += 1
                    elif candidate.isalnum():
                        stats["alnum"] += 1
                    else:
                        stats["symbols"] += 1
                    if progress_state is not None and show_live:
                        print_live_candidate(candidate, progress_state)
                    elif progress_state is not None:
                        progress_state["generated"] = progress_state.get("generated", 0) + 1
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
    del seen
    gc.collect()
    return written

def deduplicate_file(input_file, output_file=None):
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_dedup{ext}"
    try:
        if not os.path.exists(input_file):
            print(f"Error: No se encuentra el archivo {input_file}")
            return False
        
        file_size = os.path.getsize(input_file)
        print(f"Procesando archivo: {input_file} ({file_size / (1024*1024):.1f} MB)")
        seen = set()
        input_lines = 0
        output_lines = 0
        max_set_entries = 50_000_000
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
            del seen
            gc.collect()
            print(color_text("RAM insuficiente para dedup Python. Usando sort nativo del SO...", COLOR_YELLOW))
            return _deduplicate_file_os(input_file, output_file)
        
        del seen
        gc.collect()
        
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

def check_and_prompt_limits(num_tokens, options, interactive):
    """Establece el nivel de mezcla final basándose en la complejidad y los límites de seguridad."""
    comp = options.get("complexity", 2)
    # Lógica de mezcla automática (Mejorada: Comp 2 -> Mix 2)
    if comp <= 1:
        auto_combo = 1
    elif comp <= 3:
        auto_combo = 2
    elif comp == 4:
        auto_combo = 3
    else:
        auto_combo = 4

    if not interactive:
        return auto_combo

    # Resumen y confirmación
    show_pre_generation_summary(num_tokens, auto_combo, options, True)

    print(f"  Mezcla actual: {auto_combo} ({_combo_name(auto_combo)})")
    print("  Opciones:")
    print("    ENTER  = continuar con la mezcla actual")
    print("    1/2/3/4 = cambiar nivel de mezcla")
    ans = input(">> Mezcla [ENTER para continuar]: ").strip()
    
    if ans in ("1", "2", "3", "4"):
        final_combo = int(ans)
        print(f"  ✓ Cambiando a Mezcla={final_combo}")
        return final_combo
    
    print(f"  ✓ Continuando con Mezcla={auto_combo}")
    return auto_combo
