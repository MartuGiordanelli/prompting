---
status: accepted
---

# `vida.py` y `test_vida.py` viven en la raiz, sin carpeta `tests/`

`test_vida.py` de la catedra resuelve el script bajo prueba en su propio
directorio cuando se lo invoca sin argumento (`Path(__file__).parent / "vida.py"`),
y la catedra corre `python3 test_vida.py` a secas. Poner el test en `tests/` y el
script en la raiz hace que esa invocacion falle con "No encuentro ...", asi que
los dejamos hermanos en la raiz para que la invocacion sin argumento funcione.

## Consecuencias

El repo no tiene carpeta `tests/`, que es lo que un lector de Python esperaria.
Si mas adelante se agregan tests propios de la interfaz de chat, van en `tests/`
y `test_vida.py` **igual se queda en la raiz**: es un artefacto de la catedra que
se entrega tal cual y cuya ubicacion es parte de su contrato de invocacion, no
una decision de layout nuestra.
