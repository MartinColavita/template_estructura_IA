# front — los frontends

El código de **cada** aplicación de front vive en **su propio repositorio de git**, y se
**clona acá adentro**. Esta carpeta no es el repositorio: es el lugar donde se los enchufa.

```bash
git clone <url-del-repo-de-esa-app> front/<nombre-de-la-app>
```

**Una app por subcarpeta, no en `front/` directo**, y no es un detalle de estilo: `front/` ya
tiene adentro este README y los espejos de skills, así que `git clone ... front` falla con
*«destination path 'front' already exists and is not an empty directory»*. Es el mismo formato
que usa `back/`, y el Doctor encuentra cada app igual — busca la raíz por el archivo de build
del stack, no por una ruta fija.

Lo clonado **no se versiona en este repositorio** — cada app ya tiene el suyo: el código de la
aplicación no vive acá ([[decisiones#DEC-001]]). El `.gitignore` de la raíz ignora todo
`front/` salvo este README y los espejos de skills, que son lo único que este repositorio
aporta a la carpeta.

**Por qué se clona acá y no al lado.** Con el código adentro, un asistente lee en una sola
sesión el Cerebro Digital, las reglas del proyecto, la Tarea y el código que la implementa.
Al lado, cada una de esas cosas es un salto de contexto, y el que se saltea es siempre el
mismo: el conocimiento funcional.

Una vez clonadas, el **Doctor** empieza a medir cada app sola, sin configurar nada, y detecta
cuántas hay: no está atado a un número fijo (`doctor/README.md`). Mientras no haya código, no
mide: la carpeta sale **gris** («prometido: todavía sin código»), no verde.

## Estructura objetivo

```
front/                                  # <- acá se clona el repo de cada app
├─ .claude/skills/   .agents/skills/   # skills COMPARTIDAS por todas las apps (espejos idénticos)
│     guiar-tdd          (el ciclo rojo-verde-refactor, con el runner de tests del front y la API simulada desde el contrato)
│     verificar-tdd      (auditoría independiente de la evidencia)
│     auditar-codigo     (chequeos de entrega antes del Merge Request)
│     diagnosticar-repo  (corre el Doctor y explica cómo leer su informe)
│     consultar-cerebro  (read-only, bajo pedido, una ficha por vez)
│     <skills propias del stack>  (las que agregue el equipo —crear o testear un componente, etc.— van acá, compartidas)
└─ <una carpeta por app clonada>        # un repositorio separado por app
   ├─ <app-a>/
   ├─ <app-b>/
   └─ <app-n>/
```

## Cómo funcionan las skills acá

- Lo que está en `front/.claude/skills/` lo ven **todas las apps** (es lo compartido).
- Si una app necesita una variante propia, la define en su carpeta y **pisa** a la
  compartida sólo para esa app (gana la más específica).
- `.claude/` y `.agents/` son **espejos idénticos**: la primera la lee Claude Code, la
  segunda Antigravity y opencode. Tienen que quedar byte-idénticos (el hook pre-commit los
  compara).

## Reglas de desarrollo

- **Test-primero, con evidencia.** No hay código de producción sin un test que haya
  fallado antes **en su aserción**. Detalle en `guiar-tdd`.
- **El contrato manda.** Las llamadas a la API se simulan a partir del `openapi.yaml` que
  consolida el back. Nunca se inventa la forma de una respuesta.
- **La verificación es independiente**: la corre `verificar-tdd`, no quien escribió el código.
- **El Cerebro Digital no se consulta por defecto.** La Tarea es autosuficiente (contrato
  + tests). Sólo si se pide, y de a una ficha.

## Stack

Nada de esto lo fija el template: lo decide el equipo al crear el primer repositorio, y la
tabla queda para que no se dé por sobreentendido. Lo que sí está decidido es que cada app tiene
**repositorio propio y separado**, clonado en esta carpeta ([[decisiones#DEC-001]]).

| Tema | Decisión | Estado |
|---|---|---|
| Lenguaje y framework | — | ⚠ a definir por el equipo |
| Herramienta de build | — | ⚠ a definir por el equipo |
| Harness de test (runner + simulación de la API desde el contrato) | — | ⚠ a definir por el equipo |
| Versiones del lenguaje, del framework y del build | — | ⚠ a definir por el equipo. Se fijan al crear el primer repo y se pinnean |
| Umbral de cobertura | — | ⚠ a definir por el equipo |
| Librería de componentes | — | ⚠ a definir por el equipo. Antes de elegir una de afuera, preguntar qué hay publicado en el registro interno de {{ORGANIZACION}}, si lo tiene |
| Cuántas apps, y cómo se llaman | — | ⚠ a definir por el equipo |

## Antes del Merge Request

Lo mismo que rige en el back, adaptado: la **puerta de seguridad (SAST)** corriendo en el
pipeline y frenando la entrega, y la **puerta de calidad** —linter, chequeo de tipos en modo
estricto si el lenguaje lo tiene, umbral de cobertura— **exigida por el build**. Una herramienta
configurada que el build no corre es decoración: da la sensación de que la calidad está cubierta
sin cubrir nada.
