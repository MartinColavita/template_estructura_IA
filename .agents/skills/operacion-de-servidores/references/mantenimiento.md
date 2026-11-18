# Mantenimiento — lo que cambia algo en un servidor

> Parches, certificados, disco, logs, respaldos y reinicios. Todo lo que **cambia** algo pasa por un **plan de
> cambio** escrito, por `bin/gate-operacion.py` y por el «sí» de una persona. Las barreras enteras están en
> [[AGENTS]]; acá, cómo se aplican a cada tarea.

## El nivel lo pone el daño, no el apuro

Ante la duda entre dos niveles, vale el más alto. En **producción** todo cambio es **N2**, aunque se deshaga.

| Tarea | N0 — sola (leer) | N1 — un «sí» | N2 — dos «sí», con ANTES y DESPUÉS | N3 — nunca la IA |
|---|---|---|---|---|
| **Parches** | Ver qué hay pendiente, en simulación | Aplicarlos en un servidor que no es de producción | Aplicarlos en producción, empezando por el canario | Actualizar sin vuelta atrás (sin imagen ni paquete anterior) |
| **Certificados** | Medir cuánto les queda (`bin/vigencia-certificados.py`) | Disparar la renovación del cliente que ya está configurado y recargar el servicio, fuera de producción | Lo mismo, en producción | Generar, copiar, mover o mostrar una clave privada |
| **Disco** | Medir disco e inodos (`bin/salud-host.py`) | Aplicar la retención que ya está configurada (rotar logs) | Cambiar una retención o agrandar un disco | Borrar a mano archivos, datos, volúmenes o respaldos para hacer lugar |
| **Logs** | Leer una ventana acotada ([diagnosticar.md](diagnosticar.md)) | Forzar una rotación ya configurada | Cambiar la configuración de logs en producción | Apagar logs, monitoreo o alertas |
| **Respaldos** | Listarlos y chequearlos sin reparar | Lanzar un respaldo fuera de horario; restaurar una prueba en un destino aislado | Cambiar qué se respalda o cada cuánto | Borrar o podar respaldos, repararlos, restaurar encima de datos vivos |
| **Reinicios** | Ver si hay uno pendiente (`bin/salud-host.py`) | Reiniciar **un** servicio fuera de producción | Reiniciar un servicio en producción, o un servidor | Reiniciar sin saber cómo vuelve (sin vuelta atrás escrita) |

Lo que no está en la tabla se clasifica con la misma pregunta: **¿qué es lo peor que pasa si sale mal, y se puede
volver?** Si no se puede volver, es N3. La regla de [[AGENTS]] manda sobre esta tabla.

## El plan de cambio

Se escribe en `borrador/operacion/plan-<alias>-<AAAA-MM-DD>.md`, **uno por servidor**, copiando este molde (sin el
bloque de afuera) y reemplazando cada marcador `<...>`:

````markdown
# Plan de cambio — <qué, en una línea>

| Campo | Valor |
|---|---|
| Qué | <qué se cambia y por qué, en criollo> |
| Alias | `<alias del inventario>` |
| Nivel | <N1 o N2> |
| Ventana | <cuándo; la del inventario> |
| Respaldo verificado | <cuál, de cuándo y cómo se verificó; o «no toca datos ni configuración»> |

## Comando exacto

```sh
<el comando, tal cual se va a correr>
```

## Salida esperada

<lo que tiene que imprimir y con qué código sale>

## Cómo se verifica

<el script o la medición que dice que quedó bien>

## Vuelta atrás

<los pasos exactos para dejarlo como estaba, y cuánto tardan>
````

Qué exige cada parte, y lo mira `bin/gate-operacion.py` (FRENA si falta algo):

- **Alias**: el exacto del inventario. El plan es de **un** servidor; varios servidores son varios planes.
- **Nivel**: N1 o N2. Un N3 frena siempre; un N0 no necesita plan.
- **Comando exacto**: el que se va a correr, sin marcadores. «Algo como…» no es un comando.
- **Salida esperada** y **Cómo se verifica**: qué se tiene que ver para decir que salió bien, medido por un script
  siempre que exista uno (`bin/salud-host.py`, `bin/vigencia-certificados.py`).
- **Vuelta atrás**: pasos concretos. «No hay» o vacía quiere decir que el cambio es **N3**: lo hace una persona.
- **Ventana** y **Respaldo verificado**: el script los **muestra**, no los calcula ni los mide. La persona los mira.

## El ciclo, paso por paso

```
1. ANTES      diagnóstico N0 (diagnosticar.md): cómo está hoy, medido por script
2. PLAN       el molde de arriba, en borrador/operacion/
3. GATE       python -I bin/gate-operacion.py --plan <plan>   ->  OK, o se completa
4. PREGUNTA   N1: un «sí» sobre el plan mostrado. N2: dos «sí» en turnos distintos, con el ANTES y el DESPUÉS a la vista
5. CAMBIO     el comando exacto, una vez, en la sesión principal y a la vista de la persona
6. DESPUÉS    la verificación del plan, por script
7. REGISTRO   una línea en operacion/cambios.md, por cerebro-curator
```

- **Quién corre el comando.** La sesión principal, con la **identidad de cambio** que firmó la persona para esa
  ventana ([acceso.md](acceso.md)). Nunca un worker en segundo plano. Sin identidad de cambio, lo corre la persona
  con el plan a la vista, y la IA verifica después.
