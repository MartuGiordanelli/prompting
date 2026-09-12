"""Formateo de la linea de usage en pantalla (SPEC.md S1.3).

El usage crudo que devuelve OpenRouter se muestra en una sola linea, sin
acumular nada entre turnos ni conversaciones (eso es trabajo del bloque D,
``scripts/usage_report.py``). Regla dura (hallazgo criterio 3.2, ver
CONTEXT.md "Cache hit" y SPEC.md S1.3): un campo AUSENTE (clave inexistente o
``None``) se muestra como ``n/d``; un campo presente en ``0`` se muestra como
``0``. No son lo mismo y no se convierte uno en el otro.

Los nombres de campo de OpenRouter no estan 100% estandarizados entre
modelos: la forma "tipica" es ``prompt_tokens`` / ``completion_tokens`` /
``cost``, con detalles anidados en ``prompt_tokens_details.cached_tokens`` y
``completion_tokens_details.reasoning_tokens``. Se accede todo con ``.get()``
en cascada para no explotar si un modelo no manda alguna de estas claves.
"""

from __future__ import annotations

_MISSING = "n/d"

# Nombres de campo asumidos para el usage crudo de OpenRouter. Si un modelo
# usa otra forma, alcanza con ajustar estas constantes / este helper.
_FIELD_PROMPT_TOKENS = "prompt_tokens"
_FIELD_COMPLETION_TOKENS = "completion_tokens"
_FIELD_COST = "cost"
_FIELD_PROMPT_DETAILS = "prompt_tokens_details"
_FIELD_CACHED_TOKENS = "cached_tokens"
_FIELD_COMPLETION_DETAILS = "completion_tokens_details"
_FIELD_REASONING_TOKENS = "reasoning_tokens"


def _get_field(usage: dict, key: str):
    """Devuelve ``usage[key]`` o ``None`` si la clave no esta o vale ``None``.

    ``None`` explicito y clave ausente se tratan igual: los dos significan
    "la API no informo este campo".
    """
    return usage.get(key)


def _get_nested_field(usage: dict, outer_key: str, inner_key: str):
    """Como ``_get_field``, pero para un campo anidado un nivel adentro.

    Usa ``.get()`` en cada nivel: si ``outer_key`` no esta, no es un dict, o
    ``inner_key`` no esta adentro, el resultado es ``None`` (ausente), nunca
    una excepcion.
    """
    outer = usage.get(outer_key)
    if not isinstance(outer, dict):
        return None
    return outer.get(inner_key)


def _format_value(value) -> str:
    """``n/d`` si el valor es ``None`` (ausente); el valor tal cual si no."""
    return _MISSING if value is None else str(value)


def _format_cost(value) -> str:
    """Como ``_format_value``, pero con el prefijo ``$`` (incluso en ``n/d``)."""
    return f"${_format_value(value)}"


def _compute_cache_discount(usage: dict, cost):
    """Descuento por cache, derivado de forma simple para esta linea de pantalla.

    SPEC.md no fija una formula definitiva (eso lo completa el bloque D en
    ``usage_report.py``); aca alcanza con una aproximacion razonable: costo
    por token no cacheado * tokens cacheados, si hay suficiente informacion
    para derivarlo con confianza. Si falta ``cost``, ``prompt_tokens`` o
    ``cached_tokens``, o si no hay tokens no cacheados contra los cuales
    sacar un costo unitario, devuelve ``None`` (ausente) en vez de inventar
    un numero.
    """
    prompt_tokens = _get_field(usage, _FIELD_PROMPT_TOKENS)
    cached_tokens = _get_nested_field(
        usage, _FIELD_PROMPT_DETAILS, _FIELD_CACHED_TOKENS
    )

    if cost is None or prompt_tokens is None or cached_tokens is None:
        return None

    uncached_tokens = prompt_tokens - cached_tokens
    if uncached_tokens <= 0 or cached_tokens <= 0:
        return None

    cost_per_token = cost / uncached_tokens
    return cost_per_token * cached_tokens


def format_usage_line(usage: dict) -> str:
    """Formatea el bloque ``usage`` crudo de OpenRouter para mostrar en pantalla.

    Formato exacto (SPEC.md S1.3):
    ``in N (cached N) · out N (reasoning N) · $cost · cache_discount $X``

    Un campo ausente (clave inexistente o ``None``) se muestra ``n/d``; un
    campo presente en ``0`` se muestra ``0``. No se acumula nada entre
    turnos: esta funcion formatea un unico bloque de usage.
    """
    prompt_tokens = _get_field(usage, _FIELD_PROMPT_TOKENS)
    cached_tokens = _get_nested_field(
        usage, _FIELD_PROMPT_DETAILS, _FIELD_CACHED_TOKENS
    )
    completion_tokens = _get_field(usage, _FIELD_COMPLETION_TOKENS)
    reasoning_tokens = _get_nested_field(
        usage, _FIELD_COMPLETION_DETAILS, _FIELD_REASONING_TOKENS
    )
    cost = _get_field(usage, _FIELD_COST)

    cache_discount = _compute_cache_discount(usage, cost)

    return (
        f"in {_format_value(prompt_tokens)} (cached {_format_value(cached_tokens)}) · "
        f"out {_format_value(completion_tokens)} (reasoning {_format_value(reasoning_tokens)}) · "
        f"{_format_cost(cost)} · "
        f"cache_discount {_format_cost(cache_discount)}"
    )
