#!/usr/bin/env python3
"""Instancia el TEMPLATE ESTRUCTURA IA para un proyecto concreto. Solo biblioteca estandar.

    python -I bin/instanciar.py --proyecto "Gestion de Reservas" --producto "ReservaWeb" \
        --organizacion "Acme" --modulo reservas \
        --azure-org acme-devops --azure-proyecto "Reservas" --azure-team "Reservas Team"

    python -I bin/instanciar.py ... --dry-run      (muestra que haria, no toca nada)
    python -I bin/instanciar.py ... --sin-espejos  (no regenera .claude/ ni .agents/)
    python -I bin/instanciar.py --modo solo --tablero local --proyecto ... (sin Azure: el tablero son archivos del Cerebro)
    python -I bin/instanciar.py --modo solo --desatendido ...  (quien instancia firma DEC-005, el modo desatendido)

QUE HACE, en orden:
  1. Reemplaza los placeholders {{PROYECTO}}, {{PRODUCTO}}, {{ORGANIZACION}}, {{AZURE_ORG}},
     {{AZURE_PROYECTO}} y {{AZURE_TEAM}} en todos los archivos de texto del repositorio.
  2. Renombra la carpeta cerebro-digital/modulo-ejemplo/ al slug del modulo y reemplaza
     el token 'modulo-ejemplo' en todos los archivos de texto (rutas, wikilinks, frontmatter).
  3. Regenera los espejos: skills -> .agents/skills y .claude/skills; agentes -> .agents/agents
     y .claude/agents (lo mismo que bin/sync-skills.* y bin/sync-agents.*).
  4. Imprime lo que queda por completar a mano.

Conserva el BOM de los archivos que lo tenian (los .ps1) y no lo agrega a los demas. No toca
archivos binarios ni .git/. Idempotente: correrlo dos veces no rompe nada (la segunda no
encuentra placeholders).

Tres estados:  0 = OK   1 = no se pudo instanciar (argumento invalido o carpeta rota)   2 = SIN DATOS
ASCII puro en este archivo, igual que el resto de bin/.
"""

import argparse
import datetime
import os
import re
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTO = ('.md', '.html', '.py', '.sh', '.ps1', '.toml', '.yaml', '.yml', '.json', '.txt',
         '.example', '.css', '.js')
NOMBRES_TEXTO = ('.gitignore', '.gitattributes', 'pre-commit')
IGNORAR_DIRS = ('.git', 'node_modules', '__pycache__', 'salida')
# Estos dos hablan DE los placeholders: si se reemplazaran, el instanciador se rompe a si mismo
# (la segunda corrida fallaria) y la guia quedaria sin sentido.
EXCLUIR = (os.path.join('bin', 'instanciar.py'), 'COMO-USAR-ESTE-TEMPLATE.md')
MODULO_PLACEHOLDER = 'modulo-ejemplo'
RUTA_MODULO = os.path.join('cerebro-digital', MODULO_PLACEHOLDER)
ESPEJOS = (
    (os.path.join('cerebro-digital', 'configuracion-ia', 'skills'),
     (os.path.join('.agents', 'skills'), os.path.join('.claude', 'skills'))),
    (os.path.join('cerebro-digital', 'configuracion-ia', 'agentes'),
     (os.path.join('.agents', 'agents'), os.path.join('.claude', 'agents'))),
)


def es_texto(ruta):
    nombre = os.path.basename(ruta)
    return nombre.endswith(TEXTO) or nombre in NOMBRES_TEXTO


def archivos_de_texto():
    for base, dirs, archivos in os.walk(RAIZ):
        dirs[:] = sorted(d for d in dirs if d not in IGNORAR_DIRS)
        for a in sorted(archivos):
            ruta = os.path.join(base, a)
            if os.path.relpath(ruta, RAIZ) in EXCLUIR:
                continue
            if es_texto(ruta):
                yield ruta


