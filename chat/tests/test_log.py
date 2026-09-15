"""Tests de chat/log.py.

Ademas de los tests normales de ``ConversationLog``, este archivo incluye un
test de **contrato**: un parser de logs escrito desde cero contra el texto de
SPEC.md S2, que no importa nada de ``chat.log`` (ni sus regexes ni sus
constantes de formato). La idea es que ambos lados no compartan el mismo bug:
si ``ConversationLog`` se desvia del contrato documentado, el parser
independiente lo tiene que detectar.
"""

import json
import re
import tempfile
import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from chat.log import ConversationLog
from chat.slots import get_slot


# ---------------------------------------------------------------------------
# Parser independiente (SPEC.md S2), escrito sin mirar chat/log.py.
# ---------------------------------------------------------------------------


@dataclass
class ParsedBlock:
    kind: str  # "user" | "assistant" | "error"
    timestamp: str
    body: str


class LogContractError(AssertionError):
    """El log no cumple el contrato de SPEC.md S2."""


_HEADING_RE = re.compile(r"^## (user|assistant|error) — (.+)$")
_HEADER_FIELD_RE = re.compile(r"^- ([^:]+): (.+)$")
_FENCE_RE = re.compile(r"```([a-zA-Z0-9]*)\n(.*?)\n```", re.DOTALL)


def parse_log_contract(raw: str) -> tuple[dict, list[ParsedBlock]]:
    """Parsea un log completo: (encabezado, lista de bloques).

    Encabezado: todo lo que precede al primer ``## user|assistant|error``.
    Se leen sus lineas ``- Campo: valor``.

    Bloques: cada seccion que arranca en un heading ``## <tipo> — <ts>`` y
    corre hasta el proximo heading del mismo nivel (o el fin del archivo).
    """
    lines = raw.splitlines()
    heading_indexes = [
        i for i, line in enumerate(lines) if _HEADING_RE.match(line)
    ]

    if not heading_indexes:
        raise LogContractError("el log no tiene ningun bloque ## user/assistant/error")

    header_lines = lines[: heading_indexes[0]]
    header = {}
    for line in header_lines:
        match = _HEADER_FIELD_RE.match(line)
        if match:
            header[match.group(1).strip()] = match.group(2).strip()

    blocks = []
    for pos, start in enumerate(heading_indexes):
        end = (
            heading_indexes[pos + 1]
            if pos + 1 < len(heading_indexes)
            else len(lines)
        )
        heading_match = _HEADING_RE.match(lines[start])
        kind = heading_match.group(1)
        timestamp = heading_match.group(2).strip()
        body = "\n".join(lines[start + 1 : end]).strip("\n")
        blocks.append(ParsedBlock(kind=kind, timestamp=timestamp, body=body))

    return header, blocks


def assert_contract(raw: str) -> tuple[dict, list[ParsedBlock]]:
    """Corre todas las verificaciones de contrato de SPEC.md S2 y S2.3."""
    header, blocks = parse_log_contract(raw)

    required_header_fields = {"Modelo", "Effort", "Inicio"}
    missing = required_header_fields - header.keys()
    if missing:
        raise LogContractError(f"faltan campos de encabezado: {missing}")

    if not blocks:
        raise LogContractError("no hay bloques en el log")

    timestamps = []
    for block in blocks:
        if block.kind not in {"user", "assistant", "error"}:
            raise LogContractError(f"tipo de bloque desconocido: {block.kind!r}")
        timestamps.append(block.timestamp)

        fences = _FENCE_RE.findall(block.body)
        json_fences = [lang for lang, _ in fences if lang == "json"]

        if block.kind == "assistant":
            if len(json_fences) != 1:
                raise LogContractError(
                    "todo bloque assistant tiene que tener exactamente un "
                    f"fence json de usage (SPEC.md S2.3); encontrados: "
                    f"{len(json_fences)}"
                )
            # El fence json tiene que parsear como JSON (el usage crudo).
            usage_raw = next(body for lang, body in fences if lang == "json")
            json.loads(usage_raw)
        else:
            if json_fences:
                raise LogContractError(
                    f"un bloque {block.kind} no puede tener fence json "
                    "(SPEC.md S2.3, invariante)"
                )

    # Encabezado + bloques: timestamps monotonos crecientes (SPEC.md S2.3).
    all_timestamps = [header["Inicio"]] + timestamps
    parsed_ts = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in all_timestamps]
    for earlier, later in zip(parsed_ts, parsed_ts[1:]):
        if later < earlier:
            raise LogContractError(
                f"timestamps no monotonos crecientes: {earlier} luego {later}"
            )

    return header, blocks


