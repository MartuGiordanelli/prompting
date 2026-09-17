# Informe — Mision: el prompt minimo

> **Estado: esqueleto.** Cada seccion marcada `PENDIENTE` se completa cuando
> exista la evidencia que la respalda. Las tablas de la Parte 2 se generan con
> `python3 scripts/usage_report.py`, no se transcriben a mano.

Grupo: PENDIENTE
Repo: https://github.com/MartuGiordanelli/prompting

---

# Parte 1 — Trabajo previo

> Consulta propia del catalogo: **2026-09-17**, contra
> `GET https://openrouter.ai/api/v1/models` (445 entradas) y las tablas de
> `openrouter.ai/benchmarks`. Los precios se expresan por millon de tokens.

## 1.1 Que es un router de modelos

Un router recibe el prompt, lo clasifica y lo manda al modelo que mejor conviene
para esa tarea sin que el cliente cambie el codigo; resuelve el problema de
tener que elegir y mantener a mano un modelo por caso de uso, con fallback
cuando el proveedor elegido falla o se satura.

Ficha consultada: https://openrouter.ai/openrouter/auto — el Auto Router elige
"powered by the wisdom of the market", es decir segun el gasto agregado de la
comunidad de OpenRouter por tipo de tarea. La variante `openrouter/auto-beta`
lo hace explicito: clasifica el request y rutea al modelo mas usado para esa
tarea, filtrado por las preferencias de la cuenta. Ambos declaran una ventana de
2.000.000 de tokens y precio `-1` (el costo real es el del modelo que termine
atendiendo).

## 1.2 Mapa de modelos

El modelo mas avanzado de cada proveedor, al **2026-09-17** (fecha de consulta).
La posicion en benchmarks es el ranking en **GPQA Diamond** de
`openrouter.ai/benchmarks/gpqa-diamond`, sobre **135 modelos medidos**.

| Proveedor | Modelo | USD / 1M in | USD / 1M out | Ventana | Posicion en benchmarks |
|---|---|---|---|---|---|
| OpenAI | `openai/gpt-6-astra` | 10,00 | 50,00 | 1.050.000 | 4.º (GPQA 94,61 %) |
| Anthropic | `anthropic/claude-fable-5.1` | 10,00 | 50,00 | 1.000.000 | 27.º (GPQA 89,98 %) |
| Grok | `x-ai/grok-4.6` | 2,00 | 6,00 | 500.000 | 9.º (GPQA 93,27 %) |
| Gemini | `google/gemini-3.8-flash` | 0,75 | 3,75 | 1.048.576 | sin dato (aun no medido; el 3.7 Flash va 5.º con 94,53 %) |
| DeepSeek | `deepseek/deepseek-v4.1-flash` | 0,15 | 0,60 | 1.048.576 | 13.º (GPQA 92,44 %) |
| Qwen | `qwen/qwen3.8-max-0902` | 2,00 | 6,00 | 1.000.000 | sin dato (el mejor Qwen medido es `qwen3.8-2.4t-a95b`, 18.º con 91,20 %) |
| Kimi | `moonshotai/kimi-k3` | 3,00 | 15,00 | 1.048.576 | 11.º (GPQA 93,18 %) |

Vista comparativa usada:
`https://openrouter.ai/compare/openai/gpt-6-astra/anthropic/claude-fable-5.1/x-ai/grok-4.6/google/gemini-3.8-flash/deepseek/deepseek-v4.1-flash/qwen/qwen3.8-max-0902/moonshotai/kimi-k3`

Tres detalles del catalogo que la tabla sola no muestra:

- **El precio no es plano.** `gpt-6-astra` duplica su tarifa arriba de 272.000
  tokens de prompt (20,00 / 75,00) y `grok-4.6` hace lo mismo arriba de 200.000
  (4,00 / 12,00). El costo de un prompt largo no es lineal.
- **DeepSeek tiene precio por franja horaria.** `deepseek-v4.1-flash` cuesta
  0,15 / 0,60 en su ventana barata y 0,30 / 1,20 entre semana en horario pico
  (campo `pricing.overrides`, en UTC). La hora a la que se corre un intento
  cambia la factura.
- **El gap de precio es de dos ordenes de magnitud.** Entre `gpt-6-astra` (10,00
  de entrada) y el `deepseek/deepseek-v4-flash-0731` del slot 4 (0,06) hay un
  factor de 167x en entrada y de 417x en salida — y el DeepSeek barato igual
  queda 28.º en GPQA, por encima de `claude-fable-5.1` (27.º) por decimas.

## 1.3 Parametros soportados

Comparacion de `supported_parameters` entre los cuatro modelos que sirve la
interfaz, cada uno de un proveedor distinto.
Fuente programatica: `GET https://openrouter.ai/api/v1/models`, 2026-09-17.