def leer(ruta):
    with open(ruta, 'rb') as h:
        crudo = h.read()
    bom = crudo.startswith(b'\xef\xbb\xbf')
    cuerpo = crudo[3:] if bom else crudo
    try:
        return cuerpo.decode('utf-8'), bom
    except UnicodeDecodeError:
        return None, bom


def escribir(ruta, texto, bom):
    with open(ruta, 'wb') as h:
        h.write((b'\xef\xbb\xbf' if bom else b'') + texto.encode('utf-8'))


def slug_valido(s):
    return re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', s) is not None


def reemplazar_en_todo(pares, dry_run):
    """pares: lista de (literal_viejo, literal_nuevo). Devuelve cuantos archivos cambiaron."""
    cambiados = 0
    for ruta in archivos_de_texto():
        texto, bom = leer(ruta)
        if texto is None:
            print('  aviso: no es UTF-8, se deja igual: %s' % os.path.relpath(ruta, RAIZ))
            continue
        nuevo = texto
        for viejo, reemplazo in pares:
            nuevo = nuevo.replace(viejo, reemplazo)
        if nuevo != texto:
            cambiados += 1
            if not dry_run:
                escribir(ruta, nuevo, bom)
    return cambiados


def regenerar_espejos(dry_run):
    for fuente_rel, destinos in ESPEJOS:
        fuente = os.path.join(RAIZ, fuente_rel)
        if not os.path.isdir(fuente):
            print('  SIN DATOS: no existe la fuente %s' % fuente_rel)
            continue
        for destino_rel in destinos:
            destino = os.path.join(RAIZ, destino_rel)
            print('  espejo %s <- %s' % (destino_rel, fuente_rel))
            if dry_run:
                continue
            if os.path.isdir(destino):
                shutil.rmtree(destino)
            shutil.copytree(fuente, destino)


