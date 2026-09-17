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

Total de intentos: **6** (01 a 06; se incluyen los quemados y los envíos sin
respuesta).
Intento ganador: **06** (`20260916-163302-deepseek-deepseek-v4-flash-0731.md`).
Prompts en el ganador: **1**.

## 2.2 Tokens por intento

> Generado por `scripts/usage_report.py`.

| Intento | Log | Prompts | Tokens in | Tokens out | Razonamiento | Cacheados | Costo USD | Resultado |
|---|---|---|---|---|---|---|---|---|
| 01 | `20260916-153121-deepseek-deepseek-v4-flash-0731.md` | 0 | n/d | n/d | n/d | n/d | n/d | Sin respuesta; error de red antes del turno |
| 02 | `20260916-153227-deepseek-deepseek-v4-flash-0731.md` | 1 | 740 | 15839 | 15346 | 0 | 0.008493232 | Descartado en su momento por ambigüedad de extracción |
| 03 | `20260916-153635-deepseek-deepseek-v4-flash-0731.md` | 1 | 773 | 15977 | 15557 | 0 | 0.00196362 | Pasa los 9 tests; reemplazado por una serie que demuestra cache |
| 04 | `20260916-161840-deepseek-deepseek-v4-flash-0731.md` | 0 | n/d | n/d | n/d | n/d | n/d | Cliente interrumpido mientras leía la respuesta HTTP |
| 05 | `20260916-163033-deepseek-deepseek-v4-flash-0731.md` | 1 | 1243 | 2924 | 2457 | 0 | 0.0010921143 | Pasa los 9 tests; sin cache hit |
| 06 | `20260916-163302-deepseek-deepseek-v4-flash-0731.md` | 1 | 1277 | 5596 | 5108 | 1024 | 0.0019559265 | Ganador; pasa los 9 tests |
| **Total registrado** | | **4** | **4033** | **40336** | **38468** | **1024** | **0.0135048928** | **4 turnos con respuesta** |

## 2.3 Tokens de pensamiento

Los cuatro turnos que tuvieron respuesta devolvieron `reasoning_tokens`: **38.468
tokens** en total. El detalle por intento está en la tabla anterior. En estos
logs, el razonamiento forma parte de `completion_tokens` y de
`cost_details.upstream_inference_completions_cost`, por lo que está incluido en
el costo total registrado: **USD 0,0135048928**. No hay un precio separado para
razonamiento en el usage de estos turnos.

Nota a verificar: algunos modelos razonan sin devolver los tokens de
razonamiento en la respuesta. Si nos pasa, va documentado aca como hallazgo, con
el log que lo muestra.

## 2.4 Caching y ahorro

Los intentos 01, 02, 03 y 05 registraron **0** tokens cacheados; el intento 04
no tuvo respuesta y, por lo tanto, no permite conocer su usage. El intento 06
registró **1024** tokens cacheados.

La serie inicial mantuvo `prompts/conway/estatico.md` sin cambios, pero los
intentos 02 y 03 devolvieron `cached_tokens = 0`. Se abrio la serie 02 con un
prefijo mas completo en `prompts/conway/serie-02/estatico.md`, sin alterar el
prefijo anterior. El envio 04 se interrumpio antes de registrar una respuesta.
El primer intento completado de la serie 02 (05) devolvio `cached_tokens = 0`;
el segundo (06) devolvio `cached_tokens = 1024` y su codigo paso los 9 tests.
El reporte deriva un ahorro conocido de **USD 0,0000525312** para el intento 06,
comparando su entrada con la del intento 05, sin cache y con el mismo modelo y
proveedor fijado. La cuenta solo incluye ahorros con referencia comparable; no
se inventa un cero para los logs que no tienen datos suficientes.

## 2.5 Contraste contra el dashboard

| Fuente | Gasto USD |
|---|---|
| Suma de los logs (`usage_report.py`) | **USD 0,0135048928** |
| Dashboard de actividad de OpenRouter | PENDIENTE |
| Diferencia | PENDIENTE |

Explicacion de la diferencia, si la hay: falta incorporar el importe que figura
en el dashboard de actividad. Los intentos 01 y 04 no tienen bloques de usage,
por eso el total de los logs es un total **registrado**, no una prueba de que
esos envíos hayan costado USD 0.

## 2.6 Conclusion

Mantendría DeepSeek v4 flash y el presupuesto de **1 prompt**, pero haría el
prefijo estático más compacto para bajar tokens de entrada sin perder el
contrato de `vida.py`.
Mantendría el proveedor fijado y el cache por prefijo: el intento 06 logró
**1024 tokens cacheados** y redujo el costo de entrada frente al intento 05.
Evitaría generar explicaciones extensas: limitaría explícitamente la respuesta
al script y una verificación breve para reducir los **5108 tokens de
razonamiento** del ganador.
