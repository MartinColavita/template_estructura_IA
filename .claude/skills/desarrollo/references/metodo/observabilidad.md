# Observabilidad — que el sistema cuente qué le pasa

> Prioridad **ALTA**. Las cuatro patas las trae el stack; lo que falta es usarlas bien.
> Adaptado de `monitor-setup` y `slo-implement` de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## Ya viene medio resuelto, y conviene saberlo

Las cuatro patas de la observabilidad las provee el stack con sus librerías, anotadas en
`arquitectura/esqueleto-proyectos.md` (⚠ cuáles, lo fija el proyecto al elegir el stack):

| Pata | Qué habilita |
|---|---|
| **Métricas** | Las cuatro señales de abajo, expuestas para que un recolector las lea |
| **Trazas distribuidas** | `trace_id`, `span_id`: seguir un pedido entre servicios |
| **Logs estructurados** | El log como objeto con campos, no como frase |
| **Chequeos de salud** | Liveness y readiness |

**Las cuatro patas tienen que estar en todo servicio.** Lo que falta no es instalarlas: es
**usarlas bien**, que es lo que cubre este documento.

## Las cuatro señales que importan

No hace falta medir todo. Con estas cuatro se detecta casi cualquier problema:

| Señal | Qué se mide |
|---|---|
| **Latencia** | Percentiles 50, 95 y 99. **El promedio miente**: esconde la cola larga que sufre el usuario |
| **Tráfico** | Pedidos por segundo, conexiones activas |
| **Errores** | Tasa de error y conteo **por tipo**, no un total |
| **Saturación** | CPU, memoria, profundidad de cola |

> **Por qué percentiles y no promedio.** Con 99 respuestas de 50 ms y una de 10 segundos, el
> promedio da 150 ms y parece sano. El percentil 99 dice 10 segundos, que es lo que
> efectivamente le pasó a alguien.

## Logs estructurados: qué campos, sí o sí

Con logs estructurados el log es un objeto, no una frase. Los campos mínimos:

| Campo | Para qué |
|---|---|
| `@timestamp`, `level`, `message` | Lo básico |
| `service`, `version`, `environment` | Saber **cuál** de los servicios habla |
| **`trace_id`, `span_id`** | **Seguir un pedido entre servicios.** Sin esto, depurar es adivinar |
| `request_id`, `method`, `path`, `status_code`, `duration` | Correlacionar con la métrica |
| Tipo de error y traza, cuando hay error | Diagnóstico |

**Un log sin `trace_id` en una arquitectura de servicios es un log que no sirve.** Ver
[depurar.md](depurar.md).

## Lo que NUNCA va en un log

Los logs se centralizan y los ve gente fuera del equipo. Es el lugar donde más se escapa PHI:

- **Nada de datos de personas.** Marcadores: `<persona>`, `<documento>`, `<identificador>`,
  `<telefono>`, `<direccion>`, `<dato-sensible>`.
- **Nada de credenciales ni tokens.**
- **Ni el cuerpo completo** de un pedido que pueda traerlos.

Registrar un acceso a dato sensible **sí** corresponde —quién, cuándo, para qué—; **el dato
en sí, no**.

## Alertas: pocas y que se puedan atender

El peor resultado no es no tener alertas: es tener tantas que nadie las mira. Cuando una
alerta suena todos los días y nunca pasa nada, el equipo aprende a ignorarla — y el día que
es de verdad, también la ignora.

| Nivel | Cuándo | Qué se espera |
|---|---|---|
| **Crítica** | El sistema no está haciendo su trabajo | Alguien lo mira **ahora** |
| **Advertencia** | Va camino a romperse | Se mira en el día |
| **Informativa** | Queda registrado, no suena | Se ve en el tablero |

Tres reglas para que sirvan:

1. **Una alerta que nadie va a atender no se crea.** Si no hay acción posible, es un gráfico,
   no una alerta.
2. **Si suena la crítica, se callan las advertencias del mismo servicio.** Un incidente manda
   una alerta, no cuarenta.
3. **Se alerta sobre ventanas, no sobre picos.** "5% de errores sostenido 10 minutos", no
   "un error".

**Propuesta del método**, como punto de partida — se ajustan con datos reales, no antes:

| Señal | Advertencia | Crítica |
|---|---|---|
| **Tasa de error** | >1% sostenido 10 min | >5% sostenido 5 min |
| **Latencia (p95)** | >2× lo normal, 10 min | >4× lo normal, 5 min |
| **Saturación** | >70% de CPU o memoria, 15 min | >90%, 5 min |
| **Disponibilidad** | — | El chequeo de salud falla 3 veces seguidas |

> **Por qué son múltiplos y no milisegundos.** "El p95 pasó de 200 ms a 800 ms" es un problema
> real en un endpoint rápido y ruido en uno que consolida un reporte. Hasta tener la línea base
> medida, un umbral relativo avisa y uno absoluto miente.

⚠ *Propuesta del método. Los números finales salen de medir, y se revisan al mes de producción.*

## Chequeos de salud

El chequeo de salud del stack expone dos, y **no son lo mismo**:

- **Liveness** — ¿el proceso está vivo? Si falla, se reinicia. **No debe consultar la base**:
  si la base se cae, reiniciar el servicio no arregla nada y empeora todo.
- **Readiness** — ¿puede atender pedidos? Acá sí se miran las dependencias. Si falla, deja
  de recibir tráfico pero no se reinicia.

Confundirlas produce el reinicio en cadena clásico: se cae la base, todos los servicios
fallan el liveness, todos se reinician, y la base recibe una avalancha de reconexiones.

## Qué es un problema, definido antes

Antes de alertar hay que saber qué es "estar bien". Eso se declara, no se descubre:

- **Objetivo**: "el 99% de las consultas del listado principal responden en menos de 1
  segundo".
- **Presupuesto de error**: lo que queda del 1%. Mientras haya presupuesto, se sigue
  entregando; cuando se agota, se frena y se estabiliza.

**Propuesta del método:**

| Objetivo | Valor |
|---|---|
| **Disponibilidad** | 99,5% mensual — deja ~3,5 horas de presupuesto de error al mes |
| **Latencia de lectura** (consultas, listados) | p95 < 1 segundo |
| **Latencia de escritura** (alta, modificación) | p95 < 2 segundos |
| **Errores del servidor** | < 0,5% de los pedidos |

**Horario que cuenta:** el de la jornada en que se usa el sistema, no 24×7 — es un sistema
que usan personas en su horario de trabajo. Medir contra 24×7 infla la disponibilidad y
esconde las caídas del horario que importa.

⚠ *Propuesta del método, a confirmar por el equipo.*

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Las cuatro patas presentes, logs con `trace_id`, alertas con dueño |
| **HALLAZGO** | Falta una pata, logs sin `trace_id`, o **PHI en un log** (bloqueante) |
| **SIN DATOS** | No se pudo verificar qué expone el servicio |