# ---------------------------------------------------------------------------
# Tests normales de ConversationLog
# ---------------------------------------------------------------------------


class ConversationLogTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.logs_dir = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def test_start_crea_archivo_con_encabezado_y_es_idempotente(self):
        slot = get_slot(1)
        log = ConversationLog(slot=slot, logs_dir=self.logs_dir)
        ts = datetime(2026, 9, 12, 10, 0, 0)

        log.start(ts)
        first_path = log.path
        self.assertTrue(Path(first_path).exists())

        log.start(ts + timedelta(seconds=5))
        self.assertEqual(log.path, first_path, "start() no deberia recrear el archivo")

    def test_nombre_de_archivo_sigue_el_patron_de_spec(self):
        slot = get_slot(2)
        log = ConversationLog(slot=slot, logs_dir=self.logs_dir)
        log.start(datetime(2026, 1, 2, 3, 4, 5))

        self.assertEqual(
            Path(log.path).name,
            "20260102-030405-anthropic-claude-haiku-4.5.md",
        )

    def test_error_antes_del_primer_turno_se_registra(self):
        slot = get_slot(1)
        log = ConversationLog(slot=slot, logs_dir=self.logs_dir)
        ts = datetime(2026, 9, 12, 10, 0, 0)

        log.start(ts)
        log.append_error(status=500, body="server error", timestamp=ts)

        raw = Path(log.path).read_text(encoding="utf-8")
        self.assertIn("## error — 2026-09-12 10:00:00", raw)
        self.assertIn("```text", raw)
        self.assertNotIn("```json", raw)

    def test_append_falla_si_start_no_fue_llamado(self):
        slot = get_slot(1)
        log = ConversationLog(slot=slot, logs_dir=self.logs_dir)
        with self.assertRaises(RuntimeError):
            log.append_user_turn("hola", datetime(2026, 9, 12, 10, 0, 0))

    def test_append_falla_con_timestamp_no_creciente(self):
        slot = get_slot(1)
        log = ConversationLog(slot=slot, logs_dir=self.logs_dir)
        ts = datetime(2026, 9, 12, 10, 0, 0)
        log.start(ts)
        log.append_user_turn("hola", ts)

        with self.assertRaises(ValueError):
            log.append_user_turn("de nuevo", ts - timedelta(seconds=1))

    def test_effort_explicito_vs_default_vs_no_soportado(self):
        ts = datetime(2026, 9, 12, 10, 0, 0)

        log_explicito = ConversationLog(
            slot=get_slot(1), requested_effort="high", logs_dir=self.logs_dir
        )
        log_explicito.start(ts)
        raw = Path(log_explicito.path).read_text(encoding="utf-8")
        self.assertIn("- Effort: high", raw)

        log_default = ConversationLog(slot=get_slot(1), logs_dir=self.logs_dir)
        log_default.start(ts + timedelta(seconds=1))
        raw = Path(log_default.path).read_text(encoding="utf-8")
        self.assertIn("- Effort: default del modelo (medium)", raw)

        log_sin_effort = ConversationLog(slot=get_slot(2), logs_dir=self.logs_dir)
        log_sin_effort.start(ts + timedelta(seconds=2))
        raw = Path(log_sin_effort.path).read_text(encoding="utf-8")
        self.assertIn("- Effort: no aplica", raw)

    def test_slot_2_content_lista_de_partes_se_representa_legible(self):
        slot = get_slot(2)
        log = ConversationLog(slot=slot, logs_dir=self.logs_dir)
        ts = datetime(2026, 9, 12, 10, 0, 0)
        log.start(ts)

        content = [
            {"type": "text", "text": "ESTATICO", "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": "DELTA"},
        ]
        log.append_user_turn(content, ts)

        raw = Path(log.path).read_text(encoding="utf-8")
        self.assertIn("ESTATICO", raw)
        self.assertIn("DELTA", raw)
        self.assertIn("cache_control", raw)

    def test_usage_se_escribe_crudo_sin_redondear_ni_renombrar(self):
        slot = get_slot(1)
        log = ConversationLog(slot=slot, logs_dir=self.logs_dir)
        ts = datetime(2026, 9, 12, 10, 0, 0)
        log.start(ts)
        log.append_user_turn("hola", ts)

        usage = {"prompt_tokens": 123, "completion_tokens": 45, "raro_field": 0.001}
        log.append_assistant_turn(
            text="respuesta", usage=usage, timestamp=ts + timedelta(seconds=1)
        )

        raw = Path(log.path).read_text(encoding="utf-8")
        fence_match = re.search(r"```json\n(.*?)\n```", raw, re.DOTALL)
        self.assertIsNotNone(fence_match)
        self.assertEqual(json.loads(fence_match.group(1)), usage)


