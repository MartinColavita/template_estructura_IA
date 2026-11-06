# Código muerto — sacarlo con evidencia, en tandas reversibles

> Variante de [[modernizar-slice]]. Lo que nadie llama confunde a todo el que lee, infla la radiografía y
> hace creer que hay más reglas de las que hay. Pero **"nadie lo llama" es una afirmación que se prueba**,
> no una impresión.

## Evidencia convergente (hacen falta al menos dos)

| Fuente | Qué dice | Qué NO prueba |
|---|---|---|
| **Grafo de referencias** (`bin/radiografiar-codigo.py`: dependencias entre módulos; el buscador del lenguaje para símbolos) | Ningún archivo lo importa ni lo llama | Llamadas dinámicas: reflexión, nombres armados en texto, rutas registradas por configuración |
| **Rutas y configuración** | El endpoint no está en el contrato ni en el enrutado | Un cliente externo que lo llama igual |
| **Registros y tráfico** (fuente 6 de [ingenieria-inversa.md](../../../skills/desarrollo/references/metodo/ingenieria-inversa.md), con un "sí") | En N meses nadie lo pidió | Un proceso anual o un reporte de fin de ejercicio |
| **Historial** | Se reemplazó por otra cosa en el commit X | Que el reemplazo cubra todos los casos |
| **Banderas** | La bandera que lo activa está apagada en todos los ambientes | Que alguien la encienda mañana |

Con una sola fuente es una sospecha; con dos que coinciden es evidencia; **con una que contradice, no se
saca** y se pregunta.

## Cómo se saca

1. **Tanda chica y reversible**: un módulo o un grupo de funciones por Tarea, en su propio Merge Request,
   con el título `chore(muerto): <qué se saca y la evidencia>`.
2. **Se saca con sus tests, fixtures, banderas y configuración.** Dejar el test de algo que ya no existe
   es dejar código muerto de otro color.
3. **La red sigue en verde** (caracterización y suite completa) después de sacar: si algo se puso en rojo,
   no estaba muerto.
4. **Se anota en `aplicacion/mapa.md`** qué se sacó y con qué evidencia, por si alguien lo busca después.
5. **Nunca en el mismo commit que un refactor o un cambio de regla.**

## Lo que frena

- Una llamada dinámica posible (reflexión, texto, configuración) sin descartar con una persona.
- Un endpoint que no está en el contrato pero **sí en los registros**.
- Falta la red: sin caracterización no se puede saber si "nadie lo usa" o "no lo probamos".
