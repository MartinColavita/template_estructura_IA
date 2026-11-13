#!/usr/bin/env python3
"""La parte MECANICA de auditar-codigo: secretos y datos personales en el diff, y elegibilidad.
SOLO LECTURA.

    python bin/auditar-diff.py --repo <worktree> [--base origin/develop] [--id 1234]
    python bin/auditar-diff.py --archivo cambios.diff [--json]

Tres estados, nunca dos:  0 = sin hallazgos   1 = hay hallazgos   2 = SIN DATOS (diff vacio o ilegible)

QUE MIDE sobre las lineas AGREGADAS del diff:
  HALLAZGO (seguro):  claves y contrasenas escritas, claves privadas, tokens con formato conocido.
  AVISO (criterio):   correos, telefonos y numeros largos de documento en archivos de test, fixtures
                      o datos; nombres de persona asignados a un campo. Un marcador <persona>,
                      <documento>, <identificador> NO es hallazgo: es justamente lo que se pide.
  Elegibilidad:       diff vacio -> SIN DATOS; solo documentacion -> aviso; la rama no nombra el
                      --id de la Tarea -> aviso.

QUE NO MIDE: el contrato contra el codigo, los limites de modulo, la cobertura de la lista de tests
(eso lo hace verificar-tdd.py y la skill). Un diff sin hallazgos no es una entrega aprobada.
Solo biblioteca estandar. ASCII puro en este archivo.
"""

import argparse
import json
import re
import subprocess
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditoria import phi  # noqa: E402  el mismo reconocimiento de emails que auditar-tarea

OK, HALLAZGO, SIN_DATOS = 0, 1, 2

SECRETOS = [
    ('clave o contrasena escrita', re.compile(r'(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token|private[_-]?key|client[_-]?secret)\b\s*[:=]\s*["\'][^"\']{6,}["\']')),
    ('clave privada', re.compile(r'-----BEGIN (RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY')),
    ('token JWT', re.compile(r'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}')),
    ('clave de proveedor de nube', re.compile(r'\b(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|glpat-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{32,})\b')),
    ('URL con usuario y clave', re.compile(r'[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]{3,}@')),
]
PHI = [
    ('telefono', re.compile(r'(?<![\w/])\+?\d{2,4}[\s.-]\d{3,4}[\s.-]\d{3,4}\b')),
    ('numero de documento o tarjeta', re.compile(r'(?<![\w./-])\d{7,16}(?![\w.-])')),
    ('nombre de persona asignado', re.compile(r'(?i)\b(nombre|apellido|name|surname|first_?name|last_?name)\b\s*[:=]\s*["\'][A-Z][a-z]+(\s[A-Z][a-z]+)?["\']')),
]
MARCADOR = re.compile(r'<[a-z][a-z_-]{2,30}>|&lt;[a-z][a-z_-]{2,30}&gt;')
DOCS = re.compile(r'\.(md|txt|rst|adoc|html)$|(^|/)docs?/')
DATOS = re.compile(r'(^|/)(test|tests|spec|__tests__|fixtures?|datos?|data|seed|mocks?|samples?)(/|$)|\.(json|csv|sql|ya?ml|xml)$')


