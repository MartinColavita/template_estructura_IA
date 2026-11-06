# Dependencias, configuración y secretos

> Prioridad **ALTA**. Adaptado de `deps-audit`, `deps-upgrade` y `config-validate` de
> `wshobson/commands` (MIT), [referencias-externas.md](../referencias-externas.md).

## Antes de sumar una dependencia

Cuatro preguntas, en este orden. Si alguna falla, no entra:

| Pregunta | Si la respuesta es mala |
|---|---|
| **¿Está en la lista de dependencias aprobadas?** | Se pregunta antes de sumarla. La lista la define el área de Arquitectura de la organización, no el equipo. ⚠ Si la organización no tiene una, el equipo fija la suya y la anota en `arquitectura/decisiones.md` |
| **¿Sale del registro de paquetes autorizado?** | Si la organización tiene un registro o proxy interno, todo pasa por ahí. Nunca directo de internet |
| **¿Tiene vulnerabilidades conocidas?** | No entra hasta que haya una versión sin ellas |
| **¿La licencia es compatible?** | Una licencia incompatible es un problema legal, y no lo resuelve el equipo de desarrollo |

Y una quinta, que es de sentido común: **¿hace falta?** Una dependencia de 40 KB para
formatear una fecha trae su cadena de dependencias, sus vulnerabilidades futuras y su
actualización obligatoria. El código propio de 15 líneas no.

## El registro de paquetes — antes de instalar nada

Cada repositorio —el back y cada front— lleva **versionado** el archivo de configuración de su
gestor de paquetes apuntando al registro autorizado. ⚠ **Cuál es el registro y cómo se
configura lo define la organización**, y se anota en `arquitectura/esqueleto-proyectos.md`.

No es opcional. Sin eso, o no descarga, o descarga de un lugar que no está controlado.

## Revisar vulnerabilidades: en cada Merge Request

No una vez por año. Las vulnerabilidades no aparecen cuando actualizás: aparecen cuando
**alguien las descubre**, y tu versión que ayer estaba bien hoy no lo está.

| Qué se mira | Umbral |
|---|---|
| Vulnerabilidades **críticas** o **altas** | **Frenan el build.** Sin excepción sin motivo escrito |
| **Medias** | No frenan, pero llevan plazo de resolución y quedan registradas |
| **Bajas** | Se registran y se revisan al actualizar |
| En dependencias **de tus dependencias** | **El mismo criterio.** Son la mayoría, y son las que nadie mira |
| Licencias | Toda licencia nueva se declara |

La puerta que tiene que mandar sigue siendo el **analizador de seguridad (SAST/SCA)** — ⚠
**a definir por el equipo**: mientras no esté configurado y exigido por el build, esto queda
en `SIN DATOS`. Ver [seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md).

## Actualizar una versión

1. **De a una.** Actualizar quince y ver qué se rompe es garantía de no saber cuál fue.
2. **Leer qué rompe** antes de actualizar, no después.
3. **La suite completa en verde**, y si es una dependencia grande, también las pruebas
   funcionales.
4. **Se puede volver atrás**: se anota la versión anterior antes de subir.

Para subir la versión del **framework principal** no alcanza con esto: se sigue la guía de
migración que publica el propio framework, **de a un minor por vez**, y nunca mezclado con
otro cambio.

## Configuración

**Lo que cambia entre ambientes va en configuración; lo que no, en el código.** Suena obvio y
se rompe todo el tiempo: una URL de un servicio escrita en una constante funciona hasta que
hay que apuntarla a otro lado.

| Regla | Por qué |
|---|---|
| **Toda variable de entorno está documentada** | Un servicio que no arranca porque falta una variable que nadie sabía que existía cuesta una tarde |
| **El servicio falla al arrancar si falta algo obligatorio** | Mejor que arranque mal y falle raro tres horas después |
| **Valores por defecto sólo para lo que no es crítico** | Un valor por defecto en una URL de producción es un accidente esperando |
| **Los ambientes se parecen entre sí** | Cuanto más distintos, más "sólo pasa en producción" |

## Secretos

Esto es corto porque no tiene matices:

- **Nunca en el código.** Ni en un test, ni en un archivo de configuración versionado, ni
  "comentado por las dudas".
- **Nunca en un log.** Ver [observabilidad.md](observabilidad.md).
- **Nunca en la descripción de un Merge Request** ni en una captura.
- **Si se filtró a un commit, no alcanza con borrarlo: hay que rotarlo.** Queda en el
  historial de git para siempre, y el historial se clona entero.

**Propuesta del método:** los secretos se inyectan como **variable de entorno** desde el
almacén de cada ambiente; el código sólo conoce el nombre de la variable, nunca el valor ni de
dónde sale. En local, un `.env` **fuera del control de versiones** y con un `.env.ejemplo`
versionado que liste los nombres sin valores.

⚠ **Qué almacén concreto lo provee en cada ambiente lo define Infraestructura.** El patrón no
depende de esa respuesta; el servicio se escribe igual.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Dependencias aprobadas, sin vulnerabilidades pendientes, registro autorizado, sin secretos en el código |
| **HALLAZGO** | Dependencia no aprobada, vulnerabilidad sin resolver, o **un secreto en el repositorio** (bloqueante) |
| **SIN DATOS** | **No se pudo correr la revisión** de dependencias. No es "no hay vulnerabilidades" |
