"""Tests de chat/env.py. Sin red."""

import os
import tempfile
import unittest
from pathlib import Path

from chat.env import EnvError, get_openrouter_api_key, parse_env_file

KEY = "OPENROUTER_API_KEY"


class ParseEnvFileTests(unittest.TestCase):
    def test_ignora_lineas_vacias_y_comentarios(self):
        contenido = """
# esto es un comentario
OPENROUTER_API_KEY=abc123

# otro comentario
OTRA_VAR=xyz
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(contenido, encoding="utf-8")
            values = parse_env_file(path)
        self.assertEqual(values, {"OPENROUTER_API_KEY": "abc123", "OTRA_VAR": "xyz"})

    def test_archivo_inexistente_da_dict_vacio(self):
        path = Path(tempfile.mkdtemp()) / "no-existe" / ".env"
        self.assertEqual(parse_env_file(path), {})


class GetOpenrouterApiKeyTests(unittest.TestCase):
    def setUp(self):
        self._original = os.environ.pop(KEY, None)

    def tearDown(self):
        if self._original is not None:
            os.environ[KEY] = self._original
        else:
            os.environ.pop(KEY, None)

    def test_env_real_gana_sobre_archivo(self):
        os.environ[KEY] = "desde-entorno"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(f"{KEY}=desde-archivo\n", encoding="utf-8")
            self.assertEqual(get_openrouter_api_key(path), "desde-entorno")

    def test_usa_archivo_si_no_hay_env_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(f"{KEY}=desde-archivo\n", encoding="utf-8")
            self.assertEqual(get_openrouter_api_key(path), "desde-archivo")

    def test_falla_claro_si_falta_en_ambos_lados(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("OTRA_VAR=algo\n", encoding="utf-8")
            with self.assertRaises(EnvError):
                get_openrouter_api_key(path)

    def test_falla_claro_si_no_hay_archivo_ni_env(self):
        path = Path(tempfile.mkdtemp()) / ".env"
        with self.assertRaises(EnvError):
            get_openrouter_api_key(path)


if __name__ == "__main__":
    unittest.main()