# ---------------------------------------------------------------------------
# Test de contrato: parser independiente contra un log generado con
# ConversationLog, cubriendo turnos normales, reasoning y error.
# ---------------------------------------------------------------------------


class LogContractTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.logs_dir = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def _build_full_conversation_log(self) -> str:
        slot = get_slot(1)
        log = ConversationLog(
            slot=slot, requested_effort="high", logs_dir=self.logs_dir
        )
        t0 = datetime(2026, 9, 12, 10, 0, 0)

        # Primer intento de envio: falla antes de tener ningun turno.
        log.start(t0)
        log.append_error(status=500, body="internal error", timestamp=t0)

        # Segundo intento (mismo prompt): turno exitoso con reasoning.
        t1 = t0 + timedelta(seconds=30)
        log.append_user_turn("cual es la capital de Francia?", t1)
        t2 = t1 + timedelta(seconds=5)
        log.append_assistant_turn(
            text="Paris.",
            usage={"prompt_tokens": 10, "completion_tokens": 2, "reasoning_tokens": 7},
            reasoning="El usuario pregunta por una capital conocida.",
            timestamp=t2,
        )

        # Segundo turno, sin reasoning.
        t3 = t2 + timedelta(seconds=10)
        log.append_user_turn("y la de Italia?", t3)
        t4 = t3 + timedelta(seconds=3)
        log.append_assistant_turn(
            text="Roma.",
            usage={"prompt_tokens": 15, "completion_tokens": 2},
            timestamp=t4,
        )

        return Path(log.path).read_text(encoding="utf-8")

    def test_log_completo_cumple_el_contrato_de_spec(self):
        raw = self._build_full_conversation_log()
        header, blocks = assert_contract(raw)

        self.assertEqual(header["Effort"], "high")
        self.assertEqual([b.kind for b in blocks], ["error", "user", "assistant", "user", "assistant"])

    def test_contrato_detecta_assistant_sin_fence_json(self):
        raw = (
            "# Log de conversacion\n\n"
            "- Modelo: `openai/gpt-5.6-luna`\n"
            "- Effort: high\n"
            "- Inicio: 2026-09-12 10:00:00\n\n"
            "## user — 2026-09-12 10:00:00\n\nhola\n\n"
            "## assistant — 2026-09-12 10:00:01\n\nrespuesta sin usage\n"
        )
        with self.assertRaises(LogContractError):
            assert_contract(raw)

    def test_contrato_detecta_fence_json_fuera_de_lugar(self):
        raw = (
            "# Log de conversacion\n\n"
            "- Modelo: `openai/gpt-5.6-luna`\n"
            "- Effort: high\n"
            "- Inicio: 2026-09-12 10:00:00\n\n"
            "## error — 2026-09-12 10:00:00\n\n```json\n{\"status\": 500}\n```\n"
        )
        with self.assertRaises(LogContractError):
            assert_contract(raw)

    def test_contrato_detecta_timestamps_no_crecientes(self):
        raw = (
            "# Log de conversacion\n\n"
            "- Modelo: `openai/gpt-5.6-luna`\n"
            "- Effort: high\n"
            "- Inicio: 2026-09-12 10:00:05\n\n"
            "## user — 2026-09-12 10:00:00\n\nhola\n"
        )
        with self.assertRaises(LogContractError):
            assert_contract(raw)


if __name__ == "__main__":
    unittest.main()