- **Si sale distinto de lo esperado, se frena y se cuenta.** No se prueba otro comando para ver si anda. Volver
  atrás con lo que dice el plan se ofrece como una pregunta nueva. En un incidente declarado, ordena quien comanda
  ([incidente.md](incidente.md)).
- **Un cambio a la vez por servidor.** Si hay otro plan abierto para el mismo alias, se termina o se descarta antes.
- **Producción, sólo en la ventana.** La excepción es un incidente declarado.
- **`DEC-005` no cubre nada de esto**: cada «sí» se pide, en su turno.

## De a un servidor, y con canario

Cuando el mismo cambio va a varios servidores, el **primero es el canario**: se cambia, se verifica y se deja
andar el tiempo que fije `DEC-008` (⚠ propuesta: una hora en prueba, un día en producción). Recién con el canario
en OK se arma el plan del siguiente. Si el canario sale mal, se vuelve atrás y no se toca ningún otro.

Si el mismo cambio se repite, deja de ser un plan suelto: se escribe como **playbook revisado** en su repositorio
de infraestructura, por [[desarrollo]] y [[arquitectura-e-infraestructura]]. Una corrida de simulación
(`ansible-playbook --check --diff`) es **una simulación, no una garantía**: los módulos sin soporte no simulan nada,
y el diff puede mostrar un secreto (se apaga con `diff: false` en esa tarea).

## Lo propio de cada tarea

**Parches.** Automáticos, sólo los de seguridad y **sin reinicio automático en producción** (⚠ `DEC-008`). En la
familia RHEL, ojo con el temporizador `dnf-automatic-install.timer`: instala aunque la configuración diga otra cosa.
Qué falta parchear todavía no lo mide ningún script: es `SIN DATOS` hasta `parches-pendientes.py` (fase 2), y la
lista la trae una persona con la simulación del gestor de paquetes (`apt-get -s dist-upgrade`,
`dnf updateinfo list --security`). Después de parchear, el reinicio pendiente lo mide `bin/salud-host.py`.

**Certificados.** Lo sano es la renovación automática (ACME) y que un script vigile que ocurrió: renovar a mano
«no se recomienda». `bin/vigencia-certificados.py` da HALLAZGO con menos de un tercio de la vida o menos de N días,
porque la vida de los certificados baja a 64 días en 2027 y a 45 en 2028 y un umbral fijo de 30 días deja de servir.
Disparar la renovación de un cliente ya configurado no lee ni muestra la clave privada; tocar la clave a mano, sí:
eso es N3.

**Disco.** Primero se mide qué se llena (disco o inodos, qué montaje). Lo que ocupa, montaje por montaje, lo trae
una persona (`du -xh --max-depth=1 <montaje>`) hasta que lo mida un script. Rotar lo que ya tiene retención
configurada es N1; borrar a mano, N3. Un journal grande se acota con su configuración (`SystemMaxUse`), que es
cambiar la retención: N2.

**Logs.** `logrotate -d` simula y no cambia nada; forzar la rotación es N1. Cambiar qué se loguea o cuánto se
guarda, N2 en producción. Apagar el log, el monitoreo o una alerta, N3; un silencio de alerta, sólo con vencimiento
y atado a un incidente.

**Respaldos.** La regla es **3-2-1**: tres copias, en dos medios distintos, una fuera del sitio, más una copia
fuera de línea o inmutable. **Un respaldo que nunca se restauró es `SIN DATOS`, no OK.** Chequear sin reparar
(`restic check --read-data-subset`, `borg check`) es N0; reparar (`--repair`), podar (`forget`, `prune`) o borrar
es N3. Que el último respaldo esté fresco todavía no lo mide ningún script: `SIN DATOS` hasta
`frescura-respaldos.py` (fase 2). Restaurar para probar, siempre en un destino aislado.

**Reinicios.** Un servicio: N1 fuera de producción, N2 en producción. Un servidor: N2, con la vuelta atrás escrita
(por ejemplo, arrancar con el núcleo anterior) y el respaldo verificado si hay datos.

**Windows Server.** ⚠ La fase 1 no lo cubre: el colector es `sh`. Lo que se haga queda `SIN DATOS` y lo opera una
persona.

## El registro

Cada cambio N1 o N2 ejecutado deja una línea en `operacion/cambios.md` del módulo, que escribe `cerebro-curator`
con el «sí» de la persona: fecha, alias, nivel, qué, el plan, quién aprobó (rol), el resultado y la verificación.
Es el resumen: el registro completo (qué entró por SSH y qué corrió `sudo`) queda **en el servidor**, donde fije
`DEC-008`. Esa tabla es lo primero que se lee en un diagnóstico: la pregunta que más rinde es **«¿qué cambió?»**.

## Cómo entra en el veredicto

| Chequeo | OK | HALLAZGO / FRENA | SIN DATOS |
|---|---|---|---|
| Plan y nivel | `gate-operacion.py` en OK | FRENA: lo que el script dice que falta | No hay plan o inventario que leer |
| Resultado | La verificación del plan, por script, en OK | Salió distinto de lo esperado | La verificación no corrió |
| Respaldo | — | — | Siempre, hasta que lo mida un script: se muestra lo declarado |
