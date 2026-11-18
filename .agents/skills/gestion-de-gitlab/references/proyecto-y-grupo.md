# Proyecto y grupo: lo que tiene que estar configurado, las identidades y lo que no se escribe

> Fuentes: documentación oficial de GitLab (roles, ramas y tags protegidos, aprobaciones, push rules, CI/CD,
> tokens, acciones rápidas, cierre automático). Detalle en
> `cerebro-digital/devops/fuentes-gitlab.md`.

Esta lista la **mide** `bin/auditar-gitlab.py proyecto` (o `grupo`): cada fila tiene su chequeo. Lo que falta se
arregla con **el cambio exacto** de la puerta, que aplica una persona; la IA no toca la configuración. Los nombres de
pantalla son los de la interfaz en inglés, que es como aparecen en GitLab.

## El proyecto

| Ajuste | Dónde | Valor | Por qué | Plan | Chequeo |
|---|---|---|---|---|---|
| Rama por defecto protegida | Settings > Repository > Protected branches | Existe la regla | Sin ella, cualquier Developer empuja y mergea | Free | `rama-defecto-protegida` |
| Quién empuja directo | La misma regla, «Allowed to push and merge» | «No one» (o, como mínimo, Maintainers) | Quien empuja directo se saltea el Merge Request y las aprobaciones | Free | `push-directo` |
| Quién mergea | La misma regla, «Allowed to merge» | Maintainers | En Free es **la** barrera sobre el merge: la IA es Developer | Free | `merge-a-rama-defecto` |
| Force push | La misma regla | Apagado | Reescribe la historia | Free | `force-push` |
| Tags de versión protegidos | Settings > Repository > Protected tags | `v*`, los crean Maintainers | El tag lanza el pipeline con lo protegido | Free | `tags-protegidos` |
| El pipeline tiene que pasar · hilos resueltos | Settings > Merge requests > Merge checks | Encendidos | No se mergea en rojo ni con una revisión abierta | Free | `pipeline-debe-pasar`, `hilos-resueltos` |
| Cierre automático de issues | Settings > Repository > Branch defaults, «Auto-close referenced issues on default branch» | Apagado | Una palabra de cierre cambiaría un issue por afuera de los GATEs | Free | `cierre-automatico` |
| Rol mínimo para variables de pipeline | Settings > CI/CD > Variables, «Minimum role to use pipeline variables» | `no_one_allowed` (o `maintainer`) | Una variable de pipeline pisa las del YAML | Free | `variables-de-pipeline` |
| Cachés separadas | Settings > CI/CD > General pipelines | Encendido | Una rama no protegida no envenena la caché de la protegida | Free | `caches-separadas` |
| Despliegues viejos | Settings > CI/CD > General pipelines, «Prevent outdated deployment jobs» | Encendido | Un job viejo no vuelve atrás lo que desplegó uno nuevo | Free | `despliegues-viejos` |
| Lista de permitidos del job token · push con job token | Settings > CI/CD > Job token permissions | Lista activa; push apagado | Otro proyecto no usa su job token contra este; un job no cambia el código | Free | `job-token-lista`, `job-token-push` |
| Pipelines de forks en el padre | Sólo por API (`ci_allow_fork_pipelines_to_run_in_parent_project`) | Apagado en proyectos públicos o internos | Por la API no hay advertencia | Free | `forks-en-el-padre` |
| Deploy keys | Settings > Repository > Deploy keys | Sin escritura, salvo decisión escrita | Una deploy key con escritura empuja sin pasar por nadie | Free | `deploy-keys-escritura` |
| Aprobaciones requeridas | Settings > Merge requests > Merge request approvals | Una regla con 1 o más | Que nadie mergee sin una aprobación | Premium | `aprobaciones-requeridas` |
| El autor no aprueba · quien commiteó no aprueba | El mismo lugar, «Approval settings» | Encendidos | Quien produce no aprueba | Premium | `autor-no-aprueba` |
| CODEOWNERS exigido | La regla de la rama protegida, «Code owner approval» | Encendido, con el archivo ([molde](../assets/CODEOWNERS.ejemplo)) | Los cambios al pipeline los aprueba quien corresponde | Premium | `codeowners-exigido` |
| Push rules contra secretos | Settings > Repository > Push rules, «Prevent pushing secret files» | Encendido | El servidor frena un archivo de secretos | Premium | `push-rules-secretos` |
| Ambiente de producción protegido | Settings > CI/CD > Protected environments | Con al menos una aprobación | La barrera de producción en la plataforma | Premium | `produccion-protegida` |

**Además lo informa el script** (AVISO, para criterio): que el token con que corrió pase de Developer
(`rol-del-token`) y que un proyecto que despliega a producción tenga habilitados los runners de instancia
(`runners-de-instancia`).

## El grupo

| Ajuste | Dónde | Valor | Por qué | Plan | Chequeo |
|---|---|---|---|---|---|
| 2FA para los miembros | Settings > General > Permissions and group features | Encendido | Una cuenta sin 2FA es la puerta más barata | Free | `2fa-del-grupo` |
| Quién crea proyectos | El mismo lugar, «Roles allowed to create projects» | Maintainers (o nadie) | Con Developer, la identidad de la IA también crea | Free | `crear-proyectos` |
| Protección por defecto de la rama principal | Settings > Repository, «Default branch» | Empujan y mergean Maintainers, sin force push | Los proyectos nuevos nacen protegidos | Free | `proteccion-por-defecto` |
| Visibilidad | Settings > General | Privado o interno | Un grupo público muestra sus proyectos públicos | Free | `visibilidad` |
| Push rules del grupo | Settings > Repository > Push rules | «Prevent pushing secret files» | Valen para los proyectos nuevos del grupo | Premium | `push-rules-de-grupo` |

