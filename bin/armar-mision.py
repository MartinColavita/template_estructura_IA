#!/usr/bin/env python3
"""Arma la MISION de un worker o de un verificador, siempre con la misma plantilla. SOLO LECTURA del Cerebro.

    python bin/armar-mision.py --rol worker --entorno intellij --motor claude --id 1234 --titulo "..." \
        --tarea borrador/misiones/1234-tarea.md --worktree <ruta> --rama task/1234-x --sha-base <sha> \
        --nucleo <ruta del repositorio del Cerebro> --repo back --modulo reservas [--link URL] \
        [--modo-pruebas tdd] [--stack-tdd <ruta>] [--out borrador/misiones/1234-worker.md]

Tres estados, nunca dos:  0 = mision escrita   1 = (no aplica)   2 = SIN DATOS (falta algo que la mision necesita)

POR QUE EXISTE. Dos skills de orquestacion (Orca e IntelliJ) tenian cada una su plantilla de mision en
prosa, distintas entre si, y cada sesion la rearmaba de memoria: dos agentes con la misma Tarea recibian
misiones distintas. Si la arma un script, la mision es la misma en todas las sesiones y en los dos
entornos, y lo unico que cambia es lo que cambia de verdad: la Tarea, el worktree, el rol y el canal.

QUE PONE (en este orden, siempre):
  0 idioma  1 objetivo (la Tarea COMPLETA, pegada, con el Gherkin de la Historia padre si viene)
  2 donde (worktree, rama, sha de base)  3 reglas (AGENTS.md)  4 metodo (rutas absolutas, solo lo que
  ese rol necesita)  5 skills por ruta absoluta (worker: guiar-tdd y armar-swagger en back; verificador:
  verificar-tdd, code-review.md, auditar-codigo)  6 contexto de arquitectura  7 las convenciones C1..C8
  COPIADAS de orquestador-desarrollo.md (se leen del archivo, no se tipean)  8 limites  9 resultado
  esperado (el worker: su resumen; el verificador: el bloque VEREDICTO-INICIO..FIN)  10 canal.

QUE NO HACE. No lee el tablero (la Tarea la pega el orquestador en --tarea), no decide el modo de pruebas
(lo copia del campo de la Tarea), no inventa rutas: si un archivo que la mision cita no existe, SIN DATOS.
Solo biblioteca estandar. ASCII puro en este archivo; la mision sale en espanol con tildes porque las
copia de los archivos del Cerebro.
"""

import argparse
import os
import re
import sys

OK, _, SIN_DATOS = 0, 1, 2
SK = os.path.join('cerebro-digital', 'configuracion-ia', 'skills')
MET = os.path.join(SK, 'desarrollo', 'references', 'metodo')
ORQ = os.path.join('cerebro-digital', 'configuracion-ia', 'orquestador-desarrollo.md')


def leer(ruta):
    with open(ruta, 'r', encoding='utf-8-sig', errors='replace') as h:
        return h.read()


def convenciones(nucleo):
    """Las filas C1..C8 de la tabla de convenciones del orquestador, tal cual estan escritas."""
    texto = leer(os.path.join(nucleo, ORQ))
    filas = []
    for linea in texto.split('\n'):
        m = re.match(r'^\|\s*(C\d)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$', linea)
        if m:
            filas.append((m.group(1), m.group(2), m.group(3)))
    return filas


def nota_vacio(p):
    """'' si el archivo tiene contenido real; una nota si sigue en plantilla o vacio (para no mandar a leer nada)."""
    try:
        t = leer(p)
    except OSError:
        return ''
    cuerpo = re.sub(r'^---\n.*?\n---\n', '', t, count=1, flags=re.S)
    util = '\n'.join(l for l in cuerpo.split('\n') if '<completar' not in l and not l.strip().startswith('|---'))
    if cuerpo.count('<completar') >= 3 or len(util.strip()) < 400:
        return ' *(todavía en plantilla o vacío: no hace falta abrirlo)*'
    return ''


def version_motor(motor):
    """'Claude Code v1.2.3' si el CLI contesta en 5 segundos; si no, el marcador para completar a mano."""
    import subprocess
    nombre = {'claude': 'Claude Code', 'gemini': 'Gemini CLI'}.get(motor, motor)
    try:
        r = subprocess.run(motor + ' --version', shell=True, capture_output=True, text=True, timeout=5)
        v = re.search(r'\d+\.\d+(?:\.\d+)?', r.stdout or '')
        if v:
            return '%s v%s' % (nombre, v.group(0))
    except Exception:
        pass
    return '%s v<versión: `%s --version`>' % (nombre, motor)


