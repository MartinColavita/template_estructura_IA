---
name: arquitectura-e-infraestructura
description: >-
  Puerta única de la arquitectura y la infraestructura de la aplicación, y rol de su orquestador: diseñar o
  documentar la arquitectura (vista C4, atributos de calidad, una decisión técnica hasta su DEC), escribir la
  infraestructura como código (Terraform u OpenTofu, Bicep, Dockerfile, Compose, Kubernetes) y auditarla. Escribe
  y verifica; nunca aplica. Usar cuando se pida "diseñá la arquitectura", "¿qué conviene para la arquitectura, X o
  Y?", "armá la infraestructura", "dockerizá la app", "revisá este plan de infraestructura",
  "/arquitectura-e-infraestructura". NO es para el
  pipeline (despliegue-continuo). Español (Argentina).
---

# Arquitectura e infraestructura — la puerta y el rol del orquestador

Esta skill es **la puerta** a dos cosas que van juntas: **cómo está armada la aplicación** (la arquitectura y sus
decisiones) y **dónde y sobre qué corre** (la infraestructura, escrita como código). No diseña ni programa por sí
misma: clasifica el pedido por su **objeto**, carga **una** referencia y coordina a quien produce y a quien verifica.
La IA **escribe y verifica**; lo que toca la nube lo corre el pipeline y lo aprueba una persona.

**Todos los comandos se corren parados en la raíz del repositorio del Cerebro.**

## Qué NO es

- **El código de la aplicación** y el ciclo de todo código (rama, Merge Request, test primero, verificador distinto)
  son de [[desarrollo]]. La infraestructura también es código y entra por ahí (G2): acá está sólo lo específico.
- **El pipeline** (armarlo, verificarlo, desplegar, volver atrás) es de [[despliegue-continuo]]
  (`bin/verificar-pipeline.py`, `bin/gate-despliegue.py`). El `plan` y el `apply` contra un ambiente real los corre
  ese pipeline; acá se escribe lo que aplica y se lee el plan que publicó.
- **Lo que ya corre** (salud de un servidor, mantenimiento, una caída) es de [[operacion-de-servidores]].
- **Escanear imágenes y vulnerabilidades** es de [[seguridad]]. `bin/auditar-iac.py` mira los **archivos** de
  infraestructura del repositorio, no lo que corre.
- **Presentar** un diagrama como página es de [[archify]]: lo que entra al Cerebro es el Mermaid.
- **Radiografiar una aplicación que ya existe** es de [[absorber-aplicacion]]; acá se usa lo que encontró.

## Antes de empezar

1. **`DEC-007`** (`cerebro-digital/modulo-ejemplo/arquitectura/decisiones.md`): la plataforma destino, la
   herramienta de infraestructura como código, dónde vive el código, el estado, la identidad del pipeline, el gestor
   de secretos, los módulos, cómo corre la aplicación y qué escáneres frenan. **Mientras un tema esté en `⚠`, no se
   elige por el equipo**: se trabaja sin él, se dice, y lo que dependa de él es `SIN DATOS (pendiente declarado)`.
   También pesan `DEC-001` (el código no vive en este repositorio) y `DEC-003` (el stack).
2. **Las fichas del módulo**: [[infraestructura]] (recursos por ambiente, nombres, estado, secretos, vista de
   despliegue), [[ambientes]] (la lista de ambientes y quién aprueba) y [[esqueleto-proyectos]] (los repositorios).
3. **El inventario** ([[inventario]]), sólo si el pedido nombra algo que corre:
   `python -I bin/activo-autorizado.py --alias <alias>`. Sin `OK`, no existe para la IA.

## Ruteo: el objeto del pedido decide

| Pedido (frases) | Qué se hace | Referencia | Script | Barrera |
|---|---|---|---|---|
| «diseñá la arquitectura», «documentá la arquitectura», «el diagrama C4», «la vista de despliegue», «¿qué atributos de calidad pesan?» | La vista C4 (contexto, contenedores, despliegue) en Mermaid, cada elemento con su fuente o `⚠ supuesto`, y los atributos de calidad con su medida | [disenar-arquitectura.md](references/disenar-arquitectura.md) | `bin/radiografiar-codigo.py --mermaid` (si la aplicación ya existe) | Borrador; al Cerebro, por `cerebro-curator` con el «sí» |
| «¿qué conviene para la arquitectura, X o Y?», «registrá esta decisión», «hacé un ADR» | Conducir **una** decisión técnica: contexto, opciones con pros y contras, recomendación en `⚠`, cómo se confirma | [disenar-arquitectura.md](references/disenar-arquitectura.md) | — | La `DEC-nnn` la escribe `cerebro-curator` con el «sí»; la IA no decide por el equipo |
| «armá la infraestructura», «escribí el Terraform», «dockerizá la app», «armá el docker-compose», «los manifiestos de Kubernetes», «sumá un ambiente» | Escribir la infraestructura como código en su repositorio, con el ciclo de [[desarrollo]], y probarla sin tocar la nube | [armar-infraestructura.md](references/armar-infraestructura.md) | `bin/auditar-iac.py` (autochequeo de quien escribe) | **GATE de INFRAESTRUCTURA**: sólo lo que no toca la nube |
| «revisá la infraestructura», «auditá este cambio de infra», «¿está para el Merge Request?» | La verificación, por **otro agente**, en sólo lectura | [auditar-infraestructura.md](references/auditar-infraestructura.md) | `bin/auditar-iac.py` | Sólo lectura |
| «revisá este plan de infraestructura», «¿qué hace este plan?», «¿lo apruebo?» | El resumen del plan que publicó el pipeline y la pregunta de aprobación en criollo | [auditar-infraestructura.md](references/auditar-infraestructura.md) | `bin/resumir-plan.py` | Aprueba una persona **en la plataforma** (GATE de DESPLIEGUE) |
| «aplicá», «destruí esto», «importá el recurso», «desbloqueá el estado», «sacalo del estado» | **No se hace.** Se explica por qué y se arma el resumen para que lo haga una persona | [[AGENTS]] | — | **Nunca la IA** |

