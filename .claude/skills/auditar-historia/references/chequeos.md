# Los 20 chequeos de auditar-historia

Parte de la skill `auditar-historia`: se lee antes de auditar, para los chequeos de criterio que el script no hace.

## Los 20 chequeos

### Chequeo 1 — ¿Hay ficha fuente? (declarativo, NO bloqueante)

1. **¿El *Documento fuente* resuelve a una ficha del Cerebro con bloque
   `## Derivación a backlog`?** Un mockup `.html`, un acta de reunión o un link a Figma
   **no son una ficha**: son apoyo visual. Se responde **sí o no**, y la respuesta **decide
   qué se puede auditar**, no si se audita.
   - **Si NO hay ficha:** se declara como **un** hallazgo —«la Historia no tiene ficha»— y los
     chequeos **11 a 18** (bloques B y C) se reportan **NO AUDITABLES por falta de ficha**,
     nunca como ocho hallazgos sueltos. **Los otros once chequeos corren igual** y el veredicto
     sale de ellos.
   - **Nunca frena por sí solo la derivación de Tareas.**

   > **Por qué dejó de ser bloqueante.** Hoy los funcionales arman las Historias con el
   > conocimiento del OKF **y un mockup**, y eso es el flujo real del equipo. Hacer que «no hay
   > ficha» valga NO AUDITABLE convertía a esta skill en un muro: ninguna Historia real podía
   > pasar, y con el gate de `sincronizar-backlog` encima, **nada se derivaba nunca**.
   > La medición era correcta, el veredicto estaba mal calibrado.
   >
   > **Y sin ficha sigue habiendo mucho que auditar:** los **once** chequeos que no dependen de
   > ella son los que atrapan un `Entonces` que no se puede observar, un «funciona
   > correctamente», UI sin regla detrás, una `[RN-…]` citada que no existe o que no dice lo que
   > se le atribuye, y —el chequeo 20— **que el documento fuente contradiga las reglas que la
   > Historia cita**. Ese último está pensado **justamente** para el caso del mockup: es el que
   > detecta que la maqueta muestra un canal dado de baja mientras la Historia cita la regla que
   > lo eliminó.
   >
   > **Dónde sí hace falta la ficha: al CREAR el árbol**, no al auditar una Historia que ya
   > existe. El bloque enumerado es lo que fija **cuántas** Historias van (Regla de
   > cardinalidad, [[sincronizar-backlog]]). Auditar y crear son momentos distintos; confundirlos
   > fue el error.

### Bloque A — Calidad del Gherkin (campo Criterios de aceptación)

> **Este bloque es un tamiz grueso.** Sus criterios son contables a propósito, y por eso
> dejan pasar Gherkin defectuoso que un humano vería al toque. Que el bloque A pase entero
> **no significa que el Gherkin sea bueno** — significa que no tiene los defectos que se
> pueden contar. Los bloques B y C son los que de verdad separan.

2. **Hay al menos un `Escenario:`.** Cero → **NO AUDITABLE**. (Una Historia sin Escenarios no se deriva igual, pero por el DoR, no por esta auditoría: ver [[sincronizar-backlog]].)
3. **Cada `Escenario:` tiene al menos un `Entonces`** con resultado observable.
4. **Ningún `Entonces` usa vocabulario vacío.** Lista negra: *correctamente, adecuadamente,
   exitosamente, sin problemas, según corresponda, de forma apropiada, de manera adecuada,
   correcto*.
5. **Un comportamiento por Escenario.** Tres señales, no una:
   - ` o ` / ` y también ` dentro de un `Entonces`;
   - un `Y` que introduce un **sujeto distinto** al del `Entonces` anterior;
   - **un `Entonces` que describe un efecto INTERNO** (*consulta, invoca, llama a, registra
     en, persiste*) **seguido de un `Y` observable**. Es el caso que más se escapa: mismo
     sujeto, dos comportamientos, y el primero ni siquiera se puede verificar desde afuera.
6. **Actor explícito y voz activa en cada `Cuando`.** Dos señales:
   - arranca con `se ` (*se registra*, *se envía*, *es enviado*) → esconde quién actúa;
   - **el sujeto es «el sistema»** → gramaticalmente activo, pero igual esconde la acción
     del usuario que dispara el escenario. Un `Cuando` describe lo que **hace alguien**, no
     lo que el sistema hace solo.
7. **Cero UI sin regla detrás.** Lista negra ampliada: *botón, combo, grilla, pestaña, modal,
   columna, checkbox, **tarjeta, ficha, pantalla, alerta, campo, leyenda, mensaje, popup,
   menú***. Si aparece alguna sin `[RN-…]` asociada, el Escenario describe la pantalla en vez
   del comportamiento: se rompe con cualquier rediseño.
