---
name: despliegue-continuo
description: >-
  Puerta única del CI/CD y el despliegue y rol de su orquestador: armar o revisar el pipeline de un
  repositorio (GitHub Actions, GitLab CI o Azure Pipelines), preparar la promoción de una versión a un
  ambiente y su vuelta atrás, clasificar las migraciones del rango y cuidar la cadena de suministro. La
  IA prepara; despliega una persona. Usar cuando se pida "armá el pipeline", "revisá el workflow",
  "desplegá a prueba", "pasá a producción", "volvé a la versión anterior", "/despliegue-continuo". NO es
  para escribir la infraestructura (eso es arquitectura-e-infraestructura). Español (Argentina).
---

# CI/CD y despliegue continuo — la puerta y el rol del orquestador

Esta skill es **la puerta** a todo lo que es pipeline y despliegue. No despliega: clasifica el pedido por su
**objeto**, carga **una** referencia y coordina a quien produce y a quien verifica. Contesta dos preguntas,
**«¿el pipeline exige lo que dice exigir?»** y **«¿esta versión está lista para que una persona la apruebe?»**,
con evidencia y con tres estados. La regla que ordena todo: **la barrera de producción vive en la plataforma**,
no en un archivo que la IA edita.

**Todos los comandos se corren parados en la raíz del repositorio del Cerebro.**

## Qué NO es

- **Escribir código**, también el del pipeline, sigue el ciclo de [[desarrollo]] (rama, Merge Request, verificador
  distinto, nada sale sin «sí»). Acá va lo específico. Qué tiene que frenar el pipeline está en
  `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/entregar-a-produccion.md`; expandir, migrar
  y contraer, en `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/migracion-de-base.md`.
- **El código de infraestructura** que el pipeline aplica (IaC, Dockerfile, manifiestos) y su plan son de
  [[arquitectura-e-infraestructura]].
- **GitLab a fondo** (el proyecto, sus runners, la instancia y sus permisos) es de [[gestion-de-gitlab]]. Acá, sólo
  el YAML del pipeline, en lo estático.
- **Lo que corre después del despliegue** (salud, una caída, el mantenimiento) es de [[operacion-de-servidores]].
- **Escanear la aplicación o sus imágenes**, y un secreto filtrado, son de [[seguridad]].

## Antes de empezar

1. **`DEC-007`** (`cerebro-digital/<modulo>/arquitectura/decisiones.md`): la plataforma de CI/CD y dónde vive la
   aprobación de producción, la identidad con la que trabaja la IA, la estrategia y la vuelta atrás, la cadena de
   suministro y la herramienta de migraciones. Mientras esté en `⚠`, lo que dependa de ella es `SIN DATOS`
   (pendiente declarado): se trabaja con lo que dicen la ficha y el repositorio, y se avisa.
2. **La ficha de ambientes** (`cerebro-digital/<modulo>/arquitectura/ambientes.md`). Sin filas cargadas no se
   prepara ninguna promoción: el gate da `SIN DATOS`.
3. **El repositorio de la aplicación**, clonado en `back/` o `front/` (`DEC-001`).
4. **Lo que corre** (una URL, un servidor) no se toca desde acá. Si hay que mirarlo después de desplegar, va por
   el inventario (`python -I bin/activo-autorizado.py --alias <alias>`) y por [[operacion-de-servidores]].

## Ruteo: el objeto del pedido decide

| Pedido (frases) | Qué se hace | Referencia | Script | Barrera |
|---|---|---|---|---|
| «armá el pipeline», «configurá el CI», «agregá el despliegue a prueba», «sumá el paso de tests» | Armar o cambiar el pipeline de un repositorio, por Merge Request | [armar-pipeline.md](references/armar-pipeline.md) | `bin/verificar-pipeline.py` (lo corre el verificador) | Es código: [[desarrollo]]. Sacar un control es edición destructiva |
| «revisá el pipeline», «¿este workflow es seguro?», «auditá el CI heredado» | Revisión en sólo lectura, chequeo por chequeo | [armar-pipeline.md](references/armar-pipeline.md) | `bin/verificar-pipeline.py` | Libre: lee archivos |
| «desplegá a prueba», «pasá a producción», «promové la versión» | El plan de promoción con sus datos duros; aprueba una persona en la plataforma | [desplegar.md](references/desplegar.md) | `bin/gate-despliegue.py` | **GATE de DESPLIEGUE** |
| «volvé a la versión anterior», «hacé rollback» | El mismo plan, al revés | [desplegar.md](references/desplegar.md) | `bin/gate-despliegue.py` | **GATE de DESPLIEGUE** |
| «¿qué migraciones trae la versión?», «¿esta migración rompe?», «borrá la columna» | Clasificar el rango: expandir, contraer o mixta | [desplegar.md](references/desplegar.md) | `bin/clasificar-migraciones.py` | Contraer: dos «sí» en turnos distintos |
| «fijá las acciones», «armá el SBOM», «firmá la imagen», «configurá las actualizaciones automáticas» | Fijado, SBOM, firma o atestación, actualizaciones con espera | [cadena-de-suministro.md](references/cadena-de-suministro.md) | `bin/verificar-pipeline.py` (P2) | Publicar un artefacto o un tag es G4 |

