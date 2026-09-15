#!/usr/bin/env python3
"""Extrae vida.py del ultimo turno assistant de un log de conversacion (SPEC.md S2.4).

Standalone a proposito: no importa nada de `chat/`, ni siquiera para reusar un
parser. El objetivo es que esta herramienta de auditoria quede independiente
del codigo que genera el log (chat/log.py) para que un bug compartido no
contamine los dos lados de la evidencia.

Uso:
    python3 scripts/extract_code.py <log> --out vida.py
    python3 scripts/extract_code.py <log> --check vida.py
"""

from __future__ import annotations

import argparse
import sys

HEADING_PREFIX = "## "
HEADING_SEPARATOR = " — "
ASSISTANT_KIND = "assistant"
REASONING_HEADING = "### reasoning"
PYTHON_FENCE_OPEN = "```python"
FENCE_CLOSE = "```"


class ExtractError(Exception):
    """Log malformado o respuesta ambigua (SPEC.md S2.4)."""


def _turn_kind(line: str) -> str | None:
    """Devuelve el "kind" (user/assistant/error) de un encabezado de turno.

    Los encabezados tienen la forma ``## <kind> — <timestamp>`` (chat/log.py,
    funcion ``_append_block``). Exige el separador " — " para no confundir un
    encabezado real con un titulo cualquiera que una respuesta pudiera tener
    y que empiece con "## ".
    """
    if not line.startswith(HEADING_PREFIX):
        return None
    rest = line[len(HEADING_PREFIX):]
    kind, sep, _ = rest.partition(HEADING_SEPARATOR)
    if not sep:
        return None
    return kind.strip()


def _last_assistant_block(lines: list[str]) -> list[str]:
    """Aisla las lineas del ULTIMO turno ``## assistant`` del log.

    Un turno termina donde empieza el proximo encabezado de turno (o al final
    del archivo).
    """
    heading_indices = [i for i, line in enumerate(lines) if _turn_kind(line) is not None]
    assistant_indices = [i for i in heading_indices if _turn_kind(lines[i]) == ASSISTANT_KIND]
    if not assistant_indices:
        raise ExtractError("el log no tiene ningun turno '## assistant'")

    start = assistant_indices[-1]
    later = [i for i in heading_indices if i > start]
    end = later[0] if later else len(lines)
    return lines[start + 1 : end]


def _strip_reasoning(block_lines: list[str]) -> list[str]:
    """Devuelve solo las lineas de la RESPUESTA de un turno assistant.

    Si el bloque abre con la subseccion ``### reasoning`` (chat/log.py:
    ``### reasoning`` seguido de un fence ```text``` con el razonamiento, y
    recien despues la respuesta), la saltea entera -- incluido el fence de
    texto -- para que un fence ```python que aparezca DENTRO del texto de
    razonamiento (caso adversarial) nunca se confunda con codigo real.
    """
    idx = 0
    n = len(block_lines)

    while idx < n and block_lines[idx].strip() == "":
        idx += 1

    if idx < n and block_lines[idx].strip() == REASONING_HEADING:
        idx += 1
        while idx < n and block_lines[idx].strip() == "":
            idx += 1
        if idx >= n or not block_lines[idx].startswith(FENCE_CLOSE):
            raise ExtractError("la subseccion '### reasoning' no tiene el fence esperado")
        idx += 1
        while idx < n and block_lines[idx].strip() != FENCE_CLOSE:
            idx += 1
        if idx >= n:
            raise ExtractError("el fence de '### reasoning' nunca se cierra")
        idx += 1

    return block_lines[idx:]


def _python_fences(response_lines: list[str]) -> list[str]:
    """Todos los fences ```python de la respuesta, con su contenido crudo."""
    fences: list[str] = []
    idx = 0
    n = len(response_lines)
    while idx < n:
        if response_lines[idx].rstrip() == PYTHON_FENCE_OPEN:
            idx += 1
            content_lines = []
            closed = False
            while idx < n:
                if response_lines[idx].rstrip() == FENCE_CLOSE:
                    closed = True
                    break
                content_lines.append(response_lines[idx])
                idx += 1
            if not closed:
                raise ExtractError("un fence ```python nunca se cierra en el log")
            fences.append("\n".join(content_lines))
        idx += 1
    return fences


def extract(log_text: str) -> str:
    """Extrae el codigo del ultimo turno assistant de ``log_text`` (SPEC.md S2.4).

    Devuelve el contenido del unico fence ```python de la RESPUESTA (nunca de
    ``### reasoning``), con un '\\n' final garantizado. Falla (``ExtractError``)
    si esa respuesta tiene 0 o mas de 1 fence ```python, o si el log no tiene
    ningun turno assistant.
    """
    lines = log_text.splitlines()
    block = _last_assistant_block(lines)
    response = _strip_reasoning(block)
    fences = _python_fences(response)

    if len(fences) != 1:
        raise ExtractError(
            "la respuesta del ultimo turno assistant tiene "
            f"{len(fences)} fences ```python; se esperaba exactamente 1"
        )

    code = fences[0]
    if not code.endswith("\n"):
        code += "\n"
    return code


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extrae vida.py del ultimo turno assistant de un log de conversacion."
    )
    parser.add_argument("log", help="ruta al log de conversacion (logs/*.md)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", metavar="ARCHIVO", help="escribe el codigo extraido aca")
    group.add_argument(
        "--check",
        metavar="ARCHIVO",
        help="compara byte a byte el codigo extraido contra este archivo",
    )
    args = parser.parse_args(argv)

    try:
        log_text = _read(args.log)
    except OSError as exc:
        print(f"error: no se pudo leer el log '{args.log}': {exc}", file=sys.stderr)
        return 1

    try:
        code = extract(log_text)
    except ExtractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.out is not None:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(code)
        print(f"escrito: {args.out}")
        return 0

    target = args.check
    try:
        current = _read(target).encode("utf-8")
    except OSError as exc:
        print(f"error: no se pudo leer '{target}': {exc}", file=sys.stderr)
        return 1

    extracted = code.encode("utf-8")
    if extracted == current:
        print(f"coincide: el log y '{target}' son byte a byte identicos")
        return 0

    print(f"no coincide: '{target}' difiere del codigo extraido del log", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
