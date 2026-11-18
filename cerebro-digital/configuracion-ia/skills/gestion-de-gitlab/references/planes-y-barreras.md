# Qué da cada plan, y qué barrera reemplaza a la que no da

> Fuentes: la documentación oficial de GitLab, leída para la investigación de la función. Detalle y fechas en
> `cerebro-digital/devops/fuentes-gitlab.md`.

Los planes son los mismos en GitLab.com y en una instancia propia: **Free, Premium y Ultimate**. **Casi todas las
barreras de GitLab dependen del plan**, y una skill no puede prometer lo que el plan no da. El plan está en la ficha
«GitLab del proyecto» (columna Plan de «Destino autorizado»); `bin/auditar-gitlab.py` marca **NO DISPONIBLE EN EL
PLAN** lo que el plan no da, no lo pide, y no lo cuenta como OK.

## Proyecto y grupo

| Barrera | Free | Premium | Ultimate |
|---|---|---|---|
| Rama protegida: quién empuja y quién mergea, **por rol**; «No one» para el push; sin force push | Sí | + por usuario o grupo; + exigir CODEOWNERS; + ramas protegidas de grupo; + limitar quién desprotege (sólo por API) | Igual |
| Tag protegido, por rol | Sí | + por usuario o grupo | Igual |
| Aprobaciones de Merge Request | **Opcionales**: cualquier Developer aprueba, pero no frenan el merge | Requeridas, con reglas; «el autor no aprueba» y «quien commiteó no aprueba» | + aprobación según el resultado de los escaneos |
| CODEOWNERS | No | Sí | Sí |
| Push rules (rechazar secretos en archivos, formato de mensaje) | No | Sí | Sí |
| «El pipeline tiene que pasar» y «hilos resueltos» para mergear; auto-merge | Sí | Sí | Sí |
| Plantillas de descripción (`.gitlab/merge_request_templates/`) | Sí | + de grupo y de instancia | Igual |
| Marcos de cumplimiento · políticas de seguridad | No | Marcos | + políticas |

## CI/CD

| Barrera | Free | Premium | Ultimate |
|---|---|---|---|
| Variables protegidas (sólo en ramas y tags protegidos), enmascaradas, ocultas | Sí | + alcance de ambiente en variables de grupo | Igual |
| Runner protegido y con etiquetas | Sí | Sí | Sí |
| `id_tokens` (OIDC) con `ref_protected` y `environment_protected` | Sí | Sí | Sí |
| Lista de permitidos del job token | Sí | Sí | Sí |
| Ambiente protegido y aprobación de despliegue | No | Sí | Sí |
| «Protect manual jobs» | No (pide ambiente protegido) | Sí | Sí |
| `secrets:` (gestor externo) y GitLab Secrets Manager | No | Sí | Sí |
| Políticas de ejecución de pipeline (jobs inyectados en todos los proyectos) | No | No | Sí |

## La barrera de producción, según el plan

| | Free | Premium y Ultimate |
|---|---|---|
| Quién lanza el despliegue | Sólo un pipeline de una rama o un tag **protegido**, y a esas refs sólo llega un Maintainer (mergeando o creando el tag) | Los de «Allowed to deploy» del ambiente protegido |
| El «sí» de una persona en la plataforma | Mergear a la rama protegida o crear el tag protegido | La aprobación del despliegue; quien dispara no aprueba |
| La credencial | Variable **protegida** más runner **protegido**; mejor, `id_tokens` con un gestor que exija ref protegida | Igual, más variables con alcance de ambiente |
| El límite | Un Maintainer u Owner (⚠ confirmar) puede desproteger la rama | Un Maintainer u Owner (⚠ confirmar) puede desproteger el ambiente |

En los dos casos, **la barrera vale mientras la identidad de la IA no sea Maintainer**.

## Seguridad

