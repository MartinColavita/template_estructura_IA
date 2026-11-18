# Endurecer un servidor — de los hallazgos a un plan, cambio por cambio

Toma los hallazgos de una auditoría ([auditar-servidor.md](auditar-servidor.md)) y arma **un plan cambio por
cambio**: qué cambia, cómo está antes y cómo queda después, qué riesgo tiene, cómo se vuelve atrás y cómo se
prueba que el acceso sigue. **Proponer no es aplicar**: el plan lo revisa otro agente, lo aprueba una persona y
lo aplica el pipeline.

## Endurecer es código

Un cambio de endurecimiento se escribe como **playbook o infraestructura como código** en el repositorio de
infraestructura, y entra por la puerta de todo el código, [[desarrollo]] (rama, Merge Request, verificador
distinto del que produce, nada sale sin «sí»), con lo específico de [[arquitectura-e-infraestructura]]. **Lo
aplica el pipeline**, no la IA (GATE de INFRAESTRUCTURA, en [[AGENTS]]). Así el cambio queda revisado,
repetible en todos los servidores y con su vuelta atrás en la historia.

El **cambio a mano** en un servidor queda para lo que no puede esperar al pipeline, **fuera de producción**:
pasa por el GATE de SERVIDOR (el inventario tiene que autorizar ese alias hasta el nivel del cambio) y se
escribe, además, como **plan de cambio** con el molde de
`cerebro-digital/configuracion-ia/skills/operacion-de-servidores/references/mantenimiento.md`, que es lo que lee
`python -I bin/gate-operacion.py --plan <plan>` (alias, nivel, ventana, respaldo, comando exacto, cómo se
verifica, vuelta atrás). Ese script y ese molde son de [[operacion-de-servidores]]: acá no se repiten.

## El plan

Va a `borrador/seguridad/<fecha>-<alias>/plan-endurecimiento.md`. Una fila por cambio, sin agrupar:

| # | Hallazgo que cierra | Control de referencia | Qué cambia | ANTES | DESPUÉS | Riesgo | Vuelta atrás | Cómo se prueba que el acceso sigue | Nivel |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `<regla del informe>` | `<perfil · número de control>` | `<archivo o parámetro>` | `<valor actual, leído>` | `<valor nuevo>` | `<quién o qué se puede quedar afuera>` | `<el paso exacto, y el archivo guardado>` | `<la prueba, antes de cerrar la sesión>` | N1 · N2 · N3 |

- **El ANTES se lee, no se supone**: sale del informe de la auditoría o de una lectura N0. Sin él, la fila es
  `SIN DATOS` y no se propone.
- **La acción reversible más chica** que cierra el hallazgo. Si cerrar uno obliga a tocar tres cosas, son tres
  filas.
- **De a un cambio por servidor**, y en orden: primero lo que no puede dejar a nadie afuera.
- **Primero en un ambiente de prueba**, después en producción, con el mismo playbook.
- **Sin vuelta atrás escrita, no es un cambio que la IA proponga para aplicar**: es N3 (lo hace una persona,
  con el resumen a la vista).

## Qué nivel lleva cada cambio

| Cambio | Nivel | Por qué |
|---|---|---|
| Un parámetro que se deshace y no toca el acceso (un `sysctl`, un servicio que no se usa, el nivel de registro) fuera de producción | **N1**: un «sí» sobre el plan mostrado | Se deshace y no deja a nadie afuera |
| El servicio de SSH, el firewall o PAM, **a mano** en el servidor | **N3**: lo aplica una persona, o el pipeline como código | Un error corta el acceso de todos, también el de quien arregla |
| Otro cambio que puede dejar a todos afuera (la red) | **N2**: dos «sí» en turnos distintos, con el ANTES y el DESPUÉS a la vista | Igual |
| Cualquier cambio en **producción** | **N2** | El daño lo paga el negocio |
| **Quién entra**: usuarios, claves autorizadas, grupos, `sudo`, roles | **N3**: nunca la IA | Tocar accesos es de una persona |
| Rotar o revocar un secreto o una credencial | **N3** | Ver o rotar un secreto no lo hace la IA ([[AGENTS]]) |
| Desactivar un control (firewall, SELinux o AppArmor, auditd, el registro de auditoría, MFA) | **N3** | Ni para «probar» |

Para un cambio que puede dejar a todos afuera (en el plan del pipeline, en el resumen para la persona que lo aplica
a mano, o entre los dos «sí» de un N2) se muestra:

1. El **ANTES y el DESPUÉS** del archivo o la regla, completos.
2. La **validación sin aplicar**: `sshd -t` para la configuración de SSH, `ufw --dry-run` para el firewall
   (muestra lo que haría sin aplicarlo).
