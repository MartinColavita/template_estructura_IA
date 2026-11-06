# Entender código que no escribiste

> Prioridad **MEDIA**, pero es lo primero que hace cualquiera que se suma.
> Adaptado de `code-explain` y `onboard` de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## El orden, de afuera hacia adentro

Leer un archivo al azar y seguir imports es la forma más lenta. El orden que funciona:

```
1. QUÉ HACE      el README del repositorio y el openapi.yaml
2. QUÉ MÓDULOS   las carpetas de primer nivel: son los conceptos de negocio (+ shared)
3. UN FLUJO      elegir UNO y seguirlo entero: api -> application/usecase -> domain -> infra
4. LOS TESTS     dicen qué se espera, mejor que el código
5. EL HISTORIAL  por qué quedó así
```

## Los tests son la mejor documentación

Y son la única que **no puede estar desactualizada**: si el código cambia y el test no, el
test falla.

Para entender qué hace una clase, leer sus tests antes que su código: dicen qué entra, qué
sale y qué casos borde alguien consideró importantes.

## El historial contesta el "por qué"

Cuando algo se ve raro, la pregunta casi nunca es *qué hace* sino *por qué está así*. Y eso no
está en el código:

- **Quién tocó esta línea y en qué commit** — el mensaje suele explicarlo.
- **El `#ID` de la Tarea** en ese commit — ahí está el contrato y el porqué.
- **El Merge Request** — ahí está la discusión.

Esa cadena código → commit → Tarea → documento del Cerebro es toda la razón por la que
pedimos trazabilidad. Cuando funciona, contesta en dos minutos lo que si no requiere
interrumpir a alguien.

## Las cuatro preguntas antes de tocar

| Pregunta | Dónde se contesta |
|---|---|
| **¿En qué módulo vivo?** | La carpeta de primer nivel |
| **¿Qué entra y qué sale?** | El `openapi.yaml` |
| **¿Qué reglas aplican?** | Las `[RN-…]` que cita la Tarea |
| **¿Qué se rompe si me equivoco?** | Los tests. Si no hay, ésa es la primera señal |

## La arquitectura, en una pantalla

```
<modulo>/
├─ api/           habla HTTP: un punto de entrada por recurso. Traduce el pedido a un comando. No decide nada
├─ application/   usecase/ (un caso de uso por clase; orquesta, no decide reglas),
│                 gateway/ (interfaces a externos), repository/ (interfaces a la base propia)
├─ domain/        acá viven las reglas y el modelo de dominio. Sin framework ni contenedor de inyección
├─ exceptions/    las excepciones del módulo
└─ infra/         client/, repository/, config/: las implementaciones
```

Estructura completa: [[decisiones#DEC-002]].

**Ningún módulo importa la `api` ni la `infra` de otro.** Si necesita otro módulo, lo llama
sólo por su `application`. Es la regla que sostiene todo lo demás: mientras se respete, se
puede entender un módulo sin leer los otros.

## Si la aplicación es ajena de verdad (no hay Tarea, no hay Cerebro)

Entonces no es «entender para una Tarea»: es ingeniería inversa, y tiene su método en
[ingenieria-inversa.md](ingenieria-inversa.md): inventario y radiografía por script, lectura por
módulo de lo que la radiografía señala, marca de confianza por afirmación y matriz de cobertura.

## Lo que NO hay que hacer

- **No leer todo antes de empezar.** Un módulo alcanza para una Tarea.
- **No "mejorar" lo que no entendés.** Si te parece raro, primero averiguá por qué está así.
  Suele haber un motivo, y a veces está escrito.
- **No preguntar antes de mirar el historial.** La mitad de las preguntas están contestadas
  en un mensaje de commit.

## Consultar el Cerebro Digital

**No se consulta por defecto.** La Tarea es autosuficiente: trae el contrato y la lista de
tests. Sólo si hace falta contexto de negocio, y **de a una ficha por vez**.

Es a propósito: el Cerebro es grande, y cargarlo entero llena el contexto de cosas que no
hacen falta para escribir el endpoint.

## Cuando alguien se suma al equipo

Lo mínimo para arrancar, en orden:

1. Clonar el repositorio. **No hay nada que instalar**: las skills viajan en el clone.
2. Correr el instalador: `python -I bin/instalar.py` (activa el hook, materializa los agentes y verifica los espejos).
3. Leer `AGENTS.md` — las reglas y las barreras.
4. Leer el `README.md` del repositorio de código donde vaya: el back, o el front que
   corresponda.
5. Correr la suite de tests **antes de tocar nada**, para saber cómo se ve el verde.

Ese último paso evita la confusión más común: no saber si algo ya estaba roto.
