# Refactor en el lugar — un módulo por vez

> Variante de [[modernizar-slice]] cuando `DEC-004` dice **refactor**: la aplicación se transforma donde está,
> sin repositorio nuevo. La regla general de [refactor.md](../../../skills/desarrollo/references/metodo/refactor.md)
> (cambiar la forma sin cambiar el comportamiento; los tests no se tocan) vale entera; acá va el orden.

## El orden, y por qué

```
1. RED        caracterización del módulo, en verde, sin tocar producción   (caracterizar-comportamiento)
2. LÍMITES    primero los límites de módulo (DEC-002): mover, no cambiar
3. FORMA      después la forma: nombres, duplicación, casos de uso, condicionales
4. REGLAS     recién ahora, con rojo normal, lo que estaba mal y una persona decidió arreglar
5. VERIFICAR  otro agente corre la suite completa (la red sigue en verde) y verificar-tdd --modo caracterizacion
```

- **Límites antes que forma**: mientras un módulo importe la `api` o la `infra` de otro, cualquier
  refactor "de forma" se apoya en algo que se va a mover. Primero se corta la dependencia; después se
  ordena adentro.
- **De adentro hacia afuera**: `domain` primero, después `application`, después los adaptadores.
  El dominio es lo que más reglas esconde y lo que menos depende del resto.
- **Un módulo por Tarea** (C7). Si el diff abarca dos, la Tarea estaba mal partida.

## Qué se declara antes de empezar

En `arquitectura/decisiones.md`, bajo `DEC-004`, **qué código queda fuera de `C1…C8` mientras tanto y en
qué orden se trae**. Así el verificador no frena todo el repositorio el primer día: lo que está declarado
como pendiente no es `HALLAZGO` hasta que exista la Tarea que lo arregla.

## Cómo se mide el avance

- Las sondas del Doctor de límites y de prácticas pasan de `HALLAZGO` a `OK` módulo por módulo:
  `python doctor/doctor.py --comparar` muestra la tendencia.
- La fila del módulo en `aplicacion/modernizacion.md` usa los mismos estados que la migración:
  `contrato` = límites escritos; `red` = caracterización en verde; `construido` = límites y forma hechos;
  `paridad` = la red sigue en verde y `verificar-tdd` dio `OK`; `cortado` = el módulo cumple `C1…C8` y el
  Doctor no lo marca; `apagado` no aplica (no hay app vieja que apagar). Como no hay tráfico que cortar, la
  barrera es `bin/mapa-modernizacion.py corte <modernizacion.md> --slice <modulo> --veredicto <bloque VEREDICTO>`:
  exige `5 verificar-tdd : OK`, modo caracterización, cero bloqueantes, reciente, y una persona que apruebe.
  Corpus y golden no son obligatorios en esta estrategia (la red puede ser sólo tests en el repositorio).

## Lo que frena

| Freno | Por qué |
|---|---|
| Un test de caracterización en rojo | El refactor cambió comportamiento: se vuelve atrás, no se "ajusta" el test |
| Refactor y cambio de regla en el mismo commit | No se puede revisar; van separados, y si son grandes, en Merge Requests separados |
| Un bug viejo "arreglado" sin preguntar | Alguien puede depender de él: va a la curaduría como regla candidata |
| Código sin red | Sin red, un refactor es un cambio a ciegas: primero `caracterizar-comportamiento` |
