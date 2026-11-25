# El ritual mensual

Parte de la skill `mejorar-ecosistema`: se lee cuando toca la revisión mensual del ecosistema, o cuando la persona pide revisarlo entero.

## El ritual mensual (quince minutos)

```
python -B bin/medir-uso-skills.py --dias 60 --proyecto <ruta del núcleo>   # qué se usó, qué no, qué pesa
bash doctor/bin/doctor.sh --comparar                                         # cómo venimos
python -B bin/verificar-skills.py                                            # la especificación
/doctor                     (en Claude Code: skills, MCP y plugins sin uso frente a su costo; CLAUDE.md derivable)
/doctor prompt-audit        (en Claude Code: instrucciones viejas o contradictorias, con ediciones propuestas)
```

Lo que salga se convierte en propuestas, **de a una**, y se decide. Las dos herramientas de Claude Code informan
primero y piden confirmación antes de tocar: encajan en esta regla sin cambiarla.
