"""Tests de `scripts/extract_code.py` (docs/plan/bloque-a.md tarea 8).

Los logs de fixture estan escritos a mano, imitando el formato EXACTO que
emite `chat/log.py` (encabezados "## <kind> — <timestamp>", subseccion
"### reasoning" con fence ```text``` antes de la respuesta, fence ```json```
de usage al cierre de cada turno assistant). No se invoca `chat/log.py` para
generarlos: la independencia es deliberada (SPEC.md S2.4, CLAUDE.md).
"""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest

from scripts.extract_code import ExtractError, extract, main

LOG_HEADER = (
    "# Log de conversacion\n"
    "\n"
    "- Modelo: `openai/gpt-5.6-luna`\n"
    "- Effort: high\n"
    "- Inicio: 2024-01-01 00:00:00\n"
)

USAGE_FENCE = '```json\n{\n  "prompt_tokens": 10,\n  "completion_tokens": 5\n}\n```'


def _user_turn(ts: str, message: str) -> str:
    return f"\n## user — {ts}\n\n{message}\n"


def _assistant_turn(ts: str, response: str, *, reasoning: str | None = None) -> str:
    pieces = []
    if reasoning is not None:
        pieces.append(f"### reasoning\n\n```text\n{reasoning}\n```")
    pieces.append(response)
    pieces.append(USAGE_FENCE)
    body = "\n\n".join(pieces)
    return f"\n## assistant — {ts}\n\n{body}\n"


SIMPLE_RESPONSE = "Aca esta el codigo:\n\n```python\nprint('hola')\n```\n"

LOG_ONE_TURN_ONE_FENCE = (
    LOG_HEADER
    + _user_turn("2024-01-01 00:00:00", "Escribime vida.py")
    + _assistant_turn("2024-01-01 00:00:01", SIMPLE_RESPONSE)
)

ADVERSARIAL_REASONING = (
    "Voy a mostrar un ejemplo de fence dentro del razonamiento:\n"
    "```python\n"
    "print('esto NO es el codigo real')\n"
    "```\n"
    "Ahora si, la respuesta."
)

LOG_ADVERSARIAL_REASONING = (
    LOG_HEADER
    + _user_turn("2024-01-01 00:00:00", "Escribime vida.py")
    + _assistant_turn(
        "2024-01-01 00:00:01",
        SIMPLE_RESPONSE,
        reasoning=ADVERSARIAL_REASONING,
    )
)

TWO_FENCES_RESPONSE = (
    "Van dos versiones:\n\n"
    "```python\nprint('version 1')\n```\n\n"
    "```python\nprint('version 2')\n```\n"
)

LOG_TWO_FENCES = LOG_HEADER + _user_turn(
    "2024-01-01 00:00:00", "Escribime vida.py"
) + _assistant_turn("2024-01-01 00:00:01", TWO_FENCES_RESPONSE)

NO_FENCE_RESPONSE = "Ahi tenes la explicacion, sin bloque de codigo."

LOG_NO_FENCE = LOG_HEADER + _user_turn(
    "2024-01-01 00:00:00", "Escribime vida.py"
) + _assistant_turn("2024-01-01 00:00:01", NO_FENCE_RESPONSE)

FIRST_RESPONSE = "Primer intento:\n\n```python\nprint('primero')\n```\n"
SECOND_RESPONSE = "Segundo intento, mejor:\n\n```python\nprint('segundo')\n```\n"

LOG_MULTIPLE_ASSISTANT_TURNS = (
    LOG_HEADER
    + _user_turn("2024-01-01 00:00:00", "Escribime vida.py")
    + _assistant_turn("2024-01-01 00:00:01", FIRST_RESPONSE)
    + _user_turn("2024-01-01 00:00:02", "Pulilo un poco")
    + _assistant_turn("2024-01-01 00:00:03", SECOND_RESPONSE)
)

LOG_NO_ASSISTANT_TURN = LOG_HEADER + _user_turn(
    "2024-01-01 00:00:00", "Escribime vida.py"
)


@contextlib.contextmanager
def _tempfile_with(content: str, suffix: str = ".md"):
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        yield path
    finally:
        os.remove(path)


class ExtractFunctionTests(unittest.TestCase):
    def test_extracts_single_fence_with_trailing_newline(self):
        code = extract(LOG_ONE_TURN_ONE_FENCE)
        self.assertEqual(code, "print('hola')\n")

    def test_ignores_fence_inside_reasoning_subsection(self):
        code = extract(LOG_ADVERSARIAL_REASONING)
        self.assertEqual(code, "print('hola')\n")

    def test_two_fences_in_response_raises(self):
        with self.assertRaises(ExtractError):
            extract(LOG_TWO_FENCES)

    def test_no_fence_in_response_raises(self):
        with self.assertRaises(ExtractError):
            extract(LOG_NO_FENCE)

    def test_takes_last_assistant_turn(self):
        code = extract(LOG_MULTIPLE_ASSISTANT_TURNS)
        self.assertEqual(code, "print('segundo')\n")

    def test_no_assistant_turn_raises(self):
        with self.assertRaises(ExtractError):
            extract(LOG_NO_ASSISTANT_TURN)

    def test_fence_content_with_trailing_blank_line_is_not_doubled(self):
        # El fence trae una linea en blanco antes de cerrar: el contenido ya
        # termina en "\n" (join de ["print('hola')", ""]) y no se le agrega
        # un segundo salto de linea (extract() solo agrega uno si falta).
        response = "```python\nprint('hola')\n\n```\n"
        log = LOG_HEADER + _user_turn("2024-01-01 00:00:00", "hola") + _assistant_turn(
            "2024-01-01 00:00:01", response
        )
        code = extract(log)
        self.assertEqual(code, "print('hola')\n")


class CliTests(unittest.TestCase):
    def test_out_writes_extracted_content(self):
        with _tempfile_with(LOG_ONE_TURN_ONE_FENCE) as log_path:
            with tempfile.TemporaryDirectory() as tmpdir:
                out_path = os.path.join(tmpdir, "vida.py")
                exit_code = main([log_path, "--out", out_path])
                self.assertEqual(exit_code, 0)
                with open(out_path, "r", encoding="utf-8") as handle:
                    self.assertEqual(handle.read(), "print('hola')\n")

    def test_check_matches_returns_zero(self):
        with _tempfile_with(LOG_ONE_TURN_ONE_FENCE) as log_path:
            with _tempfile_with("print('hola')\n", suffix=".py") as vida_path:
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    exit_code = main([log_path, "--check", vida_path])
                self.assertEqual(exit_code, 0)

    def test_check_mismatch_returns_nonzero(self):
        with _tempfile_with(LOG_ONE_TURN_ONE_FENCE) as log_path:
            with _tempfile_with("print('chau')\n", suffix=".py") as vida_path:
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    exit_code = main([log_path, "--check", vida_path])
                self.assertNotEqual(exit_code, 0)
                self.assertIn("no coincide", stderr.getvalue())

    def test_ambiguous_response_fails_and_writes_nothing(self):
        with _tempfile_with(LOG_TWO_FENCES) as log_path:
            with tempfile.TemporaryDirectory() as tmpdir:
                out_path = os.path.join(tmpdir, "vida.py")
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    exit_code = main([log_path, "--out", out_path])
                self.assertNotEqual(exit_code, 0)
                self.assertFalse(os.path.exists(out_path))


if __name__ == "__main__":
    unittest.main()