**Desempate.** Si el pedido nombra un repositorio y su pipeline, es armar o revisar; si nombra un ambiente y una
versión, es desplegar. «Arreglá el deploy» a secas se pregunta: ¿cambiar cómo se despliega (el pipeline) o
desplegar una versión ahora? Nunca se elige por la persona.

## Las barreras

Las reglas enteras están en [[AGENTS]] («Infraestructura, despliegue, servidores, seguridad y GitLab — barreras»:
el GATE de DESPLIEGUE —la aprobación en la plataforma, disparar hacia un ambiente protegido, contraer el esquema—)
y valen aunque no se cargue esta skill. Lo propio de la función:

- **Ni con dos «sí»** la IA se saltea un chequeo del pipeline.
- **Contraer** el esquema va recién con la versión que dejó de usarlo ya en el ambiente.
- La pregunta, en criollo: *«Voy a dejar lista la versión 1.4.2 para Producción. Es la misma imagen que está en
  Prueba y trae una migración que sólo agrega una columna. Si algo sale mal, se vuelve a la 1.4.1 en unos cinco
  minutos. La aprobación la das vos en la plataforma, en el ambiente Producción. ¿La dejo lista?»*

## Cómo se trabaja

1. **Plan corto**: el objeto, la referencia que se carga, qué script corre, con qué datos de la plataforma, y qué
   barrera aplica.
2. **Quien produce no aprueba.** Una lectura N0 (correr un script sobre lo que ya hay) la corre el orquestador; el
   `nucleo-productor` se despacha cuando hay algo que producir (escribe el pipeline en la rama, corre el gate, arma
   el plan), y el `nucleo-verificador`, cuando hay criterio que aplicar, en sólo lectura y con contexto limpio:
   corre `bin/verificar-pipeline.py` sobre la rama del Merge Request, o vuelve a correr el gate con los mismos datos, y mira sólo lo que el script
   declara que no mira.
3. **La misión** de cada worker lleva sólo: **Objetivo**, **Rutas** (la referencia, el repositorio y la ficha) y
   **Resultado esperado**; y la línea «Respondé y escribí todo en español (Argentina)».
4. **Sin subagentes** (la herramienta no los tiene): cada rol corre en línea, de a uno, y se avisa que la
   verificación la hizo el mismo agente. Eso no es una verificación independiente: se declara.
5. Las preguntas a la persona van con la herramienta nativa de preguntas del entorno (por ejemplo
   `AskUserQuestion`); si no está, la pregunta va sola en la respuesta y se espera.

## Veredicto

```
VEREDICTO-INICIO
<chequeo>   : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: <su veredicto>, criterio: <...>
BLOQUEANTES: <n>   SIN DATOS (no se pudo mirar): <n>   SIN DATOS (pendiente declarado): <n>
Verificado por: <herramienta> · <modelo> · sólo lectura, contexto limpio
VEREDICTO-FIN
```

Un pipeline lleva una línea por chequeo, de P1 a P10; P9 (aprobaciones, ambientes protegidos y reglas de rama en la
plataforma) es `SIN DATOS (no se pudo mirar)` hasta que una persona lo confirme a mano o, en GitLab, lo mida
[[gestion-de-gitlab]]; P10 (CI Lint de la instancia) es `SIN DATOS` sin su archivo. Un despliegue lleva una
línea por chequeo del gate. Un chequeo que no corrió es **SIN DATOS**, no OK: herramienta ausente, ficha en molde,
un dato de la plataforma que nadie pasó.

## Qué queda dónde

| Qué | Dónde |
|---|---|
| El plan de un despliegue, los reportes crudos de las herramientas | `borrador/despliegue/` (nunca se versiona) |
| La ficha de ambientes y las filas de `DEC-007` | El Cerebro, **sólo por `cerebro-curator`**, con el «sí» de la persona |
| El pipeline, el `Dockerfile`, la configuración de las actualizaciones automáticas | Su repositorio, por [[desarrollo]] |
| La aprobación, los ambientes protegidos, las credenciales y los secretos | La plataforma; los configura una persona |
| Cómo salió un despliegue | El comentario de la tarjeta ([[comentar-tarea]]) |
