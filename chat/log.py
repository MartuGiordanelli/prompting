"""Escritura del log de una conversacion (SPEC.md S2, contrato).

El log es la evidencia de auditoria del proyecto (CONTEXT.md "Log"): se crea
en el primer intento de envio de la conversacion, no recien en el primer
turno exitoso, y la escritura es append-only — nunca se reescribe el archivo
entero (CLAUDE.md prohibicion 2: los logs no se editan nunca despues de
escritos).
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from chat.slots import Slot

LOGS_DIR = "logs"
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
DISPLAY_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def _provider_and_model(slot: Slot) -> tuple[str, str]:
    """Separa ``slot.model`` (``"<proveedor>/<modelo>"``) en sus dos partes."""
    provider, _, model_name = slot.model.partition("/")
    return provider, model_name


def _format_effort(slot: Slot, requested_effort: str | None) -> str:
    """Linea de effort del encabezado (SPEC.md S2.2).

    Explicito si se pidio; ``"default del modelo (X)"`` si se uso el default
    del slot sin pedirlo; y una nota distinta si el slot no soporta
    ``/effort`` en absoluto (slot 2).
    """
    if requested_effort is not None:
        return requested_effort
    if slot.default_effort is not None:
        return f"default del modelo ({slot.default_effort})"
    return "no aplica (el slot no soporta /effort)"


def _format_content(content: str | list[dict]) -> str:
    """Representacion textual legible del ``content`` de un mensaje.

    ``content`` es un string en la mayoria de los slots, o una lista de
    partes ``{"type": "text", "text": ..., "cache_control": {...}?}`` en el
    slot 2 (SPEC.md S1.3). No se reconstruye el JSON crudo: alcanza con una
    representacion legible para una persona.
    """
    if isinstance(content, str):
        return content

    chunks = []
    for part in content:
        text = part.get("text", "")
        if "cache_control" in part:
            chunks.append(f"[cache_control: ephemeral]\n{text}")
        else:
            chunks.append(text)
    return "\n\n".join(chunks)


class ConversationLog:
    """Escribe el log append-only de una conversacion (SPEC.md S2).

    Una instancia por conversacion (CONTEXT.md: una conversacion produce
    exactamente un log). ``start()`` crea el archivo con el encabezado en el
    primer intento de envio; cada ``append_*`` agrega un bloque al final y
    nunca reescribe lo ya escrito.
    """

    def __init__(
        self,
        *,
        slot: Slot,
        requested_effort: str | None = None,
        schema_path: str | None = None,
        logs_dir: str = LOGS_DIR,
    ) -> None:
        self._slot = slot
        self._requested_effort = requested_effort
        self._schema_path = schema_path
        self._logs_dir = logs_dir
        self.path: str | None = None
        self._last_timestamp: datetime | None = None

    @property
    def started(self) -> bool:
        """Si ``start()`` ya creo el archivo para esta conversacion."""
        return self.path is not None

    def start(self, timestamp: datetime) -> None:
        """Crea el archivo con el encabezado (SPEC.md S2.1, S2.2).

        Se llama en el primer intento de envio de la conversacion, sea
        exitoso o no (asi se puede registrar un error previo al primer
        turno). Llamadas subsiguientes son un no-op: el encabezado no se
        reescribe.
        """
        if self.started:
            return

        os.makedirs(self._logs_dir, exist_ok=True)
        provider, model_name = _provider_and_model(self._slot)
        filename = (
            f"{timestamp.strftime(FILENAME_TIMESTAMP_FORMAT)}-{provider}-{model_name}.md"
        )
        self.path = os.path.join(self._logs_dir, filename)

        lines = ["# Log de conversacion", "", f"- Modelo: `{self._slot.model}`"]
        if self._slot.fixed_provider is not None:
            lines.append(f"- Proveedor fijado: `{self._slot.fixed_provider}`")
        lines.append(
            f"- Effort: {_format_effort(self._slot, self._requested_effort)}"
        )
        if self._schema_path is not None:
            lines.append(f"- Schema: `{self._schema_path}`")
        if self._slot.cache_control:
            lines.append('- cache_control: `{"type": "ephemeral"}`')
        lines.append(f"- Inicio: {self._format_timestamp(timestamp)}")
        lines.append("")

        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

        self._last_timestamp = timestamp

    def append_user_turn(self, content: str | list[dict], timestamp: datetime) -> None:
        """Agrega el bloque ``## user`` con el mensaje tal cual se envio."""
        self._append_block(
            "user", timestamp, _format_content(content)
        )

    def append_assistant_turn(
        self,
        *,
        text: str,
        usage: dict,
        reasoning: str | None = None,
        timestamp: datetime,
    ) -> None:
        """Agrega el bloque ``## assistant`` (SPEC.md S2.2).

        Si hay ``reasoning``, va antes de la respuesta en una subseccion
        ``### reasoning`` con fence ``text``. Cierra con el ``usage`` crudo,
        sin filtrar ni reformatear, en el unico fence ``json`` del bloque.
        """
        pieces = []
        if reasoning:
            pieces.append(f"### reasoning\n\n```text\n{reasoning}\n```")
        pieces.append(text)
        pieces.append(
            "```json\n" + json.dumps(usage, indent=2, ensure_ascii=False) + "\n```"
        )
        self._append_block("assistant", timestamp, "\n\n".join(pieces))

    def append_error(
        self, *, status: int | None, body: str, timestamp: datetime
    ) -> None:
        """Agrega el bloque ``## error`` (SPEC.md S2.2). No cuenta como turno.

        El fence es siempre ``text`` (nunca ``json``, invariante SPEC.md
        S2.3): ``scripts/usage_report.py`` solo lee fences ``json`` y un
        error ahi rompe el reporte.
        """
        status_display = status if status is not None else "n/d"
        text = f"status: {status_display}\n\n{body}"
        self._append_block("error", timestamp, f"```text\n{text}\n```")

    def _append_block(self, kind: str, timestamp: datetime, body: str) -> None:
        if not self.started:
            raise RuntimeError(
                "ConversationLog.start() no fue llamado antes de escribir un bloque"
            )
        if self._last_timestamp is not None and timestamp < self._last_timestamp:
            raise ValueError(
                "los timestamps del log tienen que ser monotonos crecientes "
                "(SPEC.md S2.3)"
            )
        heading = f"## {kind} — {self._format_timestamp(timestamp)}"
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(f"\n{heading}\n\n{body}\n")
        self._last_timestamp = timestamp

    @staticmethod
    def _format_timestamp(timestamp: datetime) -> str:
        return timestamp.strftime(DISPLAY_TIMESTAMP_FORMAT)
