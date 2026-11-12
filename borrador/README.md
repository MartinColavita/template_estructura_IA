# borrador/

Carpeta de trabajo local — **nunca se versiona** (excepto este README). Acá se generan y se
iteran los borradores funcionales, mockups y presentaciones antes de convertirse en una
versión final.

## Cómo funciona

1. Cuando le pidas a un agente que genere o modifique un documento funcional, un mockup o una
   presentación, el resultado se guarda primero acá — nunca directo en `documentos/` ni en
   `entregables/`.
2. Iterá sobre el contenido las veces que haga falta. Nada de lo que hay en esta carpeta está
   "subido" a ningún lado: es descartable y no rompe nada del conocimiento ya consolidado.
3. Cuando una versión te sirva como definitiva, pedile explícitamente al agente que la
   **meta en funcional**. Recién ahí se copia al destino final para que pueda subirse al
   repositorio: **mockups y presentaciones van a `entregables/`** (`disenos/`, `presentaciones/`);
   **documentos funcionales (fichas, reglas) van al Cerebro Digital por `cerebro-curator`**; `documentos/` sólo recibe lo que entra de afuera.

Usá subcarpetas que reflejen el destino final (`borrador/disenos/` → `entregables/disenos/`,
`borrador/presentaciones/` → `entregables/presentaciones/`, `borrador/documentacion/` →
`entregables/documentacion/`; las fichas van al Cerebro por el curador) para que promover un
archivo sea simplemente moverlo a la carpeta equivalente. También viven acá, y se descartan
cuando terminan: `borrador/lote-*/` (modo lote), `borrador/adopcion/` (informes de un proyecto
enchufado), `borrador/absorcion/` y `borrador/diagramas/`.

## Por qué existe

El equipo funcional y gerencia no manejan conceptos de git, ramas o repositorios, y usan este
proyecto como una caja negra. Esta carpeta hace transparente cómo trabaja el agente: todo lo
que está en construcción queda visible acá, y nada se considera oficial hasta que se pide
explícitamente moverlo a su destino final: `entregables/` (un mockup, una presentación) o el Cerebro
por `cerebro-curator` (una ficha, una regla). Nunca a `documentos/`, que sólo recibe lo que se entrega.
