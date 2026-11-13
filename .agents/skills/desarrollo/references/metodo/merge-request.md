# El Merge Request

> Método propio. Límites de tamaño y estructura de la descripción adaptados de
> `wshobson/commands` (MIT), [referencias-externas.md](../referencias-externas.md).

## Uno por Tarea

**Un Merge Request por Tarea del tablero.** No por sprint, no por funcionalidad, no "junto
dos que son chiquitas". La trazabilidad Tarea ↔ código es lo que permite después contestar
*"¿esto por qué se hizo?"* sin preguntarle a nadie.

## Tamaño — el límite es real

| Señal | Qué hacer |
|---|---|
| **Más de 20 archivos** | Partir |
| **Más de 1000 líneas** (sumando altas y bajas) | Partir |
| **Modifica más de un módulo** | **Partir siempre** (dos Tareas en serie). O la Tarea estaba mal partida o el código se desbordó |

> Por qué importa: pasado cierto tamaño, la revisión deja de ser revisión. El que revisa
> hojea, tilda y aprueba. Un Merge Request de 2000 líneas **no se revisó**, se firmó.

Si no se puede partir —pasa, por ejemplo al mover archivos— se dice **por qué** en la
descripción y se separa el movimiento del cambio real en commits distintos.

## Qué lleva la descripción

| Bloque | Qué va |
|---|---|
| **Qué Tarea cierra** | El `#ID` del tablero. Dato duro |
| **Qué hace** | Dos o tres líneas en criollo. Qué cambia para el que usa el sistema |
| **Qué módulo modifica** | Uno. Si usa otro (por su `application`), cuál |
| **Cómo se probó** | Los tests que se agregaron, y **la evidencia del rojo y del verde** |
| **Contrato** | Si cambió el `openapi.yaml`, qué cambió y si rompe a alguien |
| **Cambios que rompen** | Explícito. Si no hay, se dice "ninguno" — no se omite |
| **Dependencias nuevas** | Cuáles, por qué, y si están en la lista de dependencias aprobadas del proyecto (⚠ la define el equipo / la organización del nuevo proyecto; se anota en `arquitectura/esqueleto-proyectos.md` del Cerebro) |
| **Lo que quedó afuera** | Lo que se decidió no hacer, con el motivo |

Ese último bloque es el que más se saltea y el más útil seis meses después.

## Checklist antes de pedir revisión

- [ ] La suite **completa** en verde, no sólo lo nuevo.
- [ ] Evidencia del **rojo** guardada, y falló **en la aserción** (verificada sobre el historial
  de trabajo; queda en la rama `evidencia/<ID>`, subida a `origin` sin Merge Request).
- [ ] Commits **agrupados por importancia**, uno por cambio lógico (alrededor de 10 por Tarea,
  como guía), con mensajes específicos.
- [ ] Cada código del contrato tiene su test.
- [ ] Ningún import de `api` / `infra` de otro módulo.
- [ ] **Sin PHI** en código, tests, fixtures, logs, mensajes de error ni en la descripción del Merge Request.
- [ ] Sin credenciales, tokens ni rutas internas pegadas.
- [ ] Sin código comentado ni salidas de depuración olvidadas.
- [ ] **SAST** corrió y frena la entrega. Supresiones con motivo escrito al lado.
      ⚠ **Pendiente de definir**: qué analizador de seguridad corre lo fija el equipo / la
      organización del nuevo proyecto; mientras no esté en el pipeline, este ítem es
      `SIN DATOS` — no se tilda. Ver
      [seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md).
- [ ] **Puerta de calidad** exigida por el build, no sólo configurada.

## Quién revisa

**No el que escribió.** La revisión la corre un agente o una persona distinta. No es
desconfianza: el que escribió ya decidió que estaba bien y va a leer buscando confirmarlo.

Las seis dimensiones y las severidades: [code-review.md](code-review.md).

**La autorevisión no cuenta como revisión.** Es un paso previo —leer el diff propio entero
antes de pedirla— y sirve, pero no reemplaza al segundo par de ojos.

**En modo solo (`DEC-006`, `DEC-005`)** el segundo par de ojos es el **agente verificador** (controles 5,
5-bis, 5-ter, 5-quater, con contexto limpio y sólo lectura) y la decisión es tu «Aprobar». El Merge Request es
**opcional**: con el Aprobar podés mergear vos a `develop` con la suite en verde, o abrirlo igual para dejar
el historial. Lo que no cambia: quien produjo no se aprueba, y un bloqueante no se negocia.

## Qué frena la entrega

Sólo los **BLOQUEANTES**: vulnerabilidad, comportamiento incorrecto, límite de módulo roto,
evidencia del rojo ausente o inválida, PHI.

Las recomendaciones y sugerencias **no frenan, pero se responden**. Una recomendación
ignorada sin respuesta enseña que revisar no sirve, y a la tercera vez nadie revisa en serio.

Un hallazgo bloqueante **no se negocia bajándole la severidad**: se arregla, o lo acepta una persona
como dice [code-review.md](code-review.md) §«Severidad».

## Hallazgos para una persona

El veredicto de la cadena lo leen scripts. Lo que lee una persona —esta descripción, una revisión
suelta— va **en criollo y en cuatro partes**, numerado de corrido para poder contestar «arreglá el 2 y
el 5», agrupado por severidad, y al final una línea con lo que no se pudo mirar:

```
2. <Título corto> (archivo:línea)
   - Qué es: qué hace ese código, en una o dos frases.
   - Problema: qué sale mal, con el caso concreto.
   - Arreglo: el cambio más chico que lo resuelve.
   - Si no lo hacemos: qué le pasa a quien usa el sistema.
```

## Después: el comentario de cierre en la Tarea

Abierto el Merge Request —o pusheada la rama, si el equipo mergea en local—, **quien terminó
el desarrollo comenta la Tarea** con la rama, el link
del Merge Request y un resumen técnico armado con los bloques de arriba. El molde y sus barreras
están en la skill `comentar-tarea` (§«Comentario de cierre de desarrollo»).

Tres cosas que no se negocian:

- **Todo sale del repositorio**: la rama y el commit de `git`, el link del Merge Request leído
  de GitLab **en sólo lectura**. El comentario no abre ni toca el Merge Request.
- **No cambia el Estado de la Tarea.** En modo equipo está en el sprint y tomada: sólo se comenta.
- **Se muestra antes de postear** y se espera el "sí", como todo lo que se escribe en Azure (con `DEC-005`
  confirmada, lo que ella fija: [[AGENTS]], «Autorización permanente»).

## Nada de PHI, tampoco acá

La descripción del Merge Request y sus capturas quedan en GitLab para siempre y las ve todo
el equipo. Marcadores: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`,
`<direccion>`, `<dato-sensible>`.

Es el lugar donde más se escapa, porque se pega un log real para explicar el bug.