**Desempate.** Si el pedido nombra una decisión o un diagrama, es arquitectura; si nombra archivos, un módulo o un
ambiente, es infraestructura; si trae un plan, es auditar. «Ocupate de la infraestructura» a secas se pregunta:
¿diseñarla, escribirla o revisarla? Nunca se elige por la persona.

## Las barreras

Las reglas enteras están en [[AGENTS]] («Infraestructura, despliegue, servidores, seguridad y GitLab — barreras»:
el GATE de INFRAESTRUCTURA y el de DESPLIEGUE) y valen aunque no se cargue esta skill. Lo propio de la función:

- **El comando no, el código sí.** Escribir un bloque `moved`, `removed` o `import` es código: entra en el Merge
  Request y lo aplica el pipeline. Los comandos son del GATE de INFRAESTRUCTURA: `state` es **entero** (también
  `state pull`, que vuelca el estado con sus secretos), no sólo `state rm`.
- **El JSON crudo del plan va a `borrador/`** y nunca a un Merge Request ni a una tarjeta; `bin/resumir-plan.py` no
  imprime valores.
- La pregunta, en criollo: *«El plan de `prueba` crea 3 recursos, cambia 1 y no borra nada. Lo aplica el
  pipeline cuando lo apruebes en la plataforma; yo no lo aplico. ¿Lo dejo así en el Merge Request?»*

## Cómo se trabaja

1. **Plan corto**: el objeto, la referencia que se carga, qué script corre, qué barrera aplica y qué temas de
   `DEC-007` están en `⚠`.
2. **Quien produce no aprueba.** Una lectura N0 (correr un script sobre lo que ya hay) la corre el orquestador; el
   `nucleo-productor` se despacha cuando hay algo que producir (escribe el borrador o el código, corre el script como
   autochequeo), y el `nucleo-verificador`, cuando hay criterio que aplicar, en sólo lectura y con contexto limpio, con
   [auditar-infraestructura.md](references/auditar-infraestructura.md) o la sección de verificación de
   [disenar-arquitectura.md](references/disenar-arquitectura.md). El código sigue el ciclo de [[desarrollo]].
3. **La misión** de cada worker lleva sólo: **Objetivo**, **Rutas** (la referencia, las fichas, el repositorio y la
   rama) y **Resultado esperado**; y la línea «Respondé y escribí todo en español (Argentina)».
4. **Sin subagentes** (la herramienta no los tiene): cada rol corre en línea, de a uno, y se avisa que la
   verificación la hizo el mismo agente. Eso no es una verificación independiente: se declara.
5. Las preguntas a la persona van con la herramienta nativa de preguntas del entorno (por ejemplo
   `AskUserQuestion`); si no está, la pregunta va sola en la respuesta y se espera.

## Veredicto

```
VEREDICTO-INICIO
<regla, herramienta o chequeo>   : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: <su veredicto>, criterio: <...>
BLOQUEANTES: <n>   SIN DATOS (no se pudo mirar): <n>   SIN DATOS (pendiente declarado): <n>
Verificado por: <herramienta> · <modelo> · sólo lectura, contexto limpio
VEREDICTO-FIN
```

Un chequeo que no corrió es **SIN DATOS**, no OK: una herramienta ausente, un reporte vacío, un plan que no llegó,
un `validate` sin `plan` (no sabe si los argumentos existen en el proveedor). Lo que depende de un tema de
`DEC-007` en `⚠` es `SIN DATOS (pendiente declarado)`: se lista y no frena.

## Qué queda dónde

| Qué | Dónde |
|---|---|
| La vista C4 en curso, una decisión en curso, la salida de los scripts, el JSON del plan | `borrador/arquitectura/` y `borrador/infraestructura/<fecha>/` (nunca se versionan) |
| Una decisión validada | `decisiones.md` del módulo, como `DEC-nnn`, **sólo por `cerebro-curator`**, con el «sí» |
| Recursos, nombres, estado, secretos y la vista de despliegue validados | [[infraestructura]], por `cerebro-curator` con el «sí» |
| El código de infraestructura | Su repositorio, donde lo fije `DEC-007` (nunca en este, `DEC-001`), por [[desarrollo]] |
