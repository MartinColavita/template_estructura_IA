# Subir de versión — framework o lenguaje, sin gran explosión

> Variante de [[modernizar-slice]] cuando `DEC-004` dice que el problema es **la versión**, no la forma:
> un framework con versión mayor nueva, un lenguaje o runtime con cambios incompatibles, una dependencia
> abandonada. Es la variante más corta y la que más se rompe por hacerla "de una".

## La regla

**Cambios chicos, reversibles y con la aplicación siempre en verde.** Cada paso es un Merge Request que
se puede revertir solo, con la suite completa y la red de caracterización en verde, y nunca mezcla subir
de versión con refactor ni con reglas.

## El orden

```
1. RED           caracterización de los flujos que la versión toca (caracterizar-comportamiento)
2. INVENTARIO    qué cambia entre versiones: la guía de migración oficial y el registro de cambios, leídos, no recordados
3. ADAPTADORES   compatibilidad primero: adaptadores que dejan convivir lo viejo y lo nuevo
4. TANDAS        transformaciones automáticas (las oficiales del framework si existen) en tandas chicas, cada una en verde
5. EN PARALELO   la suite corre en las dos versiones hasta el corte (dos trabajos en el pipeline)
6. CORTE         por bandera o por despliegue, con vuelta atrás escrita y probada
7. LIMPIEZA      recién después, se sacan los adaptadores (código muerto, con su evidencia)
```

## Qué se compara

`bin/paridad.py` sirve igual: el oráculo es la aplicación en la versión vieja; la nueva, la misma aplicación
en la versión nueva. Diferencias típicas que **no** son bugs y se aceptan con nombre: formato de fechas
por defecto, orden de claves en JSON, mensajes de error del framework. Diferencias que **sí** lo son:
códigos de estado, redondeos, zona horaria, codificación de texto.

## Lo que frena

| Freno | Por qué |
|---|---|
| Subir dos versiones mayores en un paso | Dos guías de migración mezcladas: no se sabe cuál rompió qué |
| Sin la corrida en paralelo en el pipeline | El corte se decide a ciegas |
| Vuelta atrás "obvia" no probada | Una vuelta atrás sin probar es una intención |
| Dependencia con CVE explotable o abandonada que se arrastra | Subir de versión era para eso; se resuelve o se declara en `aplicacion/deuda.md` |