def main():
    ap = argparse.ArgumentParser(description='Instancia el TEMPLATE ESTRUCTURA IA para un proyecto.')
    ap.add_argument('--proyecto', required=True, help='nombre del proyecto, p. ej. "Gestion de Reservas"')
    ap.add_argument('--producto', required=True, help='nombre del producto/sistema, p. ej. "ReservaWeb"')
    ap.add_argument('--organizacion', required=True, help='nombre de la organizacion, p. ej. "Acme"')
    ap.add_argument('--modulo', required=True, help='slug del modulo del Cerebro (minusculas, numeros y guiones), p. ej. reservas')
    ap.add_argument('--modo', choices=['solo', 'equipo'], required=True, help='solo (desarrollo personal) o equipo; se pregunta en cada proyecto (DEC-006)')
    ap.add_argument('--tablero', choices=['local', 'azure', 'jira', 'otro'], default='', help='local (archivos en el Cerebro), azure (MCP), jira u otro tablero por MCP; por defecto local en modo solo y azure en modo equipo')
    ap.add_argument('--autor', default='', help='quien instancia: queda en DEC-006 y es el nombre que firma aceptadas y cortes; por defecto git config user.name')
    ap.add_argument('--desatendido', action='store_true', help='solo con --modo solo: quien instancia firma DEC-005 (aprobar sola una Tarea con cero bloqueantes y pasarla a Resolved); sin esto queda sin firmar')
    ap.add_argument('--stack-back', default='', help='lenguaje y framework del back (DEC-003), p. ej. "Python 3.12 + FastAPI"; vacio = se decide antes de la primera Tarea')
    ap.add_argument('--stack-front', default='', help='lenguaje y framework del front (DEC-003), p. ej. "React 19 + Vite"')
    ap.add_argument('--stack-base', default='', help='motor de base y version minima (DEC-003), p. ej. "PostgreSQL 16"')
    ap.add_argument('--stack-build', default='', help='build y runner de tests del back (DEC-003), p. ej. "uv + pytest"')
    ap.add_argument('--stack-e2e', default='', help='tipo de aplicacion y motor de punta a punta (DEC-003), p. ej. "web: Playwright, data-testid" o "escritorio Tauri: Playwright sobre el front + tauri-driver"')
    ap.add_argument('--comando-tests-back', default='', help='comando que corre la suite completa del back, p. ej. "python -m unittest discover -s tests -v" (va a tdd-stack-back.md)')
    ap.add_argument('--comando-tests-front', default='', help='comando que corre la suite completa del front, p. ej. "npm.cmd test" (va a tdd-stack-front.md)')
    ap.add_argument('--azure-org', default='', help='organizacion de Azure DevOps (solo si --tablero azure)')
    ap.add_argument('--azure-proyecto', default='', help='proyecto/board autorizado (solo si --tablero azure)')
    ap.add_argument('--azure-team', default='', help='team autorizado (solo si --tablero azure)')
    ap.add_argument('--dry-run', action='store_true', help='mostrar que haria sin tocar nada')
    ap.add_argument('--sin-espejos', action='store_true', help='no regenerar .claude/ ni .agents/')
    a = ap.parse_args()

    if not slug_valido(a.modulo):
        print('ERROR: --modulo tiene que ser un slug: minusculas, numeros y guiones (ej. reservas, gestion-turnos).')
        return 1
    if a.modulo == MODULO_PLACEHOLDER:
        print('ERROR: el slug del modulo no puede ser el placeholder "%s".' % MODULO_PLACEHOLDER)
        return 1
    if a.desatendido and a.modo != 'solo':
        print('ERROR: --desatendido firma la columna del modo solo de DEC-005; en modo equipo la decide el equipo.')
        return 1
    tablero = a.tablero or ('local' if a.modo == 'solo' else 'azure')
    if tablero == 'azure':
        for nombre, valor in (('--azure-org', a.azure_org), ('--azure-proyecto', a.azure_proyecto), ('--azure-team', a.azure_team)):
            if not valor.strip():
                print('ERROR: con --tablero azure, %s no puede estar vacio.' % nombre)
                return 1
    else:
        a.azure_org, a.azure_proyecto, a.azure_team = ('tablero-' + tablero,) * 3
    autor = a.autor.strip()
    if not autor:
        try:
            import subprocess
            autor = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout.strip()
        except OSError:
            autor = ''
    autor = autor or 'equipo'
    if not os.path.isdir(os.path.join(RAIZ, 'cerebro-digital')):
        print('SIN DATOS: no encuentro cerebro-digital/ al lado de bin/. Corre esto parado en la raiz del template.')
        return 2

    modo = ' (dry-run: no se toca nada)' if a.dry_run else ''
    print('Instanciando el template en %s%s' % (RAIZ, modo))

    # 1. placeholders
    pares = [
        ('{{PROYECTO}}', a.proyecto), ('{{PRODUCTO}}', a.producto), ('{{ORGANIZACION}}', a.organizacion),
        ('{{AZURE_ORG}}', a.azure_org), ('{{AZURE_PROYECTO}}', a.azure_proyecto), ('{{AZURE_TEAM}}', a.azure_team),
        # la URL del tablero lleva los espacios codificados
        ('%7B%7BAZURE_PROYECTO%7D%7D', a.azure_proyecto.replace(' ', '%20')),
        ('%7B%7BAZURE_TEAM%7D%7D', a.azure_team.replace(' ', '%20')),
    ]
    n = reemplazar_en_todo(pares, a.dry_run)
    print('[1/4] placeholders reemplazados en %d archivo(s)' % n)

    # 2. modulo
    origen = os.path.join(RAIZ, RUTA_MODULO)
    destino = os.path.join(RAIZ, 'cerebro-digital', a.modulo)
    if os.path.isdir(origen):
        if os.path.isdir(destino):
            print('ERROR: ya existe cerebro-digital/%s y tambien modulo-ejemplo/: resolvelo a mano.' % a.modulo)
            return 1
        print('[2/4] cerebro-digital/%s -> cerebro-digital/%s' % (MODULO_PLACEHOLDER, a.modulo))
        if not a.dry_run:
            os.rename(origen, destino)
    elif os.path.isdir(destino):
        print('[2/4] la carpeta del modulo ya se llama %s (ya instanciado)' % a.modulo)
    else:
        print('[2/4] SIN DATOS: no existe ni modulo-ejemplo/ ni %s/ dentro de cerebro-digital/' % a.modulo)
    n = reemplazar_en_todo([(MODULO_PLACEHOLDER, a.modulo)], a.dry_run)
    print('      token "%s" reemplazado en %d archivo(s)' % (MODULO_PLACEHOLDER, n))

    # 2-ter. modo de trabajo (DEC-006) y, si se dijo, el stack (DEC-003)
    dec = os.path.join(RAIZ, 'cerebro-digital', a.modulo, 'arquitectura', 'decisiones.md')
    fijados = 0
    if os.path.isfile(dec):
        texto, bom = leer(dec)
        marca = '<se fija al instanciar>'
        if marca in texto:
            texto = texto.replace('**Se fija al instanciar** con `bin/instanciar.py --modo solo|equipo --tablero local|azure` y queda\nescrito acá. ' + chr(0x26a0) + ' ' + marca,
                                  '**Confirmado al instanciar (%s): modo %s, tablero %s, autor %s.**' % (datetime.date.today().isoformat(), a.modo, tablero, autor), 1)
            texto = texto.replace(marca, 'modo %s, tablero %s' % (a.modo, tablero))
        firma = '<se firma al instanciar en modo solo>'
        if a.desatendido and firma in texto:
            texto = texto.replace(chr(0x26a0) + ' **Sin firmar** ' + firma + '.',
                                  '**Confirmado para el modo solo (%s, firmado por %s).**' % (datetime.date.today().isoformat(), autor), 1)
        stack = (('Lenguaje y framework del back', a.stack_back), ('Lenguaje y framework del front', a.stack_front),
                 ('Motor de base de datos y versión mínima soportada', a.stack_base), ('Herramienta de build y runner de tests del back', a.stack_build),
                 ('Tipo de aplicación (web, Electron, escritorio con webview, escritorio nativo, móvil, línea de comandos, API) y el motor de pruebas de punta a punta que le corresponde (Playwright, WebDriver, Appium o Maestro, proceso, HTTP), con el atributo de identificación estable (`data-testid` o `automation-id`)', a.stack_e2e))
        fijados = 0
        for tema, valor in stack:
            if valor.strip():
                fila_vieja = '| %s | — | ⚠ a definir |' % tema
                if fila_vieja in texto:
                    texto = texto.replace(fila_vieja, '| %s | %s | Confirmado al instanciar (%s) |' % (tema, valor.strip(), datetime.date.today().isoformat()), 1)
                    fijados += 1
        if fijados:
            texto = texto.replace('**Estado:** ⚠ **A definir por el equipo.** Hasta que exista, toda skill que dependa del stack\nreporta `SIN DATOS` en lo que no pueda verificar.',
                                  '**Estado:** **Confirmado al instanciar** para los temas marcados abajo; el resto ⚠ a definir antes de la primera Tarea que lo necesite (hasta entonces reporta `SIN DATOS`).', 1)
        if not a.dry_run:
            escribir(dec, texto, bom)
    # 2-quater. las guias del stack: la fila del stack y el comando de la suite, si se dijeron
    MET = os.path.join(RAIZ, 'cerebro-digital', 'configuracion-ia', 'skills', 'desarrollo', 'references', 'metodo')
    for guia, fila_vieja, valor, cmd_viejo, cmd in (
            ('tdd-stack-back.md', '| Lenguaje y framework | `<completar: lenguaje + framework del back>` |', a.stack_back, '<completar: comando que corre la suite completa>        # la que vale para el verde', a.comando_tests_back),
            ('tdd-stack-front.md', '| Framework de interfaz | `<completar: framework del front>` |', a.stack_front, '<completar: comando que corre la suite completa>          # la que vale para el verde', a.comando_tests_front)):
        p = os.path.join(MET, guia)
        if not os.path.isfile(p):
            continue
        texto, bom = leer(p)
        if valor.strip():
            texto = texto.replace(fila_vieja, fila_vieja.split('|')[0] + '|' + fila_vieja.split('|')[1] + '| %s (fijado al instanciar) |' % valor.strip(), 1)
        if cmd.strip():
            texto = texto.replace(cmd_viejo, cmd.strip() + '   # la suite completa, la que vale para el verde', 1)
        if (valor.strip() or cmd.strip()) and not a.dry_run:
            escribir(p, texto, bom)
        print('[2-quater] %s: %s' % (guia, ', '.join(x for x in (('stack' if valor.strip() else ''), ('comando de tests' if cmd.strip() else '')) if x) or 'sin cambios (queda en plantilla)'))
    print('[2-ter] modo %s, tablero %s, autor %s -> DEC-006%s%s' % (a.modo, tablero, autor,
          '; DEC-005 (modo desatendido) firmada' if a.desatendido else '; DEC-005 (modo desatendido) sin firmar: todo se pregunta', ('; DEC-003: %d tema(s) del stack fijados' % fijados) if fijados else '; DEC-003 (el stack) queda a definir'))

    # 2-bis. last_updated: la fecha de instanciacion, no la del template
    hoy = datetime.date.today().isoformat()
    fechados = 0
    for ruta in archivos_de_texto():
        if not ruta.endswith('.md') or any(ruta.endswith(x) for x in EXCLUIR):
            continue
        texto, bom = leer(ruta)
        nuevo = re.sub(r'^last_updated:[^\r\n]*$', 'last_updated: ' + hoy, texto, count=1, flags=re.M)
        if nuevo != texto:
            fechados += 1
            if not a.dry_run:
                escribir(ruta, nuevo, bom)
    print('[2-bis] last_updated fijado a %s en %d archivo(s)' % (hoy, fechados))

    # 3. espejos
    if a.sin_espejos:
        print('[3/4] espejos: salteado (--sin-espejos)')
    else:
        print('[3/4] regenerando espejos')
        regenerar_espejos(a.dry_run)

    # 4. que sigue
    print('[4/4] listo (modo %s, tablero %s). Lo que sigue, a mano (nada de esto se inventa):' % (a.modo, tablero))
    if tablero == 'local':
        print('  - el tablero es cerebro-digital/%s/backlog/ (bin/tablero-local.py); el toolkit de Azure queda disponible por si se cambia' % a.modulo)
    elif tablero in ('jira', 'otro'):
        print('  - tablero %s por MCP: completar su columna en la tabla de herramientas por funcion (integracion-azure-mcp/00-index.md) y el guard en tablero-autorizado.md' % tablero)
    print('  - git init (o clonar el remoto vacio) y  python -I bin/instalar.py  (hook, agentes, espejos, spec de skills)')
    print('  - cerebro-digital/contexto.md y fuentes.md')
    print('  - tablero/conocimiento/contexto-proyecto.md (slices, etiquetas, proceso)')
    print('  - cerebro-digital/%s/arquitectura/decisiones.md: confirmar DEC-002 y tomar DEC-003 (el stack)' % a.modulo)
    print('  - cerebro-digital/%s/arquitectura/esqueleto-proyectos.md (incluida la convencion C8)' % a.modulo)
    print('  - skill desarrollo: references/metodo/tdd-stack-back.md y tdd-stack-front.md')
    print('  - back/README.md y front/README.md: tabla Stack')
    print('  - diseno/diseno-sistema.md, entregables/disenos/logo.png; bin/probar-reglas.py: ID de una Historia real')
    print('  - MCP por maquina: integracion-azure-mcp/ e integracion-gitlab-mcp/ (nunca el token en un archivo)')
    print('  - verificar: bash doctor/bin/doctor.sh  y  python -B bin/probar-*.py')
    print('Detalle: COMO-USAR-ESTE-TEMPLATE.md')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
