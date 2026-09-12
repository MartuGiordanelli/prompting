"""Tests de chat/usage.py (SPEC.md S1.3, hallazgo criterio 3.2).

Regla bajo prueba: un campo AUSENTE (clave no existe, o es ``None``) se
muestra ``n/d``; un campo presente en ``0`` se muestra ``0``. No son lo
mismo.
"""

import unittest

from chat.usage import format_usage_line


class FormatUsageLineTests(unittest.TestCase):
    def test_usage_completo_formatea_todos_los_valores(self):
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "cost": 0.002,
            "prompt_tokens_details": {"cached_tokens": 40},
            "completion_tokens_details": {"reasoning_tokens": 10},
        }

        line = format_usage_line(usage)

        self.assertIn("in 100 (cached 40)", line)
        self.assertIn("out 50 (reasoning 10)", line)
        self.assertIn("$0.002", line)
        self.assertNotIn("n/d", line)
        # cache_discount se deriva: costo por token no cacheado * cacheados
        # uncached = 60, cost_per_token = 0.002 / 60, discount = * 40
        expected_discount = (0.002 / 60) * 40
        self.assertIn(f"cache_discount ${expected_discount}", line)

    def test_campo_en_cero_real_se_muestra_cero_no_n_d(self):
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "cost": 0.001,
            "prompt_tokens_details": {"cached_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 0},
        }

        line = format_usage_line(usage)

        self.assertIn("in 100 (cached 0)", line)
        self.assertIn("out 50 (reasoning 0)", line)
        # cached_tokens en 0 real: no hay descuento posible (no hay tokens
        # cacheados), pero es "0 informado", no ausencia -> la formula
        # requiere cached_tokens > 0 para tener sentido y cae a n/d.
        self.assertIn("cache_discount $n/d", line)

    def test_campo_ausente_por_clave_inexistente_se_muestra_n_d(self):
        usage = {
            "prompt_tokens": 100,
            # completion_tokens ausente
            "cost": 0.001,
        }

        line = format_usage_line(usage)

        self.assertIn("in 100", line)
        self.assertIn("out n/d (reasoning n/d)", line)
        self.assertIn("cached n/d", line)

    def test_campo_ausente_por_valor_none_se_muestra_n_d(self):
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": None,
            "cost": None,
        }

        line = format_usage_line(usage)

        self.assertIn("out n/d", line)
        self.assertIn("$n/d", line)

    def test_estructura_anidada_parcial_no_explota(self):
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "cost": 0.001,
            # sin prompt_tokens_details ni completion_tokens_details
        }

        line = format_usage_line(usage)

        self.assertIn("cached n/d", line)
        self.assertIn("reasoning n/d", line)
        self.assertIn("cache_discount $n/d", line)

    def test_estructura_anidada_con_dict_incompleto_no_explota(self):
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "cost": 0.001,
            "prompt_tokens_details": {},  # sin cached_tokens adentro
            "completion_tokens_details": {},  # sin reasoning_tokens adentro
        }

        line = format_usage_line(usage)

        self.assertIn("cached n/d", line)
        self.assertIn("reasoning n/d", line)

    def test_usage_vacio_todo_n_d_sin_excepciones(self):
        usage = {}

        line = format_usage_line(usage)

        self.assertEqual(
            line,
            "in n/d (cached n/d) · out n/d (reasoning n/d) · $n/d · cache_discount $n/d",
        )


if __name__ == "__main__":
    unittest.main()
