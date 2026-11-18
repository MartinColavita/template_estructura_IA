# Gestionar vulnerabilidades — qué se arregla primero, en qué plazo y cómo sale la tarjeta

Toma lo que encontraron los escaneos (de una imagen, de un servidor o de la aplicación), decide **qué se
arregla primero**, le pone **el plazo** que fija `DEC-009`, lo lleva al **registro `V-nnn`** del Cerebro y
propone **la tarjeta** por el pipeline del tablero. No arregla nada: el arreglo es código, por [[desarrollo]].

## Priorizar no es ordenar por CVSS

Cuatro cosas pesan, y ninguna alcanza sola:

| Qué | De dónde sale | Por qué pesa |
|---|---|---|
| **Está en KEV** (vulnerabilidades explotadas en la práctica) | El catálogo de CISA, en un archivo | Alguien ya la está usando contra otros |
| **EPSS** (probabilidad de explotación en los próximos 30 días) | El archivo diario completo de FIRST | Separa lo probable de lo teórico |
| **CVSS** (severidad), con su versión y su vector | El reporte del escáner | Cuánto daño haría; solo, no dice si va a pasar |
| **Exposición del activo** | El inventario: «Expuesto a internet» y «Criticidad» | La misma vulnerabilidad pesa distinto en un servidor expuesto que en uno interno |

La cuenta **la hace un script**, siempre igual (es de la otra mitad de esta función):

```bash
python -I bin/priorizar-vulnerabilidades.py --informe <json normalizado> [--epss-csv <archivo>] [--kev-json <archivo>] [--inventario <ruta>] [--json]
```

- `--informe` es la salida `--json` de `bin/escanear-imagenes.py`, `bin/auditar-host.py` o
  `bin/escanear-seguridad.py`: el esquema común de hallazgos. **Nunca** el reporte crudo de un escáner.
- **Los datos de KEV y de EPSS los baja una persona** y se los pasa por archivo: el script nunca baja nada. Se
  baja **el archivo completo** (el catálogo de KEV, el CSV diario de EPSS), **nunca se consulta CVE por CVE**:
  eso le cuenta a un tercero qué vulnerabilidades tenemos.
- **Sin el archivo de KEV o de EPSS, o con uno viejo, esa parte es `SIN DATOS`**: nunca «0 en KEV». Es el mismo
  criterio que el tablero sin acceso («no "0 candidatos"»).
- Lo que el script no mira lo dice al final de su reporte; eso es lo único que se mira con criterio.

La BOD 26-04 de CISA ordena por exposición, presencia en KEV, si la explotación se automatiza y el impacto, y su
plazo más corto es de 3 días. **Obliga sólo a agencias federales de Estados Unidos**: acá es referencia, no
norma. Los plazos del proyecto los fija `DEC-009`.

## El plazo

Sale de la fila «Prioridad y plazos» de `DEC-009` (por ejemplo: KEV en un activo expuesto, KEV no expuesto, crítica con
EPSS alto, el resto). **Mientras `DEC-009` esté en `⚠`, el plazo es una propuesta y se dice así**, con la marca
`⚠`; no se presenta como compromiso. El plazo corre desde que se detectó, no desde que se cargó la tarjeta.

## El registro `V-nnn`

Vive en `cerebro-digital/modulo-ejemplo/seguridad/vulnerabilidades.md` (en cada proyecto, el del módulo). Lo
escribe `cerebro-curator`, con el «sí» de la persona, como todo el Cerebro.

- **Una fila por CVE y activo** (alias del inventario): la misma vulnerabilidad en dos imágenes son dos filas;
  la misma en el mismo activo, escaneada dos veces, es la misma fila (se actualiza la fuente y la fecha).
- Lleva el CVSS **con su versión y su vector**, el EPSS **con su fecha**, si está en KEV, la prioridad, el
  plazo, el estado, la tarjeta y, si la hay, la excepción. Si se calcula un CVSS propio, se justifica métrica por
  métrica.
- **No lleva** la salida cruda del escáner, direcciones, nombres reales de servidores ni secretos.
- **Se cierra cuando un nuevo escaneo dice que ya no está** (el script, no la palabra de quien arregló): la
  fila pasa a `resuelta` con la fecha y el informe que lo mostró.

## Excepciones: con motivo, con nombre y con vencimiento

Aceptar un riesgo **no lo hace la IA**: lo propone, con el motivo a la vista, y **decide quien fije el equipo**,
que no puede ser quien escribió el cambio (`DEC-009`, «Supresiones y excepciones»).

