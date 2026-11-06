# TDD en el front — lo específico del stack (plantilla a completar)

> **El ciclo y la evidencia viven en [tdd-ciclo-y-evidencia.md](tdd-ciclo-y-evidencia.md)**
> y no cambian con el stack: rojo en la aserción, verde con la suite completa, refactor con la
> red puesta, evidencia verificada por otro agente, veredicto de tres estados. **Este archivo
> es lo único que cambia con el stack.** Se completa cuando el proyecto elige el suyo y deja
> la decisión en `arquitectura/decisiones.md`; cada `<completar: …>` que quede sin llenar deja
> en `SIN DATOS` lo que dependa de él.

## El stack, decidido

| Tema | Decisión |
|---|---|
| Framework de interfaz | `<completar: framework del front>` |
| Build | `<completar: herramienta de build y servidor de desarrollo>` |
| Harness de test | `<completar: runner + librería para probar como el usuario (por rol, etiqueta y texto) + simulador de la API>` |
| Repositorios | **Uno por aplicación, separados.** `<completar: cuáles son las aplicaciones>` |
| Versiones del framework, del lenguaje y del build | `<completar: se fijan al crear el primer repo y se pinnean>` |
| Librería de componentes | `<completar: antes de elegir una de afuera, preguntar qué tiene publicado la organización>` |

Lo que la organización ya tenga decidido para el front —registro de paquetes, dependencias
aprobadas, design tokens— se toma tal cual y se anota en `arquitectura/esqueleto-proyectos.md`.
Lo que no esté decidido se pregunta, no se elige.

## Registro de paquetes — antes de instalar nada

`<completar: el archivo de configuración del gestor de paquetes, versionado en la raíz del
repo, apuntando al registro autorizado por la organización>`

Sin eso, o no descarga, o descarga de un lugar que no está controlado. Ver
[dependencias-y-config.md](dependencias-y-config.md).

## Qué se prueba, y desde dónde

La regla, que acá se toma entera: **se prueba lo que el usuario ve y hace, no cómo está
implementado.**

| | |
|---|---|
| **Se busca por** | rol, etiqueta, texto visible — lo que usaría una persona |
| **No se busca por** | clase de estilos, id interno (salvo los identificadores que **el contrato de la Tarea fija**, p. ej. un `data-testid`: ahí manda el contrato), estructura del árbol |
| **Se afirma sobre** | lo que aparece en pantalla y lo que se envió |
| **No se afirma sobre** | estado interno del componente, cuántas veces se dibujó |

Un test atado a la implementación se rompe en cada refactor sin que nada esté mal. Termina
ignorado, y un test ignorado figura como cobertura sin cubrir nada.

> **No choca con los identificadores estables.** "No se busca por id" vale para estos tests.
> Los elementos interactivos igual llevan un identificador estable y los que cargan datos
> exponen su estado en el DOM, pero eso es para las **pruebas de punta a punta** sobre la app
> corriendo.

## Cómo se ve un rojo válido

Lo único que cuenta es **fallar en la aserción**: el test corrió, buscó lo que esperaba ver, y
no coincidió con lo que había.

| Cómo falló | ¿Es rojo válido? |
|---|---|
| «Esperaba ver el elemento y no estaba» | **SÍ.** Llegó a la aserción |
| «Esperaba *rechazada* y obtuvo *aprobada*» | **SÍ.** Idem |
| No se encuentra el módulo o el archivo que el test importa | **NO.** No existe el archivo |
| El componente no está definido | **NO.** No existe el componente |
| Error de sintaxis o de tipos | **NO.** Ni compila |

Igual que en el back: los de abajo **no son rojo válido**. Para llegar a la aserción, creá el
componente devolviendo lo más neutro que se dibuje (nada, o un fragmento vacío) y dejá que el
test falle comparando.

`<completar: cómo se ve, en el runner elegido, el mensaje de una aserción fallida, y cómo se
ven un import roto y un error de compilación — para que el verificador los distinga de un
vistazo>`

## La simulación y el contrato — la regla dura

**Las llamadas a la API se simulan a partir del `openapi.yaml` que consolida el back.** Nunca
se inventa la forma de una respuesta. La herramienta de simulación es la del stack
(`<completar>`); el método, con sus escenarios de error, latencia y deriva, está en
[simular-api-desde-el-contrato.md](simular-api-desde-el-contrato.md).

> Si simulás una respuesta que el contrato no declara, tu front va a andar perfecto contra un
> backend que no existe. Se descubre en integración, tarde, y parece un problema del back.

Cuando el contrato todavía no tiene el endpoint, **eso es un bloqueo de la Tarea**, no una
licencia para inventarlo. Ver [contrato-openapi.md](contrato-openapi.md).

## Qué nivel para qué

| Tipo | Qué cubre |
|---|---|
| **De componente** | Render, estados visibles, interacción del usuario, accesibilidad básica |
| **De flujo** | Varios componentes juntos: completar un formulario, ver el resultado |
| **De contrato (con la API simulada)** | Que ante cada respuesta declarada —incluidos los errores— la UI haga lo correcto |

Ese último es el que más se saltea: se simula el camino feliz y ninguno de los códigos de
error del contrato. Cada código declarado lleva su test.

## Comandos

```text
<completar: comando que corre la suite completa>          # la que vale para el verde
<completar: comando que corre un solo test, por patrón>    # para el rojo
<completar: chequeo estático de tipos en modo estricto + build>
```

> **Windows con Git Bash:** `npx` y `npm test -- …` pueden fallar con *«"C:\Program" no se reconoce»* cuando el
> PATH tiene espacios. Corren `npm.cmd test` y, para un solo test, `node node_modules/<runner>/<runner>.mjs run -t "<nombre>"`
> (con Vitest: `node node_modules/vitest/vitest.mjs run -t "…"`). Antes del primer rojo se corre la suite completa una vez:
> así se sabe cómo se ve el verde y que el comando anda en esta shell.

## Design tokens

Los tokens de la organización y el design system propio del proyecto **conviven y no se
mezclan sin decidirlo**. Si un mockup y un componente real usan paletas distintas, se frena y
se pregunta: **es decisión de equipo, y mientras no se tome está abierta.**

**Nunca valores hexadecimales escritos a mano en el código, ni copiados desde acá.** La fuente
de los propios es `cerebro-digital/diseno/diseno-sistema.md`, y se lee de ahí en el momento.

> ⚠ Si el design system dice dos cosas distintas sobre un mismo color —pasa, cuando una
> migración de paleta quedó a medias—, **ese color se pregunta, no se copia de ningún lado**.
> Lo resuelve quien mantiene el design system, no quien escribe el componente. Un hexadecimal
> copiado desde una guía de método es exactamente cómo se propaga el error.

## Antes del Merge Request

1. **Analizador de seguridad (SAST/SCA)** — ⚠ **a definir por el equipo.** La intención es
   que corra en el pipeline y **frene** la entrega. Mientras no esté configurado no se tilda
   como si hubiera corrido, y sin su resultado el ítem queda en `SIN DATOS`. Ver
   [seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md).
2. **Puerta de calidad**: linter, **chequeo estático de tipos en modo estricto** (donde el
   stack lo tenga) y umbral de cobertura, exigidos por el build.
3. **Evidencia del rojo y del verde, auditada por otro agente.**
