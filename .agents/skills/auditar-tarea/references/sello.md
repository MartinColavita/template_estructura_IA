# El sello de auditar-tarea: formato y vigencia

Parte de la skill `auditar-tarea`: se lee cuando se va a dejar el veredicto en la tarjeta, o cuando hay que saber si un sello anterior sigue vigente.

```
Auditoria de Tarea - auditar-tarea
Veredicto: COMPLETA | CON HUECOS | NO AUDITABLE
Fecha: <AAAA-MM-DD>
Rev de la Tarea auditada: <System.Rev al LEER la Tarea>
Historia padre: #<ID>
Rev de la Historia padre:  <System.Rev del padre al LEERLA>
Escenarios del padre encontrados: <N>        <- si dice 0, el loop BDD no existe
Hallazgos: <cantidad>  (el detalle, en el reporte)
Pendientes a confirmar:
- <hallazgo, una linea, redactado como pendiente>   <- uno por hallazgo; "Ninguno" si no hay
```

La lista «Pendientes a confirmar» del sello es la que mira la revisión **antes de cerrar** la
Tarea ([[comentar-tarea]] §«Antes de cerrar una Tarea»): un hallazgo que sólo vive en el
reporte del chat no aparece ahí.

**Cuándo vence el sello: cuando cambia lo auditado, no cuando se guarda la tarjeta.** En Azure
**toda** escritura directa sobre un work item crea una revisión: el propio sello (un
comentario de [[comentar-tarea]]), asignarla, pasarla a Active, la regla del tablero que
activa al padre cuando un hijo arranca. Ninguna cambia lo que se auditó.

> Por eso la vigencia **no se mide contando `Rev`**. Con «venció si el `Rev` avanzó» el sello
> **nace vencido** —sellar ya suma una revisión— y con «más de uno» cualquier comentario de un
> dev, o colgarle una Tarea hermana a la Historia, frena Tareas sanas. Un control que se
> dispara por cosas que no tocan lo que controla termina ignorado, que es peor que no tenerlo.

Se mira **qué campos** cambió cada revisión posterior. Cuenta como **cambio de contenido**:

| Dónde | Campos que cuentan |
|---|---|
| La Tarea | Título · Descripción (contrato, SDD, tests, modos de falla) · Criterios de aceptación, si el tipo los tiene · de **qué Historia cuelga** |
| La Historia padre | Título · Descripción · Criterios de aceptación |

**No** cuentan: comentarios (incluido el sello), Estado, Asignado, Etiquetas, Iteración, Área,
estimaciones, ni vínculos a otros ítems (hijos, Related).

- **Vigente**: ninguna revisión de la Tarea posterior a `Rev de la Tarea auditada`, ni de la
  Historia posterior a `Rev de la Historia padre`, cambió un campo de contenido, y la Tarea
  sigue colgando de esa misma Historia.
- **Vencido**: alguno cambió — un Escenario nuevo en la Historia, un `Entonces` editado, un
  test sacado de la lista. Esto cubre el agujero de que el sistema audita **un instante** y
  después nadie mira los cambios.
- **SIN DATOS**: no se pudo leer el historial de cambios. **No es vigente.** Si el motivo es
  de la tarjeta, se re-audita. Si es de **la máquina** —sin token, sin red, sin Python— el
  script lo dice, y re-auditar **no** lo destraba: se arregla el acceso y se vuelve a correr.

**Vale solo el sello más reciente.** Como un comentario ya no vence nada, en la tarjeta puede
haber dos sellos que el script da por vigentes. Manda el **último** (el de mayor `Rev de la
Tarea auditada`): si ese no dice **COMPLETA**, sus hallazgos siguen como pendientes, aunque haya
uno anterior que sí.
Un sello **sin** la línea `Historia padre: #<ID>` (formato anterior) es **SIN DATOS** y se
re-audita: el `#ID` **nunca** se completa con el Parent de hoy, porque entonces se compararía
el padre actual contra sí mismo y daría vigente una Tarea que se movió.

**Si la Tarea cambió de Historia**, el script la da vencida y además hay que correr
[[analizar-tareas]] sobre las Tareas de **las dos** Historias: a la de origen le puede haber
quedado un Escenario que solo cubría la Tarea que se fue, y sus hermanas siguen vigentes.

**Cómo se verifica.** `get_work_item` da cómo está la tarjeta **ahora**, no qué cambió en cada
revisión, y el MCP no expone el historial. Lo lee el script de solo lectura, con los números
del sello, parado en la raíz del repositorio:

```
bash bin/verificar-sello.sh tarea <id-tarea> <Rev de la Tarea> <id-historia> <Rev de la Historia>
```

(En PowerShell, `.\bin\verificar-sello.ps1` con los mismos argumentos.) Sale `0` VIGENTE, `1`
VENCIDO —y dice qué revisión cambió qué campo— o `2` SIN DATOS. Entra igual que el MCP: con
`AZDO_PAT` o, si no está, con la sesión de Azure CLI (`az login`); nunca muestra el token y
solo lee del tablero autorizado.

El sello se postea en HTML ([[comentar-tarea]] §«Formato»), así que quien lo busca lo lee
sobre el texto del comentario **sin las etiquetas**, línea por línea.

**En modo lote** ([[planificar-lote]]) se audita el borrador, antes de que exista la tarjeta.
Al escribir, el lote verifica que el texto de la tarjeta sea **igual al archivo auditado** (con
los `[T-nn]` ya reemplazados por su `#ID`; se compara el texto sin etiquetas y con los espacios
normalizados, porque Azure reescribe el HTML) y recién ahí sella, con la revisión que quedó como
`Rev de la Tarea auditada` y, como `Rev de la Historia padre`, la revisión verificada de la
Historia. Si no son iguales, la tarjeta queda **sin sello**, se re-audita si se quiere, y el
sello nuevo pide su propia confirmación ([[comentar-tarea]]). El formato del sello no cambia,
así que `verificar-sello` lo lee igual.
