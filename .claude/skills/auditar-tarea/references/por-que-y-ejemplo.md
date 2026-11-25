# Por qué existe, dónde entra en el flujo y un ejemplo

Parte de la skill `auditar-tarea`: se lee cuando hace falta el porqué de la skill, ubicarla en el pipeline o ver un reporte de ejemplo.

> **Por qué existe esta skill.** La lista «Tests a escribir PRIMERO» es el artefacto
> más crítico de la Tarea, y su modo de falla es **silencioso**: `guiar-tdd` escribe
> **un test por ítem de la lista y nada fuera de ella**. Un caso que falta en la lista
> **no se prueba nunca** — no hay error, no hay warning, el pipeline queda verde y el
> agujero llega a producción. `verificar-tdd` tampoco lo salva: audita que *los tests
> de la lista* tengan su rojo, no que *la lista esté completa*. Nadie, en todo el
> flujo, miraba si a la lista le faltaba algo. Eso audita esta skill.

## Dónde entra en el flujo

```
redactar-tarea (DoR)  ->  [analizar-tareas, a pedido] (el SET cierra entre sí)
        -> cargar-a-azure §2b (1er chequeo: autochequeo al escribir)
        -> [auditar-tarea]    (2do chequeo, OPCIONAL y a pedido: otro agente)   <- esta skill
        -> desarrollo (no espera a esta skill; sus hallazgos quedan como pendientes)
        -> guiar-tdd (escribe un test por ítem)  ->  verificar-tdd (audita el rojo/verde)
```

Los dos chequeos son **distintos a propósito**: el de `cargar-a-azure` es **mecánico y
de forma** (¿están las secciones, los links, los campos?); este es **de fondo** (¿la
lista de tests cubre todo y sirve?). El primero lo hace quien escribe; el segundo, otro.

---

### Ejemplo (genérico)

> Una Tarea de capa `api` declara en su contrato los códigos `200`, `400`, `404` y `409`,
> y su tabla de «Casos de error» tiene tres filas. La lista de tests trae 4 ítems: caso
> feliz, `400`, `404` e «invariante de negocio».
>
> La auditoría reporta: **CON HUECOS**.
> - *Chequeo 3:* el código **`409` del contrato no tiene test**. Evidencia: aparece en
>   `responses` del fragmento OpenAPI y en la fila 3 de Casos de error, y ningún test lo
>   espera. Test que falta: «recurso ya tomado → `409` + `RECURSO_NO_DISPONIBLE`».
> - *Chequeo 8:* el test «el endpoint responde un JSON válido» **no puede fallar** —
>   ningún error de implementación lo pondría en rojo. Pregunta: ¿qué comportamiento
>   quería proteger ese test?
>
> No corrige la tarjeta: deja los dos ítems redactados para que el humano los apruebe y
> [[cargar-a-azure]] los cargue en otro turno.
