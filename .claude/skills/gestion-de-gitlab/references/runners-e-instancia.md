# Runners e instancia propia

> Fuentes: documentación oficial de GitLab Runner (seguridad, ejecutores, `config.toml`, registro) y de la
> administración de una instancia propia (política de mantenimiento, camino de actualización, respaldo, chequeos,
> endurecimiento), y los avisos de parche de 2025 y 2026. Detalle en
> `cerebro-digital/devops/fuentes-gitlab.md`.

**El host es de otro.** El sistema operativo, los parches, los respaldos y el acceso al host de un runner o de la
instancia son de [[operacion-de-servidores]]; su seguridad, de [[seguridad]]. El host está en el inventario por su
alias (`python -I bin/activo-autorizado.py --alias <alias>`) y rige el GATE de SERVIDOR. Acá va **la capa de
GitLab**: qué significa cada clave de `config.toml`, los ajustes de la instancia, la versión y el camino de
actualización.

## El runner es un servidor

| Ejecutor | Estado | Riesgo |
|---|---|---|
| Kubernetes, Docker, Docker Autoscaler, Instance | Activos | Los de abajo, si se configuran mal |
| Shell | En mantenimiento | Los jobs corren con el usuario del runner y leen el código, el token y las cachés de otros proyectos: **sólo dedicado a un proyecto** |
| SSH | En mantenimiento | Expuesto a intermediarios |
| Parallels, VirtualBox, Custom | En mantenimiento | — |
| Docker Machine | En desuso | — |

**Las tres formas documentadas de perder el host:** el ejecutor `shell` compartido, `privileged = true` (el
contenedor tiene todas las capacidades de root del host) y el **socket de Docker montado** (un job controla el
Docker del host). Para construir imágenes sin privilegio: BuildKit o Buildah.

**Cómo se endurece:**

- En `config.toml`: `allowed_images`, `allowed_privileged_images`, `allowed_services` y `allowed_pull_policies`
  (si faltan, todo está permitido); `pull_policy` sin `if-not-present` en un runner compartido (un job podría usar
  una imagen privada que otro ya bajó); sin secretos en `environment` (los ve todo job).
- En GitLab (no en `config.toml`): runner **protegido** (sólo refs protegidas), **con etiquetas** y sin «corre jobs
  sin etiqueta»; el de proyecto, **bloqueado** a ese proyecto; los runners de instancia, apagados en los proyectos
  que despliegan.
- La red: propia, sin SSH entrante desde internet, con el endpoint de metadatos de la nube filtrado.
- `GIT_STRATEGY: fetch` reutiliza la copia de trabajo: sólo si se confía en todos los que usan el runner.

**Tokens.** El flujo nuevo crea el runner en GitLab y lo registra con un token de autenticación `glrt-`; etiquetas,
bloqueo y «protegido» se fijan al crearlo. El flujo viejo (token de registro) se puede apagar en la instancia, y
conviene. Un administrador puede fijar un vencimiento: los runners renuevan el token solos.

**Quién administra qué:** el runner de instancia, un administrador; el de grupo, un Owner; el de proyecto, un
Maintainer u Owner (⚠ confirmar). **Registrar, borrar o reconfigurar un runner no lo hace la IA nunca.**

### Cómo se audita

`config.toml` guarda el token del runner: **leerlo es leer un secreto**, y eso es N3. Dos caminos:

1. **La persona copia el archivo** a `borrador/gitlab/<fecha>/config.toml` con el token tapado, dejando el
   prefijo (`token = "glrt-TAPADO"`), y la IA corre:
   `python -I bin/auditar-gitlab.py runner --config borrador/gitlab/<fecha>/config.toml`
2. **La persona corre el script** en el host o con la copia sin tapar: el script nunca imprime el token ni el
   nombre del runner (suele ser el nombre real del host); los nombra por posición (`runner[1]`).

Pide Python 3.11 o más (lee TOML con la biblioteca estándar); con uno anterior da `SIN DATOS` y lo dice. Lo que vive
en GitLab (protegido, bloqueado, etiquetas) no está en `config.toml`: se mira en la interfaz y se anota en la ficha.

## La instancia propia (GitLab empresarial)

### Versión y ventana de mantenimiento

- Los arreglos de **seguridad** van a la versión vigente y a las **dos anteriores**; los de bugs, sólo a la vigente.
  Hay parches programados dos veces por mes, y críticos fuera de calendario.
- **Por qué hay que parchear rápido:** entre septiembre y noviembre de 2026 hubo seis publicaciones de parche
  crítico, con fallas que dejaban leer archivos o ejecutar código en el servidor **sin autenticarse**
  (CVE-2026-85706, CVE-2026-97229, CVE-2026-110264); CVE-2026-97229 entró al catálogo KEV de CISA con tres días de
  plazo. El plazo para un parche crítico lo fija `DEC-009` («Prioridad y plazos»).

