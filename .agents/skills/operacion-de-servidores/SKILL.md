---
name: operacion-de-servidores
description: >-
  Puerta única de la operación y el mantenimiento de servidores y rol de su orquestador: la salud
  de un servidor, el mantenimiento con plan de cambio (parches, certificados, disco, logs,
  respaldos, reinicios), una caída y los runbooks. Clasifica cada pedido por nivel (N0 a N3) y
  enruta. Usar cuando se pida "¿cómo está el servidor?", "¿por qué anda lento?",
  "renová el certificado", "parcheá", "se cayó el servicio", "escribí el runbook",
  "/operacion-de-servidores". NO es para la seguridad del servidor (eso es seguridad) ni para
  desplegar una versión (despliegue-continuo). Español (Argentina).
---

# Operación de servidores — la puerta y el rol del orquestador

Esta skill es **la puerta** a todo lo que es operar lo que corre: un servidor, un servicio, la URL de un ambiente.
No toca nada por sí misma: clasifica el pedido por su **objeto** y por su **nivel** (N0 a N3), carga **una**
referencia y coordina a quien produce y a quien verifica. Contesta una sola pregunta, **«¿anda bien?»**, con
evidencia medida por script; lo que hay que cambiar sale como un plan de cambio que aprueba una persona.

**Todos los comandos se corren parados en la raíz del repositorio del Cerebro.**

## Qué NO es

- **«¿Está expuesto?»** (auditar o endurecer un servidor, una vulnerabilidad, una intrusión, una clave filtrada) es
  de [[seguridad]]. Una caída con sospecha de intrusión también.
- **Desplegar una versión, o volver a la anterior**, es de [[despliegue-continuo]].
- **El código de infraestructura** (un playbook, IaC, la imagen) es de [[arquitectura-e-infraestructura]], y se
  escribe por [[desarrollo]]. Acá se decide **qué** cambiar en un servidor; si se repite, se vuelve código allá.
- **La instancia de GitLab y sus runners** son de [[gestion-de-gitlab]].
- **Arreglar el código** que causó una caída es de [[desarrollo]]: acá se contiene, allá se arregla con su test.
- **Instrumentar la aplicación** (métricas, trazas, chequeos de salud) es código:
  `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/observabilidad.md`.

## Antes de empezar

1. **`DEC-008`** (`cerebro-digital/<modulo>/arquitectura/decisiones.md`): umbrales de salud, ventana y canario,
   identidades y dónde queda el registro, respaldos y observabilidad. Mientras esté en `⚠`, lo que dependa de ella
   es `SIN DATOS`; se trabaja con los valores por defecto que declara cada script, y se dice.
2. **El inventario** (`cerebro-digital/<modulo>/operacion/inventario.md`):
   `python -I bin/activo-autorizado.py --alias <alias>`. Sin `OK`, no se toca **ni para leerlo**. Si el pedido no
   nombra un alias, se pregunta cuál; nunca se deduce de un nombre parecido.
3. **Qué cambió**: `operacion/cambios.md` del módulo. Y si existe, el runbook del síntoma en `operacion/runbooks/`.
4. **Cómo se llega al servidor** ([acceso.md](references/acceso.md)): sin la identidad de lectura instalada, el
   diagnóstico se hace con reportes que trae una persona (`--archivo`), y los cambios los corre la persona.

## Ruteo: el objeto del pedido decide

| Pedido (frases) | Qué se hace | Referencia | Script | Barrera |
|---|---|---|---|---|
| «¿cómo está el servidor?», «¿por qué anda lento?», «¿se llenó el disco?», «mirá los logs de anoche», «¿cuándo vence el certificado?» | Diagnóstico en sólo lectura: el script mide, el criterio busca la causa | [diagnosticar.md](references/diagnosticar.md) | `bin/salud-host.py`, `bin/vigencia-certificados.py` | **GATE de SERVIDOR**, N0: sola |
| «no llega», «no resuelve», «no conecta», «¿es la red?», «anda lento y no es el servidor», «¿qué nivel tiene cambiar el DNS o el firewall?» | Diagnóstico de red en sólo lectura, de a un peldaño (nombre, camino, TLS, aplicación, ruta); un cambio de red sale como plan con su nivel | [diagnosticar-red.md](references/diagnosticar-red.md) | `bin/vigencia-certificados.py`, `bin/activo-autorizado.py --prueba pasivo` | **GATE de SERVIDOR**, N0; abrir un puerto de administración, tocar el firewall de administración o el del sistema operativo a mano, N3 |
| «parcheá», «renová el certificado», «liberá disco», «rotá los logs», «lanzá un respaldo», «reiniciá el servicio» | Un plan de cambio por servidor, con canario, ventana y vuelta atrás | [mantenimiento.md](references/mantenimiento.md) | `bin/gate-operacion.py` | **GATE de SERVIDOR**: N1 un «sí», N2 dos «sí», N3 nunca |
| «se cayó el servicio», «anda lentísimo», «no responde», «la gente no puede entrar» | Incidente operativo: contener antes de entender, documento vivo, avisos, postmortem sin culpa | [incidente.md](references/incidente.md) | `bin/salud-host.py`, `bin/gate-operacion.py` | La IA propone y una persona decide |
| «escribí el runbook», «documentá cómo se arregla esto», «armá el procedimiento para esta alerta» | Un runbook con cada paso completo, en borrador | [runbook.md](references/runbook.md) | — | Borrador; al Cerebro, por `cerebro-curator` |
| «¿cómo le doy acceso a la IA?», «instalá el colector», «configurá la clave de lectura» | Lo que una persona instala una vez para que la barrera viva en el servidor | [acceso.md](references/acceso.md) | `bin/activo-autorizado.py` | N3: lo hace una persona; la IA arma el resumen |

