# Runbook — cómo se escribe, para que sirva a las tres de la mañana

> Un runbook es la receta escrita para un síntoma o una alerta: qué se mira, qué se hace, cómo se sabe que volvió y
> qué hacer si no vuelve. Con uno escrito, se recupera mucho más rápido que improvisando. Se escribe **antes** de
> necesitarlo, o justo después de un incidente que lo pedía. Escribirlo no toca ningún servidor.

## Cuándo se escribe

- Después de un incidente cuyo postmortem dice que faltaba, o que el que había falló ([incidente.md](incidente.md)).
- Para cada alerta que despierta a alguien: **una alerta sin runbook no se crea** (la regla de alertas está en
  `cerebro-digital/configuracion-ia/skills/desarrollo/references/metodo/observabilidad.md`).
- Para una tarea de mantenimiento que se repite ([mantenimiento.md](mantenimiento.md)). Si se repite mucho, además
  conviene un playbook revisado en su repositorio, por [[desarrollo]].

## El molde

Es `cerebro-digital/modulo-ejemplo/operacion/runbooks/plantilla-runbook.md`: se copia, no se reinventa. Arriba
lleva el **servicio** (su alias), las **alertas** que enlazan acá, el **dueño** (un rol), el **nivel máximo** entre
sus pasos y la **última verificación** (la última vez que alguien lo corrió de verdad). Abajo, en este orden: cuándo
se usa (y qué no cubre), qué le pasa a la gente, una lista rápida, antes de empezar, diagnóstico, mitigación paso
por paso, verificación, si nada funciona, el aviso listo y el historial.

## Cada paso, con sus seis partes

```markdown
### Paso 2 — Reiniciar el servicio de la cola · Nivel N1
- Precondición: el paso 1 mostró la unidad `cola.service` caída y el disco por debajo del 90 %.
- Comando: `sudo systemctl restart cola.service`
- Salida esperada: no imprime nada y sale con 0; `systemctl is-active cola.service` dice `active`.
- Si falla: no se reintenta más de una vez; se pasa a «Si nada funciona».
- Vuelta atrás: no cambia versión ni configuración; si no levanta, queda como estaba (caída) y se escala.
```

1. **Precondición**: qué tiene que ser cierto para correrlo (lo que mostró el paso anterior). Si no se cumple, el
   paso no se corre.
2. **Comando**: el exacto, copiable, sin «según corresponda» ni marcadores sin explicar. Los valores que cambian
   (un alias, una hora) van como `<alias>` y se dicen arriba de dónde salen.
3. **Salida esperada**: lo que se tiene que ver, con el código de salida.
4. **Si falla**: qué hacer, en concreto. «Investigar» no es un paso.
5. **Nivel**: N0, N1, N2 o N3, con los criterios de [mantenimiento.md](mantenimiento.md) y de [[AGENTS]]. En
   producción, todo lo que cambia algo es N2.
6. **Vuelta atrás**: cómo se deja como estaba. Si no tiene, el paso es **N3**.

Un paso **N3** no lleva el comando para que lo corra la IA: lleva el bloque **«Lo hace una persona»**, con qué hay
que hacer, por qué no lo hace la IA y qué resumen le arma la IA para que decida.

## Para el cerebro de las tres de la mañana

- **Verbos y órdenes, no ensayos.** Quien lo lee está cansado y apurado: una acción por paso.
- **Diagnóstico primero, con scripts**: `python -I bin/salud-host.py --ssh <alias>` antes de cualquier
  mitigación, y la misma medición al final para saber que volvió.
- **Simulación antes de lo que cambia**, cuando la herramienta la tiene (`logrotate -d`, `--check`), sabiendo que
  una simulación no es una garantía.
- **Ni secretos ni datos de personas.** Un runbook dice **dónde** vive una credencial (el gestor que fije
  `DEC-008`), nunca su valor. Los ejemplos van con marcadores.
- **Sin nombres de personas**: roles. Sin IPs: alias del inventario.

## Cómo se usa durante un incidente

Correr un paso N0 no pide nada. Para un paso N1 o N2, el paso **ya es** un plan de cambio: se copia al molde de
[mantenimiento.md](mantenimiento.md) (comando, salida esperada, cómo se verifica y vuelta atrás ya están escritos),
pasa por `python -I bin/gate-operacion.py --plan <plan>` y se pregunta con el nivel que corresponde. Que esté en un
runbook **no saltea el «sí»**: lo hace más rápido de dar, porque la persona ya sabe qué va a pasar.

## Dónde nace y cómo entra al Cerebro

1. Nace en `borrador/operacion/runbooks/RB-nnn-<slug>.md`, con el siguiente número libre del módulo.
2. Lo verifica `nucleo-verificador`, en sólo lectura y con contexto limpio: que cada paso tenga sus seis partes,
   que ningún paso N3 tenga un comando para la IA, que las rutas y los alias existan, que no haya secretos ni datos
   de personas. ⚠ Esa forma todavía no la cuenta un script (`auditar-operacion.py`, fase 2): es criterio del
   verificador y así se declara en el veredicto.
3. Entra a `operacion/runbooks/` del módulo **sólo por `cerebro-curator`**, con el «sí» de la persona, y queda en
   `log.md`.
4. **Un runbook que nadie corrió no está verificado.** La fecha de última verificación se actualiza sólo cuando
   alguien lo corrió de verdad (en un incidente o en un simulacro); un runbook viejo se avisa (⚠ el plazo lo fija
   `DEC-008`).

## Cómo entra en el veredicto

```
pasos completos : criterio del verificador (seis partes por paso); SIN DATOS si no se revisó paso por paso
niveles         : ningún N3 con comando para la IA; producción en N2
datos sensibles : ni secretos ni datos de personas
verificación    : última verificación con fecha real; SIN DATOS si nunca se corrió
```