### El archivo de versiones vigentes

El script **no baja nada de internet**. La lista la arma una persona (o la IA leyendo la política de mantenimiento y
los avisos de parche oficiales, como dato) y la guarda en `borrador/gitlab/versiones-<fecha>.json`:

```json
{
  "fecha": "aaaa-mm-dd",
  "fuente": "<URL oficial de donde se tomó>",
  "vigentes": ["19.5", "19.4", "19.3"],
  "ultimo_parche": {"19.5": "19.5.4", "19.4": "19.4.6", "19.3": "19.3.8", "19.2": "19.2.8"},
  "paradas": ["18.2", "18.5", "18.8", "18.11", "19.2", "19.5"]
}
```

`ultimo_parche` tiene que traer también las ramas viejas que son parada del camino. Con más de 15 días, la lista es
vieja y la versión queda `SIN DATOS`: puede faltarle el parche crítico.

```
python -I bin/auditar-gitlab.py instancia --instancia <https://host> --versiones borrador/gitlab/versiones-<fecha>.json [--hasta 19.5]
```

Da: si la versión está **dentro de la ventana**, si está en el **último parche de su rama**, y **el camino de
actualización** hasta la versión pedida (por defecto, la última vigente).

### Actualizar (lo ejecuta una persona)

- **No se saltean las paradas obligatorias** (desde la 17.5: x.2, x.5, x.8 y x.11; en la 17 también la 17.3) y se va
  al **último parche de cada parada**, con las **migraciones en segundo plano terminadas** antes del paso siguiente.
- **Antes:** respaldo con el archivo de secretos y la configuración, **restauración probada**,
  `gitlab-rake gitlab:check` y `gitlab-rake gitlab:doctor:secrets`, y los runners en pausa.
- **Volver atrás no existe sin restaurar:** se reinstala el paquete anterior y se restaura un respaldo hecho **en esa
  misma versión y edición**. Lo que se escribió después de actualizar, se pierde. Por eso actualizar es N3, en
  cualquier ambiente: la IA arma el plan (camino, chequeos de antes y de después, vuelta atrás) y lo corre una
  persona.

### El respaldo

`gitlab-backup create` incluye la base, los repositorios, los artefactos y los registros. **No incluye**
`/etc/gitlab` (`gitlab-secrets.json` y `gitlab.rb`), las claves TLS y SSH del host, Redis ni el almacenamiento de
objetos. Es a propósito: **el archivo de secretos tiene la clave que cifra la base**; sin él, quienes usan 2FA pierden
el acceso y los runners no se autentican. Se guarda **aparte** del respaldo, y los dos se prueban juntos. Geo
replica también la corrupción: no es un respaldo. Restaurar pisa la base: **lo hace una persona**.

### Chequeos

| Sólo leen (los corre una persona y le pasa la salida a la IA: la identidad de lectura sólo corre el colector) | Cambian estado (nunca la IA) |
|---|---|
| `gitlab-rake gitlab:env:info`, `gitlab-rake gitlab:check SANITIZE=true`, `gitlab-rake db:migrate:status`, `gitlab-rake gitlab:doctor:secrets`, `/-/readiness?all=1` desde una IP permitida | `db:migrate`, `gitlab:db:reindex`, `cache:clear`, `gitlab:exclusive_lease:clear`, `gitlab:shell:setup` (reconstruye `authorized_keys` y pierde lo que tenía) |

### Los ajustes de la instancia

Los mide `bin/auditar-gitlab.py instancia` con un token de **administrador**, que la IA no tiene: lo corre una
persona y le pasa la salida.

| Ajuste | Valor | Chequeo |
|---|---|---|
| Registro de cuentas | Cerrado, o con aprobación de un administrador | `registro-abierto` |
| 2FA | Obligatorio para todos (o el ingreso por un proveedor externo que lo exija) | `2fa-instancia` |
| Admin Mode | Encendido: un administrador vuelve a autenticarse para administrar | `admin-mode` |
| Visibilidad por defecto de los proyectos | Privada | `visibilidad-por-defecto` |
| Vencimiento de tokens personales | Obligatorio (el máximo son 365 días) | `vencimiento-de-tokens` |
| Registro viejo de runners | Apagado | `registro-viejo-de-runners` |
| Pedidos de webhooks a la red local | Apagado | `webhooks-a-la-red-local` |

La guía oficial de endurecimiento suma: confirmación de correo estricta, feed token apagado, orígenes de importación
limitados y sin deploy keys públicas. El **CIS GitLab Benchmark** se cita sólo por número de control; `gitlabcis` lo
audita por API en sólo lectura, como segunda opinión opcional (no es un producto con soporte de GitLab).