def git(repo, *args):
    r = subprocess.run(['git', '-C', repo] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.returncode, r.stdout


def lineas_agregadas(diff):
    """[(archivo, nro, texto)] de las lineas '+' del diff unificado."""
    res, archivo, nro = [], None, 0
    for l in diff.splitlines():
        if l.startswith('+++ '):
            archivo = l[4:].strip()
            archivo = archivo[2:] if archivo.startswith('b/') else archivo
            continue
        if l.startswith('@@'):
            m = re.search(r'\+(\d+)', l)
            nro = int(m.group(1)) - 1 if m else 0
            continue
        if l.startswith('+') and not l.startswith('+++'):
            nro += 1
            res.append((archivo or '?', nro, l[1:]))
        elif not l.startswith('-') and not l.startswith('\\'):
            nro += 1
    return res


def main():
    ap = argparse.ArgumentParser(description='Secretos y datos personales en el diff (solo lectura).')
    ap.add_argument('--repo')
    ap.add_argument('--base', default='origin/develop')
    ap.add_argument('--archivo', help='un diff ya generado, en vez de leerlo de git')
    ap.add_argument('--id', default='')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    rama = None
    if a.archivo:
        with open(a.archivo, 'r', encoding='utf-8', errors='replace') as h:
            diff = h.read()
    elif a.repo:
        # la cascada de auditar-codigo: la primera que devuelva algo, mas lo no commiteado
        diff = ''
        for rango in (a.base + '...HEAD', '@{upstream}...HEAD', 'main...HEAD', 'HEAD~1'):
            rc, out = git(a.repo, 'diff', rango)
            if rc == 0 and out.strip():
                diff = out
                break
        rc, pend = git(a.repo, 'diff', 'HEAD')
        diff += '\n' + (pend if rc == 0 else '')
        rc, rama = git(a.repo, 'branch', '--show-current')
        rama = rama.strip()
    else:
        print('SIN DATOS -- falta --repo o --archivo.')
        return SIN_DATOS

    agregadas = lineas_agregadas(diff)
    if not agregadas:
        print('SIN DATOS -- el diff no tiene lineas agregadas: no hay que auditar (o no se pudo leer).')
        return SIN_DATOS

    archivos = sorted(set(f for f, _, _ in agregadas))
    hallazgos, avisos = [], []
    for f, n, t in agregadas:
        if MARCADOR.search(t) and not any(rx.search(t) for _, rx in SECRETOS):
            continue
        for nombre, rx in SECRETOS:
            if rx.search(t):
                hallazgos.append('%s:%d: %s' % (f, n, nombre))
        if DATOS.search(f) or not f.endswith(('.md', '.txt')):
            if any(real for _, real in phi.emails(t)):
                avisos.append('%s:%d: posible correo electronico (leerlo: si es un dato real, es PHI)' % (f, n))
            for nombre, rx in PHI:
                if nombre == 'numero de documento o tarjeta' and not DATOS.search(f):
                    continue
                if rx.search(t):
                    avisos.append('%s:%d: posible %s (leerlo: si es un dato real, es PHI)' % (f, n, nombre))
    if all(DOCS.search(f) for f in archivos):
        avisos.append('el diff solo toca documentacion: revisar si corresponde la auditoria de entrega')
    if a.id and rama is not None and a.id not in rama:
        avisos.append('la rama %s no nombra la Tarea %s' % (rama or '(sin rama)', a.id))

    estado = HALLAZGO if hallazgos else OK
    salida = {'estado': 'HALLAZGO' if hallazgos else 'OK', 'archivos': archivos, 'lineas_agregadas': len(agregadas),
              'rama': rama, 'hallazgos': hallazgos, 'avisos': avisos[:50],
              'no_mira': ['el contrato contra el codigo', 'los limites de modulo', 'la cobertura de la lista de tests']}
    if a.json:
        print(json.dumps(salida, ensure_ascii=True, indent=1))
    else:
        print('AUDITAR DIFF (mecanico) -- %s  [%d archivo(s), %d linea(s) agregada(s); secretos: %d patron(es) mirados, %d hallazgo(s); datos personales: %d patron(es), %d aviso(s)]' % (
            salida['estado'], len(archivos), len(agregadas), len(SECRETOS), len(hallazgos), len(PHI) + 1, sum(1 for v in avisos if 'posible' in v)))
        for h in hallazgos:
            print('  HALLAZGO: ' + h)
        for v in avisos[:50]:
            print('  aviso: ' + v)
        print('  Lo que este script NO mira: ' + '; '.join(salida['no_mira']) + '.')
    return estado


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