- Una excepción lleva **el motivo, quién la aceptó (rol y persona) y la fecha en que vence**. **Sin vencimiento
  no es una excepción**: es una vulnerabilidad ignorada, y se pregunta.
- **Vencida, vuelve a estar abierta**, con su plazo original vencido: se avisa en la próxima revisión.
- «No es alcanzable desde el código» (VEX) es una afirmación que **firma una persona**, con el porqué; la IA
  puede mostrar la evidencia, no firmarla.
- Una supresión en el escáner de imágenes (`.trivyignore.yaml`, reglas de ignorar de Grype) **sin motivo escrito**
  no cuenta: `bin/escanear-imagenes.py` la trata como hallazgo, leyendo el reporte. Las del código (`.trivyignore`
  de texto, `# nosec`, `.gitleaksignore`) las mira `bin/escanear-seguridad.py`.

## La tarjeta: por el pipeline del tablero, con todos sus GATEs

Cada `V-nnn` que hay que arreglar sale como tarjeta por el mismo camino que cualquier otra: redacta
[[redactar-tarea]] (tipo **Bug**, o **Habilitador técnico** si es una actualización de plataforma) y carga
[[cargar-a-azure]] (o el tablero local de `DEC-006`). Rigen **todos** los GATEs de [[AGENTS]]:

- **GATE de TABLERO**: sólo el tablero autorizado.
- **GATE de deduplicación**: antes de crear se busca por **CVE + alias del activo** y por la etiqueta del tema,
  comparando objetivo y alcance ([[deduplicacion-antes-de-crear]]). Ante la duda, es duplicado. Una
  actualización de la misma biblioteca que cierra varios CVE en el mismo activo es **una** tarjeta.
- **GATE de confirmación**: el contenido completo a la vista y un «sí» antes de escribir.
- **GATE de NIVEL** (modo equipo): una Tarea pide la frase textual de la persona; si no, se redacta la Historia
  o el Bug.
- **GATE de TARJETA CONGELADA**: si la tarjeta ya está en un sprint y tomada, sólo se comenta ([[comentar-tarea]]).

La tarjeta dice: el CVE, el alias del activo, la severidad y la prioridad, el plazo, **la versión que lo
arregla**, cómo se verifica (el mismo escaneo, otra vez) y la `V-nnn`. **No lleva** el reporte crudo adjunto
(publicarlo es G4), direcciones, nombres reales de servidores ni el valor de ningún secreto.

## El arreglo

| Dónde está la vulnerabilidad | Cómo se arregla | Por dónde |
|---|---|---|
| Una dependencia de la aplicación | Subir esa dependencia, de a una, con la suite en verde | [[desarrollo]] (`cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/dependencias-y-config.md`) |
| La imagen base o un paquete de la imagen | Reconstruir la imagen con la base nueva; la despliega el pipeline | [[desarrollo]] y [[despliegue-continuo]] |
| Un paquete del servidor | Parche en la ventana de mantenimiento | [[operacion-de-servidores]] |
| Una configuración del servidor | Un cambio del plan de endurecimiento | [endurecer-servidor.md](endurecer-servidor.md) |
| El sistema operativo sin soporte | Migrar a una versión con soporte: es un proyecto, no un parche | Una Historia o un Habilitador, con su plan |

## Cómo se trabaja

1. **Produce** `nucleo-productor`: corre `bin/priorizar-vulnerabilidades.py` sobre el informe normalizado, arma
   en `borrador/seguridad/` la propuesta de filas `V-nnn` y de tarjetas (con su bloque de dedup).
2. **Verifica** `nucleo-verificador`: que cada fila salga del script y no de memoria; que ninguna excepción
   quede sin vencimiento; que ninguna tarjeta lleve datos crudos.
3. **Decide** la persona: las filas del registro (por `cerebro-curator`), las excepciones y cada tarjeta, con
   los «sí» que piden sus GATEs.

## Veredicto

```
VEREDICTO-INICIO
priorizacion            : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: priorizar-vulnerabilidades.py <estado>
plazos (DEC-009)        : OK | SIN DATOS (DEC-009 en ⚠: plazos propuestos)
excepciones             : OK | HALLAZGO (<sin vencimiento o vencida>)
tarjetas (dedup)        : OK | HALLAZGO | SIN DATOS (sin acceso al tablero)
BLOQUEANTES: <n>   SIN DATOS (no se pudo mirar): <n>   SIN DATOS (pendiente declarado): <n>
Verificado por: <herramienta> · <modelo> · sólo lectura, contexto limpio
VEREDICTO-FIN
```
