# Prompt maestro — para pegar en Claude Code con el template abierto

> Fuente única del prompt. Lo muestra arriba de todo `INFORME-ESQUELETO.html` (con botón de copiar) y lo cita
> `COMO-USAR-ESTE-TEMPLATE.md`. Reemplazá cada `<…>`; borrá los bloques que no apliquen. Todo lo que no completes,
> la skill `arrancar-proyecto` lo pregunta en un solo mensaje y no inventa nada.

## Antes de pegar (dos pasos tuyos)

1. Copiá la carpeta del template a la carpeta donde va a vivir el núcleo del proyecto (fuera de OneDrive si vas a
   trabajar con git). El template original queda intacto como molde.
2. Abrí Claude Code parado en esa carpeta nueva y pegá el prompt.

## El prompt

```
Arrancá un proyecto con este template: <nombre del proyecto>.

Contexto decidido (no lo vuelvas a preguntar):
- Modo: <solo | equipo>. Tablero: <local | Azure DevOps (org, proyecto, team) | Jira | otro>. Soy <tu nombre, como en git>.
- Producto: <nombre del producto>. Organización: <tu nombre o la empresa>. Módulo del Cerebro: <slug corto, p. ej. reservas>.
- Tipo de aplicación: <web | Electron | escritorio con webview (Tauri) | escritorio nativo | móvil | línea de comandos | API>.
- Stack: back <lenguaje + framework, o "lo que digan los documentos del proyecto">; front <framework, o "no hay">; base <motor, o "no hay">;
  comando de la suite de tests del back <…> y del front <…>. Lo que no sepa queda a definir en DEC-003: no lo inventes.
- Pruebas de punta a punta: motor según el tipo de aplicación (Playwright para web/Electron; Playwright sobre el front con la
  API nativa simulada + WebDriver para escritorio con webview; Appium o Maestro para móvil; proceso para CLI; HTTP para API).
- Las claves (Stitch, MCP) las cargo yo después, por máquina; nunca en archivos.

[Si el proyecto YA EXISTE, dejá este bloque; si es nuevo, borralo]
- El proyecto está en <ruta de la carpeta>. Enchufalo por enlace, no lo muevas. Sumale a su CLAUDE.md la línea que importa las
  reglas del núcleo. Trae: <documentos | decisiones de arquitectura | archivos .feature | skills propias | código en <lenguaje> | nada>.
- No toques su código ni sus documentos: leés, proponés y escribís sólo en el Cerebro de este núcleo, con mi «sí».

[Si el proyecto es NUEVO, dejá este bloque; si ya existe, borralo]
- Todavía no hay nada. Lo que sé del producto, en criollo: <dos o tres frases: para quién es, qué hace, qué problema resuelve>.

Qué quiero de esta sesión, en este orden, frenando en cada «sí»:
1. Mostrame el plan de arranque en un solo mensaje (con lo propuesto al lado de cada dato) y esperá mi «sí» antes de correr nada.
2. [existente] Leé los informes de la adopción (relevamiento, inventario, radiografía) y decime qué trae el proyecto y qué choca
   con el núcleo (nombres de skills repetidos, idioma, reglas). [nuevo] Preguntame, ítem por ítem, lo que falte para la primera ficha funcional.
3. [existente] Procesá los documentos con la curaduría del Cerebro: decisiones de arquitectura como DEC heredadas (con fecha y origen),
   .feature como Escenarios de sus Historias, reglas como candidatas; ítem por ítem, con mi «sí», nada en bloque. Si hay código,
   absorbelo en modo documentar: inventario y radiografía por script, lectura por módulo, matriz de cobertura.
4. [existente, si tiene skills propias] Proponeme qué hacer con cada una: se queda, la cubre una del núcleo, o sobra. No borres nada sin mi «sí».
5. Con el Cerebro poblado, proponeme el primer slice y sus Historias por flujo, cada una con su Gherkin completo y sus Notas para QA
   (pantalla y ruta, rol, datos iniciales, identificadores, ambiente). Bajalas al tablero con mi «sí».
6. Cerrá con un resumen: qué quedó hecho, qué quedó pendiente a confirmar, y qué sigue.

Reglas de esta sesión: no inventes datos ni reglas; lo que no esté en los documentos o en lo que te dije es una pregunta o un
pendiente marcado. Nada de datos de personas. Todo en español.
```

## Lo que sigue, en frases (no hace falta leer pasos)

| Querés… | Decile a Claude |
|---|---|
| Programar lo que está listo en el tablero | «desarrollá mis tareas asignadas» (worktrees y agentes en paralelo; un «Aprobar» por Tarea en modo solo lo da DEC-005) |
| Redactar una Historia o una Tarea | «redactá la Historia de <flujo>» · «derivá las Tareas de la Historia #N» |
| Diseñar una pantalla | «diseñá la pantalla de <X> con Stitch» |
| Pruebas de punta a punta | «diseñá las pruebas de la Historia #N» · «automatizá la Historia #N» · «qué cobertura de punta a punta tenemos» |
| Una app que ya existe | «absorbé la app de <carpeta>» → «¿refactorizo o migro?» → «ponele red al slice <X>» → «migrá el slice <X>» |
| Documentar al cerrar | «armá el manual» · «armá la bitácora técnica» |
| Un diagrama | «dibujame la arquitectura de <X>» |
| Saber cómo venimos | «¿cómo venimos?» (la tendencia de las últimas sesiones) · «corré el Doctor» |
| Mejorar el propio ecosistema | «¿qué mejorarías del ecosistema?» (propone de a uno; vos decidís) |
