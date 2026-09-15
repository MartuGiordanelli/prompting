"""Parser minimo de .env (SPEC.md S1.4), solo stdlib.

La variable de entorno real del proceso (``os.environ``) siempre gana sobre lo
que diga el archivo ``.env``. No hay dependencias externas: esto es a
proposito, para no repetir un SDK/paquete de terceros por un parser de tres
lineas.
"""

import os
from pathlib import Path

API_KEY_VAR = "OPENROUTER_API_KEY"

# Raiz del repo: dos niveles arriba de este archivo (chat/env.py -> repo/).
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_ENV_PATH = _REPO_ROOT / ".env"


class EnvError(RuntimeError):
    """La configuracion de entorno requerida no esta disponible."""


def parse_env_file(path: Path) -> dict[str, str]:
    """Parsea un archivo ``.env`` simple en pares clave-valor.

    Ignora lineas vacias y comentarios que empiezan con ``#``. No hace
    expansion de variables ni des-quoting: es deliberadamente minimo.

    Si el archivo no existe, devuelve un dict vacio (no es un error: el
    proceso puede tener la variable seteada de otra forma).
    """
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def get_openrouter_api_key(env_path: Path | None = None) -> str:
    """Devuelve la ``OPENROUTER_API_KEY`` efectiva.

    Precedencia: ``os.environ`` real gana siempre sobre el archivo ``.env``.

    Args:
        env_path: ruta al archivo ``.env`` a usar. Por default, el ``.env``
            en la raiz del repo.

    Raises:
        EnvError: si la key no aparece ni en ``os.environ`` ni en el archivo.
    """
    if API_KEY_VAR in os.environ and os.environ[API_KEY_VAR]:
        return os.environ[API_KEY_VAR]

    path = env_path if env_path is not None else _DEFAULT_ENV_PATH
    file_values = parse_env_file(path)
    key = file_values.get(API_KEY_VAR)
    if key:
        return key

    raise EnvError(
        f"falta {API_KEY_VAR}: no esta seteada en el entorno ni en {path}"
    )
