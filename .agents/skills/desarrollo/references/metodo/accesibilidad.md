# Accesibilidad en el front

> Prioridad **ALTA** en todas las aplicaciones de front. Adaptado de `accessibility-audit` de
> `wshobson/commands` (MIT), [referencias-externas.md](../referencias-externas.md).

## Por qué acá pesa más que en otros lados

Las aplicaciones de gestión las usan **operadores durante una jornada entera** y, las de cara
afuera, **personas de todas las edades y condiciones**. Una pantalla que sólo se puede usar
con mouse y con buena vista deja gente afuera del sistema — y "la gente" incluye a quien
tiene que resolver un trámite que no puede esperar.

Además es la única dimensión de calidad que **no** se puede agregar al final: se diseña
adentro o se rehace.

## Los cuatro chequeos que cubren casi todo

| # | Qué | Cómo se verifica |
|---|---|---|
| 1 | **Todo se puede hacer con el teclado** | Se recorre la pantalla con Tab, sin tocar el mouse. Cada acción tiene que ser alcanzable |
| 2 | **Se ve dónde está el foco** | El elemento enfocado se distingue claramente. Sacar el contorno del foco "porque queda feo" es el error más común |
| 3 | **Todo elemento tiene nombre** | Un botón con sólo un ícono necesita texto accesible. Un campo necesita su etiqueta asociada de verdad, no un texto al lado |
| 4 | **El contraste alcanza** | Texto normal 4.5:1, texto grande 3:1 |

Con esos cuatro se resuelve la enorme mayoría de los problemas reales.

> **Es la misma inversión que la automatización.** Los agentes que generan pruebas leen la
> interfaz igual que un lector de pantalla: por elemento nativo, nombre y atributos. Por eso
> los estados dinámicos van como atributo (`aria-busy`, `aria-expanded`, `aria-invalid`), no
> sólo como color o animación.

## Los errores que más aparecen

| Error | Por qué importa |
|---|---|
| **El color como única señal** | "Los vencidos en rojo" no existe para quien no distingue rojo. Siempre **color + otra cosa**: un ícono, una palabra |
| **Un `div` que hace de botón** | No se enfoca, no responde a Enter y no se anuncia. Un botón es un botón |
| **Error de validación sólo en color** | El mensaje va en texto, asociado al campo |
| **Modal que no atrapa el foco** | Se abre y el Tab se va al fondo de la página |
| **Tabla sin encabezados de verdad** | Una grilla sin encabezados asociados es ilegible para un lector de pantalla |
| **Contraste en estado deshabilitado** | Suele ser el primero en bajarse, y es donde vive la información de por qué no se puede hacer algo |

## Cómo se prueba

**Automático — entra en la suite.** Un harness de test que busca por rol, por etiqueta y por
texto visible ya empuja en la dirección correcta: buscar así **es** probar accesibilidad. Si
un test no encuentra el botón por su rol y su nombre, un lector de pantalla tampoco.

Un chequeo automático de accesibilidad en la suite atrapa contraste, nombres faltantes y
estructura.

**Herramienta — ⚠ a definir por el equipo:** la herramienta de accesibilidad automática del
stack, anotada en `arquitectura/esqueleto-proyectos.md`. La propuesta del método es un motor
que cubra contraste, nombres faltantes y estructura, y que se use en dos lugares:

| Dónde | Con qué |
|---|---|
| En los tests de componente | Una aserción de "sin violaciones" por componente |
| En los de punta a punta | Un barrido de la pantalla entera, ya montada |

**Nivel exigido: WCAG 2.1 nivel AA.** Es el que toman como referencia las normas de
accesibilidad de sitios públicos, y el AAA no es alcanzable de forma realista en una app de
gestión.

> **Lo que el chequeo automático NO atrapa, y es la mitad del problema:** orden de foco
> ilógico, textos alternativos que existen pero no describen nada, y que la pantalla se pueda
> operar entera con el teclado. Eso se prueba a mano. Un chequeo automático en verde no es una
> pantalla accesible.

⚠ *Propuesta del método, a confirmar por el equipo.*

**A mano — lo que ninguna herramienta ve.** Una vez por pantalla, antes del Merge Request:
recorrerla **entera sólo con el teclado**. Si no se puede completar el flujo, es un
`HALLAZGO`. Tarda dos minutos y encuentra lo que las herramientas no pueden.

> Lo automático detecta alrededor de un tercio de los problemas reales. El resto necesita
> que alguien la use.

## Iconografía y colores

**Iconografía SVG profesional y cero emojis en la interfaz** — que además coincide con lo que
ya manda `cerebro-mockup-design`. Un emoji lo lee un lector de pantalla con su nombre
completo, y queda ridículo.

Los **design tokens** —los de la organización o los del design system propio; ⚠ cuáles mandan
es decisión de equipo— traen los colores ya definidos. Si una combinación no llega al
contraste, **eso se reporta**, no se acepta porque venga de arriba.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Los cuatro chequeos pasan, y la pantalla se recorrió con teclado |
| **HALLAZGO** | Algo no se alcanza con teclado, falta un nombre, o el contraste no llega |
| **SIN DATOS** | **No se probó con teclado**, o el chequeo automático no corrió |

Ese `SIN DATOS` es el normal mientras la herramienta no esté definida. Se reporta así — no se
omite.
