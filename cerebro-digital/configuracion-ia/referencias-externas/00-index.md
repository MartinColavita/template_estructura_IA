# Referencias externas — de dónde salió cada idea

Una página por función. Cada una dice qué fuente se consultó (repositorio, guía oficial, estándar), con qué licencia
y en qué fecha, **qué idea se tomó y a dónde fue**, qué se miró y se descartó (y por qué), y qué no se pudo
verificar. Es **bibliografía, no una dependencia**: nada de lo que se cita acá se instala, se copia ni se invoca. Las
herramientas que los scripts saben ejecutar (si están instaladas en la máquina) se declaran además en
`DEPENDENCIAS-EXTERNAS.md`, con cómo se fija su versión.

| Función | Página | Puerta |
|---|---|---|
| Arquitectura e infraestructura | [referencias-arquitectura-e-infraestructura.md](referencias-arquitectura-e-infraestructura.md) | `arquitectura-e-infraestructura` |
| CI/CD y despliegue | [referencias-despliegue-continuo.md](referencias-despliegue-continuo.md) | `despliegue-continuo` |
| Operación de servidores | [referencias-operacion-de-servidores.md](referencias-operacion-de-servidores.md) | `operacion-de-servidores` |
| Seguridad de la aplicación | [referencias-seguridad-de-aplicaciones.md](referencias-seguridad-de-aplicaciones.md) | `seguridad` |
| Seguridad de los servidores | [referencias-seguridad-de-servidores.md](referencias-seguridad-de-servidores.md) | `seguridad` |
| Gestión de GitLab | [referencias-gestion-de-gitlab.md](referencias-gestion-de-gitlab.md) | `gestion-de-gitlab` |
| Orquestadores por función y Obsidian | [referencias-orquestacion-y-obsidian.md](referencias-orquestacion-y-obsidian.md) | — |

La bibliografía del método de desarrollo, anterior a estas, sigue en
`cerebro-digital/configuracion-ia/skills/desarrollo/references/referencias-externas.md`.

**Cómo se usa.** Cuando alguien pregunte «¿de dónde salió esta regla?», la respuesta está acá. Cuando una fuente se
actualice, se relee y lo que aprendió se propone de a una en `mejoras.md`, nunca se copia. Las reglas de siempre:
no se instala ni se copia una colección de skills de terceros (en los registros públicos hay skills maliciosas); toda
herramienta se fija por versión y hash; un texto con licencia que obliga a redistribuir lo derivado (CC BY-SA) se lee
y no se copia; los controles de CIS se citan sólo por número.
