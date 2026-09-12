"""Armado de requests y llamada HTTP a OpenRouter (SPEC.md S1.3).

Solo stdlib: HTTP con ``urllib.request``. Nada de SDKs (pueden ocultar campos
del usage crudo, ver SPEC.md S1.1).
"""

import json
import urllib.error
import urllib.request

from chat.slots import Slot, validate_effort

API_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_SECONDS = 600


class OpenRouterError(Exception):
    """Un request a OpenRouter fallo.

    No es un turno (SPEC.md S1.3, S2.2): quien la atrape decide como
    registrarla (bloque ``## error``), pero este modulo no logea nada.

    Attributes:
        status: codigo de status HTTP si la falla vino de una respuesta de
            error de la API, o ``None`` si fue una falla de red/timeout antes
            de recibir status (p. ej. ``URLError``, timeout).
        body: cuerpo crudo de la respuesta de error, o el texto de la
            excepcion de red si no hubo respuesta HTTP.
    """

    def __init__(self, message: str, *, status: int | None = None, body: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body


def build_file_message(static_text: str, delta_text: str | None, slot: Slot) -> dict:
    """Arma el mensaje ``user`` de ``/file <estatico> [<delta>]`` (SPEC.md S1.3).

    En el slot con ``cache_control`` (el slot 2), ``content`` es una lista de
    partes ``{"type": "text", "text": ...}``: el estatico lleva
    ``cache_control: {"type": "ephemeral"}``, el delta (si existe) no.

    En el resto de los slots, ``content`` es un string ``estatico + delta``,
    sin ningun separador agregado.
    """
    if slot.cache_control:
        parts = [
            {
                "type": "text",
                "text": static_text,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        if delta_text:
            parts.append({"type": "text", "text": delta_text})
        return {"role": "user", "content": parts}

    content = static_text if not delta_text else static_text + delta_text
    return {"role": "user", "content": content}


def build_request_body(
    slot: Slot,
    messages: list[dict],
    *,
    effort: str | None = None,
    schema: dict | None = None,
) -> dict:
    """Arma el body completo del POST a ``/chat/completions``.

    Args:
        slot: slot activo (da ``model`` y ``fixed_provider``).
        messages: historial de mensajes de la conversacion (turnos previos
            mas el mensaje nuevo), en el orden en que se mandan.
        effort: nivel de ``/effort`` de sesion, o ``None`` si no hay ninguno
            activo. Se valida contra la tabla de slots antes de incluirse; si
            es ``None`` el body no lleva ``reasoning``.
        schema: JSON Schema de ``/schema`` de sesion, o ``None`` si no hay
            ninguno activo. Si esta presente, arma ``response_format``.

    Raises:
        SlotError: si ``effort`` esta seteado pero no es valido para el slot.
    """
    body: dict = {
        "model": slot.model,
        "messages": messages,
    }

    if effort is not None:
        validate_effort(slot.number, effort)
        body["reasoning"] = {"effort": effort}

    if schema is not None:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.get("name", "response"),
                "strict": True,
                "schema": schema,
            },
        }

    if slot.fixed_provider is not None:
        body["provider"] = {
            "order": [slot.fixed_provider],
            "allow_fallbacks": False,
        }

    return body


def send_request(body: dict, api_key: str) -> dict:
    """Hace el POST a OpenRouter y devuelve la respuesta parseada.

    Timeout de ``TIMEOUT_SECONDS`` (SPEC.md S1.3).

    Raises:
        OpenRouterError: si la API devuelve un status de error, si la
            respuesta no parsea como JSON, o si falla la conexion (red o
            timeout). El llamador la atrapa y decide como registrarla (no es
            un turno, ver SPEC.md S2.2).
    """
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise OpenRouterError(
            f"OpenRouter devolvio status {exc.code}",
            status=exc.code,
            body=error_body,
        ) from exc
    except urllib.error.URLError as exc:
        raise OpenRouterError(
            f"fallo la conexion a OpenRouter: {exc.reason}",
            status=None,
            body=str(exc.reason),
        ) from exc

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise OpenRouterError(
            "la respuesta de OpenRouter no parseo como JSON",
            status=None,
            body=raw_body,
        ) from exc
