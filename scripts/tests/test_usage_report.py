"""Pruebas de agregacion, cobertura y ahorro del reporte de usage."""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from scripts.usage_report import (
    IndexEntry,
    LogRecord,
    ReportError,
    UsageTurn,
    _cache_saving,
    load_records,
    metric,
    read_log,
    render,
)


def usage(*, prompt=100, output=10, cached=0, cache_write=0, prompt_cost="0.01", cost="0.02"):
    return {
        "prompt_tokens": prompt,
        "completion_tokens": output,
        "cost": Decimal(cost),
        "prompt_tokens_details": {"cached_tokens": cached, "cache_write_tokens": cache_write},
        "completion_tokens_details": {"reasoning_tokens": 2},
        "cost_details": {"upstream_inference_prompt_cost": Decimal(prompt_cost)},
    }


class LogParsingTests(unittest.TestCase):
    def test_error_text_does_not_count_as_usage(self):
        raw = (
            "# Log de conversacion\n\n- Modelo: `proveedor/modelo`\n"
            "- Inicio: 2026-09-16 10:00:00\n"
            "\n## error — 2026-09-16 10:00:01\n\n"
            "```text\n{\"prompt_tokens\": 999}\n```\n"
            "\n## user — 2026-09-16 10:00:02\n\nhola\n"
            "\n## assistant — 2026-09-16 10:00:03\n\nrespuesta\n\n"
            "```json\n{\"prompt_tokens\": 10, \"cost\": 0.001}\n```\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "log.md"
            path.write_text(raw, encoding="utf-8")
            record = read_log(path, IndexEntry("log.md", "conway", attempt="01"))

        self.assertEqual(record.error_count, 1)
        self.assertEqual(record.user_count, 1)
        self.assertEqual(len(record.turns), 1)
        self.assertEqual(record.turns[0].usage["prompt_tokens"], 10)

    def test_fails_if_a_log_is_missing_from_the_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "README.md").write_text(
                "## Ejercicio 2 — intentos de Conway\n\n"
                "| Archivo | Intento | Prompts | Delta usado | Resultado | Por que se quemo |\n"
                "|---|---|---|---|---|---|\n"
                "| `known.md` | 01 | 0 | x | error | - |\n",
                encoding="utf-8",
            )
            (directory / "known.md").write_text("- Modelo: `x/y`\n", encoding="utf-8")
            (directory / "hidden.md").write_text("- Modelo: `x/y`\n", encoding="utf-8")

            with self.assertRaisesRegex(ReportError, "hidden.md"):
                load_records(directory)


class CacheSavingsTests(unittest.TestCase):
    def test_uses_reported_discount_when_present(self):
        block = usage(cached=80)
        block["cache_discount"] = Decimal("0.003")
        hit = UsageTurn("hit.md", 1, "x/y", None, "", block)

        saving, method = _cache_saving(hit, [])

        self.assertEqual(saving, Decimal("0.003"))
        self.assertEqual(method, "informado por la API")

    def test_derives_saving_from_uncached_turn_with_same_fixed_provider(self):
        base = UsageTurn("first.md", 1, "x/y", "same-provider", "", usage())
        hit = UsageTurn(
            "second.md", 1, "x/y", "same-provider", "",
            usage(prompt=110, cached=80, prompt_cost="0.004"),
        )
        saving, method = _cache_saving(hit, [base])

        self.assertEqual(saving, Decimal("0.007"))
        self.assertIn("first.md", method)

    def test_does_not_invent_saving_across_unfixed_conversations(self):
        base = UsageTurn("first.md", 1, "x/y", None, "", usage())
        hit = UsageTurn("second.md", 1, "x/y", None, "", usage(cached=80))

        saving, method = _cache_saving(hit, [base])

        self.assertIsNone(saving)
        self.assertIn("sin referencia", method)

    def test_ignores_a_reference_turn_that_paid_the_cache_write_rate(self):
        # Un turno con cache_write_tokens > 0 pago la tarifa de ESCRITURA de
        # cache (mas cara que la tarifa base de entrada, ver el par de logs
        # del slot 2 en logs/20260915-155359 y -155404). Usarlo como "tarifa
        # sin cache" infla el ahorro derivado (bug verificado en el reporte).
        base = UsageTurn(
            "write.md", 1, "x/y", "same-provider", "",
            usage(prompt=9348, cached=0, cache_write=9346, prompt_cost="0.0116845"),
        )
        hit = UsageTurn(
            "read.md", 1, "x/y", "same-provider", "",
            usage(prompt=9348, cached=9346, prompt_cost="0.0009366"),
        )

        saving, method = _cache_saving(hit, [base])

        self.assertIsNone(saving)
        self.assertIn("sin referencia", method)


class ReportTests(unittest.TestCase):
    def test_absent_reasoning_is_unknown_not_zero(self):
        block = usage()
        del block["completion_tokens_details"]
        turn = UsageTurn("log.md", 1, "x/y", None, "", block)

        self.assertIsNone(metric([turn], "reasoning"))
        self.assertEqual(metric([turn], "cached"), 0)

    def test_keeps_no_usage_and_flags_unequal_demo_context(self):
        slot2 = LogRecord(
            IndexEntry("slot2.md", "ej1", slot="2"), 1, 0,
            (UsageTurn("slot2.md", 1, "a/m", "a", "catalogo\nPregunta: precio?",
                       usage(cost="0.02")),),
        )
        slot4 = LogRecord(
            IndexEntry("slot4.md", "ej1", slot="4"), 1, 0,
            (UsageTurn("slot4.md", 1, "b/m", None, "Pregunta: precio?",
                       usage(cost="0.01")),),
        )
        failed = LogRecord(IndexEntry("failed.md", "conway", attempt="01"), 0, 1, ())

        report = render([slot2, slot4, failed])

        self.assertIn("Logs sin usage: **1**", report)
        self.assertIn("Misma pregunta, distinto contexto", report)
        self.assertIn("| Todos los logs | 3 | 2 |", report)
        self.assertIn("| 01 | `failed.md` | 0 | n/d", report)

    def test_flags_equal_demo_context_as_a_valid_comparison(self):
        catalogo_y_pregunta = "catalogo\nPregunta: precio?"
        slot2 = LogRecord(
            IndexEntry("slot2.md", "ej1", slot="2"), 1, 0,
            (UsageTurn("slot2.md", 1, "a/m", "a", catalogo_y_pregunta,
                       usage(cost="0.02")),),
        )
        slot4_equivalente = LogRecord(
            IndexEntry("slot4.md", "ej1", slot="4"), 1, 0,
            (UsageTurn("slot4.md", 1, "b/m", None, catalogo_y_pregunta,
                       usage(cost="0.01")),),
        )

        report = render([slot2, slot4_equivalente])

        self.assertIn("Mismo contexto de entrada", report)
        self.assertIn("`slot4.md`", report)
        self.assertNotIn("Misma pregunta, distinto contexto", report)


if __name__ == "__main__":
    unittest.main()
