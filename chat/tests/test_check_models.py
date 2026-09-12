"""Tests de chat/check_models.py. Sin red: urlopen se mockea."""

import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from chat.check_models import (
    ModelsCheckError,
    check_models,
    fetch_catalog,
    format_report,
)


def _fake_response(payload: dict) -> MagicMock:
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps(payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False
    return fake_response


def _catalog_todo_coincide() -> dict:
    """Catalogo donde los 4 ids de chat/slots.py siguen vigentes y los
    efforts reportados coinciden exactamente con la tabla."""
    return {
        "data": [
            {
                "id": "openai/gpt-5.6-luna",
                "reasoning": {
                    "supported_efforts": [
                        "max",
                        "xhigh",
                        "high",
                        "medium",
                        "low",
                        "none",
                    ]
                },
            },
            {"id": "anthropic/claude-haiku-4.5"},
            {
                "id": "google/gemini-3.7-flash",
                "reasoning": {"supported_efforts": ["high", "medium", "low"]},
            },
            {
                "id": "deepseek/deepseek-v4-flash-0731",
                "reasoning": {"supported_efforts": ["max", "high", "low"]},
            },
        ]
    }


class FetchCatalogTests(unittest.TestCase):
    def test_caso_exitoso_devuelve_dict_parseado(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_fake_response({"data": []}),
        ) as mock_urlopen:
            result = fetch_catalog("fake-key")

        self.assertEqual(result, {"data": []})
        _, kwargs = mock_urlopen.call_args
        self.assertEqual(kwargs["timeout"], 30)

    def test_status_de_error_levanta_models_check_error(self):
        http_error = HTTPError(
            url="https://openrouter.ai/api/v1/models",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
        http_error.read = MagicMock(return_value=b'{"error": "bad key"}')

        with patch("urllib.request.urlopen", side_effect=http_error):
            with self.assertRaises(ModelsCheckError):
                fetch_catalog("fake-key")

    def test_falla_de_red_levanta_models_check_error(self):
        with patch("urllib.request.urlopen", side_effect=URLError("timed out")):
            with self.assertRaises(ModelsCheckError):
                fetch_catalog("fake-key")

    def test_respuesta_no_json_levanta_models_check_error(self):
        fake_response = MagicMock()
        fake_response.read.return_value = b"no soy json"
        fake_response.__enter__.return_value = fake_response
        fake_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=fake_response):
            with self.assertRaises(ModelsCheckError):
                fetch_catalog("fake-key")


class CheckModelsScenarioTests(unittest.TestCase):
    def test_todo_coincide_sin_avisos(self):
        with patch(
            "urllib.request.urlopen",
            return_value=_fake_response(_catalog_todo_coincide()),
        ):
            results = check_models("fake-key")

        self.assertEqual(len(results), 4)
        for result in results:
            self.assertTrue(result.in_catalog)
            self.assertTrue(result.efforts_match if result.efforts_match is not None else True)

        report = format_report(results)
        self.assertIn("sin diferencias", report)
        self.assertNotIn("[!]", report)

    def test_id_caido_del_catalogo_avisa_claro(self):
        catalog = _catalog_todo_coincide()
        catalog["data"] = [
            entry
            for entry in catalog["data"]
            if entry["id"] != "deepseek/deepseek-v4-flash-0731"
        ]

        with patch(
            "urllib.request.urlopen",
            return_value=_fake_response(catalog),
        ):
            results = check_models("fake-key")

        slot4 = next(r for r in results if r.slot_number == 4)
        self.assertFalse(slot4.in_catalog)
        self.assertIsNone(slot4.catalog_efforts)
        self.assertIsNone(slot4.efforts_match)

        report = format_report(results)
        self.assertIn("hay diferencias para revisar", report)
        self.assertIn("cayo", report)

    def test_efforts_de_un_slot_cambiaron_avisa_claro(self):
        catalog = _catalog_todo_coincide()
        for entry in catalog["data"]:
            if entry["id"] == "google/gemini-3.7-flash":
                entry["reasoning"] = {"supported_efforts": ["high", "medium"]}

        with patch(
            "urllib.request.urlopen",
            return_value=_fake_response(catalog),
        ):
            results = check_models("fake-key")

        slot3 = next(r for r in results if r.slot_number == 3)
        self.assertTrue(slot3.in_catalog)
        self.assertFalse(slot3.efforts_match)
        self.assertEqual(slot3.catalog_efforts, ("high", "medium"))

        report = format_report(results)
        self.assertIn("hay diferencias para revisar", report)
        self.assertIn("efforts distintos", report)


if __name__ == "__main__":
    unittest.main()
