# Detalle del plan (paso 4)

Parte de la skill `desarrollar-asignadas`: se lee en el paso 4, al armar el plan que se muestra para confirmar.

- si programa Gemini, su modo de permisos (`--approval-mode`): se
  recomienda `auto_edit`, que aprueba solo las ediciones y deja los
  comandos para que el humano los apruebe en la pestaña;
- **avisos**, sin pregunta aparte: el Cerebro de `develop` atrasado
  respecto de `main`, un el `ARCHITECTURE.md` de la carpeta `docs` del repo que contradice
  al Cerebro, Tareas que tocan los mismos archivos (van en serie) y
  Tareas que van a superar los 20 archivos ([[orquestador-desarrollo]]
  §«Convenciones del Cerebro: reglas que se chequean»).

**Motor único (`DEC-005`, modo solo).** Si el proyecto desarrolla con un solo motor, verifica **otro agente del
mismo motor, con contexto limpio y sólo lectura**, y el veredicto lo declara («Verificado por: Claude Code ·
sólo lectura, contexto limpio»). Si hay otro motor instalado, se prefiere.
