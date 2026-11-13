#!/usr/bin/env python3
"""Genera INFORME-ESQUELETO.html: el informe visual del esqueleto (que tiene, como fluye, que mide, que falta).

    python -B bin/generar-informe.py [--salida INFORME-ESQUELETO.html] [--rapido]

Tres estados, nunca dos:  0 = informe escrito   1 = (no aplica)   2 = SIN DATOS (falta la fuente)

POR QUE EXISTE. Un informe escrito a mano envejece el dia que se agrega una skill o un script. Este se
GENERA: lee las skills (nombre y descripcion del frontmatter), los scripts (su docstring), las sondas del
Doctor (su README), las propuestas de mejoras.md, las decisiones, y -si no se pasa --rapido- CORRE las
pruebas y el Doctor para que las cifras sean las de hoy. Los diagramas son SVG embebido (sin dependencias
externas) y la prosa que explica el flujo vive aca, en un solo lugar.

QUE NO HACE. No modifica nada fuera del archivo de salida. No inventa cifras: lo que no corrio se
marca "no corrido". Solo biblioteca estandar. ASCII puro en el codigo; el HTML sale en espanol con tildes.
"""

import argparse
import datetime
import glob
import html
import json
import os
import re
import subprocess
import sys

OK, _, SIN_DATOS = 0, 1, 2
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills')
MET = os.path.join(SK, 'desarrollo', 'references', 'metodo')
GRUPOS = [
    ('Cerebro Digital', ['cerebro-orquestador', 'cerebro-knowledge', 'cerebro-architect-ui', 'cerebro-mockup-design',
                         'cerebro-ppt-generator', 'cerebro-meet-analyst', 'cognitive-doc-design', 'engram-memory-protocol', 'disenar-con-stitch']),
    ('Pipeline Azure DevOps', ['redactar-tarea', 'estimar-story-points', 'consultar-backlog', 'analizar-tareas',
                               'auditar-historia', 'auditar-tarea', 'sincronizar-backlog', 'planificar-lote',
                               'cargar-a-azure', 'tomar-tarea', 'comentar-tarea', 'desarrollar-asignadas',
                               'atender-hallazgos']),
    ('Desarrollo, QA y evolución', ['arrancar-proyecto', 'desarrollo', 'absorber-aplicacion', 'planificar-modernizacion', 'caracterizar-comportamiento', 'modernizar-slice', 'disenar-pruebas', 'automatizar-e2e', 'mejorar-ecosistema', 'documentar-aplicacion']),
    ('Externa, vendorizada', ['archify']),
]
ESCRIBEN_EN_EL_TABLERO = {'sincronizar-backlog', 'planificar-lote', 'cargar-a-azure', 'tomar-tarea', 'comentar-tarea', 'desarrollar-asignadas'}
NUEVAS_HOY = {'disenar-pruebas', 'automatizar-e2e'}

