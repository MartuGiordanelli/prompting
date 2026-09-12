"""Loop de comandos del REPL de terminal (SPEC.md S1.1, S1.3).

Estado de sesion (`ReplState`): slot activo, `effort` y `schema` de sesion,
toggle de pantalla `show_reasoning`, historial de turnos en memoria (`messages`)
y el `ConversationLog` de la conversacion actual (`None` si todavia no se mando
nada). Cambiar de slot, `/effort` o `/schema` cierra la conversacion actual y
abre una nueva (SPEC.md S1.3): pide confirmacion `[y/N]` solo si la
conversacion en curso ya tiene turnos. `/show-reasoning` es puramente de
pantalla, no toca la conversacion. `/file` es el unico comando que puede
"quemar" el intento (CONTEXT.md "Quemado"): al tercer prompt de una
conversacion (y cualquiera despues) pide la misma confirmacion, con otro
mensaje.

Sin slot elegido no hay default implicito distinto del slot 1: la interfaz
arranca en el slot 1 (`DEFAULT_SLOT_NUMBER`) para poder escribir texto libre
sin forzar un `/model` primero; cambiarlo con `/model` no pide confirmacion
porque la conversacion inicial no tiene turnos.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from chat.log import ConversationLog
from chat.openrouter import (
    OpenRouterError,
    build_file_message,
    build_request_body,
    send_request,
)
from chat.slots import Slot, SlotError, get_slot, validate_effort
from chat.usage import format_usage_line

DEFAULT_SLOT_NUMBER = 1

# CONTEXT.md "Quemado": el intento se quema al mandar el TERCER prompt. Con
# prompt_count = turnos ya completados, el proximo envio es prompt_count + 1.
BURN_PROMPT_THRESHOLD = 3

EXIT_COMMANDS = frozenset({"/exit", "/quit"})
MULTILINE_MARKER = '"""'

InputFunc = Callable[[str], str]
PrintFunc = Callable[[str], None]


class ReplState:
    """Estado mutable de la sesion del REPL.

    Una instancia vive durante toda la ejecucion del proceso; `open_conversation`
    la reinicia a una conversacion nueva sin tocar los parametros de sesion
    (esos los cambia quien llama, antes de abrir la conversacion).
    """

    def __init__(self, slot: Slot) -> None:
        self.slot = slot
        self.effort: str | None = None
        self.schema_path: str | None = None
        self.schema: dict | None = None
        self.show_reasoning = False
        self.messages: list[dict] = []
        self.log: ConversationLog | None = None
        self.prompt_count = 0

    def has_turns(self) -> bool:
        """Si la conversacion actual ya tiene al menos un turno completado."""
        return self.prompt_count > 0

    def open_conversation(self) -> None:
        """Cierra la conversacion actual (si la habia) y abre una vacia."""
        self.messages = []
        self.log = None
        self.prompt_count = 0


def run_repl(
    state: ReplState,
    api_key: str,
    *,
    input_func: InputFunc = input,
    print_func: PrintFunc = print,
) -> None:
    """Corre el loop principal del REPL hasta que el usuario sale.

    Sale con `/exit`, `/quit`, o `EOFError`/`KeyboardInterrupt` (Ctrl+D /
    Ctrl+C) — todas salidas limpias, sin traceback.
    """
    print_func(f"slot activo: {state.slot.number} ({state.slot.model})")

    while True:
        try:
            line = input_func("> ")
        except (EOFError, KeyboardInterrupt):
            print_func("")
            return

        stripped = line.strip()
        if not stripped:
            continue

        if stripped in EXIT_COMMANDS:
            return

        if stripped.startswith(MULTILINE_MARKER):
            text = _read_multiline(stripped, input_func)
            _handle_free_text(state, api_key, text, print_func, input_func)
            continue

        if stripped.startswith("/"):
            _handle_command(state, api_key, stripped, print_func, input_func)
            continue

        _handle_free_text(state, api_key, stripped, print_func, input_func)