**Desempate.** «¿Anda bien?» es de acá; «¿está expuesto?», de [[seguridad]]. Un pedido que mezcla mirar y cambiar
(«mirá qué pasa y arreglalo») es primero un diagnóstico (N0) y después, con lo medido, un plan. Si la gente ya está
afectada, es un incidente aunque se haya pedido como diagnóstico. Si no se puede saber, se pregunta: nunca se elige
por la persona.

## Las barreras

Las reglas enteras (el GATE de SERVIDOR y los niveles N0 a N3) están en [[AGENTS]], «Infraestructura, despliegue,
servidores, seguridad y GitLab — barreras», y valen aunque no se cargue esta skill. Lo propio de la función:

- **El nivel de cada tarea** sale de la tabla de ejemplos de [mantenimiento.md](references/mantenimiento.md); ante
  la duda, el más alto.
- **La barrera vive en el servidor**: la identidad de lectura sólo puede correr el colector, y la de cambio vence en
  una hora y sólo corre comandos exactos ([acceso.md](references/acceso.md)). Las reglas del cliente son una capa más.
- **Si sale distinto de lo esperado, se frena y se cuenta**: no se prueba otro comando en producción.
- **Ni secretos ni datos de personas**: no se leen variables de entorno ni archivos de credenciales; lo que sale de
  un log va resumido y con marcadores.
- La pregunta, en criollo: *«Quiero reiniciar el servidor `db-prod-1` para terminar el parche del núcleo. La base
  queda afuera unos 3 minutos, en la ventana de hoy a las 23, y el respaldo de las 22 está verificado. Si no arranca,
  vuelvo al núcleo anterior desde el menú de arranque. Antes de reiniciar te muestro cómo está y cómo tiene que
  quedar, y te pregunto de nuevo. ¿Preparo el cambio?»*

## Cómo se trabaja

1. **Plan corto**: el alias, el objeto, el nivel, la referencia que se carga, qué script corre y qué barrera aplica.
2. **Quien produce no aprueba.** Una lectura N0 (correr el script de sólo lectura) la corre el orquestador; el
   `nucleo-productor` se despacha cuando hay algo que producir (el diagnóstico, el plan de cambio o el runbook en
   `borrador/`), y el `nucleo-verificador`, cuando hay criterio que aplicar, en sólo lectura y con contexto limpio: vuelve a leer el reporte guardado (`bin/salud-host.py --archivo`), corre `bin/gate-operacion.py` sobre el
   plan y mira sólo lo que los scripts declaran que no miran.
3. **Quien cambia no certifica.** Un comando N1 o N2 lo corre la **sesión principal**, a la vista de la persona y
   después de su «sí», con la identidad de cambio; nunca un worker. El DESPUÉS lo mide un script, no la palabra de
   quien cambió.
4. **La misión** de cada worker lleva sólo: **Objetivo**, **Rutas** (la referencia, el plan o el reporte, el alias)
   y **Resultado esperado**; y la línea «Respondé y escribí todo en español (Argentina)».
5. **Sin subagentes** (la herramienta no los tiene): cada rol corre en línea, de a uno, y se avisa que la
   verificación la hizo el mismo agente. Eso no es una verificación independiente: se declara.
6. Las preguntas a la persona van con la herramienta nativa de preguntas del entorno (por ejemplo
   `AskUserQuestion`); si no está, la pregunta va sola en la respuesta y se espera. Un N2 son dos preguntas, en dos
   turnos.

## Veredicto

```
VEREDICTO-INICIO
<categoría o chequeo>   : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: <su veredicto>, criterio: <...>
BLOQUEANTES: <n>   SIN DATOS (no se pudo mirar): <n>   SIN DATOS (pendiente declarado): <n>
Verificado por: <herramienta> · <modelo> · sólo lectura, contexto limpio
VEREDICTO-FIN
```

Un chequeo que no corrió es **SIN DATOS**, no OK: el colector que no está, un reporte cortado o viejo, un servidor
que no conecta, un inventario vacío. Lo que todavía no mide ningún script (parches pendientes, frescura de los
respaldos, reglas de alerta) es `SIN DATOS (pendiente declarado)`. No hay puntaje único.

## Qué queda dónde

| Qué | Dónde |
|---|---|
| Reportes crudos del colector, diagnósticos, planes de cambio, documentos vivos de incidentes, runbooks y postmortems en curso | `borrador/operacion/` (nunca se versiona) |
| El inventario, el registro de cambios, un runbook (`RB-nnn`) y un incidente cerrado (`INC-nnn`) | El pilar `operacion/` del módulo ([[inventario]], [[cambios]]), **sólo por `cerebro-curator`**, con el «sí» |
| Lo aprendido y la deuda que deja un incidente | `aplicacion/aprendizajes.md` (`AP-nnn`) y `aplicacion/deuda.md` (`DT-nnn`), por `cerebro-curator` |
| Las acciones de un postmortem | Tareas, por [[redactar-tarea]], con los GATEs del tablero |
| Un playbook, el código de infraestructura, el colector instalado | Su repositorio, por [[desarrollo]]; el colector, en el servidor, por una persona |
| El registro completo de cada cambio (SSH y `sudo`) | En el servidor, donde fije `DEC-008` |