8. **Cobertura de caminos:** al menos un caso feliz **y** al menos uno de error o borde.
   Si la Historia **o alguna de las reglas que cita** menciona roles o permisos distintos,
   al menos uno de permiso.
9. **Cero keywords en inglés** (`Given/When/Then/Scenario/Feature/And/But`).
10. **Cada `Escenario:` lleva su `[RN-…]`, esa regla existe, y contiene el criterio que el
    Escenario le atribuye.** Dos trampas frecuentes: la regla existe pero habla de **otro rol,
    otra pantalla u otro sistema**; o el Escenario afirma algo que la regla **no menciona**.
    Las dos son **trazabilidad falsa**: simulan cobertura, y es peor que no citar nada.

### Bloque B — La Historia cierra contra su ficha

> **La Regla del cero también rige acá.** Si un bloque de la Historia **no existe**
> (*Casos de uso*, *Datos y estados (funcional)*), el conteo da `0 = 0` y el chequeo pasaría
> por vacuidad. **Bloque ausente → NO AUDITABLE, nunca PASA**, y se dice cuál falta.

11. **Cada `CU-nn` de *Casos de uso* está cubierto por al menos un Escenario.** Este bloque no
    tenía **ningún consumidor** aguas abajo: se escribía y moría ahí.
12. **Cada campo y cada transición de *Datos y estados (funcional)* aparece en algún Escenario
    o `CU-nn`.** Es el inventario que la Tarea necesita para su Contrato técnico. Si el bloque
    falta, las Tareas hijas armaron su contrato **sin fuente**.
13. **Las `[RN-…]` que la Historia cita son exactamente las que la ficha asigna a su `[F-nn]`.**
    Ninguna de más (alcance inventado), ninguna de menos (regla huérfana: si la Historia
    declara 4 de 21, las otras 17 **no existen para nadie aguas abajo**).
14. **La Historia rastrea a un `[F-nn]` concreto y su título describe el mismo alcance.** Un
    título más amplio —o que junta dos alcances— es una bomba con el GATE de dedup: cuando
    llegue el alcance que quedó afuera, va a encontrar esta Historia y **bloquear el alta del
    ítem equivocado**.

### Bloque C — Suficiencia del bloque `## Derivación a backlog`

> El único que mira **hacia afuera**. La Regla de cardinalidad prohíbe crear nodos fuera de la
> enumeración: **lo que falta en la lista no puede nacer nunca**, en ninguna herramienta.
> Si el chequeo 1 falló, estos cuatro se reportan como **derivados** de él.

15. **Prosa → enumeración.** Cada flujo o acción de negocio descripto en la prosa de la ficha
    aparece como `[F-nn]`, **o** está declarado fuera de alcance **por escrito y con motivo**.
16. **Enumeración → prosa.** Cada `[F-nn]` rastrea a un lugar concreto de la ficha. Un
    enumerado sin respaldo es un flujo inventado.
17. **Reparto de reglas sin residuo.** `reglas de la ficha` = `asignadas a algún [F-nn]` +
    `declaradas fuera de alcance con motivo`.
18. **Pendientes abiertos que tocan un `[F-nn]` derivado.** Barrer **las cuatro formas** que
    conviven: `## Dudas y Preguntas`, `## Dudas y preguntas`, `## Pendientes`, y cualquier
    `- [ ]` o marca de alerta suelta.

### Bloque D — Lo que se afirma sin respaldo

19. **Ningún `Entonces` afirma sobre un punto que el Cerebro tiene ABIERTO.** Cruzar el texto
    de cada Escenario contra los pendientes (`P-nnn`, marcas de alerta, «a definir», «en
    discusión», «falta definir», «a confirmar») y contra las reglas en estado PENDIENTE.
    > **Es el mecanismo exacto por el que una duda se vuelve requisito sin que nadie la vote.**
    > Un Escenario afirma un comportamiento que el equipo todavía está discutiendo; baja a las
    > Tareas como dato duro; los tests lo fijan; y queda implementado como si hubiera sido una
    > decisión. El chequeo 18 barre pendientes, pero solo pregunta si tocan un `[F-nn]`: este
    > los cruza contra **el texto de los Escenarios**, que es donde el daño se materializa.
20. **El Documento fuente NO contradice las reglas que la Historia cita.** Leer el contenido
    del fuente —no solo su bloque de derivación— y verificar que lo que muestra siga vigente.
    Un mockup dibujado antes de una decisión puede seguir mostrando el flujo **que esa
    decisión descartó**, y la Historia lo cita como fuente de verdad. Es la dirección inversa
    del drift que [[consultar-backlog]] detecta (doc → ticket): acá se mira **ticket → doc**,
    y hoy no la mira nadie.
