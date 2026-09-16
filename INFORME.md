# Informe — Mision: el prompt minimo

> **Estado: esqueleto.** Cada seccion marcada `PENDIENTE` se completa cuando
> exista la evidencia que la respalda. Las tablas de la Parte 2 se generan con
> `python3 scripts/usage_report.py`, no se transcriben a mano.

Grupo: PENDIENTE
Repo: https://github.com/MartuGiordanelli/prompting

---

# Parte 1 — Trabajo previo

## 1.1 Que es un router de modelos

PENDIENTE — una linea: que hace y que problema resuelve.
Fuente: https://openrouter.ai/openrouter/auto

## 1.2 Mapa de modelos

El modelo mas avanzado de cada proveedor, al PENDIENTE (fecha de consulta).

| Proveedor | Modelo | USD / 1M in | USD / 1M out | Ventana | Posicion en benchmarks |
|---|---|---|---|---|---|
| OpenAI | | | | | |
| Anthropic | | | | | |
| Grok | | | | | |
| Gemini | | | | | |
| DeepSeek | | | | | |
| Qwen | | | | | |
| Kimi | | | | | |

Vista comparativa usada: PENDIENTE (`openrouter.ai/compare/...`)

## 1.3 Parametros soportados

Comparacion de `supported_parameters` entre fichas de proveedores distintos.
Fuente programatica: `GET https://openrouter.ai/api/v1/models`.

| Parametro | | | |
|---|---|---|---|
| `reasoning.effort` | | | |
| `reasoning.max_tokens` | | | |
| Salidas estructuradas | | | |
| `cache_control` explicito | | | |
| `temperature` / sampling | | | |

Hallazgo: PENDIENTE — que acepta uno que el otro no, y que implica para el diseno
de la interfaz.

## 1.4 Sustituciones de catalogo

Los ids de la mision estan verificados al 2026-09-02. Verificacion propia:
PENDIENTE (fecha).

| Slot | Id de la mision | Sigue vigente | Reemplazo | Por que |
|---|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | | | |
| 2 | `anthropic/claude-haiku-4.5` | | | |
| 3 | `google/gemini-3.7-flash` | | | |
| 4 | `deepseek/deepseek-v4-flash-0731` | | | |

---

# Parte 2 — La cuenta final (ejercicio 3)

## 2.1 Intentos

Un intento = una conversacion (ver `CONTEXT.md`). Estan **todos**, incluidos los
quemados. El detalle archivo-por-archivo esta en `logs/README.md`.

Total de intentos: PENDIENTE
Intento ganador: PENDIENTE
Prompts en el ganador: PENDIENTE

## 2.2 Tokens por intento

> Generado por `scripts/usage_report.py`.

| Intento | Log | Prompts | Tokens in | Tokens out | Razonamiento | Cacheados | Costo USD | Resultado |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| **Total** | | | | | | | | |

## 2.3 Tokens de pensamiento

PENDIENTE — cuantos y que se facturo por ellos.

Nota a verificar: algunos modelos razonan sin devolver los tokens de
razonamiento en la respuesta. Si nos pasa, va documentado aca como hallazgo, con
el log que lo muestra.

## 2.4 Caching y ahorro

PENDIENTE — `cached_tokens` por intento y el **ahorro derivado** en USD, no solo
el conteo.

La serie inicial mantuvo `prompts/conway/estatico.md` sin cambios, pero los
intentos 02 y 03 devolvieron `cached_tokens = 0`. Se abrio la serie 02 con un
prefijo mas completo en `prompts/conway/serie-02/estatico.md`, sin alterar el
prefijo anterior. El envio 04 se interrumpio antes de registrar una respuesta.
El primer intento completado de la serie 02 (05) devolvio `cached_tokens = 0`;
el segundo (06) devolvio `cached_tokens = 1024` y su codigo paso los 9 tests.
El ahorro en USD queda pendiente del reporte de usage.

## 2.5 Contraste contra el dashboard

| Fuente | Gasto USD |
|---|---|
| Suma de los logs (`usage_report.py`) | PENDIENTE |
| Dashboard de actividad de OpenRouter | PENDIENTE |
| Diferencia | PENDIENTE |

Explicacion de la diferencia, si la hay: PENDIENTE.

## 2.6 Conclusion

PENDIENTE — tres lineas. Tiene que nombrar una **decision concreta**: un modelo,
un parametro o un cambio puntual de prompt. "Mejorar el prompt" no cuenta.
