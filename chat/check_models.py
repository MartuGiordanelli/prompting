"""`--check-models`: compara la tabla de slots contra `GET /models` en vivo.

SPEC.md S1.2: "python3 -m chat --check-models compara esta tabla contra
/models en vivo y avisa diferencias (id caido del catalogo, efforts que
cambiaron)". No falla duro: imprime avisos y sigue.

No reusa `chat/openrouter.py` a proposito: ese modulo arma y manda el POST de
`/chat/completions` (body, `reasoning`, `provider`, etc.), que no aplica aca.
Lo unico que se comparte en espiritu es "usar urllib con la Authorization
header y mapear errores a una excepcion propia", asi que este modulo repite
ese patron minimo en vez de forzar una abstraccion comun para un solo GET.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from chat.slots import SLOTS, Slot

MODELS_URL = "https://openrouter.ai/api/v1/models"
TIMEOUT_SECONDS = 30


class ModelsCheckError(Exception):
    """Fallo el GET a `/models` o la respuesta no se pudo interpretar."""


@dataclass(frozen=True)
class SlotCheckResult:
    """Resultado de comparar un slot de la tabla contra el catalogo vivo.

    Attributes:
        slot_number: numero de slot (1 a 4).
        model: id del modelo segun `chat/slots.py`.
        in_catalog: si el id todavia aparece en `/models`.
        table_efforts: efforts que dice `chat/slots.py` para este slot.
        catalog_efforts: efforts que reporta el catalogo para este modelo, o
            ``None`` si el modelo no esta en el catalogo.
        efforts_match: si `table_efforts` y `catalog_efforts` coinciden
            (mismo conjunto). ``None`` si no aplica (modelo no esta en el
            catalogo).
    """

    slot_number: int
    model: str
    in_catalog: bool
    table_efforts: tuple[str, ...]
    catalog_efforts: tuple[str, ...] | None
    efforts_match: bool | None


def fetch_catalog(api_key: str) -> dict:
    """Hace el GET a `/models` y devuelve el JSON parseado.

    Raises:
        ModelsCheckError: si la conexion falla, la API devuelve un status de
            error, o la respuesta no parsea como JSON.
    """
    request = urllib.request.Request(
        MODELS_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise ModelsCheckError(
            f"OpenRouter devolvio status {exc.code} en GET /models: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ModelsCheckError(
            f"fallo la conexion a OpenRouter: {exc.reason}"
        ) from exc

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ModelsCheckError(
            "la respuesta de GET /models no parseo como JSON"
        ) from exc


def _index_by_id(catalog: dict) -> dict[str, dict]:
    """Mapea id -> entrada de modelo a partir de `catalog["data"]`."""
    return {entry["id"]: entry for entry in catalog.get("data", []) if "id" in entry}


def _catalog_efforts(entry: dict) -> tuple[str, ...]:
    """Extrae `reasoning.supported_efforts` de una entrada del catalogo."""
    reasoning = entry.get("reasoning") or {}
    efforts = reasoning.get("supported_efforts") or []
    return tuple(efforts)


def compare_slot(slot: Slot, catalog_index: dict[str, dict]) -> SlotCheckResult:
    """Compara un slot de la tabla contra el catalogo indexado por id."""
    entry = catalog_index.get(slot.model)
    if entry is None:
        return SlotCheckResult(
            slot_number=slot.number,
            model=slot.model,
            in_catalog=False,
            table_efforts=slot.supported_efforts,
            catalog_efforts=None,
            efforts_match=None,
        )

    catalog_efforts = _catalog_efforts(entry)
    efforts_match = set(catalog_efforts) == set(slot.supported_efforts)
    return SlotCheckResult(
        slot_number=slot.number,
        model=slot.model,
        in_catalog=True,
        table_efforts=slot.supported_efforts,
        catalog_efforts=catalog_efforts,
        efforts_match=efforts_match,
    )


def check_models(api_key: str) -> list[SlotCheckResult]:
    """Trae el catalogo vivo y compara los 4 slots contra el.

    Raises:
        ModelsCheckError: si falla el GET a `/models` (ver `fetch_catalog`).
    """
    catalog = fetch_catalog(api_key)
    catalog_index = _index_by_id(catalog)
    return [compare_slot(slot, catalog_index) for slot in SLOTS]


def format_report(results: list[SlotCheckResult]) -> str:
    """Arma el reporte legible para stdout a partir de los resultados."""
    lines = ["--check-models: tabla de chat/slots.py vs GET /models", ""]
    any_warning = False

    for result in results:
        lines.append(f"slot {result.slot_number} ({result.model}):")
        if not result.in_catalog:
            any_warning = True
            lines.append(
                "  [!] el id ya no esta en el catalogo de OpenRouter (cayo)"
            )
            continue

        lines.append("  [ok] el id sigue en el catalogo")
        if result.efforts_match:
            lines.append("  [ok] efforts coinciden con la tabla")
        else:
            any_warning = True
            tabla = ", ".join(result.table_efforts) or "(ninguno)"
            catalogo = ", ".join(result.catalog_efforts or ()) or "(ninguno)"
            lines.append(
                "  [!] efforts distintos: "
                f"tabla=[{tabla}] catalogo=[{catalogo}]"
            )

    lines.append("")
    lines.append(
        "hay diferencias para revisar" if any_warning else "sin diferencias"
    )
    return "\n".join(lines)