| Capacidad | Free | Ultimate |
|---|---|---|
| SAST | Analizadores abiertos; el resultado es un JSON | Advanced SAST, hallazgos en el Merge Request |
| Detección de secretos | La del pipeline | + protección al hacer push (se saltea con una opción de push, y queda auditado) |
| Escaneo de dependencias | No | Sí |
| Escaneo de contenedores | Trivy, reporte JSON | + escaneo del registro y remediación |
| Políticas de seguridad | No | Sí |

**En Free, GitLab corre el escáner pero no decide**: deja un JSON. El veredicto lo da [[seguridad]].

## Qué reemplaza a lo que el plan no da

Es lo mismo que el script imprime al final, en «Barreras que este plan no da».

| Lo que el plan no da | Qué lo reemplaza | Dónde vive |
|---|---|---|
| Aprobaciones requeridas | Quién puede mergear a la rama protegida (Maintainers) y que la identidad de la IA no pase de Developer | GitLab (rama protegida) y el token |
| «El autor no aprueba» | Mergea una persona Maintainer; el verificador distinto del que produjo lo pone el método | [[desarrollo]] |
| CODEOWNERS exigido | Quién revisa los cambios de `.gitlab-ci.yml` lo fija el método y lo mira una persona antes de mergear | [[desarrollo]] |
| Push rules contra secretos | `bin/auditar-diff.py` y el hook local, antes del push (las push rules tampoco ven los commits hechos por la interfaz o por la API) | El repositorio |
| Ambiente protegido con aprobación | Rama o tag protegido, variables y runners protegidos; mejor, `id_tokens` | GitLab y el gestor de secretos |
| `when: manual` protegido | Nada: sin ambiente protegido, un job manual lo corre cualquiera que pueda correr el pipeline. No es barrera | — |

## Lo que pesa en el diseño

- **En Free, GitLab no puede exigir el «Aprobar».** La única barrera de plataforma sobre el merge es quién puede
  mergear a la rama protegida. Si la IA usa el token de una persona Maintainer u Owner, esa barrera no existe.
- **La identidad de la IA:** un token de permisos finos o, donde no los hay, un token de acceso de proyecto (rol
  Reporter para leer, Developer para escribir); **nunca** el token personal clásico con alcance `api`. El push de la
  rama sale con la credencial git de la persona: si es Maintainer u Owner, la protección de la rama no frena ese
  push, y eso se declara (no se da por cubierto).
- **Aun en Premium, la IA no aprueba.** Con una identidad distinta de la del autor, su aprobación contaría para la
  regla: la regla nombra a las personas (o al grupo) que aprueban, y el token de la IA no tiene el permiso de aprobar.
- **Quien puede empujar directo a la rama protegida se saltea las aprobaciones**: «Allowed to push and merge» va en
  «No one» o en el mínimo.
- **El congelamiento de despliegues no es barrera**: GitLab sólo pone la variable `CI_DEPLOY_FREEZE`, y el job la
  tiene que mirar.
- **Las barreras de GitLab valen lo que vale el parche.** En 2026 se corrigieron fallas que dejaban correr
  pipelines en ramas protegidas con rol Developer (CVE-2026-16301), leer variables protegidas (CVE-2026-79708),
  desactivar las aprobaciones de un ambiente protegido (CVE-2026-86341) o aprobar habiendo commiteado
  (CVE-2026-92528). Por eso los secretos de producción conviene tenerlos **fuera** de GitLab, con `id_tokens`, y la
  instancia propia, al día ([runners-e-instancia.md](runners-e-instancia.md)).

## Permisos por rol: lo que no está claro

La tabla vigente de permisos dice **Owner** para administrar variables, runners de proyecto y ambientes protegidos;
las páginas de cada función siguen diciendo **Maintainer**. La conclusión no cambia: **la IA no pasa de Developer**,
y el cambio exacto dice el rol mínimo que figura en la página de la función, con la marca `⚠ confirmar`.
