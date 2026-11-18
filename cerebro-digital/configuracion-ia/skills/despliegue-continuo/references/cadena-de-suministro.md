# La cadena de suministro del pipeline

> La carga [[despliegue-continuo]] cuando el pedido es fijar dependencias del pipeline, armar el SBOM, firmar o
> atestar un artefacto, o configurar las actualizaciones automáticas. Las dependencias **de la aplicación**
> (licencias, vulnerabilidades, actualizar de a una) están en
> `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/dependencias-y-config.md`; escanearlas es de
> [[seguridad]]. Qué se decide y con qué herramienta, en `DEC-007` ⚠.

## Por qué: lo que pasó

En marzo de 2025 se comprometieron dos acciones de GitHub muy usadas (`tj-actions/changed-files` y una de
`reviewdog`): alguien movió sus etiquetas a un código que **imprimía los secretos del pipeline en el log**. Los
pipelines que las llamaban por etiqueta corrieron ese código sin que nadie cambiara nada; la autoridad de
ciberseguridad de Estados Unidos pidió revisar qué versión había corrido y **rotar todos los secretos**. Las
lecciones que quedan:

1. **Una etiqueta se mueve; un SHA completo, no.** Lo que se revisó tiene que ser lo que corre.
2. **Fijar no es auditar**: un SHA fija lo que había, bueno o malo. Por eso, pocas acciones de terceros, y las que
   quedan, de fuentes conocidas.
3. **Lo que no está en el pipeline no se puede robar desde el pipeline**: identidad federada en lugar de claves de
   larga vida (P5 de `bin/verificar-pipeline.py`).
4. **Ante un compromiso, se rota todo lo que el pipeline pudo leer.** Rotar lo hace una persona ([[AGENTS]]).

## Fijar

| Plataforma | Qué se fija | Cómo |
|---|---|---|
| **GitHub** | Acciones y workflows reutilizables | Por **SHA completo** (40 caracteres) con la versión en un comentario: `uses: <dueño>/<acción>@<sha> # v4.4.0`. O un **lockfile** (`.github/workflows/actions.lock`, lo genera la extensión `gh actions-lock`), que cubre también las dependencias de las dependencias, pero **no** los workflows reutilizables: esos van siempre por SHA |
| **GitLab** | `include` y componentes | `include` de proyecto con `ref` a un SHA o a una versión completa; componentes sin `~latest` |
| **Azure** | Repositorios de plantillas | `resources.repositories` con `ref: refs/tags/...` o un SHA. Las tareas (`Tarea@2`) no se pueden fijar por SHA: se usan las mínimas y se dice |
| **Las tres** | Imágenes de contenedor | Por **digest** (`@sha256:...`). Sin digest es AVISO, porque una imagen oficial se reconstruye con parches |

**De dónde sale el SHA.** Del repositorio **de la acción**, nunca de un fork: se resuelve la etiqueta de la versión
exacta (`v4.4.0`, no `v4`) en la API pública del repositorio y, si la etiqueta es anotada, se sigue hasta el commit.
Si no se puede confirmar, la línea no se cambia y se dice. Herramientas que lo hacen solas, por máquina: `pinact` o
la extensión del lockfile. GitHub permite además **exigir** el fijado por política: lo configura una persona.

## Actualizar, con espera

- **Una sola herramienta**: Dependabot si el código está en GitHub (actualiza también acciones y workflows
  reutilizables, y por defecto espera unos días antes de proponer una versión nueva); **Renovate** si está en Azure
  Repos o en GitLab, donde Dependabot sólo existe como extensión de terceros. Nunca las dos a la vez.
- **Con espera mínima** antes de proponer una versión recién publicada: una versión comprometida suele detectarse
  en pocos días.
- **Cada propuesta es un Merge Request más**: pasa por el método de [[desarrollo]] y por
  `bin/verificar-pipeline.py`. Ninguna se mergea sola.

## SBOM: qué hay adentro

- Un **SBOM** (la lista de componentes del artefacto) se genera **en el pipeline**, de la imagen o de la carpeta
  construida. Una herramienta alcanza: Syft, en formato **CycloneDX** (estándar abierto) o SPDX.
- El SBOM viaja **con** el artefacto (como adjunto o dentro de la atestación); no se versiona en el repositorio del
  Cerebro.
- Buscar vulnerabilidades en ese SBOM es de [[seguridad]].

## Firma o atestación: de dónde salió

| Nivel (SLSA, pista de build) | Qué pide | Para este template |
|---|---|---|
| L1 | Que haya procedencia: un registro de cómo se construyó | Mínimo |
| **L2** | Que la genere y la firme **la plataforma** que construye | **Objetivo de arranque** (⚠ `DEC-007`) |
| L3 | Build aislado, y la clave de firma fuera del alcance de los pasos | Más adelante; no desde el día uno |

- **En GitHub**: la atestación de la plataforma (`actions/attest`, con los permisos `id-token: write`,
  `attestations: write` y `contents: read` sólo en ese job); se verifica con `gh attestation verify`.
- **Fuera de GitHub**: `cosign` **sin claves** (firma con la identidad federada del pipeline y un certificado de
  vida corta). Administrar claves de firma propias no es para arrancar.
- **Verificar antes de promover** (`gh attestation verify` o `cosign verify`) lo hace el pipeline del despliegue o
  una persona. `bin/gate-despliegue.py` **no** lo verifica (lo declara en lo que no mira).
- Firmar no dice que el código sea bueno: dice **de dónde salió**.

## Publicar es salir del repositorio

Publicar un release, un tag firmado o una imagen en un registro es **G4**: un «sí» sobre lo que se publica, en su
propio turno ([[AGENTS]]). Crear, rotar o leer las credenciales del registro o de la firma, nunca la IA.

## La pregunta, en criollo

*«Voy a cambiar las tres acciones del pipeline para que queden fijadas por su código exacto en lugar de por la
etiqueta, que se puede mover. Confirmé cada una en el repositorio oficial de la acción; el pipeline hace lo mismo
que antes. Va en un Merge Request. ¿Lo armo?»*

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | P2 sin HALLAZGO, una sola herramienta de actualización con espera, y SBOM y atestación donde `DEC-007` los pide |
| **HALLAZGO** | Una acción, un `include` o una plantilla por referencia movible; una credencial de larga vida donde hay identidad federada |
| **SIN DATOS** | `DEC-007` sin decidir la cadena; una atestación que nadie verificó; un SHA que no se pudo confirmar |
