# back — el backend

El código del backend vive en **su propio repositorio de git**, y se **clona acá adentro**.
Esta carpeta no es el repositorio: es el lugar donde se lo enchufa.

```bash
git clone <url-del-repo-de-back> back/<nombre-del-repo>
```

**En una subcarpeta, no en `back/` directo**, y no es un detalle de estilo: `back/` ya tiene
adentro este README y los espejos de skills, así que `git clone ... back` falla con
*«destination path 'back' already exists and is not an empty directory»*. Es el mismo formato
que usa `front/` para sus apps, y el Doctor encuentra el repositorio igual — busca la raíz por
el archivo de build del stack, no por una ruta fija.

Lo clonado **no se versiona en este repositorio** — ya tiene el suyo: el código de la
aplicación no vive acá ([[decisiones#DEC-001]]). El `.gitignore` de la raíz ignora todo `back/`
salvo este README y los espejos de skills, que son lo único que este repositorio aporta a la
carpeta.

**Por qué se clona acá y no al lado.** Con el código adentro, un asistente lee en una sola
sesión el Cerebro Digital, las reglas del proyecto, la Tarea y el código que la implementa.
Al lado, cada una de esas cosas es un salto de contexto, y el que se saltea es siempre el
mismo: el conocimiento funcional.

Una vez clonado, el **Doctor** empieza a medir este repositorio solo — límites entre módulos,
contrato contra código, trazabilidad al ticket, puerta de seguridad (SAST) y puerta de calidad.
No hay nada que configurar (`doctor/README.md`). Mientras no haya código, no mide: la carpeta
sale **gris** («prometido: todavía sin código»), no verde.

## Estructura objetivo

```
back/                                   # <- acá se clona el repositorio del backend
├─ .claude/skills/   .agents/skills/   # skills scoped a este repo (espejos idénticos)
│     guiar-tdd          (el ciclo rojo-verde-refactor, con el runner de tests del repo)
│     verificar-tdd      (auditoría independiente de la evidencia)
│     auditar-codigo     (chequeos de entrega antes del Merge Request)
│     armar-swagger      (consolida el openapi.yaml + Spectral + Swagger UI)
│     diagnosticar-repo  (corre el Doctor y explica cómo leer su informe)
│     consultar-cerebro  (read-only, bajo pedido, una ficha por vez)
└─ <nombre-del-repo>/                   # el repositorio clonado
   ├─ openapi.yaml                      # contrato consolidado (lo genera armar-swagger)
   ├─ <código, con el layout que fije el stack>
   │  ├─ shared/{api/error,exceptions,infra/config}/   # transversal: no depende de ningún módulo
   │  ├─ <modulo-a>/{api,application,domain,infra,exceptions}/
   │  ├─ <modulo-b>/{api,application,domain,infra,exceptions}/
   └─ <migraciones de base de datos>/{shared,<modulo-a>,<modulo-b>}/   # una carpeta por módulo
```

Arquitectura: **monolito modular por módulos de dominio** ([[decisiones#DEC-002]]). Cada módulo
es dueño de un concepto de negocio y de sus tablas; adentro tiene cuatro capas más `exceptions/`:

- `api/` (los recursos HTTP + `dto/request/` y `dto/response/`) → `application`, `domain`.
- `application/` (`usecase/`, y las interfaces de salida `gateway/` y `repository/`) → `domain`.
- `infra/` (`client/<sistema>/`, `client/mock/`, `repository/`, `config/`) → `application`,
  `domain`: **implementa** las interfaces de `application/gateway` y `application/repository`.
- `domain/` → nada. La entidad persistida **es** el modelo de dominio (sin mapper): las
  anotaciones de persistencia del stack sí; el framework, la inyección de dependencias, la capa
  HTTP y los atajos del ORM, no.
- `exceptions/` la usan todas las capas del módulo y sólo depende de `shared.exceptions`.

**Entre módulos** se **llama** sólo a la `application` del otro (sus casos de uso), y se pueden
importar los tipos que devuelven o lanzan (`<otro>.domain`, `<otro>.exceptions`). **Prohibido**
importar `<otro>.api` y `<otro>.infra`. Una Tarea modifica **un solo módulo** (puede *usar*
otro por su `application`). `shared` lo usa cualquiera y no depende de ningún módulo.

En el código se dice **módulo**; en el tablero sigue siendo **vertical slice = Épica**. ⚠ Si
cada módulo es un slice o un slice reúne varios módulos lo decide el equipo; hasta entonces
queda abierto. Detalle completo: [[decisiones#DEC-002]] en el Cerebro.

## Cómo funcionan las skills acá

- Lo que está en `back/.claude/skills/` está **scoped a este repo**: gobierna cómo se
  desarrolla el código clonado acá, y no se mezcla con las skills del Cerebro, que viven en la
  raíz.
- `.claude/` y `.agents/` son **espejos idénticos**: la primera la lee Claude Code, la
  segunda Antigravity y opencode. Tienen que quedar byte-idénticos (el hook pre-commit los
  compara).

## Reglas de desarrollo

- **Test-primero, con evidencia.** No hay código de producción sin un test que haya
  fallado antes **en su aserción**. Detalle en `guiar-tdd`.
- **El contrato es la fuente.** Cada Tarea de capa `api` trae su fragmento OpenAPI;
  `armar-swagger` los consolida y valida. El front lo consume simulándolo.
- **Test de integración** sólo si la Tarea lo declara (dependencia externa real).
- **La verificación es independiente**: la corre `verificar-tdd`, no quien escribió el código.
- **El Cerebro Digital no se consulta por defecto.** La Tarea es autosuficiente. Sólo si se
  pide, y de a una ficha.

## Stack

Nada de esto lo fija el template: lo decide el equipo al crear el repositorio, y la tabla queda
para que no se dé por sobreentendido. Lo que sí está decidido es que el repositorio es **propio
y separado**, y se clona en esta carpeta ([[decisiones#DEC-001]]).

| Tema | Decisión | Estado |
|---|---|---|
| Lenguaje y framework | — | ⚠ a definir por el equipo |
| Herramienta de build | — | ⚠ a definir por el equipo |
| Harness de test (runner + cliente HTTP para los tests de API) | — | ⚠ a definir por el equipo |
| Versión del lenguaje y del framework | — | ⚠ a definir por el equipo. Se fijan al crear el repo y se pinnean |
| Umbral de cobertura | — | ⚠ a definir por el equipo. Es el número que la puerta de calidad va a exigir (abajo) |

## Antes del Merge Request

Dos cosas que no se saltean, y ninguna de las dos es opcional:

- **Puerta de seguridad (SAST).** El analizador estático de seguridad corre en el pipeline y
  tiene que **frenar la entrega**, no sólo avisar. Si una regla se suprime, la supresión lleva
  su motivo escrito al lado: una supresión sin justificación es un hallazgo tapado.
- **Puerta de calidad.** Cobertura, análisis estático y tests **exigidos por el build**.
  Una herramienta configurada que el build no corre es decoración. El **umbral de cobertura**
  es el que fije el equipo — ver la tabla de Stack, arriba; mientras esté ⚠, la puerta no tiene
  número que exigir.

El Doctor no reemplaza a ninguna de las dos —ésas hacen fallar el build, que frena mucho
más que un informe— pero sí verifica que estén puestas y que el pipeline las exija.
