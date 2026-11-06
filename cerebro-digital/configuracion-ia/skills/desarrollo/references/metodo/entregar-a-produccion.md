# Entregar — el pipeline y el despliegue

> Prioridad **ALTA** por hito. Adaptado de `deploy-checklist` y `workflow-automate` de
> `wshobson/commands` (MIT), [referencias-externas.md](../referencias-externas.md).

## La regla que ordena todo

**Si el build no lo exige, no existe.**

Una herramienta configurada que el pipeline no corre —o que corre y no frena— es decoración:
da la sensación de que la calidad está cubierta sin cubrir nada. Es la misma idea que "un
control que no deja evidencia no es un control", aplicada al pipeline.

## Lo que el pipeline tiene que exigir

| Etapa | Qué corre | ¿Frena? |
|---|---|---|
| **Compilar** | Build, y el chequeo estático de tipos del stack en modo estricto, donde exista | **Sí** |
| **Tests** | La suite completa | **Sí** |
| **Cobertura** | El umbral | **Sí** |
| **Análisis estático** | Linter, reglas de código | **Sí** |
| **Análisis de seguridad (SAST/SCA)** | Código y dependencias | ⚠ **A definir por el equipo.** La intención es que frene; mientras no esté configurado, no existe |
| **Contrato** | Que el `openapi.yaml` consolide y valide | **Sí** |
| **Dependencias** | Vulnerabilidades y licencias | **Sí**, ante críticas o altas |

Las filas con **Sí** frenan la entrega. Un pipeline que reporta y sigue de largo no es una
puerta: es un informe que nadie lee.

> ⚠ **Ojo con la fila del análisis de seguridad.** **Todavía no está definido y no se sabe
> cómo va a quedar**: qué herramienta, con qué alcance y en qué etapa. La intención declarada
> es que frene, pero **no se afirma que corra ni que frene** hasta que esté configurado y el
> build lo exija, y no se tilda el ítem como si hubiera corrido. Mientras tanto, sin su
> resultado la seguridad de la entrega queda en `SIN DATOS`, que no es aprobado. Detalle:
> [seguridad-y-datos-sensibles.md](seguridad-y-datos-sensibles.md).

## Antes de desplegar

- [ ] Todas las etapas del pipeline en verde, **sin saltear ninguna**.
- [ ] Las migraciones de base son compatibles hacia atrás. Ver [migracion-de-base.md](migracion-de-base.md).
- [ ] Las variables de entorno nuevas **están cargadas en el ambiente destino**.
- [ ] Los secretos nuevos están donde corresponde, y **no en el repositorio**.
- [ ] Hay forma de volver atrás, y alguien sabe cuál es.
- [ ] Se sabe **qué mirar** después: qué métrica, qué log, qué tablero.
- [ ] El orden entre repositorios está claro (el back antes que el front que lo consume).

## Volver atrás — se decide antes, no durante

El peor momento para inventar cómo volver atrás es cuando ya está roto.

| Qué se define antes | |
|---|---|
| **Cómo se vuelve** | El comando o el procedimiento, escrito |
| **Cuánto tarda** | Si tarda 40 minutos, eso es parte del daño |
| **Qué NO vuelve solo** | **Las migraciones de base.** Por eso van en pasos separados |
| **Quién decide** | Una persona, no un comité en el momento |

> **Lo que más se olvida:** el código vuelve atrás fácil, los datos no. Si la migración ya
> borró una columna, volver la versión del código no la trae. Ése es el motivo real del
> patrón expandir/migrar/contraer.

## Después de desplegar

No termina cuando el despliegue dice "OK". Termina cuando alguien miró:

1. **Las cuatro señales**, contra cómo estaban antes: latencia, tráfico, errores, saturación.
2. **Los logs de error del servicio desplegado**, filtrando por versión.
3. **Un flujo real de punta a punta**, a mano.

**Propuesta del método:**

| Momento | Qué se hace |
|---|---|
| **Los primeros 30 minutos** | Alguien mira. No "está atento": mira las cuatro señales y los logs de error de la versión nueva |
| **Las primeras 24 horas** | La entrega sigue siendo "reciente": ante cualquier incidente, **lo primero que se sospecha es el despliegue** |
| **Nunca un viernes a última hora** | No por superstición: porque la ventana de observación cae cuando no hay nadie |

⚠ *Propuesta del método, a confirmar por el equipo.*

Ver [observabilidad.md](observabilidad.md).

## Los tres despliegues de una migración

Vale repetirlo acá porque es donde se rompe:

```
Despliegue 1  ->  EXPANDIR   el esquema admite lo viejo y lo nuevo
Despliegue 2  ->  el código nuevo, que usa lo nuevo
Despliegue 3  ->  CONTRAER   se borra lo viejo, ya sin nadie usándolo
```

Hacerlo en uno solo funciona en desarrollo, donde no hay dos versiones conviviendo. En
producción, durante el despliegue, **siempre** conviven.

## Nada de PHI

Ni en los logs del pipeline, ni en los artefactos, ni en las capturas del despliegue.
Marcadores siempre. Los logs de CI suelen ser visibles para más gente que el repositorio.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Todas las etapas frenan de verdad, hay vuelta atrás probada, y se observó después |
| **HALLAZGO** | Una etapa configurada que **no frena**, o no hay vuelta atrás definida |
| **SIN DATOS** | **No se pudo verificar** que el pipeline exija lo que dice exigir |

Ese último es el que más aparece al revisar un pipeline heredado: está todo puesto, y nadie
comprobó nunca que alguna de esas etapas efectivamente rompa el build.
