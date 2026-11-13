#!/usr/bin/env python3
"""Prueba de bin/auditoria/cerebro.py: qué reglas existen. Una regla existe donde el Cerebro la DEFINE (un título o la
primera celda de una fila de tabla), no donde se la nombra: si no, una regla inventada en un ticket se validaba sola.
Se corre:  python -B bin/probar-auditoria-cerebro.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from auditoria import cerebro  # noqa: E402

ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def escribir(raiz, rel, t):
    p = os.path.join(raiz, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(t)


def main():
    print('== auditoria/cerebro: que reglas existen')
    raiz = tempfile.mkdtemp(prefix='probar-cerebro-')
    try:
        escribir(raiz, 'cerebro-digital/res/funcional/reservas.md',
                 '# Reservas\n\n### RN-RES-001 — Una sala por turno\nTexto.\n\n'
                 'Ver también RN-RES-009, que todavía no existe.\n\n'
                 '| Regla | Qué dice |\n|---|---|\n| RN-RES-002 | Se cancela hasta 2 h antes |\n')
        escribir(raiz, 'cerebro-digital/res/arquitectura/decisiones.md', '## DEC-001 — Código fuera del repo\n\nTexto.\n')
        escribir(raiz, 'cerebro-digital/res/backlog/0007-tarea.md', '---\nid: 7\n---\n### RN-RES-007 — inventada en un ticket\n[RN-RES-007]\n')
        escribir(raiz, 'cerebro-digital/res/pendientes.md', '## P-001\n¿RN-RES-008 aplica a feriados?\n')
        escribir(raiz, 'cerebro-digital/res/funcional/plantilla-ficha-flujo.md', '### RN-MOD-001 — Una regla de la plantilla\n')
        escribir(raiz, 'cerebro-digital/res/funcional/permisos.md', '### RN-RES-013 — <persona> sólo ve sus reservas\n')
        escribir(raiz, 'cerebro-digital/res/funcional/otra.md', '### RN-RES-010 — <a completar>\n')
        escribir(raiz, 'cerebro-digital/configuracion-ia/skills/x/SKILL.md', '### RN-XXX-001 — ejemplo de una skill\n')
        idx = cerebro.indice_reglas(raiz)
        caso('una regla definida como título existe, con su archivo', idx.get('RN-RES-001') == 'cerebro-digital/res/funcional/reservas.md', str(idx))
        caso('una regla definida en la primera celda de una tabla existe', 'RN-RES-002' in idx, str(idx))
        caso('una decisión definida como título existe', 'DEC-001' in idx, str(idx))
        caso('nombrada en un texto, no existe', 'RN-RES-009' not in idx, str(idx))
        caso('definida en un ticket del tablero local (backlog/), no existe: no se valida sola', 'RN-RES-007' not in idx, str(idx))
        caso('nombrada en un pendiente, no existe', 'RN-RES-008' not in idx, str(idx))
        caso('la de una plantilla, o un título que es un hueco (<...>), no existe', 'RN-MOD-001' not in idx and 'RN-RES-010' not in idx, str(idx))
        caso('la de una skill (configuracion-ia/), no existe', 'RN-XXX-001' not in idx, str(idx))
        caso('un titulo que empieza con un marcador pero dice algo (<persona> sólo ve...), existe', 'RN-RES-013' in idx, str(idx))
    finally:
        shutil.rmtree(raiz, ignore_errors=True)

    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
