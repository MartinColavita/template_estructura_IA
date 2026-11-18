---
name: seguridad
description: >-
  Puerta única de la seguridad informática del proyecto y rol de su orquestador: escanear la
  aplicación (código, dependencias, secretos), modelar amenazas, probar un ambiente
  que corre, auditar y endurecer un servidor, priorizar vulnerabilidades y atender un incidente de
  seguridad. Evalúa y propone; no arregla sola. Usar cuando se pida "escaneá la seguridad", "¿hay
  dependencias vulnerables?", "modelo de amenazas", "hacé un pentest", "auditá el servidor", "¿qué
  parcheo primero?", "se filtró una clave", "/seguridad". NO es para escribir código seguro (eso es
  desarrollo) ni para la salud de un servidor (operacion-de-servidores). Español (Argentina).
---

# Seguridad — la puerta y el rol del orquestador

Esta skill es **la puerta** a todo lo que es seguridad: la de la aplicación y la de lo que corre. No
escanea ni arregla por sí misma: clasifica el pedido por su **objeto**, carga **una** referencia y
coordina a quien produce y a quien verifica. Contesta una sola pregunta, **«¿está expuesto?»**, con
evidencia y con tres estados; lo que hay que arreglar sale como trabajo para una persona.

**Todos los comandos se corren parados en la raíz del repositorio del Cerebro.**

## Qué NO es

- **Escribir código seguro** es del método de [[desarrollo]]
  (`cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/seguridad-y-datos-sensibles.md` y
  `dependencias-y-config.md`). Acá se evalúa; el arreglo sigue ese método, con su test primero.
- **«¿Anda bien?»** (salud, parches, certificados, una caída) es de [[operacion-de-servidores]]. Una caída con
  sospecha de intrusión, o una clave filtrada, sí es de acá.
- **El código de infraestructura** y su revisión estática (`bin/auditar-iac.py`) son de
  [[arquitectura-e-infraestructura]]; **el pipeline** (`bin/verificar-pipeline.py`), de [[despliegue-continuo]].
- **Un secreto en lo que se está por commitear** ya lo frena `bin/auditar-diff.py`: no se duplica.
- **Los hallazgos del Doctor** (el diagnóstico del ecosistema) se recorren con [[atender-hallazgos]]; los de
  seguridad, acá, con su propio paso («Cómo se trabaja»).

## Antes de empezar

1. **`DEC-009`** (`cerebro-digital/<modulo>/arquitectura/decisiones.md`): herramientas, umbrales, plazos y quién
   responde. Mientras esté en `⚠`, lo que dependa de ella es `SIN DATOS`; se trabaja con los valores por defecto
   que declara cada script, y se dice.
2. **El inventario** (`cerebro-digital/<modulo>/operacion/inventario.md`), si el pedido nombra algo que corre:
   `python -I bin/activo-autorizado.py --alias <alias>`. Sin `OK`, no se toca.
3. **La política** del módulo (`cerebro-digital/<modulo>/seguridad/politica.md`), si existe.

## Ruteo: el objeto del pedido decide

| Pedido (frases) | Qué se hace | Referencia | Script | Barrera |
|---|---|---|---|---|
| «escaneá la seguridad del repo», «escaneá el diff de la Tarea #NNNN», «¿hay dependencias vulnerables?», «buscá secretos», «corré el análisis estático» | Escaneo de un repositorio o del diff de una Tarea, informe normalizado, y cada hallazgo crítico o alto verificado por otro agente | [escanear-aplicacion.md](references/escanear-aplicacion.md) | `bin/escanear-seguridad.py` | Libre: lee el repositorio y corre lo instalado, sin red; lo crudo va a `borrador/` |
| «modelá las amenazas», «¿qué puede salir mal en este flujo?», «hacé el STRIDE» | El modelo de amenazas de **un** flujo, anclado en este sistema | [modelar-amenazas.md](references/modelar-amenazas.md) | — | Borrador; al Cerebro, por `cerebro-curator` |
| «hacé un pentest», «escaneá el ambiente de prueba», «prueba dinámica» | Una prueba contra una aplicación que corre | [probar-ambiente.md](references/probar-ambiente.md) | `bin/escanear-ambiente.py` | **GATE de PRUEBA ACTIVA** |
| «auditá el servidor», «¿qué tan seguro está?», «escaneá la imagen» | Auditoría de sólo lectura de un servidor y de sus imágenes | [auditar-servidor.md](references/auditar-servidor.md) | `bin/auditar-host.py`, `bin/escanear-imagenes.py` | **GATE de SERVIDOR**, nivel N0 |
| «endurecé el servidor», «cerrá lo que encontró la auditoría», «configurá el firewall» | Un plan cambio por cambio, escrito como código | [endurecer-servidor.md](references/endurecer-servidor.md) | `bin/gate-operacion.py` | **GATE de SERVIDOR**: N1, o N2 en producción; SSH, firewall o PAM a mano, N3 (una persona o el pipeline) |
| «¿qué parcheo primero?», «priorizá las vulnerabilidades», «¿estamos expuestos a este CVE?» | Prioridad, plazo y registro `V-nnn` | [gestionar-vulnerabilidades.md](references/gestionar-vulnerabilidades.md) | `bin/priorizar-vulnerabilidades.py` | Las tarjetas salen por el pipeline del tablero, con sus GATEs |
| «nos hackearon», «hay un proceso raro», «se filtró una clave» | Bitácora, evidencia con su hash y contención **propuesta** | [incidente-de-seguridad.md](references/incidente-de-seguridad.md) | `bin/juntar-evidencia.py` | La IA propone y una persona decide |