BITACORA = [
    ('2026-10-22', 'Nace el template', 'Ingeniería inversa del proyecto de origen (rama develop): Cerebro OKF, 5 agentes, 26 skills, toolkit de Azure DevOps, Doctor, hook, scripts. Sin negocio ni lenguajes; placeholders e instanciador.'),
    ('2026-10-30', 'Vuelta 1 — determinismo y evolución', 'Seis scripts nuevos (gate-worktree, verificar-tdd, auditar-diff, datos-cierre, derivar-arbol, inventariar-codigo); skills absorber-aplicacion (refactor o migración, DEC-004) y mejorar-ecosistema (autocorrección consultada, mejoras.md, regla 8); carpeta qa/ y método de pruebas de aceptación; «Modo de pruebas» por Tarea; paso 7-bis de retroalimentación al Cerebro; pipeline .gitlab-ci.yml.'),
    ('2026-10-30', 'Vuelta 2 — el Cerebro aprende con la aplicación', 'Cuarto pilar aplicacion/ (mapa, aprendizajes AP-nnn, deuda DT-nnn); verificar-skills.py contra la especificación abierta de Agent Skills (ocho descripciones acortadas; lo corre el hook); instalador bin/instalar.py; bloque «Para DEC-004» en el inventario; notas de carga por herramienta corregidas con la documentación oficial; propuestas M-001 a M-003.'),
    ('2026-10-30', 'Vuelta 3 — ingeniería inversa', 'radiografiar-codigo.py (endpoints, entidades, estados, pantallas, reglas candidatas, integraciones, permisos, dependencias; cada hecho con archivo:línea; --mermaid dibuja módulos y tablas); método ingenieria-inversa.md (siete fuentes, marcas CONFIRMADO/INFERIDO/HUECO, evidencia por regla, matriz de cobertura, modo sólo documentar).'),
    ('2026-10-30', 'Vuelta 4 — auditoría completa', 'Dos auditores en paralelo (skills de desarrollo; Cerebro, pipeline y docs). Arreglos: dos clases de SIN DATOS; bloque canónico del veredicto; armar-mision.py (misión única para Orca e IntelliJ); verificar-tdd.py --modo; auditar-codigo operativa y sin solapes; 5-bis con code-review.md en cualquier motor; DoD en una sola fuente; Engram condicional; restos del origen limpiados; CI sin probar-reglas; Gemini CLI en la guía del MCP; instanciar.py fija last_updated. Propuestas M-004 a M-009.'),
    ('2026-10-30', 'Vuelta 5 — modo desatendido, Archify e informe', 'DEC-005 «modo desatendido» como borrador a confirmar y el GATE de WORKTREE acepta una autorización escrita; Archify declarado como herramienta externa opcional (instalar.py --con-archify); este informe, generado por bin/generar-informe.py.'),
    ('2026-11-02', 'Vuelta 6 — modo solo, tablero local y fusión', 'El template se instancia en modo solo o equipo (DEC-006, se pregunta en cada proyecto); tablero local en archivos (bin/tablero-local.py) con los mismos GATEs; DEC-005 confirmada para el modo solo (Claude único, verificación por otro agente del mismo motor); DEC-002 confirmada para cualquier lenguaje; las dos skills de orquestación fusionadas en desarrollar-asignadas (modo sin Orca en references/sin-orca.md); Archify vendorizada con su licencia; adopción de proyectos que ya usan IA (relevar-config-ia.py + adoptar-proyecto-existente.md).'),
    ('2026-11-02', 'Vuelta 7 — automejora, adopción en un comando, tablero genérico', 'Señales de automejora con las herramientas de Claude Code (/doctor, /doctor prompt-audit, /usage, auto memory, skill-creator con evals) y el script bin/medir-uso-skills.py (uso real de cada skill desde las transcripciones locales); criterio de poda y ritual mensual en mejorar-ecosistema; bin/adoptar-proyecto.py enchufa una carpeta existente al núcleo en un comando; archify ruteada para todo diagrama; el modo equipo acepta Azure, Jira u otro tablero por MCP.'),
    ('2026-11-02', 'Vuelta 8 — la puerta de entrada', 'Skill arrancar-proyecto: «arrancá un proyecto» o «agarrá el proyecto X» pregunta lo básico en un mensaje, muestra el plan y con el «sí» corre bin/arrancar-proyecto.py (instanciar, git init, instalar, enchufar, informe) en orden fijo e idempotente. bin/derivar-a-tablero-local.py baja una ficha validada al tablero local 1:1, sin MCP. Propuestas M-011 (hook duro de escrituras al tablero) y M-012 (exportar el tablero local a Azure o Jira).'),
    ('2026-11-02', 'Vuelta 9 — Stitch y los entregables de cierre', 'Google Stitch como herramienta de diseño UX/UI por MCP (integracion-stitch-mcp/00-index.md) y la skill disenar-con-stitch: brief desde la ficha, generar, pulir en Stitch, exportar a entregables/disenos/ como maqueta vigente, tokens al design system, bajada al front por cerebro-architect-ui. Skill documentar-aplicacion con bin/generar-documentacion.py: guía de uso (empezar en pocos pasos, flujos con pantallas y paso a paso dibujado, glosario, FAQ) y documentación técnica y funcional (14 secciones con grafo de módulos, modelo de datos, API, reglas, decisiones, bitácora, diagramas de Archify).'),
    ('2026-11-03', 'Vuelta 10 — ensayo multiagente y postmortem', 'Un aplicativo descartable (reservas, Python puro, tablero local, modo solo) corrió el flujo real de punta a punta con agentes en paralelo: worker con guiar-tdd, verificador con el bloque VEREDICTO, absorción de un proyecto real en sólo lectura y un auditor en frío de las skills. Lo que el ensayo rompió y se arregló: commits chore(firma) y test(verde-de-entrada) para el rojo en la aserción y el ítem que nace verde; la misión ya no carga endpoints ni contratos a una Tarea sin API ni duplica el Gherkin; N/A en los controles que la Tarea no toca; la radiografía lee SQL y Mermaid dentro de .md y deja de ver estado= en diccionarios; el relevamiento saca comandos en línea; adoptar detecta un proyecto sin código y manda al flujo de documentos. Lo que el auditor en frío cerró: la fusión de desarrollar-asignadas terminada (dos modos, un flujo; verificador según DEC-005; tablero según DEC-006), una sola tabla «Quién contesta qué» que las skills citan, las ocho notas del tablero local reducidas a una línea, cerebro-mockup-design ya no se carga con cualquier HTML, y verificar-skills.py frena las frases muertas.'),
    ('2026-11-03', 'Vuelta 11 — estructura y flujo de modernización', 'Carpetas con los nombres de hoy: tablero/ (antes 04-integracion-azure-devops), borrador/ (antes output), documentos/ (antes funcionales); back/ y front/ siguen separados porque sus convenciones difieren. El flujo de una app existente deja de ser una sola skill: absorber-aplicacion (ingeniería inversa) → planificar-modernizacion (estrategias comparadas con lo medido, curaduría de reglas migrar/descartar/decide el humano, DEC-004, slices) → caracterizar-comportamiento (corpus desde la radiografía, golden firmado contra la vieja, test(caracterizacion)) → modernizar-slice (contrato del código viejo, construcción, paridad, corte sólo con la barrera en OK, apagado). Cuatro scripts nuevos con sus pruebas: esquema-base.py, armar-corpus.py, paridad.py y mapa-modernizacion.py. Estructura tomada de Fig, Reversa, el pack legacy-modernization y tbls; nada copiado. Postmortem en frío del 2026-11-04: la barrera del corte aceptaba un resultado de paridad escrito a mano; ahora paridad.py firma también el resultado, registra los campos volátiles y quién aceptó cada diferencia, rechaza aprobadores que son agentes, y mapa-modernizacion.py corte verifica las dos firmas, abre el golden que cita la tabla y prueba el refactor en el lugar con el bloque VEREDICTO. armar-corpus.py numera CP-nn, cubre los cinco tipos de regla y cuenta con --verificar qué endpoint o regla quedó sin caso; el VEREDICTO tiene el renglón 5-quinquies paridad.'),
    ('2026-11-04', 'Vuelta 12 — para una sola persona', 'Decisión del dueño: el template es para una persona, a lo sumo un segundo dev; él hace lo funcional, QA y UX/UI. Se eliminó lo que sólo sirve con varias personas: las skills cerebro-sync-knowledge, cerebro-auditor y cerebro-consultar-cambios, los scripts enviar-notas y actualizacion-semanal, el agente cerebro-auditor, autores-autorizados.txt y reporte-auditoria.md. Simplificado para modo solo: la revisión del Merge Request es el veredicto del verificador más el Aprobar (el MR es opcional), el GATE de NIVEL no se pregunta, sprints y tarjeta congelada aplican sólo en modo equipo, y el modo equipo existe sólo si al arrancar se dice que habrá equipo. Al arrancar un proyecto se pregunta además con qué se va a hacer (DEC-003), y lo que no se sabe queda a definir. Mejoras: M-008 aplicada; M-009 aplicada en las tablas únicas; M-007 cubierta por DEC-006; M-001 descartada (rompería el ruteo conversacional); M-010 aceptada para los 60 días; M-011 y M-012 diferidas hasta que un proyecto use un tablero por MCP.'),
    ('2026-11-04', 'Vuelta 13 — ensayo de front y base de datos', 'Segundo ensayo con un aplicativo descartable: back Python + SQLite con migraciones (V2 expandir, cancelar, listar activas) y front TypeScript + Vitest + jsdom (pantalla de lista con estado). Cuatro agentes con contexto limpio: dos workers (11 y 15 commits rojo → verde, suites en verde, typecheck limpio) y dos verificadores (cero bloqueantes, cada rojo verificado en su aserción, control de migraciones con esquema-base.py). Cincuenta y cuatro fricciones reportadas y arregladas en el template: la misión del front ya no copia las convenciones del back y reporta las reglas R1..R12; una Tarea que toca migraciones lleva el método y el control de migraciones; la guía del stack en plantilla no se manda a leer y los archivos vacíos se marcan; AGENTS.md se cita por sección; «pendiente a confirmar» es la vía por defecto; la aserción del rojo va en el cuerpo del commit; un ítem con dos comportamientos del mismo contrato son dos aserciones; la vuelta atrás de una migración nace como firma vacía; el modo de pruebas de la Tarea gana sobre la tabla; esquema-base.py --aplicar lee el esquema resultante de las migraciones; auditar-diff.py dice cuántos patrones miró; auditar-tarea.py avisa los ítems compuestos; el verificador no invoca /code-review ni corre módulos de la app con argumentos de prueba; instanciar completa las guías del stack con el comando de la suite; y en Windows con Git Bash, npm.cmd.'),
    ('2026-11-04', 'Vuelta 14 — QA de punta a punta sin esperar un repo', 'Dos skills nuevas: disenar-pruebas (el tester: plan de pruebas de aceptación desde el Gherkin, qué se automatiza y qué queda exploratorio, datos sin datos de personas) y automatizar-e2e (QA automatización). El motor no es siempre Playwright: lo fija DEC-003 según el tipo de aplicación: Playwright para web, Electron y el front de una app con webview; WebDriver para Tauri y escritorio nativo; Appium o Maestro para móvil; un proceso para línea de comandos; HTTP para una API. Dos scripts con pruebas: armar-e2e.py (esqueleto desde el Gherkin con la traza Historia #id · Escenario, cada test marcado sin automatizar, no pisa lo que existe) y cobertura-e2e.py (automatizado / sólo esqueleto / sin prueba, por Escenario). Ensayo real con Playwright sobre una página estática y el Edge instalado.'),
    ('2026-11-04', 'Vuelta 15 — la tendencia se mide sola, y la tarjeta trae lo que la prueba de punta a punta necesita', 'bin/registrar-sesion.py (hook SessionEnd) deja una línea de conteos por sesión en configuracion-ia/sesiones.jsonl: skills, veredictos con bloqueantes y SIN DATOS, fricciones, Tareas terminadas y fallidas, preguntas, errores de script, duración; nunca texto ni datos de personas. bin/tendencia.py (hook SessionStart) dice en una frase si las últimas sesiones vienen MEJOR, IGUAL o PEOR, con los números; PEOR es la señal con la que mejorar-ecosistema propone un ajuste, de a uno y con el sí de la persona. Los hooks viajan en .claude/settings.json. En QA: las Notas para QA de la Historia pasan a cinco líneas fijas (pantalla y ruta, rol y usuario de prueba, datos iniciales, identificadores estables, ambiente) que redactar-tarea completa y armar-e2e.py lee; lo que falte sale como aviso al armar el esqueleto, como pregunta a la Historia. El plan de disenar-pruebas es un comentario en la tarjeta, no un archivo: la tarjeta ya trae los Escenarios y la tabla SDD de sus Tareas.'),
]

PENDIENTES_HUMANO = [
    ('DEC-003 — el stack', 'cerebro-digital/<modulo>/arquitectura/decisiones.md y las guías tdd-stack-back.md / tdd-stack-front.md de la skill desarrollo. Hasta que exista, C8, SAST, cobertura y la guía del stack son SIN DATOS (pendiente declarado): se listan, no frenan.'),
    ('DEC-005 — modo equipo', 'El template la trae sin firmar; en modo solo la firma quien arranca el proyecto. La columna del modo equipo sigue en propuesta: quién aprueba, quién abre el Merge Request, el otro motor.'),
    ('DEC-002 — módulos de dominio', 'Confirmar la estructura <modulo>/{api,application,domain,infra,exceptions} + shared/ o cambiarla.'),
    ('Contexto del tablero', 'tablero/conocimiento/contexto-proyecto.md: slices, etiquetas temáticas, proceso del tablero. Y cerebro-digital/contexto.md.'),
    ('Propuestas M-001 a M-009', 'configuracion-ia/mejoras.md: cada una espera Aplicar / Rechazar / Posponer. Las que cambian reglas duras (M-004, M-006) son las que más pesan para el flujo automático.'),
    ('Repositorio de QA', 'Pasarlo para absorberlo con absorber-aplicacion y atar cada prueba a su #ID y Escenario.'),
    ('Primera poda por uso (M-010)', 'A los 60 días de uso real: python -B bin/medir-uso-skills.py --proyecto <núcleo>, más /doctor y /doctor prompt-audit en Claude Code; lo que no se usó y cuya pregunta cubre otra skill se propone sacar.'),
    ('Stitch: la clave y la primera pantalla', 'Crear la API key en stitch.withgoogle.com/settings, registrar el MCP (claude mcp add stitch …) y diseñar la primera pantalla desde una ficha con disenar-con-stitch.'),
    ('Primera radiografía real', 'Correr bin/radiografiar-codigo.py sobre una aplicación de verdad: las tablas de expresiones están calibradas sobre un fixture y una app real muestra qué stack falta.'),
]


