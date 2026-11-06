# Cambiar el esquema de la base sin romper nada

> Prioridad **ALTA** cuando toca, y es de lo más caro de arreglar mal.
> Adaptado de `db-migrate` de `wshobson/commands` (MIT),
> [referencias-externas.md](../referencias-externas.md).

## El motor, y el piso que manda sobre todo el SQL

**El motor de base y su versión mínima los fija el proyecto** (⚠ a definir, se anotan en
`arquitectura/decisiones.md`): la versión más moderna que se pueda, **con compatibilidad
obligatoria hacia la más vieja que haya en algún ambiente**. Ese piso decide qué sintaxis se
puede usar.

No es un detalle de infraestructura: **decide cómo se escribe cada consulta.** Lo que
escribamos tiene que correr en la versión más vieja, y eso suele dejar afuera justo lo que hoy
sale natural: funciones nuevas de texto y de agregación, funciones de JSON, sintaxis de borrado
condicional, generadores de series. Al fijar el piso se completa esta tabla y queda acá:

| No se usa | Existe desde |
|---|---|
| `<completar: función o sintaxis que el piso no soporta>` | `<completar: versión del motor desde la que existe>` |

> **Por qué está escrito acá.** Nada de esto falla al escribirlo ni en la revisión: falla **al
> ejecutarse contra el motor viejo**, con un error de sintaxis que aparece recién en el
> ambiente donde corre esa versión.

**Al conectar:** los valores por defecto del driver cambian entre versiones —el cifrado de la
conexión, por ejemplo, puede pasar a venir activado—. Contra un servidor sin certificado
válido la conexión falla al arrancar, y el mensaje habla de SSL, no de configuración.

**Herramienta de migraciones — ⚠ a definir por el equipo**, se anota en
`arquitectura/decisiones.md`. Lo que el método le pide, sea cual sea: que soporte el motor
desde el piso de versión fijado; que las migraciones se escriban en SQL plano, que es lo que
el equipo ya sabe leer; y que se integre al arranque del servicio —aplica las migraciones al
levantar y **falla el arranque si el esquema no está donde debería**—, que es mejor que
descubrirlo con el servicio andando.

Todo lo de abajo supone que hay una herramienta: sin ella no hay guión que volver atrás, nada
que correr dos veces ni historial de qué se aplicó, y el veredicto queda en `SIN DATOS`.

## La regla

**Ningún cambio de esquema rompe la versión de código que está corriendo.**

Durante un despliegue conviven el código viejo y el nuevo, aunque sea por minutos. Si la
migración asume que ya está el nuevo, el viejo falla en ese rato — y falla en producción, con
gente usando el sistema.

## Expandir, migrar, contraer

El patrón que hace posible lo de arriba. **Tres despliegues, no uno.**

```
1. EXPANDIR   se AGREGA lo nuevo, nada se borra ni se vuelve obligatorio
              -> el código viejo sigue andando igual

2. MIGRAR     se llenan los datos nuevos, de a tandas, con el sistema andando
              -> el código nuevo ya puede usarlos; el viejo los ignora

3. CONTRAER   recién acá se borra lo viejo, cuando NADIE lo usa
              -> y "nadie" se verifica, no se supone
```

Ejemplo, renombrar una columna:

| Paso | Qué se hace | Qué NO |
|---|---|---|
| Expandir | Agregar la columna nueva, **admitiendo nulos** | Renombrar |
| Migrar | Copiar los datos por tandas · el código escribe en las dos | Dejar de escribir en la vieja |
| Contraer | Borrar la vieja | Hacerlo el mismo día |

> **Por qué nunca se renombra de una:** un `RENAME` es instantáneo para la base y catastrófico
> para el código viejo, que deja de encontrar la columna. No hay ventana de convivencia.

## Reglas duras

1. **Columna nueva: siempre admite nulos al principio.** Ponerla obligatoria en el mismo paso
   rompe todo lo que inserta hoy.
2. **Los datos se llenan por tandas**, con pausa entre una y otra. Una actualización de un
   millón de filas de un saque bloquea la tabla y frena el sistema.
3. **Toda migración se puede volver atrás**, y ese guion se escribe **al mismo tiempo** que
   el de ida — no después, no "si hace falta".
4. **Se puede correr dos veces sin romper.** Si se corta a la mitad, se vuelve a correr y
   termina bien.
5. **Índices sin bloquear**, cuando el motor lo permita.

## Antes de tocar producción

Chequeos que se corren **sobre los datos reales**, porque los supuestos se caen ahí:

- [ ] ¿Hay nulos en la columna que va a pasar a obligatoria?
- [ ] ¿Hay duplicados donde va a haber una restricción de unicidad?
- [ ] ¿Hay filas huérfanas que romperían una clave foránea?
- [ ] ¿Cuánto tarda con el **volumen de producción**? (Se prueba en un ambiente con volumen
      parecido, no con 200 filas.)

## Después

- [ ] **Contar filas** antes y después. Si no coincide, algo se perdió.
- [ ] **Sumas de control** sobre los campos numéricos.
- [ ] **Revisar a mano una muestra** al azar de los datos transformados.

El conteo solo no alcanza: se puede migrar la cantidad correcta de filas con el contenido
mal.

## Cómo se prueba

**Igual que todo lo demás: el test primero.**

1. Un test que carga datos como los de producción —con marcadores, nunca PHI real— y verifica
   el estado **antes**.
2. Se corre la migración.
3. El test verifica el estado **después**.
4. Se corre la vuelta atrás, y el test verifica que quedó como al principio.

**Con TDD estricto**, la regla dura 3 («la vuelta se escribe al mismo tiempo que la ida») y el verde mínimo
chocan: si el guion de vuelta se escribe completo junto con el de ida, el test 4 nace verde. Se resuelve como
cualquier firma: el guion de vuelta **nace vacío** en el mismo commit que la ida (`chore(firma): R<n> vacío`) y
se completa con el rojo del test 4. Así existe desde el primer momento y queda probado.

**Piso del motor para la vuelta atrás:** borrar una columna no existe en todos los motores ni en todas las
versiones (SQLite lo tiene desde 3.35 y no si la columna está indexada o en la clave): el piso de versión fijado
en `DEC-003` decide si la vuelta es `DROP COLUMN` o una tabla nueva con copia.

Ese cuarto paso es el que casi nadie hace, y es el único que prueba que la vuelta atrás
funciona. Un guion de rollback sin probar es una intención.

## Nada de PHI

Los datos de prueba de una migración se versionan igual que cualquier otro fixture.
Marcadores: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`,
`<dato-sensible>`.

**Y nunca se copia una tabla de producción a un ambiente de prueba** para "probar con datos
reales". Eso es sacar datos de personas de donde están protegidos.

## Quién aprueba

Una migración destructiva —borrar una columna, borrar una tabla, cambiar un tipo— **no la
decide la IA**. Se muestra qué se va a perder y **lo confirma un humano**, igual que el GATE
de BORRADO del tablero.

Con datos, la diferencia con un ticket es que acá no hay papelera.

## Cómo entra en el veredicto

| Estado | Cuándo |
|---|---|
| **OK** | Expandir/migrar/contraer respetado, vuelta atrás **probada**, conteos y sumas coinciden |
| **HALLAZGO** | Columna obligatoria de una, migración sin vuelta atrás, o no se puede correr dos veces |
| **SIN DATOS** | **No se probó con volumen parecido al de producción**, o no se probó la vuelta atrás. Si todavía no hay ambiente de producción definido (plataforma `⚠` en `DEC-003`), el volumen es **pendiente declarado**, no «no se pudo mirar»: se lista y no frena |