| Parametro | `openai/gpt-5.6-luna` | `anthropic/claude-haiku-4.5` | `google/gemini-3.7-flash` | `deepseek/deepseek-v4-flash-0731` |
|---|---|---|---|---|
| `reasoning` | si | si | si | si |
| `reasoning.effort` | si | **no** | si | si |
| `reasoning.max_tokens` | no | si | si | si |
| Salidas estructuradas (`structured_outputs` / `response_format`) | si | si | si | si |
| `cache_control` explicito | no aplica (cache automatico) | si (`ephemeral`) | no aplica (cache automatico) | no aplica (cache por prefijo) |
| `temperature` / sampling | **no** (ni `temperature`, ni `top_p`, ni `top_k`) | `temperature`, `top_p`, `top_k` | `temperature`, `top_p` | el set completo: `temperature`, `top_p`, `top_k`, `top_a`, `min_p`, `frequency_penalty`, `presence_penalty`, `repetition_penalty`, `logit_bias`, `seed` |
| Precio de lectura de cache (USD / 1M) | 0,02 | 0,10 | 0,075 | 0,012 |
| Precio de escritura de cache (USD / 1M) | 0,25 | 1,25 (2,00 a 1 h) | 0,042 | no se cobra |

Hallazgo: **`cache_control` no es un parametro de sampling y no aparece en
`supported_parameters`** — es un campo del mensaje, y lo que delata el soporte
es el precio: solo Anthropic y OpenAI cobran `input_cache_write`, o sea que en
Anthropic escribir el cache se paga aparte (1,25 por millon, 2,00 si se pide
1 hora de TTL) y recien rinde si el prefijo se reusa. En DeepSeek la escritura
es gratis y la lectura cuesta 0,012: por eso el ejercicio 2 se banca abrir un
intento tras otro con el mismo prefijo sin penalidad.

Los otros dos hallazgos, los que efectivamente condicionaron el diseno de la
interfaz (`chat/slots.py`):

- **Claude Haiku 4.5 no acepta `reasoning_effort`.** Acepta `reasoning`, pero el
  presupuesto se expresa en `max_tokens`, no en niveles. Por eso el slot 2 se
  declara con `supported_efforts=()` y el comando `/effort` no aplica ahi. Un
  selector de effort global, igual para los cuatro slots, habria roto contra
  Anthropic.
- **Los modelos de OpenAI no aceptan `temperature`.** Ni `temperature`, ni
  `top_p`, ni `top_k`, ni penalties: lo unico que se regula es `reasoning`. Una
  interfaz que mandara un `temperature` por defecto a los cuatro slots habria
  fallado justo en el slot 1.

Ademas, los efforts no son el mismo conjunto en todos lados: el slot 1 declara
`max, xhigh, high, medium, low, none`; el slot 3, `high, medium, low`; y el slot
4, `max, high, low`. La tabla de `chat/slots.py` guarda esa diferencia por slot,
y `python3 -m chat --check-models` la re-verifica en vivo contra el catalogo.

## 1.4 Sustituciones de catalogo

Los ids de la mision estan verificados al 2026-09-02. Verificacion propia:
**2026-09-17**. Los cuatro siguen en el catalogo: **no hubo sustituciones**.

| Slot | Id de la mision | Sigue vigente | Reemplazo | Por que |
|---|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | si | — | Presente; 0,20 / 1,20 por millon, ventana 1.050.000. Ya no es el tope de OpenAI (lo es `gpt-6-astra`), pero la mision lo pide por su effort configurable, no por ser el mas avanzado. |
| 2 | `anthropic/claude-haiku-4.5` | si | — | Presente; 1,00 / 5,00 por millon, ventana 200.000 (la mas chica de los cuatro). Es el unico con `cache_control` explicito, que es justo lo que el slot ejercita. |
| 3 | `google/gemini-3.7-flash` | si | — | Presente; 0,75 / 3,75 por millon, ventana 1.048.576. Ya salio el `gemini-3.8-flash` al mismo precio, pero el 3.7 sigue publicado y es el que la mision fija. |
| 4 | `deepseek/deepseek-v4-flash-0731` | si | — | Presente; 0,06 / 0,12 por millon, ventana 1.310.720 (la mas grande de los cuatro). Sigue siendo el escalon barato: 16,7x mas barato en entrada y 41,7x en salida que el slot 2. |

Nota sobre el "15 veces mas barato" de la consigna: contra el slot 2 medido hoy,
la relacion de entrada es **16,7x** (1,00 contra 0,06) y la de salida **41,7x**
(5,00 contra 0,12).

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

El subtotal de los intentos de Conway es **USD 0,0135048928**. Para contrastar
el gasto de la cuenta con el dashboard se toma el total de todos los logs
registrados, que incluye las demos del ejercicio 1 y la validación del
proveedor:

| Fuente | Gasto USD |
|---|---|
| Suma de todos los logs (`usage_report.py`) | **USD 0,0325394089** |
| Dashboard de actividad de OpenRouter | **USD 0,0325394089** |
| Diferencia | **USD 0** |

La suma cierra con el dashboard. Los intentos 01 y 04 no tienen bloques de
usage; por eso el total de los logs es un total **registrado**, no una prueba de
que esos envíos hayan costado USD 0.

## 2.6 Conclusion

Mantendría DeepSeek v4 flash y el presupuesto de **1 prompt**, pero haría el
prefijo estático más compacto para bajar tokens de entrada sin perder el
contrato de `vida.py`.
Mantendría el proveedor fijado y el cache por prefijo: el intento 06 logró
**1024 tokens cacheados** y redujo el costo de entrada frente al intento 05.
Evitaría generar explicaciones extensas: limitaría explícitamente la respuesta
al script y una verificación breve para reducir los **5108 tokens de
razonamiento** del ganador.
