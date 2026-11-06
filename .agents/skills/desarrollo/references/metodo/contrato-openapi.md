# El contrato OpenAPI es la fuente

> Método propio. No depende de ninguna skill externa ni del stack elegido.

## La regla

**Cada Tarea de capa `api` trae su fragmento OpenAPI. `armar-swagger` los consolida y valida.
El front lo consume simulándolo.**

El contrato no es documentación que se escribe al final. Es **lo que se acuerda antes**, y de
lo que dependen las dos puntas para poder trabajar en paralelo sin esperarse.

## Por qué importa tanto acá

El back y los repositorios de front del proyecto (uno por aplicación) viven **separados**. Sin
contrato, la única forma de saber qué devuelve un endpoint es preguntarle a quien lo escribió,
o leerle el código. Las dos cosas se hacen mal y tarde.

Con contrato:

- El front arranca **sin esperar** al back: simula el contrato con la herramienta de su stack
  ([simular-api-desde-el-contrato.md](simular-api-desde-el-contrato.md)).
- El back sabe exactamente **qué tiene que devolver**, incluidos los errores.
- Los tests de los dos lados salen de **la misma fuente**.
- Un desacuerdo aparece **al consolidar**, no en integración.

## Quién gana cuando el código y el contrato difieren

**Gana el contrato.** Si el código devuelve algo que el `openapi.yaml` no declara, el
hallazgo es del código.

La excepción es una sola y es explícita: si el contrato está mal, **se cambia el contrato
primero** —con su revisión— y recién después el código. Nunca al revés, y nunca en el mismo
commit sin decirlo.

> Si el código puede alejarse del contrato sin que nada falle, el contrato dejó de ser la
> fuente y pasó a ser un comentario largo.

## Qué tiene que declarar cada endpoint

No alcanza con el camino feliz. Lo mínimo:

| | |
|---|---|
| **Todos los códigos de respuesta** | No sólo el `200`. Cada `4xx` y `5xx` que el endpoint puede devolver |
| **La forma del cuerpo**, en éxito y en error | Incluido el formato del error |
| **Qué campos son obligatorios** y cuáles pueden venir nulos | Es la mitad de los tests de validación |
| **Los límites**: largos máximos, formatos, rangos | La otra mitad |

Cada código declarado **lleva su test de los dos lados**: el back lo produce, el front lo
maneja.

## Cuando el endpoint todavía no está en el contrato

**Es un bloqueo de la Tarea, no una licencia para inventarlo.** Se frena y se pide cerrar el
contrato.

Inventar la forma de una respuesta para poder seguir es la falla más cara de esta cadena: el
front queda andando perfecto contra un backend que no existe, se descubre en integración, y
parece un problema del back.

## Nada de datos personales sensibles

Los ejemplos del contrato se versionan y se publican en la interfaz navegable de la API, la
que todo el mundo abre para entenderla. **Marcadores siempre**:
`<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`, `<dato-sensible>`.

Un ejemplo con un dato real queda en el historial de git y en esa interfaz.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | El contrato consolida, valida y cubre todos los códigos que el código devuelve |
| **HALLAZGO** | El código devuelve algo no declarado, o el contrato declara algo que el código no implementa |
| **SIN DATOS** | **No se pudo consolidar o validar** el contrato |

`SIN DATOS` acá es frecuente y engaña: si `armar-swagger` no corrió, nadie comparó nada.
Eso no es "el contrato está bien": es que no se miró.

## Lo que pone el stack

La librería que expone el contrato en tiempo de ejecución y la que lo publica en una interfaz
navegable las provee el stack del back; cuáles son, se anota en
`arquitectura/esqueleto-proyectos.md`. Nada de lo de arriba depende de esa elección: el
contrato se consolida, se valida y manda sobre el código, sea cual sea la herramienta.