**Desempate.** Si el pedido nombra un repositorio o una Tarea, es la aplicación; si nombra un alias del
inventario, es lo que corre. «Revisá la seguridad» a secas se pregunta: ¿del código o del servidor? Nunca se
elige por la persona.

## Las barreras

Las reglas enteras están en [[AGENTS]] («Infraestructura, despliegue, servidores, seguridad y GitLab — barreras»:
el GATE de SERVIDOR, el de PRUEBA ACTIVA y «Siempre») y valen aunque no se cargue esta skill. Lo propio de la
función:

- **Un secreto encontrado** se cita por regla, archivo y línea; «verificarlo» contra el proveedor también es
  usarlo. Lo rota una persona: borrarlo no alcanza.
- **Un informe de escaneo es un mapa para un atacante**: comentarlo en un Merge Request o en una tarjeta también es
  publicarlo.
- **La IA no arregla sola ni en lote**, y **no acepta un riesgo**: lo propone, y decide una persona.
- La pregunta, en criollo: *«Voy a correr una prueba activa contra `https://app-prueba.<dominio>/`, la URL exacta
  de la fila `app-prueba` del inventario, que la autoriza. Manda pedidos de ataque y puede ensuciar datos de
  prueba. ¿La corro?»*

## Cómo se trabaja

1. **Plan corto**: el objeto, la referencia que se carga, qué script corre y qué barrera aplica.
2. **Quien produce no aprueba.** Una lectura N0 (correr un script sobre lo que ya hay) la corre el orquestador; el
   `nucleo-productor` se despacha cuando hay algo que producir (el borrador, el plan), y el `nucleo-verificador`,
   cuando hay criterio que aplicar, en sólo lectura y con contexto limpio. Para un hallazgo crítico o alto, el
   verificador contesta: ¿la entrada la controla un atacante?, ¿hay un control antes?, ¿qué gana? El resultado es
   **confirmado**, **falso positivo** o **SIN DATOS**.
3. **Los hallazgos se recorren con la persona, de a uno por turno**: cada uno con su evidencia, su prioridad y lo
   que se propone (arreglarlo por [[desarrollo]], proponer su supresión o su excepción con motivo y vencimiento, o
   anotarlo como `V-nnn`). Decide la persona; lo que no decidió queda abierto.
4. **La misión** de cada worker lleva sólo: **Objetivo**, **Rutas** (la referencia y los archivos) y **Resultado
   esperado**; y la línea «Respondé y escribí todo en español (Argentina)».
5. **Sin subagentes** (la herramienta no los tiene): cada rol corre en línea, de a uno, y se avisa que la
   verificación la hizo el mismo agente. Eso no es una verificación independiente: se declara.
6. Las preguntas a la persona van con la herramienta nativa de preguntas del entorno (por ejemplo
   `AskUserQuestion`); si no está, la pregunta va sola en la respuesta y se espera.

## Veredicto

```
VEREDICTO-INICIO
<categoría o chequeo>   : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: <su veredicto>, criterio: <...>
BLOQUEANTES: <n>   SIN DATOS (no se pudo mirar): <n>   SIN DATOS (pendiente declarado): <n>
Verificado por: <herramienta> · <modelo> · sólo lectura, contexto limpio
VEREDICTO-FIN
```

Un chequeo que no corrió es **SIN DATOS**, no OK: herramienta ausente, base de vulnerabilidades vieja, cero
archivos analizados. No hay puntaje único.

## Qué queda dónde

| Qué | Dónde |
|---|---|
| Informes crudos, modelos de amenazas en curso, planes de endurecimiento | `borrador/seguridad/` y `borrador/amenazas/` (nunca se versionan) |
| La política, el registro `V-nnn`, un modelo de amenazas validado, un incidente cerrado | El pilar `seguridad/` y `operacion/incidentes/` del módulo, **sólo por `cerebro-curator`**, con el «sí» |
| La evidencia de un incidente | **Fuera del repositorio**, donde fije `DEC-009`; acá sólo su hash y su ubicación |
| Un arreglo, un playbook de endurecimiento | Su repositorio, por [[desarrollo]] |
