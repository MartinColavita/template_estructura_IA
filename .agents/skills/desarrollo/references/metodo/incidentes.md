# Incidentes en producción

> Prioridad **MEDIA** mientras no haya producción, **ALTA** el día que la haya.
> Adaptado de `incident-response` de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## El orden se invierte

En desarrollo: entender, después arreglar. En un incidente es al revés.

```
1. CONTENER    cortar el daño. Sin entender todavía
2. AVISAR      quién está afectado y desde cuándo
3. ENTENDER    la causa, con calma, ya sin sangre
4. ARREGLAR    con su test, como cualquier bug
5. APRENDER    qué lo dejó pasar
```

**Los pasos 1 y 2 van antes de saber qué pasó.** Cada minuto buscando la causa con el sistema
roto es daño acumulándose.

## Contener primero

De más rápido a más lento:

| Opción | Cuándo |
|---|---|
| **Apagar la funcionalidad** | Si se puede desactivar sin desplegar. La más rápida |
| **Volver atrás el despliegue** | Si empezó justo después de una entrega |
| **Arreglo caliente** | Sólo si es evidente y chiquito. Con test igual |

> **Volver atrás no es rendirse.** Es la decisión correcta la enorme mayoría de las veces: el
> sistema vuelve a andar en minutos y la causa se investiga sin gente esperando. El orgullo de
> "lo arreglo ya" cuesta horas de sistema caído.

**Ojo con la base:** si el despliegue incluyó una migración, volver el código **no** vuelve
los datos. Ver [migracion-de-base.md](migracion-de-base.md).

## Qué decir al avisar

En criollo, para gente que no es técnica:

| | |
|---|---|
| **Qué no anda**, en términos del negocio | "No se pueden cargar solicitudes nuevas", no "falla el endpoint POST" |
| **Desde cuándo** | |
| **A quiénes afecta** | Todos, o sólo un grupo |
| **Qué se está haciendo** | Y cuándo hay novedades |

Lo que **no** va: el detalle técnico, especulaciones sobre la causa, y **jamás datos de
personas**. Marcadores siempre.

## Entender, después

Con el sistema andando, el método normal: `trace_id`, logs correlacionados, qué cambió.
Ver [depurar.md](depurar.md).

La pregunta que más rinde: **¿qué cambió?** La enorme mayoría de los incidentes empiezan
justo después de algo — un despliegue, un cambio de configuración, un pico de tráfico, un
servicio externo que cambió.

## Cerrar bien

Un incidente contenido **no está cerrado**. Falta:

- [ ] El arreglo de verdad, **con su test**, siguiendo el ciclo normal.
- [ ] Si hubo arreglo caliente sin test: **registrado como deuda, con fecha**.
- [ ] Qué lo dejó pasar: ¿faltaba un test? ¿una alerta? ¿una validación?
- [ ] **Una mejora concreta** que lo habría evitado o detectado antes.

Ese último punto es el que convierte un incidente en algo útil. Si el resultado es sólo "ya
está arreglado", el mismo incidente vuelve en otra forma.

## Sobre las culpas

**Se busca qué falló en el sistema, no quién se equivocó.** Si alguien pudo romper producción
con un cambio, el problema es que el sistema lo permitió: faltaba un test, una puerta, una
revisión.

Un análisis que termina en un nombre no produce ninguna mejora, y garantiza que la próxima
vez nadie cuente lo que pasó.

## Nada de PHI, tampoco acá

Ni en el aviso, ni en las capturas, ni en el registro del incidente. Es el momento donde más
se filtra, porque pegar el caso real de la persona afectada parece lo más rápido para explicar.

Marcadores: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`,
`<dato-sensible>`.

## Qué es "crítico" — propuesta del método

Lo primero que hay que poder contestar sin discutir, a las tres de la tarde de un martes
complicado:

| Nivel | Qué significa | Respuesta |
|---|---|---|
| **Crítico** | El sistema no puede hacer su trabajo: no se puede cargar lo principal, o lo que se carga queda mal | Se atiende **ahora**, se avisa al equipo |
| **Alto** | Una funcionalidad caída pero con forma de seguir trabajando | Se atiende **en el día** |
| **Medio** | Molesta, hay cómo evitarlo | Entra al backlog con prioridad |
| **Bajo** | Cosmético o de borde | Backlog normal |

**El criterio que ordena los cuatro: ¿hay una persona afuera esperando algo que el sistema no
va a resolver?** Si la respuesta es sí, es crítico, sin importar cuántas personas afecte.

⚠ **Quién atiende, en qué horario, a quién se avisa y dónde se registran los incidentes lo
define el equipo** — son decisiones de organización, no de método, y no se proponen acá.

Lo que sí dice el método: **mientras no haya una persona nombrada por franja horaria, no hay
guardia.** "Lo vemos entre todos" quiere decir que no lo ve nadie.