def _read_multiline(first_line: str, input_func: InputFunc) -> str:
    """Lee lineas hasta encontrar el marcador de cierre (SPEC.md S1.1)."""
    remainder = first_line[len(MULTILINE_MARKER):]
    if remainder.endswith(MULTILINE_MARKER):
        return remainder[: -len(MULTILINE_MARKER)]

    lines = [remainder] if remainder else []
    while True:
        try:
            line = input_func("... ")
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip() == MULTILINE_MARKER:
            break
        lines.append(line)
    return "\n".join(lines)


def _handle_command(
    state: ReplState,
    api_key: str,
    line: str,
    print_func: PrintFunc,
    input_func: InputFunc,
) -> None:
    parts = line.split(maxsplit=1)
    command = parts[0]
    argument = parts[1] if len(parts) > 1 else ""

    if command == "/model":
        _cmd_model(state, argument, print_func, input_func)
    elif command == "/effort":
        _cmd_effort(state, argument, print_func, input_func)
    elif command == "/schema":
        _cmd_schema(state, argument, print_func, input_func)
    elif command == "/file":
        _cmd_file(state, api_key, argument, print_func, input_func)
    elif command == "/show-reasoning":
        state.show_reasoning = not state.show_reasoning
        print_func(f"show-reasoning: {'on' if state.show_reasoning else 'off'}")
    else:
        print_func(f"comando desconocido: {command}")


def _confirm_close(
    state: ReplState, reason: str, print_func: PrintFunc, input_func: InputFunc
) -> bool:
    """Pide `[y/N]` solo si la conversacion actual ya tiene turnos.

    Devuelve `True` si esta OK cerrar (sin turnos, o el usuario confirmo).
    """
    if not state.has_turns():
        return True
    answer = input_func(f"{reason} va a cerrar la conversacion actual. Confirmar? [y/N] ")
    return answer.strip().lower() == "y"


def _cmd_model(
    state: ReplState, argument: str, print_func: PrintFunc, input_func: InputFunc
) -> None:
    argument = argument.strip()
    if not argument:
        print_func("uso: /model <1-4>")
        return

    try:
        number = int(argument)
        new_slot = get_slot(number)
    except ValueError:
        print_func("uso: /model <1-4>")
        return
    except SlotError as exc:
        print_func(f"error: {exc}")
        return

    if new_slot.number == state.slot.number:
        print_func(f"ya estas en el slot {new_slot.number}")
        return

    if not _confirm_close(state, "/model", print_func, input_func):
        print_func("cancelado")
        return

    state.slot = new_slot
    # el effort y el schema de sesion son especificos del slot anterior;
    # cambiar de slot ya cierra la conversacion, asi que arrancan limpios.
    state.effort = None
    state.schema_path = None
    state.schema = None
    state.open_conversation()
    print_func(f"slot activo: {new_slot.number} ({new_slot.model})")


def _cmd_effort(
    state: ReplState, argument: str, print_func: PrintFunc, input_func: InputFunc
) -> None:
    argument = argument.strip()
    if not argument:
        current = state.effort if state.effort is not None else "ninguno"
        print_func(f"effort actual: {current}")
        return

    if argument == "off":
        if state.effort is None:
            print_func("no hay effort activo")
            return
        if not _confirm_close(state, "/effort off", print_func, input_func):
            print_func("cancelado")
            return
        state.effort = None
        state.open_conversation()
        print_func("effort: off")
        return

    try:
        validate_effort(state.slot.number, argument)
    except SlotError as exc:
        print_func(f"error: {exc}")
        return

    if argument == state.effort:
        print_func(f"el effort ya es {argument}")
        return

    if not _confirm_close(state, f"/effort {argument}", print_func, input_func):
        print_func("cancelado")
        return

    state.effort = argument
    state.open_conversation()
    print_func(f"effort: {argument}")


def _cmd_schema(
    state: ReplState, argument: str, print_func: PrintFunc, input_func: InputFunc
) -> None:
    argument = argument.strip()
    if not argument:
        current = state.schema_path if state.schema_path is not None else "ninguno"
        print_func(f"schema actual: {current}")
        return

    if argument == "off":
        if state.schema_path is None:
            print_func("no hay schema activo")
            return
        if not _confirm_close(state, "/schema off", print_func, input_func):
            print_func("cancelado")
            return
        state.schema_path = None
        state.schema = None
        state.open_conversation()
        print_func("schema: off")
        return

    path = Path(argument)
    if not path.exists():
        print_func(f"error: no existe el archivo {argument}")
        return

    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print_func(f"error: {argument} no parsea como JSON: {exc}")
        return

    if argument == state.schema_path:
        print_func(f"el schema ya es {argument}")
        return

    if not _confirm_close(state, f"/schema {argument}", print_func, input_func):
        print_func("cancelado")
        return

    state.schema_path = argument
    state.schema = schema
    state.open_conversation()
    print_func(f"schema: {argument}")