def leer(ruta):
    with open(ruta, 'r', encoding='utf-8-sig', errors='replace') as h:
        return h.read()


def frontmatter(texto):
    if not texto.startswith('---\n'):
        return {}
    fin = texto.find('\n---', 4)
    if fin < 0:
        return {}
    datos, lineas, i = {}, texto[4:fin].split('\n'), 0
    while i < len(lineas):
        m = re.match(r'^([A-Za-z0-9_-]+):\s*(.*)$', lineas[i])
        if not m:
            i += 1
            continue
        clave, valor = m.group(1), m.group(2).strip()
        if valor in ('>', '>-', '|', '|-'):
            partes = []
            i += 1
            while i < len(lineas) and (lineas[i].startswith(' ') or lineas[i].strip() == ''):
                partes.append(lineas[i].strip())
                i += 1
            datos[clave] = ' '.join(p for p in partes if p)
            continue
        datos[clave] = valor.strip('"\'')
        i += 1
    return datos


def primera_oracion(texto, maximo=230):
    texto = re.sub(r'\s+', ' ', texto).strip()
    m = re.match(r'(.+?[.!?])(\s|$)', texto)
    frase = m.group(1) if m else texto
    return frase if len(frase) <= maximo else frase[:maximo - 1].rstrip() + '…'


def skills():
    datos = {}
    for d in sorted(os.listdir(SK)):
        p = os.path.join(SK, d, 'SKILL.md')
        if os.path.isfile(p):
            t = leer(p)
            fm = frontmatter(t)
            datos[d] = {'nombre': d, 'descripcion': fm.get('description', ''), 'lineas': t.count('\n') + 1,
                        'referencias': len(glob.glob(os.path.join(SK, d, 'references', '**', '*.md'), recursive=True))}
    return datos


def scoped():
    out = {}
    for lado in ('back', 'front'):
        base = os.path.join(RAIZ, lado, '.claude', 'skills')
        out[lado] = []
        if os.path.isdir(base):
            for d in sorted(os.listdir(base)):
                p = os.path.join(base, d, 'SKILL.md')
                if os.path.isfile(p):
                    out[lado].append((d, frontmatter(leer(p)).get('description', '')))
    return out


def scripts():
    filas = []
    for p in sorted(glob.glob(os.path.join(RAIZ, 'bin', '*.py'))):
        nombre = os.path.basename(p)
        if nombre.startswith('probar-'):
            continue
        t = leer(p)
        m = re.search(r'"""\s*(.+?)\n', t)
        filas.append((nombre, (m.group(1).strip() if m else '').rstrip('.')))
    pares = sorted(set(re.sub(r'\.(sh|ps1)$', '', os.path.basename(p)) for p in glob.glob(os.path.join(RAIZ, 'bin', '*.sh')) + glob.glob(os.path.join(RAIZ, 'bin', '*.ps1'))))
    return filas, pares


def correr_pruebas(rapido):
    filas = []
    for p in sorted(glob.glob(os.path.join(RAIZ, 'bin', 'probar-*.py'))):
        nombre = os.path.basename(p)
        if nombre == 'probar-reglas.py':
            filas.append((nombre, 'no corre acá', 'mide a un modelo con su CLI; se corre a mano'))
            continue
        if rapido:
            filas.append((nombre, 'no corrido', '--rapido'))
            continue
        r = subprocess.run([sys.executable, '-B', p], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=RAIZ)
        ultima = (r.stdout.strip().splitlines() or [''])[-1]
        m = re.search(r'(\d+) de (\d+) casos', ultima)
        filas.append((nombre, 'OK' if r.returncode == 0 else 'FALLA', ('%s de %s casos' % (m.group(1), m.group(2))) if m else ultima[:80]))
    return filas


def correr_doctor(rapido):
    if rapido:
        return None
    r = subprocess.run([sys.executable, '-B', os.path.join(RAIZ, 'doctor', 'doctor.py'), '--json'], capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=RAIZ)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return None
    return d['sondas'] if isinstance(d, dict) and 'sondas' in d else d


def sondas_readme():
    filas = []
    for l in leer(os.path.join(RAIZ, 'doctor', 'README.md')).split('\n'):
        m = re.match(r'^\|\s*(\d+)\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|', l)
        if m:
            filas.append((int(m.group(1)), m.group(2), re.sub(r'\s*\|\s*(back|front|ambos)\s*$', '', m.group(3))))
    return filas


def mejoras():
    filas = []
    p = os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'mejoras.md')
    for l in leer(p).split('\n'):
        m = re.match(r'^\|\s*(M-\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$', l)
        if m:
            filas.append(m.groups())
    return filas


def decisiones():
    filas = []
    p = glob.glob(os.path.join(RAIZ, 'cerebro-digital', '*', 'arquitectura', 'decisiones.md'))
    if not p:
        return filas
    t = leer(p[0])
    for m in re.finditer(r'^## (DEC-\d+) — (.+?)\n(.*?)(?=^## DEC-|\Z)', t, re.S | re.M):
        est = re.search(r'\*\*Estado:\*\*\s*(.+)', m.group(3))
        filas.append((m.group(1), m.group(2).strip(), re.sub(r'\*\*', '', est.group(1)).strip()[:160] if est else '—'))
    return filas


# ------------------------------------------------------------------------------------------------
# SVG
# ------------------------------------------------------------------------------------------------
def _t(x, y, s, cls='', anchor='middle'):
    return '<text x="%d" y="%d" text-anchor="%s" class="%s">%s</text>' % (x, y, anchor, cls, html.escape(s))