def gherkin_de(tarea_md):
    m = re.search(r'(?ims)^#+\s*(criterios de aceptaci.n|gherkin)[^\n]*\n(.*?)(?=^#+\s|\Z)', tarea_md)
    return m.group(2).strip() if m else ''


def modo_de(tarea_md):
    m = re.search(r'(?i)modo de pruebas\s*:?\**\s*:?\s*`?([^`\n|]+)', tarea_md)
    return m.group(1).strip().strip('*').strip() if m else ''


def main():
    ap = argparse.ArgumentParser(description='Arma la mision de un worker o un verificador.')
    ap.add_argument('--rol', choices=['worker', 'verificador'], required=True)
    ap.add_argument('--entorno', choices=['orca', 'intellij'], required=True)
    ap.add_argument('--motor', choices=['claude', 'gemini'], required=True)
    ap.add_argument('--id', required=True)
    ap.add_argument('--titulo', required=True)
    ap.add_argument('--tarea', required=True, help='archivo .md con el texto COMPLETO de la Tarea (y el Gherkin del padre bajo un titulo "Criterios de aceptacion")')
    ap.add_argument('--worktree', required=True)
    ap.add_argument('--rama', required=True)
    ap.add_argument('--sha-base', required=True)
    ap.add_argument('--nucleo', required=True, help='ruta absoluta del repositorio del Cerebro')
    ap.add_argument('--repo', choices=['back', 'front'], required=True)
    ap.add_argument('--modulo', required=True, help='slug del modulo del Cerebro (carpeta en cerebro-digital/)')
    ap.add_argument('--link', default='')
    ap.add_argument('--modo-pruebas', default='', help='si no se pasa, se copia del campo de la Tarea; si no esta, tdd')
    ap.add_argument('--stack-tdd', default='', help='ruta de la guia de TDD del stack; por defecto tdd-stack-<repo>.md')
    ap.add_argument('--out', default='')
    a = ap.parse_args()

    nucleo = os.path.abspath(a.nucleo)
    if not os.path.isfile(a.tarea):
        print('SIN DATOS -- no existe el archivo de la Tarea: %s' % a.tarea)
        return SIN_DATOS
    tarea = leer(a.tarea).strip()
    if not tarea:
        print('SIN DATOS -- el archivo de la Tarea esta vacio.')
        return SIN_DATOS
    faltan = []

    def ruta(*partes):
        p = os.path.join(nucleo, *partes)
        if not os.path.exists(p):
            faltan.append(os.path.relpath(p, nucleo))
        return p

    agents = ruta('AGENTS.md')
    arq = ruta('cerebro-digital', a.modulo, 'arquitectura')
    esqueleto = ruta('cerebro-digital', a.modulo, 'arquitectura', 'esqueleto-proyectos.md')
    decisiones = ruta('cerebro-digital', a.modulo, 'arquitectura', 'decisiones.md')
    aplicacion = ruta('cerebro-digital', a.modulo, 'aplicacion', 'index.md')
    tdd = ruta(MET, 'tdd-ciclo-y-evidencia.md')
    endpoint = ruta(MET, 'crear-endpoint.md')
    contrato = ruta(MET, 'contrato-openapi.md')
    stack = a.stack_tdd or ruta(MET, 'tdd-stack-%s.md' % a.repo)
    code_review = ruta(MET, 'code-review.md')
    skills_repo = os.path.join(nucleo, a.repo, '.claude', 'skills')
    guiar = ruta(a.repo, '.claude', 'skills', 'guiar-tdd', 'SKILL.md')
    verificar = ruta(a.repo, '.claude', 'skills', 'verificar-tdd', 'SKILL.md')
    auditar = ruta(a.repo, '.claude', 'skills', 'auditar-codigo', 'SKILL.md')
    swagger = os.path.join(skills_repo, 'armar-swagger', 'SKILL.md') if a.repo == 'back' else ''
    if swagger and not os.path.exists(swagger):
        faltan.append(os.path.relpath(swagger, nucleo))
    frontend = []
    if a.repo == 'front':
        for f in ('index.md', 'reglas-generales.md'):
            frontend.append(ruta('cerebro-digital', a.modulo, 'arquitectura', 'frontend', f))
    if faltan:
        print('SIN DATOS -- la mision cita archivos que no existen en %s:' % nucleo)
        for f in faltan:
            print('  - ' + f)
        return SIN_DATOS
    conv = convenciones(nucleo)
    if len(conv) < 8:
        print('SIN DATOS -- no encontre las 8 filas C1..C8 en %s (hay %d).' % (ORQ, len(conv)))
        return SIN_DATOS
    gherkin = gherkin_de(tarea)
    tiene_api = bool(re.search(r'(?i)\bopenapi\b|\bendpoint\b|capa[^\n]{0,20}\bapi\b|/swagger|@(Get|Post)Mapping|\bHTTP\b', tarea))
    toca_paridad = bool(re.search(r'(?i)\bparidad\b|slice en moderniz|modernizacion\.md|test\(caracterizacion\)', tarea))
    toca_base = bool(re.search(r'(?i)\bmigraci[oó]n(?:es)?\b|\bschema\b|\bALTER TABLE\b|\bCREATE TABLE\b|\besquema de (?:la )?base\b', tarea))
    migracion_md = ruta(MET, 'migracion-de-base.md')
    SOLO_BACK = {'C1', 'C2', 'C5'}   # describen la estructura de modulos y el contrato OpenAPI del back; en el front mandan las reglas de frontend/
    modo = a.modo_pruebas or modo_de(tarea) or 'tdd'

    L = []
    rol = 'WORKER (programa)' if a.rol == 'worker' else 'VERIFICADOR (solo lectura)'
    L.append('# Misión %s — Tarea #%s %s' % (rol, a.id, a.titulo))
    L.append('')
    L.append('> Generada por `bin/armar-mision.py` (plantilla única para Orca e IntelliJ). Entorno: %s · motor: %s · repo: %s · módulo: %s · modo de pruebas: **%s**.' % (a.entorno, a.motor, a.repo, a.modulo, modo))
    L.append('')
    L.append('## 0. Idioma')
    L.append('Todo en **español (Argentina)**: respuestas, preguntas, resumen, mensajes de commit y comentarios en el código. Los nombres de código siguen la regla C3 de abajo. No heredás el idioma de nadie: si no lo dijera esta misión, contestarías en inglés.')
    L.append('')
    L.append('## 1. Objetivo')
    L.append('**#%s %s**%s. El texto completo de la Tarea es el siguiente; **no reconstruyas la tarjeta de memoria ni la leas del tablero**: es ésta.' % (a.id, a.titulo, (' — ' + a.link) if a.link else ''))
    L.append('')
    L.append('```markdown')
    L.append(tarea)
    L.append('```')
    if gherkin:
        L.append('')
        L.append('> El Gherkin de la Historia padre está arriba, en la sección «Criterios de aceptación» de la Tarea: es la fuente del cierre BDD↔TDD (chequeo 7).')
    else:
        L.append('')
        L.append('> ⚠ La Tarea no trae pegado el Gherkin de la Historia padre: el cierre BDD↔TDD (chequeo 7 de `verificar-tdd`) queda **SIN DATOS**; no lo reconstruyas.')
    L.append('')
    L.append('## 2. Dónde')
    L.append('- Worktree: `%s` — **se trabaja sólo ahí** (`git -C "%s" …`).' % (a.worktree, a.worktree))
    L.append('- Rama: `%s`. Base anotada al abrir el worktree: `%s`. Lo que se audita son los commits `%s..%s`.' % (a.rama, a.sha_base, a.sha_base, a.rama))
    L.append('- Repositorio del Cerebro (sólo lectura): `%s`.' % nucleo)
    L.append('')
    L.append('## 3. Reglas')
    L.append('- `%s` — leé sólo «Instrucciones obligatorias» y «Skills de desarrollo» (los guardarraíles G1–G6 y la regla del idioma); lo del tablero, los tickets y el modo lote no te aplica.' % agents)
    L.append('')
    L.append('## 4. Método (leer antes de tocar nada, en este orden)')
    L.append('- `%s` — el ciclo rojo → verde → refactor y qué es evidencia.' % tdd)
    if a.rol == 'worker':
        if tiene_api:
            L.append('- `%s` — cómo se crea un endpoint con el contrato primero.' % endpoint)
            L.append('- `%s` — el contrato OpenAPI.' % contrato)
        else:
            L.append('- (esta Tarea no toca la capa `api` ni un contrato OpenAPI: no hace falta leer `crear-endpoint.md` ni `contrato-openapi.md`)')
    else:
        L.append('- `%s` — la revisión por dimensiones (control 5-bis), en cualquier motor.' % code_review)
        L.append('- El rojo se verifica **por lectura, sin checkout**: la aserción está en el test del commit `test(rojo)` (y sus 1 a 3 líneas de salida en el cuerpo del commit, `git log -1 --format=%B <sha>`), y el estado de producción anterior se lee con `git show <sha>^:<archivo>`; con eso se sabe si falló en la aserción o por un símbolo inexistente.')
    if leer(stack).count('<completar') >= 5:
        L.append('- `%s` — la guía del stack **está en plantilla** (sin completar): no hace falta leerla; valen los comandos de la Tarea, y el control que dependa de la guía es `SIN DATOS (pendiente DEC-003)`.' % stack)
    else:
        L.append('- `%s` — lo específico del stack (si tiene `<completar>`, el control que dependa de eso es `SIN DATOS (pendiente DEC-003)`: se lista, no frena).' % stack)
    if toca_base:
        L.append('- `%s` — la Tarea toca el esquema de la base: expandir / migrar / contraer, columna nueva admite nulos, vuelta atrás escrita **y probada**, se puede correr dos veces, conteos antes y después.' % migracion_md)
    L.append('')
    L.append('## 5. Skills (por ruta absoluta; no se heredan)')
    if a.rol == 'worker':
        L.append('- `%s` — la disciplina del ciclo. Un commit `test(rojo): <n.º de ítem> <resumen>` con **sólo el test**, después el de la implementación.' % guiar)
        if swagger and tiene_api:
            L.append('- `%s` — consolidar el fragmento OpenAPI (sólo back).' % swagger)
        L.append('- **No** cargás `verificar-tdd` ni `auditar-codigo`: son del verificador. Quien produce no lee la guía de cómo auditarse.')
    else:
        L.append('- `%s` — control 5: ¿el ciclo ocurrió? Primero el script: `python "%s" --repo "%s" --base %s --id %s --modo %s%s`.' % (
            verificar, os.path.join(nucleo, 'bin', 'verificar-tdd.py'), a.worktree, a.sha_base, a.id, modo.split(':')[0].strip().replace(' ', '-').lower(), (' --motivo "%s"' % modo.split(':', 1)[1].strip()) if ':' in modo else ''))
        L.append('- `%s` — control 5-ter: contrato de la Tarea, límites de módulo, sin PHI ni secretos. Primero el script: `python "%s" --repo "%s" --base %s --id %s`.' % (
            auditar, os.path.join(nucleo, 'bin', 'auditar-diff.py'), a.worktree, a.sha_base, a.id))
        if toca_paridad:
            L.append('- Control de **paridad** (la Tarea pertenece a un slice en modernización): `python "%s" comparar --corpus <corpus.json> --golden <golden.json> --nuevo <url o cmd de la nueva> --json` con el corpus y el golden que cita la Tarea; OK sólo con cero diferencias sin aceptar. Si no corrió, `SIN DATOS`. Vos no aceptás diferencias: las listás.' % os.path.join(nucleo, 'bin', 'paridad.py'))
        if toca_base:
            L.append('- Control de **migraciones** (la Tarea toca el esquema): con `migracion-de-base.md` a la vista, verificá expandir antes que contraer, columna nueva que admite nulos, guion de vuelta atrás presente **y con test que lo corre**, y que migrar dos veces no rompe. El esquema resultante se lee con `python "%s" <carpeta de migraciones> --aplicar` (o sobre una base de prueba ya migrada; sobre la carpeta sin `--aplicar` sólo se ven los CREATE TABLE); nunca filas de datos. Se reporta dentro de 5-ter.' % os.path.join(nucleo, 'bin', 'esquema-base.py'))
        L.append('- Control 5-bis con `code-review.md` (el documento está en la sección 4, Método): **aplicá el método a mano, una dimensión por vez**, y entregalo como la línea 5-bis del bloque más sus hallazgos. No invoques `/code-review` desde un sub-agente: dispara revisores propios con su costo y no reporta en este formato.')
    L.append('')
    L.append('## 6. Contexto de arquitectura (sólo lectura)')
    L.append('- `%s`%s y `%s`.' % (esqueleto, nota_vacio(esqueleto), decisiones))
    apl_dir = os.path.dirname(aplicacion)
    vacios = [n for n in ('mapa', 'aprendizajes', 'deuda') if nota_vacio(os.path.join(apl_dir, n + '.md'))]
    L.append('- `%s` — la memoria de la aplicación: trampas ya pisadas (`aprendizajes.md`), deuda (`deuda.md`), qué existe (`mapa.md`).%s' % (aplicacion, (' *(todavía vacíos: %s)*' % ', '.join(vacios)) if vacios else ''))
    for f in frontend:
        L.append('- `%s`.%s' % (f, nota_vacio(f)))
    L.append('- Si el repositorio contradice al Cerebro, manda el Cerebro (C6).')
    L.append('')
    L.append('## 7. Convenciones del Cerebro (reglas duras, copiadas de `orquestador-desarrollo.md`)')
    if a.repo == 'front':
        L.append('- **Las reglas 1 a 12 de `arquitectura/frontend/reglas-generales.md`** (sección 6) son las convenciones del front: el verificador da **un veredicto por regla** en el renglón 5-quater (`R1..R12`); las que dependen de `DEC-003` son `SIN DATOS (pendiente declarado)`.')
        L.append('- **C1, C2 y C5 describen el back** (módulos `api/application/domain/infra`, traductor de errores HTTP, `openapi.yaml`): **no aplican a este repositorio**. En el front mandan `arquitectura/frontend/reglas-generales.md` e `index.md` (sección 6); el verificador reporta C1, C2 y C5 como `N/A (front)`.')
    for c, regla, chequeo in conv:
        if a.repo == 'front' and c in SOLO_BACK:
            continue
        if chr(0x26a0) in regla:
            L.append('- **%s** — ' % c + chr(0x26a0) + ' todavía no definida (`DEC-003`, se cierra antes de la primera Tarea que la necesite): no te aplica; el verificador la reporta `SIN DATOS (pendiente declarado)`.')
        else:
            L.append('- **%s** — %s *Cómo se chequea:* %s' % (c, regla, chequeo))
    L.append('')
    L.append('## 8. Límites')
    if a.rol == 'worker':
        L.append('- Sólo lo que dicen la Tarea y sus `[RN-…]`. Si falta un dato o la Tarea toca una decisión `⚠`, **no elegís ni inventás**: hacés lo que no depende de eso, dejás afuera lo que sí y lo devolvés como **pendiente a confirmar**. Frenás sólo si el gris impide toda la Tarea.')
        L.append('- **Antes del primer rojo, corré la suite completa una vez**: así sabés cómo se ve el verde y que el comando anda en tu shell (en Windows con Git Bash, `npm.cmd` en vez de `npm`/`npx` si el PATH tiene espacios).')
        L.append('- Agregá los archivos **por nombre** (`git add <archivo> …`; un commit puede llevar varios), nunca `git add -A`. Lo generado (`__pycache__`, `target/`, `node_modules/`, `dist/`) no se versiona: si el repositorio no tiene `.gitignore` que lo cubra, **agregalo en un commit `chore(gitignore): …` aparte**, antes del primer rojo.')
        L.append('- Un solo módulo (C7). Sin PHI: marcadores `<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<direccion>`, `<dato-sensible>`.')
        L.append('- **No pusheás, no abrís Merge Request, no tocás el tablero, no escribís el Cerebro, no delegás en otros agentes.** El README del repo se actualiza en el mismo cambio si cambian dependencias, variables o comandos.')
        L.append('- Modo de pruebas de esta Tarea: **%s**. Sin declaración, es TDD.' % modo)
    else:
        L.append('- **Sólo lectura**: no escribís código, no commiteás, no pusheás, no tocás el tablero ni el Cerebro, no delegás, no leés lo que dejó quien programó (ni su memoria ni su resumen): verificás sobre el repositorio y esta misión. Sin PHI.')
        L.append('- **Corrés sólo los comandos que nombran la misión y la Tarea** (los scripts de `bin/`, la suite, `git`): nunca un módulo de la aplicación con argumentos de prueba (`--help` puede ser una entrada y crear un archivo). Si necesitás ejecutar código del repo para verificar, lo hacés en una carpeta temporal fuera del worktree (`git archive`), nunca adentro.')
        L.append('- **Lo que el esqueleto o una decisión tiene `⚠`** se reporta `SIN DATOS (pendiente declarado)`, nunca OK; C1 y C2 se juzgan sólo sobre lo que sí está definido.')
        L.append('- Dos clases de `SIN DATOS`: «no se pudo mirar» **frena**; «pendiente declarado en una DEC-nnn» (C8, SAST, cobertura, guía del stack) **se lista y no frena**. Decí cuál es cada uno.')
    L.append('')
    L.append('## 9. Resultado esperado (Markdown, corto)')
    if a.rol == 'worker':
        L.append('- Estado: **terminado** / **frenado con pregunta**.')
        L.append('- Los commits rojo → verde en orden, los tests que pasan (N de M de la lista), archivos tocados, qué cambió del README.')
        L.append('- **Pendientes a confirmar**: qué es cada gris, qué se hizo mientras tanto, qué hace falta para cerrarlo.')
        L.append('- **Conocimiento para el Cerebro** (negocio) y **memoria de la aplicación** (bug y causa, trampa del stack, deuda aceptada): un renglón por ítem, o «Nada nuevo».')
    else:
        L.append('```')
        L.append('VEREDICTO-INICIO')
        L.append('5       verificar-tdd   : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: <OK/HALLAZGO/SIN DATOS>, criterio: <...>')
        L.append('5-bis   code-review     : OK | HALLAZGO | SIN DATOS (<motivo>)')
        L.append('5-ter   auditar-codigo  : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: <...>')
        if a.repo == 'front':
            L.append('5-quater C3,C4,C6,C7,C8 + R1..R12 : C3 <OK|HALLAZGO|SIN DATOS|N/A> · C4 … · C8 SIN DATOS (pendiente DEC-003) · R1 <OK|HALLAZGO|SIN DATOS|N/A> · R2 … · R12   -- C1, C2 y C5 son N/A (front); R1..R12 son las reglas de frontend/reglas-generales.md, una por una')
        else:
            L.append('5-quater C1..C8         : C1 <OK|HALLAZGO|SIN DATOS|N/A> · C2 … · C8 SIN DATOS (pendiente DEC-003)   -- N/A si la Tarea no toca esa capa')
        if toca_paridad:
            L.append('5-quinquies paridad     : OK | HALLAZGO | SIN DATOS (<motivo>)   -- script: paridad.py comparar')
        else:
            L.append('5-quinquies paridad     : N/A (la Tarea no es de un slice en modernización; ya resuelto, no hay que fundamentarlo)')
        L.append('BLOQUEANTES: <n>   SIN DATOS (no se pudo mirar): <n>   SIN DATOS (pendiente declarado): <n>')
        L.append('Verificado por: %s · <modelo> · sub-agente de sólo lectura, contexto limpio' % version_motor(a.motor))
        L.append('VEREDICTO-FIN')
        L.append('```')
        L.append('Debajo, un hallazgo por línea: `archivo:línea — qué — por qué frena o no`, y para el control 5 una línea por ítem de la lista con la aserción citada (`archivo:línea`). Sin piso de hallazgos: un informe vacío es válido.')
    L.append('')
    L.append('## 10. Cómo avisás')
    if a.entorno == 'orca':
        if a.motor == 'claude':
            L.append('- Dudas bloqueantes: con el `ask` del preámbulo de Orca. Al terminar: `worker_done` una sola vez, con `--outcome` y el resultado de la sección 9.')
        else:
            L.append('- Dudas bloqueantes: una línea `PREGUNTA-ORQUESTADOR: …` sola en la salida. Al terminar: la línea `TAREA-TERMINADA` o `TAREA-FALLIDA`, seguida del resultado de la sección 9.')
    else:
        L.append('- Dudas bloqueantes: una línea `PREGUNTA-ORQUESTADOR: …` sola en la salida y terminás el turno; el orquestador te reanuda con la respuesta. Al terminar: la línea `TAREA-TERMINADA` o `TAREA-FALLIDA`, seguida del resultado de la sección 9.%s' % (' Para el verificador: **TERMINADA** = la verificación se completó (con o sin hallazgos); **FALLIDA** = no se pudo verificar (SIN DATOS que frena).' if a.rol == 'verificador' else ''))
    L.append('- **«Pendiente a confirmar» es la vía por defecto** para un gris chico: hacés lo que no depende de eso y lo dejás escrito en el resultado. La pregunta bloqueante es sólo para lo que impide toda la Tarea. Nunca una pregunta suelta que el orquestador no vea; nunca «asumo que…» callado: o pendiente escrito, o pregunta.')
    texto = '\n'.join(L) + '\n'
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, 'w', encoding='utf-8', newline='\n') as h:
            h.write(texto)
        print('mision escrita en %s (%d lineas, rol %s, entorno %s, motor %s, modo %s%s)' % (a.out, texto.count('\n'), a.rol, a.entorno, a.motor, modo, '' if gherkin else ', SIN Gherkin del padre'))
    else:
        sys.stdout.write(texto)
    return OK


if __name__ == '__main__':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
