# Referencias externas — de dónde salió cada idea

Las fuentes de cada función se mudaron a su sección del Cerebro, donde se ven en Obsidian junto con el método y las
decisiones de la función. Es **bibliografía, no una dependencia**: nada de lo que se cita se instala, se copia ni se
invoca; las herramientas que los scripts saben ejecutar se declaran además en `DEPENDENCIAS-EXTERNAS.md`.

| Función | Fuentes | Sección |
|---|---|---|
| Arquitectura e infraestructura | [fuentes.md](../../arquitectura/fuentes.md) | [Arquitectura](../../arquitectura/index.md) |
| CI/CD y despliegue | [fuentes-despliegue.md](../../devops/fuentes-despliegue.md) | [DevOps](../../devops/index.md) |
| Operación de servidores | [fuentes-operacion.md](../../devops/fuentes-operacion.md) | [DevOps](../../devops/index.md) |
| Gestión de GitLab | [fuentes-gitlab.md](../../devops/fuentes-gitlab.md) | [DevOps](../../devops/index.md) |
| Seguridad de la aplicación | [fuentes-aplicaciones.md](../../seguridad/fuentes-aplicaciones.md) | [Seguridad](../../seguridad/index.md) |
| Seguridad de los servidores | [fuentes-servidores.md](../../seguridad/fuentes-servidores.md) | [Seguridad](../../seguridad/index.md) |
| Networking (la red, que entra por dos puertas) | [fuentes.md](../../networking/fuentes.md) | [Networking](../../networking/index.md) |
| Orquestadores por función y Obsidian | [referencias-orquestacion-y-obsidian.md](referencias-orquestacion-y-obsidian.md) (se queda acá: es del ecosistema, no de una función) | — |

La bibliografía del método de desarrollo sigue en
`cerebro-digital/configuracion-ia/skills/desarrollo/references/referencias-externas.md`.

**Cómo se usa.** Cuando alguien pregunte «¿de dónde salió esta regla?», la respuesta está en la página de su función.
Cuando una fuente se actualice, se relee y lo que aprendió se propone de a una en `mejoras.md`, nunca se copia. Las
reglas de siempre: no se instala ni se copia una colección de skills de terceros (en los registros públicos hay
skills maliciosas); toda herramienta se fija por versión y hash; un texto con licencia que obliga a redistribuir lo
derivado (CC BY-SA) se lee y no se copia; los controles de CIS se citan sólo por número.