**La membresía se hereda hacia abajo y un subgrupo no puede dar un rol menor que el heredado**: la identidad de la IA
no se agrega arriba en el árbol de grupos, sino en el proyecto o el subgrupo que la necesita.

## Tokens e identidades

| Token | Prefijo | Qué alcanza | Uso |
|---|---|---|---|
| Personal de **permisos finos** (19.2 o más, todos los planes) | ⚠ sin confirmar | Los recursos y permisos elegidos, en los proyectos elegidos; cada pedido pasa el permiso del token **y** el de la persona | **La identidad de la IA**: uno por persona |
| Personal clásico | `glpat-` | **Todo lo que la persona alcanza**, según el scope | No es la identidad de la IA; con alcance `api`, **nunca** |
| De acceso de proyecto o de grupo | `glpat-` | Un proyecto o un grupo, con un rol; cada token crea su usuario bot | La identidad de la IA donde no hay tokens finos (instancia anterior a la 19.2): uno de **proyecto**, rol Reporter para leer y Developer para escribir |
| Deploy token · deploy key | `gldt-` · — | Leer el repositorio y los registros · un repositorio por SSH | Que un servidor o Flux traigan código o imágenes; con escritura, sólo por decisión escrita |
| Job token | `glcbt-` | Lo de quien disparó, en endpoints listados, mientras dura el job | Dentro del pipeline, antes que cualquier token personal |
| De runner, de trigger, de agente | `glrt-`, `glptt-`, `glagent-` | Tomar jobs, disparar pipelines, conectar un cluster | **Nunca los ve la IA** |

Reglas (las fija `DEC-010`):

- **La identidad de la IA no pasa de Developer** (Planner si sólo escribe en el tablero) y **nunca** es el token
  personal clásico con alcance `api`: con el de una persona con más rol, la IA podría desproteger una rama. Donde no
  hay tokens de permisos finos, es un token de acceso de proyecto (Reporter para leer, Developer para escribir).
- **El push de la rama sale con la credencial git de la persona**: si es Maintainer u Owner, la protección de la
  rama no frena ese push, y eso se declara (no se da por cubierto).
- **Sólo los proyectos del destino** (el de permisos finos, uno por persona). Lectura: permisos de lectura, **sin el recurso de variables**
  (y «MCP tool: Execute» si se usa el MCP oficial). Escritura, si se habilita: crear y actualizar Merge Requests,
  notas e issues; **sin** aprobar, mergear, proteger, variables ni miembros.
- **Modo solo:** la persona es Owner de todo y su token clásico también; la barrera se conserva con un token de
  permisos finos (o uno de acceso de proyecto), que no puede lo que la persona sí puede.
- El token va en la variable `GITLAB_TOKEN`, por referencia: cómo, en
  `cerebro-digital/configuracion-ia/integracion-gitlab-mcp/00-index.md`. Si se filtró, se revoca: borrarlo no alcanza.

## Lo que no se escribe en GitLab

**Palabras de cierre.** `Close`, `Fix`, `Resolve` e `Implement`, en todas sus formas, seguidas de `#N`,
`grupo/proyecto#N` o la URL de un issue, en un commit o en la descripción de un Merge Request, **cierran el issue**
cuando el commit llega a la rama por defecto. Apagar el ajuste del proyecto no cubre los issues de otros proyectos.
Se enlaza con `Related to #N` (y con Azure Boards, `AB#N` sin verbo).

**Acciones rápidas.** Una línea que empieza con `/` en una descripción o un comentario **se ejecuta al guardar**:
`/merge`, `/approve`, `/close`, `/assign`, `/label`, `/target_branch`… Una plantilla de descripción también puede
traerlas. Rompen la regla de la tarjeta congelada («sólo se comenta»).

**Opciones de push.** `git push -o ci.skip`, `-o merge_request.auto_merge`, `-o secret_push_protection.skip_all`
saltean un control: nunca. Abrir un Merge Request con `-o merge_request.create` es una escritura en GitLab: va con su «sí».

**Cómo se mide.** Antes de mostrar el preview de cualquier texto que se va a escribir en GitLab (descripción,
comentario, issue), se guarda en `borrador/gitlab/` y se corre:

```
python -I bin/auditar-gitlab.py texto borrador/gitlab/<archivo>.md
```

Mira palabras de cierre, acciones rápidas, prefijos de token y datos personales. Un HALLAZGO se corrige antes de
preguntar; el script no reemplaza la lectura de la persona.

## Los moldes para un repositorio de código

| Molde | Va en el repositorio de código como | Plan |
|---|---|---|
| [merge-request-default.md](../assets/merge-request-default.md) | `.gitlab/merge_request_templates/Default.md` | Free |
| [CODEOWNERS.ejemplo](../assets/CODEOWNERS.ejemplo) | `.gitlab/CODEOWNERS` | Premium (en Free el archivo no frena nada) |

Entran como cualquier cambio de código, por [[desarrollo]]. La descripción completa del Merge Request y su checklist
están en `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/merge-request.md`.