3. La **segunda sesión**: quien aplica abre una sesión nueva con el cambio aplicado **antes de cerrar la que está
   abierta**; si no abre, vuelve atrás desde la que quedó.
4. Una **persona con acceso por consola** presente, y el camino de vuelta por consola escrito.

La pregunta, en criollo: *«Para cerrar el hallazgo 3 propongo prohibir el ingreso con contraseña al acceso
remoto de `web-prueba-1`. Ese cambio no lo aplico yo: va en el playbook, o lo hacés vos a mano. Antes de cerrar tu
sesión, **abrí vos** otra para comprobar que entrás; si no entra, volvé a la configuración guardada desde la que
quedó abierta. Si sale mal, alguien tiene que poder entrar por la consola. ¿Te preparo el cambio?»*

## Controles de referencia: por número, nunca por texto

- La línea base por sistema operativo la fija `DEC-009` y la escribe la política del módulo
  (`cerebro-digital/modulo-ejemplo/seguridad/politica.md`).
- Se cita **el perfil y el número de control** («perfil `<id del perfil>` de ComplianceAsCode para
  `<sistema>`, control `<número>`»). **Nunca se copia el texto** de un benchmark de CIS ni de una guía STIG al plan, al
  Cerebro ni a una skill: la licencia de CIS lo prohíbe; la de STIG no está verificada: tampoco se copia.
- **Nunca se escribe «cumple CIS»** ni «certificado»: se escribe «resultado del perfil X de ComplianceAsCode,
  fecha Y». Un escaneo no es una certificación.
- Lo que se puede automatizar sale del contenido libre de ComplianceAsCode. Si una persona corre OpenSCAP, el
  playbook se genera **desde los resultados** (`oscap xccdf generate fix --fix-type ansible` sobre el ARF), no
  desde el perfil entero, para no incluir lo que ya está bien; y se revisa fila por fila como cualquier cambio.

## Lo que no se hace nunca

- **Remediación en lote**: `oscap xccdf eval --remediate`, `oscap xccdf remediate`, un rol de endurecimiento
  entero de una sola vez, `apt upgrade` de corrido. Algunos roles publicados avisan que pueden tener
  consecuencias no deseadas, incluso desinstalar el firewall o el motor de contenedores.
- **Confiar en `--check` de Ansible como simulacro** de un rol de endurecimiento: hay roles que avisan que no lo
  soportan. El simulacro es un ambiente de prueba.
- **Copiar una skill o un guion publicado que endurece de corrido**, o «nunca te deja sin SSH» sin prueba: sirven
  como lista de temas, no como forma de trabajar.
- **Aplicar un cambio que no estaba en el plan mostrado**, o dos cambios con un solo «sí».
- **Cambiar de servidor por su cuenta**: si el plan sirve para otro alias, es otro plan y otra pregunta.

## Cómo se trabaja

1. **Produce** `nucleo-productor`: lee el informe, lee el ANTES (N0), arma el plan y, aprobado el plan, escribe
   el playbook en el repositorio de infraestructura por [[desarrollo]].
2. **Verifica** `nucleo-verificador` (sólo lectura, contexto limpio): que cada fila tenga ANTES leído, vuelta
   atrás y prueba de acceso; que el nivel sea el de la tabla; que ningún control se cite por texto.
3. **Aprueba** una persona, con los «sí» que pide el nivel. **Aplica** el pipeline (o, a mano y fuera de
   producción, con `bin/gate-operacion.py`; si es N3, una persona).
4. **Quien cambia no certifica**: después del cambio se vuelve a auditar con el mismo script
   (`bin/auditar-host.py`) y el veredicto de antes y de después va al cierre. Si el hallazgo sigue, la fila no
   está cerrada.

## Veredicto

```
VEREDICTO-INICIO
plan (<alias>), fila <n>   : OK | HALLAZGO | SIN DATOS (<motivo>)   -- criterio: ANTES leído, vuelta atrás, prueba de acceso, nivel
re-auditoría (<alias>)     : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: auditar-host.py <estado>
BLOQUEANTES: <n>   SIN DATOS (no se pudo mirar): <n>   SIN DATOS (pendiente declarado): <n>
Verificado por: <herramienta> · <modelo> · sólo lectura, contexto limpio
VEREDICTO-FIN
```

## Qué queda dónde

| Qué | Dónde |
|---|---|
| El plan, mientras se discute | `borrador/seguridad/<fecha>-<alias>/` (nunca se versiona) |
| El playbook o la infraestructura como código | Su repositorio, por [[desarrollo]] |
| Un control que se decide **no** aplicar, con su motivo | Las excepciones de control de `seguridad/politica.md`, por `cerebro-curator` con el «sí» |
| El cambio hecho a mano | El registro de cambios de [[operacion-de-servidores]] |
