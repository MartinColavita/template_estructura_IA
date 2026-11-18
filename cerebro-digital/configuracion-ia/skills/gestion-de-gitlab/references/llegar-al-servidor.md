# Llegar al servidor desde GitLab: los caminos y su barrera

> Fuentes: documentación oficial de GitLab (claves SSH en CI, deploy keys y deploy tokens, alcance de runners,
> agente de Kubernetes, GitOps con Flux, infraestructura como código) y la página de manual de `sshd(8)`. Detalle en
> `cerebro-digital/configuracion-ia/referencias-externas/referencias-gestion-de-gitlab.md`.

**Primero, el inventario.** El servidor o el cluster destino tiene que figurar en el inventario autorizado, por su
alias exacto: `python -I bin/activo-autorizado.py --alias <alias>`. Si no figura, no existe, ni para leerlo (GATE de
SERVIDOR, en [[AGENTS]]). Esta referencia elige **el camino**; desplegar es de [[despliegue-continuo]]
(`bin/gate-despliegue.py`), el pipeline es código que entra por [[desarrollo]], y el lado del servidor (usuario,
`authorized_keys`, el runner instalado) es de [[operacion-de-servidores]].

## Los cinco caminos

| Camino | Cómo es | Qué credencial del servidor queda en GitLab | Cuándo conviene | La barrera |
|---|---|---|---|---|
| **Runner propio en el destino** | Un runner de proyecto en el servidor, o en su red, toma los jobs: la conexión **sale del servidor** hacia GitLab | Ninguna | Servidor interno detrás de un firewall: lo habitual en una empresa | Runner protegido, con etiqueta, bloqueado al proyecto y sin jobs sin etiqueta; con ejecutor `shell`, dedicado a ese proyecto |
| **GitOps con Flux más el agente de Kubernetes** | Flux, dentro del cluster, trae el estado desde un registro OCI (lo que recomienda GitLab) o desde Git, con un deploy token de sólo lectura | Ninguna con escritura | Producción en Kubernetes | Mergear es desplegar: la barrera es la rama protegida del repositorio de configuración |
| **SSH desde el job** | Clave privada en una variable de tipo archivo, **protegida**; las claves del host en `SSH_KNOWN_HOSTS`, juntadas desde una red de confianza, **no** con `ssh-keyscan` en el job. En el servidor, la clave entra en `authorized_keys` con `restrict,command="…",from="…"`: sólo corre el comando fijo, sin terminal ni reenvíos | La clave privada | Una o pocas máquinas, sin Kubernetes | Variable protegida, ref protegida y comando forzado |
| **Ansible desde el pipeline** | El job corre el playbook del repositorio de infraestructura; por abajo es el camino anterior | La clave SSH o las credenciales del inventario de Ansible | Configuración repetible en varias máquinas | La del camino anterior; `--check` es una simulación con límites |
| **Agente de Kubernetes, flujo CI/CD** | El job usa `kubectl` contra el contexto del agente, autorizado con `ci_access` y limitado por ambiente y por rama protegida | Ninguna: el acceso lo da el agente | Clusters de prueba | GitLab dice que tiene un modelo de seguridad más débil y **no lo recomienda para producción** |

## La regla que sale de la tabla

**Si el servidor trae** (runner propio en el destino, Flux), GitLab no guarda nada que sirva para entrar al servidor:
conviene siempre que se pueda. **Si el pipeline empuja**, la credencial vive en GitLab y hay que protegerla:

1. Variable **protegida** (sólo llega a refs protegidas) y runner **protegido**, con etiqueta.
2. Donde se pueda, **`id_tokens`** con un gestor de secretos que entregue la credencial sólo a una ref protegida, en
   lugar de una clave guardada ([ci-en-gitlab.md](ci-en-gitlab.md)).
3. Del lado del servidor, la clave con **comando forzado** y origen limitado: el mismo modelo que la cuenta de
   lectura de [[operacion-de-servidores]].
4. La barrera de producción, la del plan ([planes-y-barreras.md](planes-y-barreras.md)): en Free, la rama o el tag
   protegido; en Premium, el ambiente protegido con aprobación. **El «sí» de producción se da en la plataforma**, no
   en el chat (GATE de DESPLIEGUE).

## Lo que no conviene

- Una deploy key **con escritura** agregada a la regla de la rama protegida: empuja a la rama protegida. Sólo por
  decisión escrita (`DEC-010`); pertenece a un usuario, y si se bloquea al dueño deja de andar (mejor, una cuenta de
  servicio).
- Un deploy token para la API: no sirve; es para que un servidor o Flux **lean** el repositorio o el registro.
- El flujo CI/CD del agente de Kubernetes contra producción.
- Runners de instancia para jobs que tienen secretos de despliegue.
- **El estado de OpenTofu en GitLab sin pensar quién es Developer**: cualquier Developer lo puede bajar, y guarda
  secretos. El código de infraestructura y su estado son de [[arquitectura-e-infraestructura]].

## Qué se escribe y quién lo aplica

| Qué | Lo escribe | Lo aplica |
|---|---|---|
| El job del pipeline (con `environment`, `tags`, `rules`, `id_tokens`) | La IA, por [[desarrollo]] | Merge Request, mergea una persona |
| La variable protegida con la clave, el runner y su registro | — | Una persona, en GitLab (la IA nunca ve el valor) |
| La línea de `authorized_keys` con comando forzado, el runner instalado en el servidor | El plan, la IA | Una persona, por [[operacion-de-servidores]] (GATE de SERVIDOR) |
| El camino elegido, el alias del destino y el runner por alias | La IA, como borrador | La ficha «GitLab del proyecto», por `cerebro-curator` |