def _cmd_file(
    state: ReplState,
    api_key: str,
    argument: str,
    print_func: PrintFunc,
    input_func: InputFunc,
) -> None:
    args = argument.split(maxsplit=1)
    if not args:
        print_func("uso: /file <estatico> [<delta>]")
        return

    static_path = Path(args[0])
    if not static_path.exists():
        print_func(f"error: no existe {static_path}")
        return
    static_text = static_path.read_text(encoding="utf-8")

    delta_text = None
    if len(args) > 1:
        delta_path = Path(args[1])
        if not delta_path.exists():
            print_func(f"error: no existe {delta_path}")
            return
        delta_text = delta_path.read_text(encoding="utf-8")

    message = build_file_message(static_text, delta_text, state.slot)
    _send_message(state, api_key, message, print_func, input_func)


def _handle_free_text(
    state: ReplState,
    api_key: str,
    text: str,
    print_func: PrintFunc,
    input_func: InputFunc,
) -> None:
    """Un mensaje de texto libre (no `/file`) es igual un prompt (SPEC.md S1.1)."""
    message = {"role": "user", "content": text}
    _send_message(state, api_key, message, print_func, input_func)


def _send_message(
    state: ReplState,
    api_key: str,
    message: dict,
    print_func: PrintFunc,
    input_func: InputFunc,
) -> None:
    """Manda `message` como el proximo prompt de la conversacion actual.

    Pide confirmacion de quemado antes del tercer prompt (y cualquiera
    despues). Crea/arranca el log en el primer intento de envio de la
    conversacion, exitoso o no (SPEC.md S2.2).
    """
    next_prompt_number = state.prompt_count + 1
    if next_prompt_number >= BURN_PROMPT_THRESHOLD:
        answer = input_func(
            f"este es el prompt numero {next_prompt_number}: esto quema el "
            "intento. Confirmar? [y/N] "
        )
        if answer.strip().lower() != "y":
            print_func("no se mando el mensaje")
            return

    if state.log is None:
        state.log = ConversationLog(
            slot=state.slot,
            requested_effort=state.effort,
            schema_path=state.schema_path,
        )
    if not state.log.started:
        state.log.start(datetime.now())

    messages_to_send = state.messages + [message]
    try:
        body = build_request_body(
            state.slot, messages_to_send, effort=state.effort, schema=state.schema
        )
        response = send_request(body, api_key)
    except OpenRouterError as exc:
        state.log.append_error(status=exc.status, body=exc.body, timestamp=datetime.now())
        print_func(f"error: {exc}")
        return

    choice = response["choices"][0]["message"]
    text = choice.get("content", "")
    reasoning = choice.get("reasoning")
    usage = response.get("usage", {})

    user_timestamp = datetime.now()
    state.log.append_user_turn(message["content"], user_timestamp)
    assistant_timestamp = datetime.now()
    state.log.append_assistant_turn(
        text=text, usage=usage, reasoning=reasoning, timestamp=assistant_timestamp
    )

    state.messages.append(message)
    state.messages.append({"role": "assistant", "content": text})
    state.prompt_count += 1

    if reasoning:
        if state.show_reasoning:
            print_func("--- reasoning ---")
            print_func(reasoning)
            print_func("--- fin reasoning ---")
        else:
            print_func("[reasoning colapsado; /show-reasoning para verlo]")

    print_func(text)

    if state.schema is not None:
        try:
            json.loads(text)
        except (json.JSONDecodeError, TypeError):
            print_func("✗ la respuesta no parsea como JSON valido")
        else:
            print_func("✓ la respuesta parsea como JSON valido")

    print_func(format_usage_line(usage))
