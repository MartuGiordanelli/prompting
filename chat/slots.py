"""Tabla hardcodeada de los 4 slots (SPEC.md S1.2) y su validacion.

Un slot es un modelo mas la capacidad que ejercita (ver CONTEXT.md). La tabla
se re-verifica a mano contra ``GET /models`` de OpenRouter; este modulo no
hace red.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Slot:
    """Un slot de los cuatro que sirve la interfaz de chat.

    Attributes:
        number: numero de slot, 1 a 4.
        model: id del modelo en el catalogo de OpenRouter.
        supported_efforts: efforts que el catalogo reporta para este modelo,
            en el orden de SPEC.md. Vacia si el slot no soporta ``/effort``.
        default_effort: effort que se usa cuando no se pide ``/effort``
            explicitamente. ``None`` si el slot no soporta efforts.
        cache_control: si el bloque estatico de este slot se marca con
            ``cache_control: {"type": "ephemeral"}``.
        fixed_provider: slug de proveedor fijado (``provider: {order: [...],
            allow_fallbacks: false}``), o ``None`` si no se fija ninguno.
            El slot 4 lo deja en ``None`` hasta que el bloque C lo decida.
    """

    number: int
    model: str
    supported_efforts: tuple[str, ...] = field(default_factory=tuple)
    default_effort: str | None = None
    cache_control: bool = False
    fixed_provider: str | None = None


SLOTS: tuple[Slot, ...] = (
    Slot(
        number=1,
        model="openai/gpt-5.6-luna",
        supported_efforts=("max", "xhigh", "high", "medium", "low", "none"),
        default_effort="medium",
        cache_control=False,
        fixed_provider=None,
    ),
    Slot(
        number=2,
        model="anthropic/claude-haiku-4.5",
        supported_efforts=(),
        default_effort=None,
        cache_control=True,
        fixed_provider="anthropic",
    ),
    Slot(
        number=3,
        model="google/gemini-3.7-flash",
        supported_efforts=("high", "medium", "low"),
        default_effort="medium",
        cache_control=False,
        fixed_provider=None,
    ),
    Slot(
        number=4,
        model="deepseek/deepseek-v4-flash-0731",
        supported_efforts=("max", "high", "low"),
        default_effort="high",
        cache_control=False,
        fixed_provider=None,  # TBD: lo fija el bloque C.
    ),
)


class SlotError(ValueError):
    """Error de slot o de effort invalido para un slot."""


def get_slot(number: int) -> Slot:
    """Devuelve el slot con ese numero.

    Raises:
        SlotError: si ``number`` no es 1, 2, 3 o 4.
    """
    for slot in SLOTS:
        if slot.number == number:
            return slot
    valid = ", ".join(str(slot.number) for slot in SLOTS)
    raise SlotError(f"no existe el slot {number!r}; los validos son: {valid}")


def validate_effort(number: int, effort: str) -> None:
    """Valida que ``effort`` este soportado por el slot ``number``.

    Un slot sin efforts soportados (como el slot 2) rechaza cualquier
    ``/effort`` que se le pida.

    Raises:
        SlotError: si el slot no existe, o si no soporta ese effort.
    """
    slot = get_slot(number)
    if not slot.supported_efforts:
        raise SlotError(
            f"el slot {number} ({slot.model}) no soporta /effort"
        )
    if effort not in slot.supported_efforts:
        supported = ", ".join(slot.supported_efforts)
        raise SlotError(
            f"effort {effort!r} invalido para el slot {number} "
            f"({slot.model}); soportados: {supported}"
        )
