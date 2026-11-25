# Lo que exige el método

Parte de la skill `desarrollo`: se lee cuando hay que explicar o defender por qué el método pide más que una guía genérica (evidencia, verificador distinto, tres estados).

## Lo que este método exige y una guía genérica no

| Agregado | Por qué |
|---|---|
| **Evidencia** del rojo antes del verde | Mandar «escribí el test primero» sin pedir prueba no cambia nada: un test escrito después cumple la letra |
| **Verificador distinto del productor** | Si el mismo agente codea y se aprueba, no hay control: hay una declaración |
| **Veredicto de tres estados** | Sin `SIN DATOS`, "no encontré nada" y "no pude mirar" se confunden, y el segundo pasa por aprobado |
| **Regla del cero** | Cero hallazgos sobre entrada externa no es aprobado: es no auditable |
| **Límites de módulo** ([[decisiones#DEC-002]]) | Sin esto, el código generado rompe la arquitectura del proyecto |
| **PHI prohibido con marcadores** | En código, tests, fixtures, logs, contrato y descripción del Merge Request |
