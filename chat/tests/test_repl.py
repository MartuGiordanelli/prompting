"""Tests de chat/repl.py. Sin red: send_request se mockea."""

import unittest
from unittest.mock import MagicMock, patch

from chat.openrouter import OpenRouterError
from chat.repl import ReplState, run_repl
from chat.slots import get_slot


def _scripted_input(lines):
    """input_func que devuelve `lines` en orden y despues EOFError.

    Guarda los `prompt` que le pasaron en `.prompts`: en un terminal real
    `input(prompt)` los muestra por stdout, pero en el mock no pasan por
    `print_func`, asi que los tests que necesitan verificar que SE PIDIO una
    confirmacion (no solo su respuesta) inspeccionan esta lista.
    """
    it = iter(lines)
    prompts: list[str] = []

    def _input(prompt=""):
        prompts.append(prompt)
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    _input.prompts = prompts
    return _input


def _fake_response(text="respuesta", reasoning=None):
    return {
        "choices": [{"message": {"content": text, "reasoning": reasoning}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001},
    }


def _mock_log():
    """ConversationLog mockeado con `started` como atributo real (no Mock)."""
    log = MagicMock()
    log.started = False

    def _start(timestamp):
        log.started = True

    log.start.side_effect = _start
    return log


class ModelCommandTests(unittest.TestCase):
    def test_cambiar_model_sin_turnos_no_pide_confirmacion(self):
        state = ReplState(get_slot(1))
        input_func = _scripted_input(["/model 2", "/exit"])
        run_repl(state, "fake-key", input_func=input_func, print_func=lambda _: None)
        self.assertEqual(state.slot.number, 2)
        self.assertFalse(any("Confirmar" in p for p in input_func.prompts))

    @patch("chat.repl.send_request")
    def test_cambiar_model_con_turnos_pide_confirmacion_y_respeta_no(self, mock_send):
        mock_send.return_value = _fake_response()
        state = ReplState(get_slot(1))
        input_func = _scripted_input(["hola", "/model 2", "n", "/exit"])
        run_repl(state, "fake-key", input_func=input_func, print_func=lambda _: None)
        self.assertEqual(state.slot.number, 1)
        self.assertTrue(any("Confirmar" in p for p in input_func.prompts))

    @patch("chat.repl.send_request")
    def test_cambiar_model_con_turnos_pide_confirmacion_y_respeta_si(self, mock_send):
        mock_send.return_value = _fake_response()
        state = ReplState(get_slot(1))
        run_repl(
            state,
            "fake-key",
            input_func=_scripted_input(["hola", "/model 2", "y", "/exit"]),
            print_func=lambda _: None,
        )
        self.assertEqual(state.slot.number, 2)
        self.assertEqual(state.prompt_count, 0)
        self.assertEqual(state.messages, [])


class EffortCommandTests(unittest.TestCase):
    def test_effort_invalido_para_el_slot_activo_se_rechaza(self):
        state = ReplState(get_slot(2))  # slot 2 no soporta ningun effort
        outputs = []
        run_repl(
            state,
            "fake-key",
            input_func=_scripted_input(["/effort high", "/exit"]),
            print_func=outputs.append,
        )
        self.assertIsNone(state.effort)
        self.assertTrue(any("error" in o.lower() for o in outputs))

    @patch("chat.repl.send_request")
    def test_effort_valido_que_cambia_el_valor_cierra_la_conversacion(self, mock_send):
        mock_send.return_value = _fake_response()
        state = ReplState(get_slot(1))
        run_repl(
            state,
            "fake-key",
            input_func=_scripted_input(["hola", "/effort high", "y", "/exit"]),
            print_func=lambda _: None,
        )
        self.assertEqual(state.effort, "high")
        self.assertEqual(state.prompt_count, 0)
        self.assertEqual(state.messages, [])


class BurnConfirmationTests(unittest.TestCase):
    @patch("chat.repl.send_request")
    def test_tercer_prompt_pide_confirmacion(self, mock_send):
        mock_send.return_value = _fake_response()
        state = ReplState(get_slot(1))
        input_func = _scripted_input(["uno", "dos", "tres", "y", "/exit"])
        run_repl(state, "fake-key", input_func=input_func, print_func=lambda _: None)
        self.assertEqual(mock_send.call_count, 3)
        self.assertEqual(state.prompt_count, 3)
        self.assertTrue(any("quema" in p.lower() for p in input_func.prompts))

    @patch("chat.repl.send_request")
    def test_tercer_prompt_con_no_no_manda_el_request(self, mock_send):
        mock_send.return_value = _fake_response()
        state = ReplState(get_slot(1))
        run_repl(
            state,
            "fake-key",
            input_func=_scripted_input(["uno", "dos", "tres", "n", "/exit"]),
            print_func=lambda _: None,
        )
        self.assertEqual(mock_send.call_count, 2)
        self.assertEqual(state.prompt_count, 2)


class SendMessageTests(unittest.TestCase):
    @patch("chat.repl.ConversationLog")
    @patch("chat.repl.send_request")
    def test_error_no_agrega_historial_y_llama_append_error(self, mock_send, mock_log_cls):
        mock_send.side_effect = OpenRouterError("fallo", status=500, body="boom")
        log = _mock_log()
        mock_log_cls.return_value = log

        state = ReplState(get_slot(1))
        outputs = []
        run_repl(
            state,
            "fake-key",
            input_func=_scripted_input(["hola", "/exit"]),
            print_func=outputs.append,
        )

        log.append_error.assert_called_once()
        log.append_user_turn.assert_not_called()
        log.append_assistant_turn.assert_not_called()
        self.assertEqual(state.messages, [])
        self.assertEqual(state.prompt_count, 0)

    @patch("chat.repl.ConversationLog")
    @patch("chat.repl.send_request")
    def test_turno_exitoso_agrega_user_y_assistant_al_historial_y_al_log(
        self, mock_send, mock_log_cls
    ):
        mock_send.return_value = _fake_response(text="hola de vuelta")
        log = _mock_log()
        mock_log_cls.return_value = log

        state = ReplState(get_slot(1))
        outputs = []
        run_repl(
            state,
            "fake-key",
            input_func=_scripted_input(["hola", "/exit"]),
            print_func=outputs.append,
        )

        log.append_user_turn.assert_called_once()
        log.append_assistant_turn.assert_called_once()
        self.assertEqual(len(state.messages), 2)
        self.assertEqual(state.messages[0], {"role": "user", "content": "hola"})
        self.assertEqual(
            state.messages[1], {"role": "assistant", "content": "hola de vuelta"}
        )
        self.assertEqual(state.prompt_count, 1)


if __name__ == "__main__":
    unittest.main()
