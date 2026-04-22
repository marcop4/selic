#!/usr/bin/env python3
"""
<<<<<<< HEAD
Archivo de pruebas para SELIC v1.2.0
=======
Archivo de pruebas para selic.py
>>>>>>> d8918307b9a99716543fe47c061b23c5a9771bf3
Ejecuta con: python -m unittest test_selic.py
"""

import unittest
from unittest.mock import patch
import os
import tempfile

# Importar funciones del script principal
from selic import (
    validate_date,
    validate_dni,
    validate_length_params,
    estimate_wordlist_size,
    parse_multi_values,
    load_dictionary,
    generate_combination_variants,
    COLOR_MAGENTA,
    color_text
)


class TestSocialWordlist(unittest.TestCase):
    """Pruebas unitarias para selic.py"""

    def test_validate_date_valid(self):
        """Prueba fechas válidas"""
        self.assertTrue(validate_date("08/04/1990"))
        self.assertTrue(validate_date("08-04-1990"))
        self.assertTrue(validate_date("1990"))
        self.assertTrue(validate_date("31/12/2020"))

    def test_validate_date_invalid(self):
        """Prueba fechas inválidas"""
        self.assertFalse(validate_date("99/99/9999"))
        self.assertFalse(validate_date("31/02/2020"))  # Febrero no tiene 31
        self.assertFalse(validate_date("abc"))
        self.assertFalse(validate_date(""))

    def test_validate_dni_valid(self):
        """Prueba DNI válidos"""
        self.assertTrue(validate_dni("12345678"))
        self.assertTrue(validate_dni("123456789012"))

    def test_validate_dni_invalid(self):
        """Prueba DNI inválidos"""
        self.assertFalse(validate_dni("123"))  # Muy corto
        self.assertFalse(validate_dni("1234567890123"))  # Muy largo
        self.assertFalse(validate_dni("abc123"))

    def test_validate_length_params_valid(self):
        """Prueba parámetros de longitud válidos"""
        errors = validate_length_params(4, 32, 1000)
        self.assertEqual(errors, [])

    def test_validate_length_params_invalid(self):
        """Prueba parámetros de longitud inválidos"""
        errors = validate_length_params(0, 32, 1000)
        self.assertIn("Longitud mínima debe ser al menos 1", errors)

        errors = validate_length_params(10, 5, 1000)
        self.assertIn("Longitud máxima debe ser mayor o igual a la mínima", errors)

        errors = validate_length_params(4, 150, 1000)
        self.assertIn("Longitud máxima no puede exceder 100 caracteres", errors)

    def test_parse_multi_values(self):
        """Prueba parsing de múltiples valores"""
        result = parse_multi_values("07/04/2004, 2005, 04/04/2007")
        expected = ["07/04/2004", "2005", "04/04/2007"]
        self.assertEqual(result, expected)

        result = parse_multi_values("single value")
        self.assertEqual(result, ["single", "value"])  # Separa por espacios

        result = parse_multi_values("single,value")
        self.assertEqual(result, ["single", "value"])  # Separa por comas

        result = parse_multi_values("")
        self.assertIsNone(result)

    def test_estimate_wordlist_size(self):
        """Prueba estimación de tamaño"""
        config = {
            "lower": True,
            "upper": True,
            "digits": True,
            "specials": False,
            "leet": True,
            "patterns": None,
            "min_length": 4,
            "max_length": 32,
            "complexity": 2
        }
        social_tokens = ["juan", "1990", "rojo"]
        size = estimate_wordlist_size(config, social_tokens)
        self.assertIsInstance(size, int)
        self.assertGreater(size, 0)

    def test_load_dictionary(self):
        """Prueba carga de diccionario"""
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("password\n123456\nadmin\n")
            temp_file = f.name

        try:
            words = load_dictionary(temp_file)
            self.assertIn("password", words)
            self.assertIn("123456", words)
            self.assertIn("admin", words)
        finally:
            os.unlink(temp_file)

    def test_generate_combination_variants(self):
        """Prueba generación de variantes"""
        tokens = ["juan", "1990"]
        options = {
            "lower": True,
            "upper": False,
            "digits": False,
            "specials": False,
            "leet": False,
            "complexity": 1
        }
        variants = list(generate_combination_variants(tokens, options, count_limit=10))
        self.assertIsInstance(variants, list)
        self.assertGreater(len(variants), 0)
        # Verificar que incluye combinaciones
        self.assertIn("juan", variants)
        self.assertIn("1990", variants)

    def test_color_text(self):
        """Prueba función de color"""
        result = color_text("test", COLOR_MAGENTA)
        self.assertIn("test", result)
        self.assertIn("\033[38;5;201m", result)  # Código de color magenta

    @patch('builtins.input')
    def test_interactive_mode_mock(self, mock_input):
        """Prueba modo interactivo con mock (ejemplo básico)"""
        # Esto es un ejemplo; necesitarías mockear todas las entradas
        mock_input.side_effect = ["Juan", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "n", "4", "32", "", "s", "n", "n", "s", "2"]
        # Nota: Para probar completamente, necesitarías importar y llamar prompt_interactive
        # Por simplicidad, solo verificamos que las funciones existen
        self.assertTrue(callable(validate_date))


if __name__ == "__main__":
    unittest.main()