"""Punto de entrada `python3 -m chat` (SPEC.md S1.1).

Resuelve la API key, arma el estado inicial (slot 1 por defecto, ver
`chat/repl.py`) y corre el loop del REPL. Si falta la key, sale con un
mensaje claro y sin traceback.
"""

from __future__ import annotations

import sys

from chat.check_models import ModelsCheckError, check_models, format_report
from chat.env import EnvError, get_openrouter_api_key
from chat.repl import DEFAULT_SLOT_NUMBER, ReplState, run_repl
from chat.slots import get_slot


def main() -> int:
    try:
        api_key = get_openrouter_api_key()
    except EnvError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if "--check-models" in sys.argv[1:]:
        try:
            results = check_models(api_key)
        except ModelsCheckError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(format_report(results))
        return 0

    state = ReplState(get_slot(DEFAULT_SLOT_NUMBER))
    run_repl(state, api_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
