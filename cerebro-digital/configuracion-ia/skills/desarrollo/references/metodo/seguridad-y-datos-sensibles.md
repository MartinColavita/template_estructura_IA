# Seguridad y datos sensibles

> Prioridad **ALTA**. **Este es el documento que fija la postura de seguridad del método, y el
> resto apunta acá.** Adaptado de `security-scan`, `compliance-check` y `security-hardening`
> de `wshobson/commands` (MIT), [referencias-externas.md](../referencias-externas.md).

## ⚠ El analizador de seguridad (SAST/SCA): a definir por el equipo

**Qué herramienta analiza el código y las dependencias, con qué alcance y en qué etapa del
pipeline, lo decide el equipo al arrancar** — y se anota en `arquitectura/decisiones.md`.
Escrito para que nadie lo lea al revés:

| | |
|---|---|
| **Qué está decidido** | Nada hasta que el equipo lo defina. Ni qué herramienta, ni con qué alcance, ni en qué etapa del pipeline |
| **Cuál es la intención declarada** | Que sea una **puerta que frene** la entrega |
| **Qué NO se afirma** | Que corra. Que frene. Que esté configurado en algún pipeline |
| **Qué falta para cerrarlo** | Que el equipo lo defina y quede configurado y exigido por el build |

Mientras tanto, lo que sí se sostiene: **sin resultado del analizador, la seguridad de una
entrega queda en `SIN DATOS`** — y `SIN DATOS` no es aprobado. Lo que no se puede hacer es
tildar el ítem como si hubiera corrido.

## Las dos puertas que tienen que frenar

| Puerta | Qué hace | Estado | Si no corrió |
|---|---|---|---|
| **Analizador de seguridad (SAST/SCA)** | Análisis de seguridad del código y de las dependencias, en el pipeline | ⚠ **A definir.** No configurado hasta que el equipo lo decida | `SIN DATOS`. **No es aprobado** |
| **Puerta de calidad** | Cobertura, análisis estático, tests, exigidos por el build | Intención declarada | `SIN DATOS` |

**Una supresión lleva su motivo escrito al lado.** Una supresión sin justificación no es una
supresión: es un hallazgo tapado, y se reporta como `HALLAZGO`.

Una herramienta configurada que el build no corre es decoración.

## Datos sensibles — la parte que no se negocia

El sistema maneja datos de personas reales. En este método, **PHI** es la sigla para *dato
personal o sensible real*, y en el código eso significa una cosa sola: **PHI real está
PROHIBIDO** en código, tests, fixtures, logs, mensajes de error, contratos, capturas y
descripciones de Merge Request.

Marcadores obligatorios: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`,
`<direccion>`, `<dato-sensible>`.

### Controles que sí aplican

La fuente original está escrita sobre la ley de datos de salud de otro país. **Acá no
aplica**: rige **el régimen legal de datos personales que aplique a la organización**, y en
casi todos esos regímenes los datos sensibles del dominio tienen una protección reforzada.
Los *controles*, en cambio, se traducen bien:

| Control | Qué significa en el código |
|---|---|
| **Mínimo necesario** | Cada consulta trae **sólo los campos que ese caso de uso usa**. Nunca un `SELECT *` de la ficha de la persona para mostrar un nombre |
| **Propósito declarado** | El acceso al dato de la persona se justifica por el caso de uso, no "porque el endpoint lo devuelve" |
| **Registro de acceso** | Toda lectura de dato sensible deja rastro: quién, cuándo, para qué. **Sin el dato en el registro** |
| **Cifrado en tránsito** | TLS siempre. Si la organización exige además **autenticación mutua** entre servicios para lo saliente, se toma tal cual |
| **Permiso por rol** | Según el mecanismo del stack, y por tipo de usuario (⚠ los tipos de usuario los define el proyecto) |

> ⚠ **El régimen legal aplicable, los plazos de retención y el procedimiento ante un
> incidente los define el área legal y de seguridad de la organización, no este documento.**
> Acá están los controles técnicos; la norma la ponen ellos. Falta confirmarlo con el equipo.

## Los chequeos técnicos, por capa

### Entrada — donde entra casi todo

- **Validar en el servidor, siempre.** La validación del front es comodidad, no seguridad.
- **Lista de permitidos, no de prohibidos.** Enumerar lo malo siempre deja algo afuera.
- **Consultas parametrizadas.** Nunca armar una consulta —ni la del motor ni la del ORM—
  concatenando texto.
- **Tamaño máximo** de cada campo y del cuerpo entero.

### Salida

- **Nunca devolver más de lo que el contrato declara.** Un objeto de dominio serializado
  entero filtra campos que nadie pensó exponer.
- **Mensajes de error genéricos hacia afuera**, detalle en el log. Un error que dice *"la
  persona `<documento>` no está registrada"* le confirma a un atacante que ese documento
  existe.

### Dependencias

- **Vulnerabilidades conocidas**: se revisan en cada Merge Request, no una vez por año.
- **Licencias**: una dependencia con licencia incompatible es un problema legal, no técnico.
- **Sólo lo que está en la lista de dependencias aprobadas.** Ver
  [dependencias-y-config.md](dependencias-y-config.md).

### Secretos

- **Nunca en el código, ni en un test, ni en un archivo de configuración versionado.**
- Si un secreto se filtró a un commit, **no alcanza con borrarlo**: hay que rotarlo. Queda en
  el historial de git para siempre.

## Veredicto de tres estados

| Estado | Cuándo |
|---|---|
| **OK** | Se revisó el punto y está bien |
| **HALLAZGO** | Se revisó y hay algo — con archivo y línea |
| **SIN DATOS** | **No se pudo revisar.** No hay resultado del analizador de seguridad (mientras no esté definido: siempre), no hay logs, no compila |

**Regla del cero:** cero hallazgos sobre entrada externa **no es un aprobado**. Cero
validaciones en un servicio que recibe datos de afuera no quiere decir que esté limpio:
quiere decir que no es auditable.

## Quién revisa

**No el que escribió el código.** Y esto vale doble acá: el que programó ya decidió que su
validación alcanzaba.

## Lo que este documento no reemplaza

Las guías de desarrollo seguro que la organización tenga publicadas —las generales, como
OWASP, y las específicas de su stack— se toman tal cual. Lo de arriba **se suma**, no las
reemplaza: es la capa que una guía general no trae — el veredicto de tres estados, la regla
del cero, el PHI prohibido con sus marcadores y quién revisa.