def flujo(pasos, por_fila=5, ancho=196, alto=66, gap=34, salto=104):
    filas = [pasos[i:i + por_fila] for i in range(0, len(pasos), por_fila)]
    W = por_fila * ancho + (por_fila - 1) * gap + 20
    H = len(filas) * salto + 10
    out = ['<svg viewBox="0 0 %d %d" class="diagrama" role="img" aria-label="flujo">' % (W, H),
           '<defs><marker id="f" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="flecha"/></marker></defs>']
    for fi, fila in enumerate(filas):
        y = 10 + fi * salto
        for ci, (titulo, sub, tono) in enumerate(fila):
            x = 10 + ci * (ancho + gap)
            out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" class="caja %s"/>' % (x, y, ancho, alto, tono))
            out.append(_t(x + ancho // 2, y + 27, titulo, 'caja-t'))
            out.append(_t(x + ancho // 2, y + 48, sub, 'caja-s'))
            if ci < len(fila) - 1:
                out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="linea" marker-end="url(#f)"/>' % (x + ancho, y + alto // 2, x + ancho + gap - 2, y + alto // 2))
        if fi < len(filas) - 1:
            xe = 10 + (len(fila) - 1) * (ancho + gap) + ancho // 2
            out.append('<path d="M%d,%d V%d H%d V%d" class="linea" fill="none" marker-end="url(#f)"/>' % (xe, y + alto, y + alto + 18, 10 + ancho // 2, y + salto - 3))
    out.append('</svg>')
    return '\n'.join(out)


def bucles():
    return '''<svg viewBox="0 0 900 300" class="diagrama" role="img" aria-label="los tres bucles">
<defs><marker id="b" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="flecha"/></marker></defs>
<rect x="20" y="110" width="250" height="90" rx="12" class="caja acento"/>
<text x="145" y="145" text-anchor="middle" class="caja-t">1. Construir</text>
<text x="145" y="168" text-anchor="middle" class="caja-s">conocimiento → tickets → código → verificación</text>
<rect x="325" y="20" width="250" height="90" rx="12" class="caja"/>
<text x="450" y="55" text-anchor="middle" class="caja-t">3. Alimentar el Cerebro</text>
<text x="450" y="78" text-anchor="middle" class="caja-s">7-bis: funcional / aplicacion/ / mejoras.md</text>
<rect x="630" y="110" width="250" height="90" rx="12" class="caja suave"/>
<text x="755" y="145" text-anchor="middle" class="caja-t">2. Autocorregirse</text>
<text x="755" y="168" text-anchor="middle" class="caja-s">mejorar-ecosistema: propone, nunca aplica</text>
<path d="M270,140 C300,60 320,60 325,60" class="linea" fill="none" marker-end="url(#b)"/>
<path d="M575,60 C600,60 620,80 630,130" class="linea" fill="none" marker-end="url(#b)"/>
<path d="M755,200 C755,270 145,270 145,205" class="linea" fill="none" marker-end="url(#b)"/>
<text x="450" y="262" text-anchor="middle" class="caja-s">cada vuelta deja el esqueleto y el Cerebro mejor que antes, con un «sí» humano en cada cambio</text>
</svg>'''


def arbol_cerebro():
    nodos = [
        (20, 20, 'cerebro-digital/', 'acento'),
        (20, 120, 'index · contexto · fuentes', ''), (20, 175, 'roadmap · log · autores', ''), (20, 230, 'diseno/diseno-sistema.md', ''),
        (300, 120, 'configuracion-ia/', 'suave'), (300, 175, 'agentes/ (4) · skills/ (31)', ''), (300, 230, 'orquestador-desarrollo · mejoras', ''), (300, 285, 'integracion-azure-mcp · gitlab-mcp', ''),
        (580, 120, '<modulo>/  (modulo-ejemplo)', 'suave'), (580, 175, 'funcional/ · metodologia/', ''), (580, 230, 'arquitectura/ (DEC-nnn, esqueleto)', ''), (580, 285, 'aplicacion/ (mapa · AP · DT)', 'acento'), (580, 340, 'pendientes.md · extraccion-reuniones/', ''),
    ]
    out = ['<svg viewBox="0 0 860 400" class="diagrama" role="img" aria-label="estructura del Cerebro">']
    for x, y, s, tono in nodos:
        out.append('<rect x="%d" y="%d" width="250" height="40" rx="8" class="caja %s"/>' % (x, y, tono))
        out.append(_t(x + 125, y + 25, s, 'caja-t'))
    for x in (145, 425, 705):
        out.append('<line x1="145" y1="60" x2="%d" y2="120" class="linea"/>' % x)
    for x in (20, 300, 580):
        out.append('<line x1="%d" y1="160" x2="%d" y2="350" class="linea"/>' % (x + 8, x + 8))
    out.append('</svg>')
    return '\n'.join(out)


def piramide():
    return '''<svg viewBox="0 0 700 260" class="diagrama" role="img" aria-label="tres capas de pruebas">
<polygon points="350,20 470,110 230,110" class="caja acento"/>
<polygon points="230,116 470,116 540,176 160,176" class="caja suave"/>
<polygon points="160,182 540,182 620,242 80,242" class="caja"/>
<text x="350" y="92" text-anchor="middle" class="caja-t">Aceptación · qa/</text>
<text x="350" y="153" text-anchor="middle" class="caja-t">Integración · back/ front/ (si la Tarea lo declara)</text>
<text x="350" y="219" text-anchor="middle" class="caja-t">Unitaria y de contrato · guiar-tdd · test(rojo) → verde</text>
<text x="620" y="60" text-anchor="start" class="caja-s">pocas, contra el</text>
<text x="620" y="78" text-anchor="start" class="caja-s">sistema desplegado,</text>
<text x="620" y="96" text-anchor="start" class="caja-s">trazadas al #ID</text>
</svg>'''


def absorber():
    pasos = [('Fase 0 · Encuadre', 'qué app, qué se espera, qué no se toca', ''),
             ('Fase 1 · Inventario', 'inventariar-codigo.py (+ Para DEC-004)', 'acento'),
             ('Fase 1-bis · Radiografía', 'radiografiar-codigo.py (+ --mermaid)', 'acento'),
             ('Fase 2 · Lectura', 'por módulo, marca CONFIRMADO / INFERIDO / HUECO', ''),
             ('Cobertura', 'matriz: cada módulo leído o HUECO', ''),
             ('Modo documentar', 'termina acá: Cerebro poblado', 'suave'),
             ('Fase 3 · DEC-004', 'tabla medida → decide una persona', ''),
             ('Fase 4 · Plan', 'fichas → tickets → TDD (refactor o migración)', '')]
    return flujo(pasos, por_fila=4)


def refactor_migracion():
    return '''<svg viewBox="0 0 900 250" class="diagrama" role="img" aria-label="refactor o migración">
<rect x="20" y="20" width="410" height="210" rx="12" class="caja suave"/>
<rect x="470" y="20" width="410" height="210" rx="12" class="caja suave"/>
<text x="225" y="50" text-anchor="middle" class="caja-t">Refactor — se modifica en su lugar</text>
<text x="675" y="50" text-anchor="middle" class="caja-t">Migración — se construye de nuevo</text>
<text x="40" y="85" class="caja-s" text-anchor="start">1. RED: test(caracterizacion) congela lo que hace hoy</text>
<text x="40" y="110" class="caja-s" text-anchor="start">2. LÍMITES: módulos de dominio (DEC-002), sin cambiar conducta</text>
<text x="40" y="135" class="caja-s" text-anchor="start">3. FORMA · 4. REGLAS con rojo normal</text>
<text x="40" y="160" class="caja-s" text-anchor="start">5. La red sigue en verde; otro agente audita</text>
<text x="40" y="200" class="caja-s" text-anchor="start">El Doctor mide el avance módulo por módulo</text>
<text x="490" y="85" class="caja-s" text-anchor="start">1. CONTRATO: openapi.yaml sacado del código viejo</text>
<text x="490" y="110" class="caja-s" text-anchor="start">2. ORÁCULO: paridad, el mismo caso contra las dos</text>
<text x="490" y="135" class="caja-s" text-anchor="start">3. SLICE NUEVO con el pipeline normal</text>
<text x="490" y="160" class="caja-s" text-anchor="start">4. CORTE de tráfico por slice (estrangulador)</text>
<text x="490" y="200" class="caja-s" text-anchor="start">5. APAGADO de la vieja, con un «sí»</text>
</svg>'''


# ------------------------------------------------------------------------------------------------
# HTML
# ------------------------------------------------------------------------------------------------
CSS = '''
:root{--ink:#1f2328;--paper:#fff;--muted:#57606a;--line:#d0d7de;--soft:#f6f8fa;--acento:#0b5fff;--acento-s:#e8f0ff;--ok:#1a7f37;--warn:#9a6700;--bad:#cf222e;--mono:ui-monospace,SFMono-Regular,Consolas,monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:15px/1.55 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--paper)}
header.portada{background:linear-gradient(135deg,#0b2a66,#0b5fff);color:#fff;padding:48px 48px 40px}
header.portada h1{margin:0 0 8px;font-size:34px;letter-spacing:-.5px}header.portada p{margin:4px 0;opacity:.92;max-width:900px}
.meta{font-family:var(--mono);font-size:12px;opacity:.85;margin-top:16px}
.layout{display:grid;grid-template-columns:270px 1fr;min-height:100vh}
nav{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;border-right:1px solid var(--line);padding:20px 16px;background:var(--soft)}
nav h2{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:8px 8px 10px}
nav a{display:block;padding:6px 10px;border-radius:6px;color:var(--ink);text-decoration:none;font-size:14px}nav a:hover{background:var(--acento-s)}
nav a span{display:inline-block;min-width:26px;color:var(--muted);font-family:var(--mono);font-size:12px}
main{padding:28px 48px 80px;max-width:1240px}
section{padding:28px 0 8px;border-bottom:1px solid var(--line)}section:last-of-type{border-bottom:0}
h2{font-size:24px;margin:0 0 6px;letter-spacing:-.3px}h3{font-size:17px;margin:22px 0 8px}
.lead{color:var(--muted);margin:0 0 18px;max-width:900px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:14px 0 6px}
.tile{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:var(--soft)}
.tile b{display:block;font-size:28px;letter-spacing:-.5px}.tile span{color:var(--muted);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin:12px 0}
.card{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#fff}
.card h4{margin:0 0 6px;font-family:var(--mono);font-size:14px}.card p{margin:0;color:var(--muted);font-size:13.5px}
.card .pie{margin-top:8px;font-size:12px;color:var(--muted)}
.badge{display:inline-block;font-size:11.5px;font-weight:600;padding:2px 8px;border-radius:999px;border:1px solid var(--line);background:var(--soft);vertical-align:middle;margin-left:6px}
.badge.ok{color:var(--ok);border-color:#aceebb;background:#dafbe1}.badge.warn{color:var(--warn);border-color:#f0d58c;background:#fff8c5}
.badge.bad{color:var(--bad);border-color:#ffb3b3;background:#ffebe9}.badge.acento{color:var(--acento);border-color:#b6ccff;background:var(--acento-s)}
table{border-collapse:collapse;width:100%;margin:10px 0 16px;font-size:14px}th,td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}
th{background:var(--soft);font-weight:600}td code,p code,li code{font-family:var(--mono);font-size:12.5px;background:var(--soft);padding:1px 5px;border-radius:4px}
pre{background:#0d1117;color:#e6edf3;padding:14px 16px;border-radius:10px;overflow:auto;font-size:12.5px;line-height:1.5}
.diagrama{width:100%;height:auto;max-width:1100px;display:block;margin:12px 0 18px}
.caja{fill:#fff;stroke:var(--line);stroke-width:1.5}.caja.acento{fill:var(--acento-s);stroke:#b6ccff}.caja.suave{fill:var(--soft)}
.caja-t{font-size:13.5px;font-weight:600;fill:var(--ink)}.caja-s{font-size:11.5px;fill:var(--muted)}
.linea{stroke:#8b949e;stroke-width:1.6}.flecha{fill:#8b949e}
.timeline{list-style:none;padding:0;margin:14px 0;border-left:2px solid var(--line)}
.timeline li{position:relative;padding:0 0 18px 22px}.timeline li::before{content:"";position:absolute;left:-7px;top:6px;width:12px;height:12px;border-radius:50%;background:var(--acento);border:2px solid #fff}
.timeline time{font-family:var(--mono);font-size:12px;color:var(--muted)}.timeline b{display:block}
.check{list-style:none;padding:0}.check li{padding:8px 0 8px 30px;position:relative;border-bottom:1px dashed var(--line)}
.check li::before{content:"";position:absolute;left:4px;top:12px;width:14px;height:14px;border:2px solid var(--acento);border-radius:4px}
.nota{border-left:4px solid var(--acento);background:var(--acento-s);padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0}
.dos{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media(max-width:900px){.layout{grid-template-columns:1fr}nav{position:static;height:auto}.dos{grid-template-columns:1fr}main{padding:20px}}
footer{color:var(--muted);font-size:13px;padding:24px 48px;border-top:1px solid var(--line)}
.prompt-maestro{margin:0;padding:28px 48px 24px;background:#eef3ff;border-bottom:1px solid #c9d6f5}.prompt-maestro h2{margin-top:0}.prompt-maestro pre{max-height:520px}.pasos-previos{margin:6px 0 12px 20px}.barra-prompt{display:flex;align-items:center;gap:12px;margin:8px 0}.copiar{background:#0b5fff;color:#fff;border:0;border-radius:8px;padding:9px 16px;font-size:14px;cursor:pointer}.copiar:hover{background:#0b2a66}.prompt-maestro details{margin-top:12px}.prompt-maestro summary{cursor:pointer;font-weight:600}
@media print{nav{display:none}.copiar{display:none}.layout{grid-template-columns:1fr}header.portada{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
'''


def badge(texto, tono=''):
    return '<span class="badge %s">%s</span>' % (tono, html.escape(texto))


def generar(rapido):
    sks = skills()
    sc = scoped()
    scr, pares = scripts()
    pruebas = correr_pruebas(rapido)
    sondas_hoy = correr_doctor(rapido)
    sondas = sondas_readme()
    mej = mejoras()
    decs = decisiones()
    metodos = sorted(os.path.basename(p) for p in glob.glob(os.path.join(MET, '*.md')))
    total_casos = sum(int(re.match(r'(\d+)', d).group(1)) for _, e, d in pruebas if e == 'OK' and re.match(r'\d+', d))
    suites_ok = sum(1 for _, e, _ in pruebas if e == 'OK')
    agrupadas = []
    vistos = set()
    for titulo, lista in GRUPOS:
        presentes = [n for n in lista if n in sks]
        vistos.update(presentes)
        agrupadas.append((titulo, presentes))
    sobrantes = [n for n in sks if n not in vistos]
    if sobrantes:
        agrupadas.append(('Sin grupo asignado (revisar el informe)', sobrantes))
    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    secciones = [
        ('resumen', 'Resumen ejecutivo'), ('mapa', 'Mapa del esqueleto'), ('bucles', 'Los tres bucles'),
        ('codigo', 'Cómo se construye código'), ('pruebas', 'Pruebas: tres capas'), ('inversa', 'Ingeniería inversa, refactor y migración'),
        ('autocorreccion', 'Autocorrección consultada'), ('skills', 'Skills'), ('scripts', 'Scripts determinísticos'),
        ('doctor', 'El Doctor'), ('instalacion', 'Instalación e instanciación'), ('bitacora', 'Bitácora'),
        ('pendientes', 'Pendientes y decisiones'), ('regenerar', 'Cómo se regenera este informe'),
    ]
    H = []
    H.append('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    H.append('<title>Informe del esqueleto — TEMPLATE ESTRUCTURA IA</title><style>%s</style></head><body>' % CSS)
    H.append('<header class="portada"><h1>TEMPLATE ESTRUCTURA IA — informe del esqueleto</h1>')
    H.append('<p>Qué tiene, cómo fluye, qué mide y qué falta. Un Cerebro Digital (OKF) con agentes, skills y scripts determinísticos para crear, absorber, refactorizar o migrar aplicaciones con IA, con un «sí» humano en cada barrera.</p>')
    # Solo el nombre de la carpeta: la ruta completa es de la maquina de quien lo genero, y el informe se versiona.
    H.append('<p class="meta">Generado el %s por bin/generar-informe.py%s · carpeta: %s</p></header>' % (ahora, ' (modo rápido: sin correr pruebas ni Doctor)' if rapido else ' (pruebas y Doctor corridos hoy)', html.escape(os.path.basename(RAIZ))))
    prompt, pasos, frases = prompt_maestro()
    if prompt:
        H.append('<section id="prompt" class="prompt-maestro"><h2>00 · Prompt maestro — para pegar en Claude Code con el template abierto</h2>')
        H.append('<p class="lead">Copiá el template a la carpeta del proyecto, abrí Claude Code ahí y pegá esto. Reemplazá cada <code>&lt;…&gt;</code>; borrá los bloques que no apliquen. Lo que no completes, la skill <code>arrancar-proyecto</code> lo pregunta en un solo mensaje y no inventa nada. Fuente única: <code>cerebro-digital/configuracion-ia/skills/arrancar-proyecto/references/prompt-maestro.md</code>.</p>')
        if pasos:
            H.append('<ol class="pasos-previos">' + ''.join('<li>%s</li>' % html.escape(p) for p in pasos) + '</ol>')
        H.append('<div class="barra-prompt"><button type="button" class="copiar" onclick="copiarPrompt()">Copiar el prompt</button><span id="copiado" class="meta"></span></div>')
        H.append('<pre id="prompt-texto">%s</pre>' % html.escape(prompt))
        if frases:
            H.append('<details><summary>Lo que sigue, en frases (no hace falta leer pasos)</summary><table><tr><th>Querés…</th><th>Decile a Claude</th></tr>' + ''.join('<tr><td>%s</td><td>%s</td></tr>' % (html.escape(a), html.escape(b)) for a, b in frases) + '</table></details>')
        H.append('<script>function copiarPrompt(){var t=document.getElementById("prompt-texto").innerText;var m=document.getElementById("copiado");function ok(){m.textContent="Copiado. Pegalo en Claude Code.";}function fb(){var r=document.createRange();r.selectNodeContents(document.getElementById("prompt-texto"));var s=window.getSelection();s.removeAllRanges();s.addRange(r);try{document.execCommand("copy");ok();}catch(e){m.textContent="Seleccioná el texto y copialo con Ctrl+C.";}}if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(ok,fb);}else{fb();}}</script>')
        H.append('</section>')
    H.append('<div class="layout"><nav><h2>Índice</h2>')
    if prompt:
        H.append('<a href="#prompt"><span>00</span>Prompt maestro</a>')
    for i, (anc, tit) in enumerate(secciones, 1):
        H.append('<a href="#%s"><span>%02d</span>%s</a>' % (anc, i, html.escape(tit)))
    H.append('</nav><main>')

    # 1 resumen
    H.append('<section id="resumen"><h2>01 · Resumen ejecutivo</h2>')
    H.append('<p class="lead">El esqueleto separa <b>conocimiento</b> (el Cerebro), <b>reglas</b> (AGENTS.md y sus barreras), <b>habilidades</b> (skills, una pregunta por skill) y <b>hechos</b> (scripts que cuentan siempre igual). Lo que es conteo lo hace un script; lo que pide criterio lo hace el modelo; lo que es decisión la toma una persona.</p>')
    H.append('<div class="tiles">')
    for n, s in ((len(sks), 'skills canónicas'), (len(sc['back']) + len(sc['front']), 'skills scoped back/front'), (len(scr), 'scripts determinísticos'),
                 (len(pruebas), 'suites de prueba'), (total_casos if not rapido else '—', 'casos en OK hoy'), (len(sondas), 'sondas del Doctor'),
                 (len(metodos), 'documentos de método'), (len(mej), 'propuestas de mejora')):
        H.append('<div class="tile"><b>%s</b><span>%s</span></div>' % (n, s))
    H.append('</div>')
    H.append('<div class="nota"><b>Principios que sostienen todo.</b> Fuente única de verdad en <code>cerebro-digital/</code>. Nada se inventa: lo que no está es pendiente. Lo que se cuenta lo cuenta un script y un script que no corrió es <code>SIN DATOS</code>, no OK. Quien verifica no es quien produce. Nada se escribe en el tablero, en el Cerebro ni afuera sin un «sí» sobre lo ya mostrado. Sin PHI, nunca. Todo en español (Argentina).</div></section>')

    # 2 mapa
    H.append('<section id="mapa"><h2>02 · Mapa del esqueleto</h2><p class="lead">Un repositorio de conocimiento y reglas; el código de la aplicación vive en repositorios propios que se clonan adentro de <code>back/</code>, <code>front/</code> y <code>qa/</code> (DEC-001).</p>')
    H.append('<table><tr><th>Carpeta</th><th>Qué es</th></tr>')
    for c, q in (('AGENTS.md · CLAUDE.md · GEMINI.md · opencode.json', 'Las reglas y las barreras, una sola fuente; los otros tres la importan para Claude Code, Gemini CLI y opencode. Antigravity la lee nativa.'),
                 ('cerebro-digital/', 'El Cerebro Digital (OKF): contexto, fuentes, roadmap, log, el módulo con sus cuatro pilares, la configuración de IA (agentes, skills, orquestador, mejoras, integraciones MCP).'),
                 ('.claude/skills · .agents/skills', 'Espejos versionados de las skills, idénticos a la fuente (el hook y el instalador lo verifican). Los agentes se materializan por máquina.'),
                 ('bin/', 'Scripts determinísticos (Python, biblioteca estándar, exit 0/1/2) y sus pruebas; instalador, instanciador, sincronizadores.'),
                 ('doctor/', 'El Doctor: 23 sondas sobre el repositorio y, si hay código clonado, sobre el código.'),
                 ('tablero/', 'El toolkit de tickets: método, plantillas, checklists, ejemplos neutros, guías HTML.'),
                 ('back/ · front/ · qa/', 'Dónde se clonan los repositorios de código y de pruebas de aceptación; traen sus skills scoped (back 6, front 5).'),
                 ('documentos/ · borrador/ · entregables/', 'Lo que se recibe del equipo funcional; el borrador de trabajo (no se versiona); lo promovido.'),
                 ('.githooks/ · .gitlab-ci.yml', 'El hook pre-commit (espejos, conteos, BOM, control chars, especificación de skills) y el pipeline opcional del propio Cerebro.')):
        H.append('<tr><td><code>%s</code></td><td>%s</td></tr>' % (html.escape(c), q))
    H.append('</table><h3>El Cerebro, por dentro</h3>' + arbol_cerebro())
    H.append('<p>Los cuatro pilares del módulo: <b>funcional/</b> (el qué: reglas <code>RN-&lt;MOD&gt;-nnn</code>, flujos con su bloque <code>## Derivación a backlog</code>), <b>metodologia/</b> (cómo trabaja el equipo), <b>arquitectura/</b> (cómo se construye: <code>DEC-nnn</code>, esqueleto, C1..C8) y <b>aplicacion/</b> (qué existe y qué se aprendió: <code>mapa.md</code>, <code>AP-nnn</code>, <code>DT-nnn</code>). <code>pendientes.md</code> (<code>P-nnn</code>) cruza a los cuatro.</p></section>')

    # 3 bucles
    H.append('<section id="bucles"><h2>03 · Los tres bucles</h2><p class="lead">Construir, autocorregirse y alimentar el Cerebro. Cada uno con un «sí» humano en el punto que importa.</p>' + bucles())
    H.append('<div class="cards"><div class="card"><h4>1. Construir</h4><p>Documento funcional → ficha del Cerebro con su bloque de derivación → tickets 1:1 (<code>derivar-arbol.py</code>) → Tareas con contrato, SDD y lista de tests → código con TDD en worktrees aislados → verificación por otro motor → Merge Request → cierre en la tarjeta.</p></div>')
    H.append('<div class="card"><h4>2. Autocorregirse</h4><p>Lo que el ecosistema muestra que tiene mal (una convención que todos rompen, un control siempre SIN DATOS, un script que cuenta mal) va a <code>mejoras.md</code> como propuesta, de a una, y se pregunta. Nunca se aplica solo.</p></div>')
    H.append('<div class="card"><h4>3. Alimentar el Cerebro</h4><p>Paso 7-bis: lo del negocio a <code>funcional/</code> o <code>decisiones.md</code> por la Consulta Interactiva; lo de la aplicación a <code>aplicacion/</code> (mapa, aprendizajes, deuda) con datos de <code>datos-cierre.py</code>; lo del ecosistema a <code>mejoras.md</code>.</p></div></div></section>')

    # 4 codigo
    H.append('<section id="codigo"><h2>04 · Cómo se construye código</h2><p class="lead">Un worker por Tarea, en un worktree aislado, con una misión única generada por script; verifica otro agente, con otro motor; aprueba una persona.</p>')
    H.append(flujo([('Tarea lista (DoR)', 'contrato · SDD · tests · modo de pruebas', ''), ('GATE de WORKTREE', 'gate-worktree.py · base, techo, árbol', ''), ('Misión única', 'armar-mision.py · Tarea + Gherkin + C1..C8', 'acento'),
                    ('Worker · TDD', 'guiar-tdd · test(rojo) → verde', 'acento'), ('Verificador · otro agente', '5 · 5-bis · 5-ter · 5-quater', 'acento'),
                    ('Aprobar', 'una persona, con el veredicto a la vista', ''), ('Merge Request', 'commits por importancia · evidencia/<ID>', ''), ('Cierre en la Tarea', 'comentar-tarea · datos-cierre.py', ''),
                    ('7-bis · Cerebro', 'funcional / aplicacion / mejoras', 'suave')], por_fila=5))
    H.append('<h3>Los cuatro controles, una pregunta cada uno</h3><table><tr><th>Control</th><th>Pregunta</th><th>Quién</th><th>Lo mecánico</th></tr>')
    for c, p, q, m in (('5 · verificar-tdd', '¿El ciclo rojo → verde ocurrió?', 'otro agente (DEC-005)', '<code>verificar-tdd.py --modo</code>: commits <code>test(rojo): n</code> sólo con tests, verde después, <code>evidencia/&lt;ID&gt;</code>'),
                       ('5-bis · code-review.md', '¿El código está bien escrito?', 'el mismo verificador', 'seis dimensiones; en Claude Code <code>/code-review</code> es un atajo'),
                       ('5-ter · auditar-codigo', '¿La entrega cumple lo que el pipeline exige?', 'el mismo verificador', '<code>auditar-diff.py</code>: secretos, PHI, elegibilidad; contrato y límites de módulo'),
                       ('5-quater · C1..C8', '¿Cumple las convenciones del Cerebro?', 'el mismo verificador', 'un veredicto por regla; C8 es SIN DATOS (pendiente DEC-003) hasta que el equipo lo escriba')):
        H.append('<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (c, p, q, m))
    H.append('</table><h3>El veredicto, siempre igual</h3><pre>VEREDICTO-INICIO\n5        verificar-tdd   : OK | HALLAZGO | SIN DATOS (&lt;motivo&gt;)\n5-bis    code-review     : OK | HALLAZGO | SIN DATOS (&lt;motivo&gt;)\n5-ter    auditar-codigo  : OK | HALLAZGO | SIN DATOS (&lt;motivo&gt;)\n5-quater C1..C8          : C1 OK · C2 … · C8 SIN DATOS (pendiente DEC-003)\nBLOQUEANTES: n   SIN DATOS (no se pudo mirar): n   SIN DATOS (pendiente declarado): n\nVerificado por: &lt;motor&gt; v&lt;versión&gt; · &lt;modelo&gt;\nVEREDICTO-FIN</pre>')
    H.append('<div class="nota"><b>Dos clases de SIN DATOS.</b> «No se pudo mirar» frena (el script no corrió, la suite no se ejecutó). «Pendiente declarado» (C8, SAST, cobertura, la guía del stack: lo que una DEC todavía no fijó) se lista y no frena. Sin esta distinción nada se aprobaría hasta DEC-003.</div>')
    H.append('<h3>TDD por defecto, con alternativas declaradas</h3><table><tr><th>Modo de pruebas (campo de la Tarea)</th><th>Cuándo</th><th>Qué exige igual</th></tr>')
    for m, c, e in (('TDD (default)', 'reglas, casos de uso, endpoints, lógica de front, bugs', 'el ciclo entero con el commit de rojo por ítem'),
                    ('test-después, con motivo', 'esqueleto, configuración, migraciones, UI puramente visual', 'la red mínima: tests y producción en el rango; sin motivo se audita como TDD'),
                    ('caracterización primero', 'código existente sin red (refactor o migración)', '<code>test(caracterizacion)</code> antes de tocar producción'),
                    ('sin tests, con motivo', 'un spike que no va a producción', 'SIN DATOS declarado; que no entre a una rama de entrega')):
        H.append('<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (m, c, e))
    H.append('</table><p><b>Back y front en paralelo</b> porque el contrato ya está cerrado en la Tarea: el back simula al front y el front simula la API desde el contrato (<code>simular-api-desde-el-contrato.md</code>). Dos modos de lanzamiento de <code>desarrollar-asignadas</code>: dentro de Orca o sin Orca (IntelliJ o terminal, <code>references/sin-orca.md</code>); la misión es la misma. En modo solo (DEC-006) el tablero es local y verifica otro agente del mismo motor. <b>Hoy el flujo es supervisado por diseño</b>: pregunta la base del worktree, el motor y el «Aprobar». Con <code>DEC-005</code> confirmada, esas respuestas salen de la decisión escrita y se citan.</p></section>')

    # 5 pruebas
    H.append('<section id="pruebas"><h2>05 · Pruebas: tres capas, ninguna redundante</h2>' + piramide())
    H.append('<p>Las dos primeras prueban <b>piezas</b> y viven en los repositorios de código; la tercera prueba <b>el sistema desplegado</b> contra los Escenarios de la Historia, trazada al <code>#ID</code>, y vive en <code>qa/</code> o donde decida <code>DEC-003</code>. Un repositorio de QA existente se absorbe con <code>absorber-aplicacion</code>. Método: <code>pruebas-de-aceptacion.md</code>.</p></section>')

    # 6 inversa
    H.append('<section id="inversa"><h2>06 · Ingeniería inversa, refactor y migración</h2><p class="lead">La skill <code>absorber-aplicacion</code> lee una aplicación existente, la vuelca al Cerebro ítem por ítem con su marca de confianza, y recién después, si se quiere, decide con una persona si se refactoriza o se migra. También sirve <b>sólo para documentar</b>.</p>' + absorber())
    H.append('<h3>Las siete fuentes, en orden</h3><table><tr><th>#</th><th>Fuente</th><th>Qué da</th><th>Quién</th></tr>')
    for n, f, q, qn in ((1, 'Inventario', 'qué hay: lenguajes, build, pipeline, contratos, migraciones, tests, deuda', '<code>inventariar-codigo.py</code>'),
                        (2, 'Radiografía', 'dónde mirar: endpoints, entidades, estados, pantallas, reglas candidatas, integraciones, permisos, dependencias; cada hecho con archivo:línea', '<code>radiografiar-codigo.py</code>'),
                        (3, 'Lectura por módulo', 'qué hace cada cosa, empezando por lo que la radiografía señaló', 'la skill'),
                        (4, 'Contrato y tests existentes', 'lo prometido y lo que alguien consideró importante', 'lectura'),
                        (5, 'Base de datos', 'estados reales, volúmenes, tablas muertas; esquema y conteos, nunca filas', 'con un «sí»'),
                        (6, 'Runtime', 'qué se usa de verdad; agregados', 'con un «sí»'),
                        (7, 'Personas', 'el porqué; preguntas juntas y numeradas', 'el turno de preguntas')):
        H.append('<tr><td>%d</td><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (n, f, q, qn))
    H.append('</table><p>Cada afirmación lleva su marca: <b>CONFIRMADO</b> (archivo:línea), <b>INFERIDO</b> (entra sólo como ⚠), <b>HUECO</b> (<code>P-nnn</code>, nunca una suposición). Una regla candidata se presenta con su fragmento de 10 a 20 líneas y el test que la cubre, o no se presenta. La <b>matriz de cobertura</b> dice qué módulo quedó sin leer. Los diagramas que van al Cerebro son texto: <code>--mermaid</code> (módulos, cruces de capa, ER del DDL); Archify, si está instalado, dibuja el HTML interactivo para presentar.</p>')
    H.append('<h3>Refactor o migración (DEC-004, la toma una persona)</h3>' + refactor_migracion() + '<p>La regla que ordena las dos: <b>primero la red, después el cambio</b>. Sin red no se refactoriza ni se migra: SIN DATOS. Método: <code>refactor-y-migracion.md</code>.</p></section>')

    # 7 autocorreccion
    H.append('<section id="autocorreccion"><h2>07 · Autocorrección consultada</h2><p class="lead">La IA propone cambios al esqueleto (arquitectura, reglas, skills, scripts) con señal, cambio exacto, impacto y qué pasa si no; los registra en <code>mejoras.md</code> y pregunta de a uno. Nunca aplica solo. Es la regla 8 de AGENTS.md.</p>')
    H.append('<table><tr><th>#</th><th>Señal</th><th>Qué cambiar</th><th>Estado</th></tr>')
    for fila in mej:
        est = fila[6].lower()
        tono = 'ok' if 'aplicada' in est or 'aceptada' in est else ('warn' if 'propuesta' in est or 'curso' in est else '')
        H.append('<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (html.escape(fila[0]), html.escape(fila[2][:220]), html.escape(fila[3][:260]), badge(fila[6][:40], tono)))
    H.append('</table></section>')

    # 8 skills
    H.append('<section id="skills"><h2>08 · Skills (%d canónicas + %d scoped)</h2><p class="lead">Una pregunta por skill, sin solapes. La fuente es <code>cerebro-digital/configuracion-ia/skills/</code>; los espejos se regeneran con <code>bin/sync-skills</code> y el hook exige que sean idénticos y que cada <code>SKILL.md</code> cumpla la especificación abierta (nombre igual a la carpeta, descripción de hasta 1024 caracteres).</p>' % (len(sks), len(sc['back']) + len(sc['front'])))
    for titulo, lista in agrupadas:
        H.append('<h3>%s (%d)</h3><div class="cards">' % (html.escape(titulo), len(lista)))
        for n in lista:
            s = sks[n]
            marcas = ''
            if n in ESCRIBEN_EN_EL_TABLERO:
                marcas += badge('escribe en el tablero', 'warn')
            if n in NUEVAS_HOY:
                marcas += badge('nueva', 'acento')
            H.append('<div class="card"><h4>%s%s</h4><p>%s</p><div class="pie">%d líneas · %d referencias</div></div>' % (html.escape(n), marcas, html.escape(primera_oracion(s['descripcion'])), s['lineas'], s['referencias']))
        H.append('</div>')
    H.append('<h3>Skills scoped de los repositorios de código</h3><div class="dos">')
    for lado in ('back', 'front'):
        H.append('<div><h4><code>%s/.claude/skills</code> (%d)</h4><table><tr><th>Skill</th><th>Qué contesta</th></tr>' % (lado, len(sc[lado])))
        for n, d in sc[lado]:
            H.append('<tr><td><code>%s</code></td><td>%s</td></tr>' % (html.escape(n), html.escape(primera_oracion(d, 170))))
        H.append('</table></div>')
    H.append('</div><p>El método de desarrollo vive en <code>desarrollo/references/metodo/</code> (%d documentos): %s.</p></section>' % (len(metodos), ', '.join('<code>%s</code>' % html.escape(m) for m in metodos)))

    # 9 scripts
    H.append('<section id="scripts"><h2>09 · Scripts determinísticos (%d)</h2><p class="lead">Python, biblioteca estándar, salida en tres estados: 0 OK, 1 HALLAZGO, 2 SIN DATOS. Lo que cuentan no lo discute el modelo; lo que no corrió es SIN DATOS.</p><table><tr><th>Script</th><th>Qué hace</th></tr>' % len(scr))
    for n, d in scr:
        H.append('<tr><td><code>bin/%s</code></td><td>%s</td></tr>' % (html.escape(n), html.escape(d)))
    H.append('</table><p>Con versión <code>.sh</code> y <code>.ps1</code>: %s.</p>' % ', '.join('<code>%s</code>' % html.escape(p) for p in pares))
    H.append('<h3>Pruebas de los scripts%s</h3><table><tr><th>Suite</th><th>Resultado</th><th>Detalle</th></tr>' % ('' if not rapido else ' (no corridas en modo rápido)'))
    for n, e, d in pruebas:
        H.append('<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>' % (html.escape(n), badge(e, 'ok' if e == 'OK' else ('bad' if e == 'FALLA' else '')), html.escape(d)))
    H.append('</table><p>%s</p></section>' % ('<b>%d suites en OK, %d casos.</b>' % (suites_ok, total_casos) if not rapido else 'Corré sin <code>--rapido</code> para que el informe traiga las cifras del día.'))

    # 10 doctor
    H.append('<section id="doctor"><h2>10 · El Doctor</h2><p class="lead"><code>doctor/doctor.py</code> revisa el repositorio en reposo (13 sondas) y, si hay código clonado en back/ o front/, el código (10 sondas). Es periódico y manual, nunca por Tarea; sus hallazgos se atienden uno por uno con <code>atender-hallazgos</code>. También existe <code>bin/verificar-skills.py</code> para la especificación de las skills y <code>bin/instalar.py</code> para el estado de un clone.</p>')
    hoy = {s.get('id'): s for s in (sondas_hoy or [])}
    H.append('<table><tr><th>#</th><th>Sonda</th><th>Qué mira</th>%s</tr>' % ('<th>Hoy</th>' if sondas_hoy else ''))
    ids = [s.get('id') for s in (sondas_hoy or [])]
    for n, t, d in sondas:
        celda = ''
        if sondas_hoy:
            s = hoy.get(ids[n - 1]) if n - 1 < len(ids) else None
            if s:
                est = s.get('estado', '')
                celda = '<td>%s<br><span style="color:var(--muted);font-size:12px">%s</span></td>' % (badge(est, 'ok' if est == 'OK' else ('bad' if est == 'HALLAZGO' else '')), html.escape((s.get('resumen') or '')[:150]))
            else:
                celda = '<td>—</td>'
        H.append('<tr><td>%d</td><td><b>%s</b></td><td>%s</td>%s</tr>' % (n, html.escape(t), html.escape(d[:220]), celda))
    H.append('</table>')
    if sondas_hoy:
        H.append('<p class="lead">En la carpeta del template, «Guardarraíles» da HALLAZGO porque no es un repositorio git todavía, y «Tamaño» y «Deuda declarada» son informativas. En una instancia clonada con el instalador corrido, las tres dan OK o informan.</p>')
    H.append('</section>')

    # 11 instalacion
    H.append('<section id="instalacion"><h2>11 · Instalación e instanciación</h2>' + flujo([('1 · Copiar', 'la carpeta del template, renombrarla', ''), ('2 · Instanciar', 'bin/instanciar.py: placeholders, módulo, espejos, fechas', 'acento'),
                                                                                           ('3 · git init + instalar', 'bin/instalar.py: hook, agentes, espejos, spec', 'acento'), ('4 · Completar el Cerebro', 'contexto, DEC-002/003/005, tablero, autores', ''),
                                                                                           ('5 · MCP por máquina', 'Azure DevOps, GitLab; opcional Engram, Archify', ''), ('6 · Verificar', 'doctor + probar-*.py + hook', ''), ('7 · Primera ficha', 'plantilla-ficha-flujo → sincronizar-backlog', 'suave')], por_fila=4))
    H.append('<pre>python -I bin/instanciar.py --proyecto "Gestión de Reservas" --producto "ReservaWeb" --organizacion "Acme" --modulo reservas --azure-org acme-devops --azure-proyecto "Reservas" --azure-team "Reservas Team"\ngit init\npython -I bin/instalar.py            # --con-archify para sumar Archify (opcional, Node)\nbash doctor/bin/doctor.sh            # o .ps1\nfor t in bin/probar-*.py; do python -B "$t"; done</pre>')
    H.append('<p>Quien clona después corre sólo <code>python -I bin/instalar.py</code>. Guía completa: <code>COMO-USAR-ESTE-TEMPLATE.md</code> e <code>INSTALACION.md</code>.</p></section>')

    # 12 bitacora
    H.append('<section id="bitacora"><h2>12 · Bitácora</h2><ul class="timeline">')
    for f, t, d in BITACORA:
        H.append('<li><time>%s</time><b>%s</b>%s</li>' % (f, html.escape(t), html.escape(d)))
    H.append('</ul><p class="lead">El historial fino del Cerebro vive en <code>cerebro-digital/log.md</code>; el de las propuestas, en <code>mejoras.md</code>.</p></section>')

    # 13 pendientes
    H.append('<section id="pendientes"><h2>13 · Pendientes y decisiones</h2><p class="lead">Lo que el esqueleto no puede decidir solo. Mientras falte, lo que depende de cada punto es SIN DATOS (pendiente declarado): se lista y no frena.</p><ul class="check">')
    for t, d in PENDIENTES_HUMANO:
        H.append('<li><b>%s</b><br><span style="color:var(--muted)">%s</span></li>' % (html.escape(t), html.escape(d)))
    H.append('</ul><h3>Decisiones de arquitectura (<code>decisiones.md</code>)</h3><table><tr><th>DEC</th><th>Qué</th><th>Estado</th></tr>')
    for c, t, e in decs:
        H.append('<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (c, html.escape(t), html.escape(e)))
    H.append('</table></section>')

    # 14 regenerar
    H.append('<section id="regenerar"><h2>14 · Cómo se regenera este informe</h2><pre>python -B bin/generar-informe.py              # corre pruebas y Doctor; tarda unos minutos\npython -B bin/generar-informe.py --rapido     # sin correr nada: estructura y catálogo</pre><p>Las skills, los scripts, las sondas, las propuestas y las decisiones se leen de sus archivos; la bitácora y los pendientes se editan en el propio script, en un solo lugar. Los diagramas son SVG embebido: el informe no depende de nada externo y se abre en cualquier navegador o se imprime.</p></section>')
    H.append('</main></div><footer>TEMPLATE ESTRUCTURA IA · informe generado el %s · bin/generar-informe.py · sin dependencias externas</footer></body></html>' % ahora)
    return '\n'.join(H)


PROMPT_MD = os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills', 'arrancar-proyecto', 'references', 'prompt-maestro.md')


def prompt_maestro():
    """(texto del prompt entre los primeros ``` del .md, pasos previos, filas de la tabla 'Lo que sigue'); '' si no esta."""
    if not os.path.isfile(PROMPT_MD):
        return '', [], []
    t = open(PROMPT_MD, 'r', encoding='utf-8', errors='replace').read()
    partes = t.split('```')
    prompt = partes[1].strip('\n') if len(partes) >= 3 else ''
    pasos = re.findall(r'^\d+\.\s+(.+?)(?=\n\d+\.|\n\n|\Z)', t.split('## Antes de pegar')[1].split('## El prompt')[0], re.S | re.M) if '## Antes de pegar' in t else []
    filas = []
    for l in t.split('## Lo que sigue')[1].split('\n') if '## Lo que sigue' in t else []:
        if l.startswith('|') and not l.startswith('|---') and 'Querés' not in l:
            c = [x.strip() for x in l.strip().strip('|').split('|')]
            if len(c) == 2:
                filas.append(c)
    return prompt, [' '.join(p.split()) for p in pasos], filas


def main():
    ap = argparse.ArgumentParser(description='Genera el informe visual del esqueleto.')
    ap.add_argument('--salida', default=os.path.join(RAIZ, 'INFORME-ESQUELETO.html'))
    ap.add_argument('--rapido', action='store_true', help='no correr pruebas ni Doctor')
    a = ap.parse_args()
    if not os.path.isdir(SK):
        print('SIN DATOS -- no existe %s' % SK)
        return SIN_DATOS
    texto = generar(a.rapido)
    salida = os.path.abspath(a.salida)
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)
    print('informe escrito en %s (%d KB%s)' % (salida, len(texto.encode('utf-8')) // 1024, ', modo rapido' if a.rapido else ''))
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
