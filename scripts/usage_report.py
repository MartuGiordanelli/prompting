#!/usr/bin/env python3
"""Genera las tablas de usage del informe desde todos los logs versionados.

El indice ``logs/README.md`` solo clasifica los archivos; los numeros salen
exclusivamente de los bloques de usage ``json`` de cada log. Un envio sin
respuesta se conserva en el reporte como "sin usage". No se le asigna costo
cero, porque el log no permite saber si el proveedor lo facturo.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


DEFAULT_LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
USAGE_FENCE = re.compile(r"(?m)^```json\n(.*?)\n```[ \t]*$", re.DOTALL)
TURN_HEADING = re.compile(r"(?m)^## (user|assistant|error) — [^\n]+$")
MODEL_FIELD = re.compile(r"(?m)^- Modelo: `([^`]+)`$")
PROVIDER_FIELD = re.compile(r"(?m)^- Proveedor fijado: `([^`]+)`$")
INDEX_FILE = re.compile(r"^`([^`]+\.md)`$")


class ReportError(Exception):
    """Falta evidencia o un log no cumple el contrato de SPEC.md §2."""


@dataclass(frozen=True)
class IndexEntry:
    filename: str
    category: str
    attempt: str = ""
    slot: str = ""
    result: str = ""


@dataclass(frozen=True)
class UsageTurn:
    filename: str
    number: int
    model: str
    fixed_provider: str | None
    user_text: str
    usage: dict


@dataclass(frozen=True)
class LogRecord:
    entry: IndexEntry
    user_count: int
    error_count: int
    turns: tuple[UsageTurn, ...]


def read_index(logs_dir: Path) -> dict[str, IndexEntry]:
    path = logs_dir / "README.md"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ReportError(f"no se pudo leer el indice {path}: {exc}") from exc

    entries: dict[str, IndexEntry] = {}
    category = ""
    for line in lines:
        if line.startswith("## Ejercicio 1"):
            category = "ej1"
        elif line.startswith("## Ejercicio 2"):
            category = "conway"
        elif line.startswith("## Validacion"):
            category = "validacion"
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        match = INDEX_FILE.fullmatch(cells[0]) if cells else None
        if match is None:
            continue
        filename = match.group(1)
        if filename in entries:
            raise ReportError(f"el indice repite {filename}")
        if category == "ej1" and len(cells) >= 2:
            entries[filename] = IndexEntry(filename, category, slot=cells[1])
        elif category == "conway" and len(cells) >= 5:
            entries[filename] = IndexEntry(
                filename, category, attempt=cells[1], result=cells[4]
            )
        elif category == "validacion":
            entries[filename] = IndexEntry(filename, category)
        else:
            raise ReportError(f"fila de indice sin categoria valida: {filename}")
    return entries


def read_log(path: Path, entry: IndexEntry) -> LogRecord:
    raw = path.read_text(encoding="utf-8")
    model_match = MODEL_FIELD.search(raw)
    if model_match is None:
        raise ReportError(f"{path.name}: falta el modelo en el encabezado")
    provider_match = PROVIDER_FIELD.search(raw)
    model = model_match.group(1)
    fixed_provider = provider_match.group(1) if provider_match else None

    headings = list(TURN_HEADING.finditer(raw))
    turns: list[UsageTurn] = []
    user_count = 0
    error_count = 0
    last_user = ""
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(raw)
        body = raw[heading.end() : end].strip("\n")
        kind = heading.group(1)
        if kind == "user":
            user_count += 1
            last_user = body
        elif kind == "error":
            error_count += 1
        else:
            fences = USAGE_FENCE.findall(body)
            if len(fences) != 1:
                raise ReportError(
                    f"{path.name}: turno assistant con {len(fences)} bloques de usage"
                )
            try:
                usage = json.loads(fences[0], parse_float=Decimal)
            except json.JSONDecodeError as exc:
                raise ReportError(f"{path.name}: usage invalido: {exc}") from exc
            if not isinstance(usage, dict):
                raise ReportError(f"{path.name}: el usage no es un objeto JSON")
            turns.append(
                UsageTurn(path.name, len(turns) + 1, model, fixed_provider, last_user, usage)
            )
    if len(turns) != user_count:
        raise ReportError(
            f"{path.name}: {user_count} turnos user y {len(turns)} assistant"
        )
    return LogRecord(entry, user_count, error_count, tuple(turns))


def load_records(logs_dir: Path) -> list[LogRecord]:
    entries = read_index(logs_dir)
    files = {path.name: path for path in logs_dir.glob("*.md") if path.name != "README.md"}
    unindexed = sorted(files.keys() - entries.keys())
    missing = sorted(entries.keys() - files.keys())
    if unindexed or missing:
        raise ReportError(f"indice incompleto: sin indice={unindexed}; sin archivo={missing}")
    return [read_log(files[name], entries[name]) for name in sorted(files)]


def _field(usage: dict, *keys: str) -> Decimal | None:
    value = usage
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    return Decimal(str(value))


METRICS = {
    "input": ("prompt_tokens",),
    "output": ("completion_tokens",),
    "reasoning": ("completion_tokens_details", "reasoning_tokens"),
    "cached": ("prompt_tokens_details", "cached_tokens"),
    "cost": ("cost",),
}


def metric(turns: list[UsageTurn], name: str) -> Decimal | None:
    if not turns:
        return None
    values = [_field(turn.usage, *METRICS[name]) for turn in turns]
    if any(value is None for value in values):
        return None
    return sum(values, Decimal(0))


def money(value: Decimal | None) -> str:
    if value is None:
        return "n/d"
    return f"{value:.12f}".rstrip("0").rstrip(".") or "0"


def count(value: Decimal | None) -> str:
    return "n/d" if value is None else str(int(value))


def _row(record: LogRecord) -> str:
    cells = [record.entry.attempt, f"`{record.entry.filename}`", str(record.user_count)]
    for name in ("input", "output", "reasoning", "cached"):
        cells.append(count(metric(list(record.turns), name)))
    cells.extend((money(metric(list(record.turns), "cost")), record.entry.result))
    return "| " + " | ".join(cells) + " |"


def _total_row(label: str, records: list[LogRecord]) -> str:
    turns = [turn for record in records for turn in record.turns]
    values = [label, str(len(records)), str(sum(record.user_count for record in records))]
    for name in ("input", "output", "reasoning", "cached"):
        values.append(count(metric(turns, name)))
    values.append(money(metric(turns, "cost")))
    return "| " + " | ".join(values) + " |"


def _cache_saving(turn: UsageTurn, earlier: list[UsageTurn]) -> tuple[Decimal | None, str]:
    direct = _field(turn.usage, "cache_discount")
    if direct is not None:
        return direct, "informado por la API"

    current_prompt = _field(turn.usage, "prompt_tokens")
    current_cost = _field(turn.usage, "cost_details", "upstream_inference_prompt_cost")
    if current_prompt is None or current_cost is None:
        return None, "sin costo de entrada desglosado"

    for base in reversed(earlier):
        if base.model != turn.model or base.fixed_provider != turn.fixed_provider:
            continue
        if turn.fixed_provider is None and base.filename != turn.filename:
            continue
        if _field(base.usage, "prompt_tokens_details", "cached_tokens") != 0:
            continue
        base_write = _field(base.usage, "prompt_tokens_details", "cache_write_tokens")
        if base_write is not None and base_write > 0:
            # Un turno con cache_write_tokens > 0 pago la tarifa de escritura
            # de cache (mas cara que la de entrada base), no la tarifa base:
            # usarlo como referencia "sin cache" infla el ahorro derivado.
            continue
        base_prompt = _field(base.usage, "prompt_tokens")
        base_cost = _field(base.usage, "cost_details", "upstream_inference_prompt_cost")
        if base_prompt is None or base_prompt <= 0 or base_cost is None:
            continue
        expected = current_prompt * base_cost / base_prompt
        saving = expected - current_cost
        if saving >= 0:
            return saving, f"estimado con entrada sin cache de `{base.filename}`"
    return None, "sin referencia comparable sin cache"


def render(records: list[LogRecord]) -> str:
    lines = ["# Reporte de usage generado desde logs/", ""]
    conway = [record for record in records if record.entry.category == "conway"]
    demos = [record for record in records if record.entry.category == "ej1"]
    validation = [record for record in records if record.entry.category == "validacion"]

    lines.extend((
        "## Ejercicio 2 — intentos", "",
        "| Intento | Log | Prompts registrados | Tokens in | Tokens out | Razonamiento | Cacheados | Costo USD | Resultado |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ))
    lines.extend(_row(record) for record in conway)
    lines.extend(("", "## Totales registrados", "",
        "| Alcance | Logs | Prompts registrados | Tokens in | Tokens out | Razonamiento | Cacheados | Costo USD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"))
    for label, group in (("Ejercicio 1", demos), ("Conway", conway),
                         ("Validacion", validation), ("Todos los logs", records)):
        lines.append(_total_row(label, group))
    no_usage = [record.entry.filename for record in records if not record.turns]
    lines.extend(("", f"Logs sin usage: **{len(no_usage)}**. Su facturacion real "
                  "no se puede inferir del log; contrastar el total registrado con "
                  "el dashboard de OpenRouter.", ""))

    lines.extend(("## Ahorro por cache", "",
        "| Log | Turno | Modelo | Cacheados | Ahorro USD | Metodo |",
        "|---|---:|---|---:|---:|---|"))
    earlier: list[UsageTurn] = []
    savings: list[Decimal] = []
    cached_turns = 0
    for record in records:
        for turn in record.turns:
            cached = _field(turn.usage, "prompt_tokens_details", "cached_tokens")
            if cached is not None and cached > 0:
                cached_turns += 1
                saving, method = _cache_saving(turn, earlier)
                if saving is not None:
                    savings.append(saving)
                lines.append(
                    f"| `{turn.filename}` | {turn.number} | `{turn.model}` | "
                    f"{count(cached)} | {money(saving)} | {method} |"
                )
            earlier.append(turn)
    lines.extend(("", f"Ahorro conocido o estimado: **${money(sum(savings, Decimal(0)))}** "
                  f"en **{len(savings)}/{cached_turns}** turnos con cache. "
                  "`n/d` no se suma como cero.",
                  "Estimacion: costo de entrada esperado sin cache = tokens de entrada "
                  "del turno × costo por token de un turno anterior sin cache "
                  "del mismo modelo y proveedor; ahorro = esperado − costo de entrada "
                  "registrado. Sin proveedor fijado se usa solo un turno previo "
                  "de la misma conversacion.", ""))

    lines.extend(("## Ejercicio 1 — slot 2 vs slot 4", "",
        "| Slot | Log | Tokens in | Cacheados | Tokens out | Costo USD |",
        "|---:|---|---:|---:|---:|---:|"))
    comparison = [record for record in demos if record.entry.slot in {"2", "4"}]
    for record in comparison:
        turns = list(record.turns)
        lines.append(
            f"| {record.entry.slot} | `{record.entry.filename}` | "
            f"{count(metric(turns, 'input'))} | {count(metric(turns, 'cached'))} | "
            f"{count(metric(turns, 'output'))} | {money(metric(turns, 'cost'))} |"
        )
    cache_marker = "[cache_control: ephemeral]\n"
    def _strip_marker(text: str) -> str:
        return text[len(cache_marker):] if text.startswith(cache_marker) else text

    slot2 = [_strip_marker(turn.user_text) for record in comparison
             if record.entry.slot == "2" for turn in record.turns]
    slot4 = [(record.entry.filename, _strip_marker(turn.user_text))
             for record in comparison if record.entry.slot == "4"
             for turn in record.turns]
    # Cada log del slot 4 se juzga contra el slot 2 por separado: un log puede
    # haber recibido el mismo contexto (catalogo + pregunta, byte a byte) y
    # otro solo la pregunta, y ambos pueden convivir en el indice.
    equivalent = sorted({filename for filename, text in slot4 if text in slot2})
    non_equivalent = sorted({
        filename for filename, text in slot4
        if text not in slot2 and any(text in context for context in slot2)
    })
    if non_equivalent:
        lines.extend(("", "Misma pregunta, distinto contexto de entrada: el slot 2 "
                      "recibio el catalogo y el slot 4 solo la pregunta en "
                      + ", ".join(f"`{name}`" for name in non_equivalent) + ". "
                      "Estos costos no miden una tarea equivalente."))
    if equivalent:
        lines.extend(("", "Mismo contexto de entrada (catalogo + pregunta, byte a byte "
                      "identico al del slot 2) en "
                      + ", ".join(f"`{name}`" for name in equivalent) + ": "
                      "esta fila si compara una tarea equivalente (mission.md:47)."))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS_DIR)
    args = parser.parse_args(argv)
    try:
        records = load_records(args.logs_dir)
        print(render(records), end="")
    except (OSError, ReportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
