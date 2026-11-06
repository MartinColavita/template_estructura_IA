# Arrancar una funcionalidad completa (back + front)

> Prioridad **ALTA** por hito. Es el documento que ordena a todos los demás.
> Adaptado de `feature-development` y `full-stack-feature` de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## Dónde empieza — y dónde NO

**Empieza en una Tarea del tablero.** No en una charla, no en un mockup suelto, no en
"arranquemos y después vemos". La auditoría de la Tarea (`auditar-tarea`) es **opcional**: no
se exige para arrancar.

Si no hay Tarea con contrato cerrado y lista de tests, **esto no arranca**: se avisa y se
manda a cerrar por el pipeline del Cerebro (`redactar-tarea`). Un hueco o un gris de una Tarea
que sí tiene contrato y lista **no frena**: se deja como pendiente a confirmar en la tarjeta
(`comentar-tarea`). Ver el guardarraíl **G1**: la Tarea define **qué**, esta skill define
**cómo**.

## El orden entre back y front

```
1. CONTRATO       se acuerda y se cierra el fragmento OpenAPI
                  |
        +---------+---------+
        |                   |
2. BACK             2'. FRONT            <- EN PARALELO, de verdad
   contrato-first       simula la API       ninguno espera al otro
   tests en rojo        desde el contrato
   código              tests en rojo
        |                   |
        +---------+---------+
                  |
3. INTEGRACIÓN    el front deja de simular y apunta al back real
4. VERIFICACIÓN   otro agente audita los dos lados
5. ENTREGA        un Merge Request por Tarea, por repositorio
```

**El contrato es lo que hace posible el paralelo.** Sin él, el front espera al back, o
inventa la respuesta y se rompe en el paso 3. Ver
[contrato-openapi.md](contrato-openapi.md).

## Qué pasa en cada tramo

| Tramo | Qué se hace | Detalle |
|---|---|---|
| **Contrato** | Todos los códigos de respuesta, forma del cuerpo, obligatorios, límites | [contrato-openapi.md](contrato-openapi.md) |
| **Back** | Contrato → tests en rojo → firma mínima → código → refactor | [crear-endpoint.md](crear-endpoint.md) · [tdd-stack-back.md](tdd-stack-back.md) |
| **Front** | Simulación desde el contrato → tests en rojo → componente → refactor | [simular-api-desde-el-contrato.md](simular-api-desde-el-contrato.md) · [tdd-stack-front.md](tdd-stack-front.md) |
| **Integración** | Se quita la simulación y se apunta al back real | Acá aparecen los desacuerdos de contrato |
| **Verificación** | Evidencia del rojo, revisión por dimensiones, seguridad, accesibilidad | [code-review.md](code-review.md) |
| **Entrega** | Un Merge Request por Tarea, en cada repositorio | [merge-request.md](merge-request.md) |

## Varios repositorios, y eso cambia cosas

El back y los repositorios de front del proyecto viven **cada uno en su repositorio** (cuáles
son, en `arquitectura/esqueleto-proyectos.md` del Cerebro). Consecuencias prácticas:

- **Un Merge Request por repositorio.** Una funcionalidad que toca back y front son
  **varios** —uno por repositorio que toca—, y hay que decir en cada uno que existen los
  otros.
- **El contrato es el único punto de encuentro.** No hay forma de "mirar el código del otro
  lado" sin cambiar de repositorio.
- **El orden de mergeo importa**: primero el back, o el front queda apuntando a un endpoint
  que todavía no existe.

## Trabajo en paralelo de verdad

Si se despachan varias Tareas a la vez, manda el **GATE de WORKTREE** de `AGENTS.md` (la base se
pregunta, techo de espacios de trabajo, árbol sucio frena, mismo archivo serializa); los datos los da
`bin/gate-worktree.py`. No se repite acá.

Y la regla propia de acá: **una Tarea modifica un solo módulo** (puede usar otro, sólo por su
`application`; [[decisiones#DEC-002]]). Si el diff abarca dos, o la Tarea estaba mal partida o
el código se desbordó: son dos Tareas en serie.

## Lo que frena, en cualquier punto

| Freno | Por qué |
|---|---|
| **No hay contrato** para el endpoint | El front no puede simular y el back no sabe qué devolver. No se inventa |
| **No hay evidencia del rojo** | No se puede afirmar que los tests verifican algo |
| **PHI real** en cualquier lado | Bloqueante, sin discusión |
| **SAST no corrió** | `SIN DATOS`, y `SIN DATOS` no es aprobado. ⚠ Qué analizador de seguridad corre lo define el equipo / la organización del nuevo proyecto; mientras no esté configurado en el pipeline, este freno es la intención, no algo que corra ([seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md)) |

## Cómo cierra

```
FUNCIONALIDAD — <Tarea #NNNN>

  Contrato ........ cerrado / con cambios / ⚠ pendiente
  Back ............ tests N · rojo OK · verde OK · MR #___
  Front ........... tests N · rojo OK · verde OK · MR #___
  Integración ..... el front apunta al back real: sí / no
  Verificación .... por <agente distinto>

  OK / HALLAZGO(n) / SIN DATOS(n)

  Aprobado sólo con 0 bloqueantes y 0 SIN DATOS no declarados
  (las dos clases de SIN DATOS: orquestador-desarrollo.md).
```
