"""Tests de chat/openrouter.py. Sin red: urlopen se mockea."""

import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from chat.openrouter import (
    OpenRouterError,
    build_file_message,
    build_request_body,
    send_request,
)
from chat.slots import SlotError, get_slot


class BuildFileMessageTests(unittest.TestCase):
    def test_slot_2_content_es_lista_de_dos_partes_con_cache_control_solo_en_la_primera(self):
        slot2 = get_slot(2)
        message = build_file_message("ESTATICO", "DELTA", slot2)

        self.assertEqual(message["role"], "user")
        content = message["content"]
        self.assertIsInstance(content, list)
        self.assertEqual(len(content), 2)

        self.assertEqual(
            content[0],
            {
                "type": "text",
                "text": "ESTATICO",
                "cache_control": {"type": "ephemeral"},
            },
        )
        self.assertEqual(content[1], {"type": "text", "text": "DELTA"})
        self.assertNotIn("cache_control", content[1])

    def test_slot_2_sin_delta_tiene_un_solo_bloque_con_cache_control(self):
        slot2 = get_slot(2)
        message = build_file_message("ESTATICO", None, slot2)

        content = message["content"]
        self.assertEqual(len(content), 1)
        self.assertEqual(
            content[0],
            {
                "type": "text",
                "text": "ESTATICO",
                "cache_control": {"type": "ephemeral"},
            },
        )

    def test_otro_slot_content_es_string_pegado_sin_separador(self):
        slot1 = get_slot(1)
        message = build_file_message("ESTATICO", "DELTA", slot1)

        self.assertEqual(message["role"], "user")
        self.assertEqual(message["content"], "ESTATICODELTA")

    def test_otro_slot_sin_delta_content_es_solo_el_estatico(self):
        slot1 = get_slot(1)
        message = build_file_message("ESTATICO", None, slot1)

        self.assertEqual(message["content"], "ESTATICO")


class BuildRequestBodyTests(unittest.TestCase):
    def test_reasoning_ausente_sin_effort(self):
        slot1 = get_slot(1)
        body = build_request_body(slot1, [{"role": "user", "content": "hola"}])

        self.assertNotIn("reasoning", body)
        self.assertEqual(body["model"], "openai/gpt-5.6-luna")
        self.assertEqual(body["messages"], [{"role": "user", "content": "hola"}])

    def test_reasoning_presente_con_effort_valido(self):
        slot1 = get_slot(1)
        body = build_request_body(
            slot1, [{"role": "user", "content": "hola"}], effort="high"
        )

        self.assertEqual(body["reasoning"], {"effort": "high"})

    def test_effort_invalido_para_el_slot_falla(self):
        slot4 = get_slot(4)
        with self.assertRaises(SlotError):
            build_request_body(
                slot4, [{"role": "user", "content": "hola"}], effort="medium"
            )

    def test_provider_ausente_si_el_slot_no_fija_proveedor(self):
        slot1 = get_slot(1)
        body = build_request_body(slot1, [{"role": "user", "content": "hola"}])
        self.assertNotIn("provider", body)

    def test_provider_presente_si_el_slot_fija_proveedor(self):
        slot2 = get_slot(2)
        body = build_request_body(slot2, [{"role": "user", "content": "hola"}])
        self.assertEqual(
            body["provider"], {"order": ["anthropic"], "allow_fallbacks": False}
        )

    def test_response_format_armado_con_schema_activo(self):
        slot3 = get_slot(3)
        schema = {
            "name": "mi_schema",
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
        }
        body = build_request_body(
            slot3, [{"role": "user", "content": "hola"}], schema=schema
        )

        self.assertEqual(
            body["response_format"],
            {
                "type": "json_schema",
                "json_schema": {
                    "name": "mi_schema",
                    "strict": True,
                    "schema": schema,
                },
            },
        )

    def test_response_format_ausente_sin_schema(self):
        slot3 = get_slot(3)
        body = build_request_body(slot3, [{"role": "user", "content": "hola"}])
        self.assertNotIn("response_format", body)

    def test_soporta_historial_de_turnos_previos(self):
        slot1 = get_slot(1)
        historial = [
            {"role": "user", "content": "primero"},
            {"role": "assistant", "content": "respuesta"},
            {"role": "user", "content": "segundo"},
        ]
        body = build_request_body(slot1, historial)
        self.assertEqual(body["messages"], historial)


class SendRequestTests(unittest.TestCase):
    def test_caso_exitoso_devuelve_dict_parseado(self):
        expected = {
            "id": "abc",
            "choices": [{"message": {"content": "hola"}}],
            "usage": {},
        }
        fake_response = MagicMock()
        fake_response.read.return_value = json.dumps(expected).encode("utf-8")
        fake_response.__enter__.return_value = fake_response
        fake_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
            result = send_request({"model": "x"}, "fake-key")

        self.assertEqual(result, expected)
        _, kwargs = mock_urlopen.call_args
        self.assertEqual(kwargs["timeout"], 600)

    def test_status_de_error_levanta_openrouter_error_con_status_y_body(self):
        http_error = HTTPError(
            url="https://openrouter.ai/api/v1/chat/completions",
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=None,
        )
        http_error.read = MagicMock(return_value=b'{"error": "rate limited"}')

        with patch("urllib.request.urlopen", side_effect=http_error):
            with self.assertRaises(OpenRouterError) as ctx:
                send_request({"model": "x"}, "fake-key")

        self.assertEqual(ctx.exception.status, 429)
        self.assertEqual(ctx.exception.body, '{"error": "rate limited"}')

    def test_falla_de_red_levanta_openrouter_error_con_status_none(self):
        with patch(
            "urllib.request.urlopen", side_effect=URLError("timed out")
        ):
            with self.assertRaises(OpenRouterError) as ctx:
                send_request({"model": "x"}, "fake-key")

        self.assertIsNone(ctx.exception.status)
        self.assertIn("timed out", ctx.exception.body)

    def test_respuesta_no_json_levanta_openrouter_error(self):
        fake_response = MagicMock()
        fake_response.read.return_value = b"no soy json"
        fake_response.__enter__.return_value = fake_response
        fake_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=fake_response):
            with self.assertRaises(OpenRouterError) as ctx:
                send_request({"model": "x"}, "fake-key")

        self.assertIsNone(ctx.exception.status)

    def test_200_sin_choices_levanta_openrouter_error_con_body_crudo(self):
        raw_body = json.dumps({"error": {"message": "algo raro"}})
        fake_response = MagicMock()
        fake_response.read.return_value = raw_body.encode("utf-8")
        fake_response.__enter__.return_value = fake_response
        fake_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=fake_response):
            with self.assertRaises(OpenRouterError) as ctx:
                send_request({"model": "x"}, "fake-key")

        self.assertIsNone(ctx.exception.status)
        self.assertEqual(ctx.exception.body, raw_body)

    def test_200_con_choices_vacio_levanta_openrouter_error_con_body_crudo(self):
        raw_body = json.dumps({"choices": []})
        fake_response = MagicMock()
        fake_response.read.return_value = raw_body.encode("utf-8")
        fake_response.__enter__.return_value = fake_response
        fake_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=fake_response):
            with self.assertRaises(OpenRouterError) as ctx:
                send_request({"model": "x"}, "fake-key")

        self.assertIsNone(ctx.exception.status)
        self.assertEqual(ctx.exception.body, raw_body)


if __name__ == "__main__":
    unittest.main()
