#!/usr/bin/env python3
"""Prueba de bin/mapa-modernizacion.py sobre un Cerebro de mentira (modernizacion.md + decisiones.md), con un golden y
un resultado de paridad firmados por el mismo codigo de bin/paridad.py (y uno escrito a mano, que NO tiene que valer).
Se corre:  python -B bin/probar-mapa-modernizacion.py   -> OK o FALLA, con el detalle de cada caso."""

import datetime
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'mapa-modernizacion.py')
sys.path.insert(0, AQUI)
paridad = importlib.import_module('paridad')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def escribir(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(t)


def golden_firmado(p, oraculo='http://127.0.0.1:1'):
    casos = {'CP-01': {'estado': 200, 'tipo': 'application/json', 'cuerpo': {'ok': True}}}
    g = {'grabado_por': 'bin/paridad.py', 'version': 1, 'fecha': '2026-11-01', 'oraculo': oraculo, 'slice': 'reservas',
         'corpus_sha256': 'abc', 'casos': casos}
    g['firma'] = paridad.firmar(casos, oraculo, 'abc')
    paridad.escribir_json(p, g)
    return g


def resultado_firmado(p, **cambios):
    d = {'veredicto': 'OK', 'slice': 'reservas', 'fecha': datetime.date.today().isoformat(), 'golden': '/x/golden-reservas.json',
         'golden_firma': '', 'nuevo': 'http://127.0.0.1:2', 'casos': 1, 'iguales': 1, 'con_hallazgo': 0, 'volatiles': [],
         'aceptadas_archivo': '', 'aceptadas_detalle': [], 'aceptadas_sin_aprobar': [], 'filas': [], 'escrito_por': 'bin/paridad.py'}
    d.update(cambios)
    d['firma'] = paridad.firmar_resultado(d)
    paridad.escribir_json(p, d)


TABLA = '''# Modernización

| Slice | Estrategia | Estado | Contrato | Corpus | Golden | Paridad | Corte aprobado por | Notas |
|---|---|---|---|---|---|---|---|---|
| **reservas** | migración | %s | openapi.yaml | corpus.json | golden-reservas.json | 2026-11-03 OK | %s | |
| reportes | migración | pendiente | | | | | | |
| usuarios | refactor | %s | limites.md | | | | %s | solo tests en el repo |
| `<completar: nombre del slice>` | `<completar>` | pendiente | | | | | | |
'''


def main():
    print('== mapa-modernizacion')
    tmp = tempfile.mkdtemp(prefix='probar-mapa-')
    apl = os.path.join(tmp, 'cerebro-digital', 'reservas', 'aplicacion')
    mod = os.path.join(apl, 'modernizacion.md')
    dec = os.path.join(tmp, 'cerebro-digital', 'reservas', 'arquitectura', 'decisiones.md')
    escribir(mod, TABLA % ('paridad', 'Persona de prueba', 'cortado', 'Persona de prueba'))
    escribir(dec, '# Decisiones\n\n## DEC-003 — Stack\n\n**Estado:** Confirmado.\n\n## DEC-004 — Refactor o migración\n\n**Estado:** **Confirmado (2026-11-03).**\n\n## DEC-005 — x\n')
    g = golden_firmado(os.path.join(apl, 'paridad', 'reservas', 'golden-reservas.json'))
    rc, out = correr('ver', mod)
    caso('ver: OK (0), 3 slices (la fila <completar> se ignora), negritas normalizadas', rc == 0 and '3 slice(s)' in out and 'reservas ' in out and '**' not in out, out[:300])
    caso('un refactor sin corpus ni golden no es hallazgo', 'usuarios' in out and 'HALLAZGO' not in out)
    rc, out = correr('ver', mod, '--mermaid')
    caso('--mermaid dibuja la secuencia de estados', 'flowchart LR' in out and 'pendiente --> contrato' in out)
    rc, out = correr('ver', mod, '--json')
    d = json.loads(out)
    caso('--json devuelve los slices', d['veredicto'] == 'OK' and len(d['slices']) == 3)
    escribir(mod, TABLA % ('paridad', 'Persona de prueba', 'cortado', ''))
    rc, out = correr('verificar', mod)
    caso('un refactor cortado sin persona que apruebe: HALLAZGO (1)', rc == 1 and 'Corte aprobado por' in out, out[:300])
    escribir(mod, TABLA % ('paridad', 'Persona de prueba', 'red', 'Persona de prueba'))
    par = os.path.join(tmp, 'paridad.json')
    resultado_firmado(par, golden_firma=g['firma'])
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('corte con todo en orden (golden y resultado firmados): OK (0), 9 de 9', rc == 0 and '9 de 9' in out, out[:500])
    resultado_firmado(par, golden_firma=g['firma'], filas=[{'id': 'RC-03', 'resultado': 'SIN DATOS'}])
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('un resultado en OK pero con un caso sin comparar (de un paridad.py viejo): HALLAZGO', rc == 1 and 'FALTA ningun caso de la paridad quedo sin comparar' in out, out[:500])
    resultado_firmado(par, golden_firma=g['firma'], filas=[{'id': 'RC-03', 'resultado': 'sin comparar, aceptado'}])
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('un caso sin comparar aceptado por una persona: OK, pero lo avisa', rc == 0 and 'AVISO casos sin comparar' in out and 'RC-03' in out, out[:500])
    resultado_firmado(par, golden_firma=g['firma'])
    # resultado escrito a mano: no es evidencia
    with open(par, 'w', encoding='utf-8') as h:
        json.dump({'veredicto': 'OK', 'slice': 'reservas', 'fecha': datetime.date.today().isoformat(), 'golden': 'golden-reservas.json', 'aceptadas_sin_aprobar': []}, h)
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('un resultado de paridad escrito a mano: SIN DATOS (2), no OK', rc == 2 and 'NO verifica' in out, out[:300])
    resultado_firmado(par, golden_firma=g['firma'], veredicto='HALLAZGO')
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('paridad en HALLAZGO: el corte es HALLAZGO (1)', rc == 1 and 'FALTA la paridad dio OK' in out, out[:400])
    resultado_firmado(par, golden_firma='otra-firma', fecha='2026-01-01')
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('paridad vieja y de otro golden (firma distinta): HALLAZGO con las dos marcadas', rc == 1 and 'FALTA la paridad es reciente' in out and 'FALTA la paridad corrio contra el golden' in out, out[:500])
    resultado_firmado(par, golden_firma=g['firma'], volatiles=['/0/fecha'])
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('con volatiles: OK igual pero AVISA cuales se ignoraron', rc == 0 and 'AVISO volatiles' in out and '/0/fecha' in out, out[:400])
    escribir(mod, TABLA % ('paridad', 'Claude (agente)', 'red', 'Persona de prueba'))
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('un agente como aprobador del corte no vale: HALLAZGO', rc == 1 and 'FALTA una persona aprobo' in out, out[:400])
    escribir(mod, (TABLA % ('paridad', 'Persona de prueba', 'red', 'Persona de prueba')).replace('golden-reservas.json', 'no-existe.json'))
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('la tabla cita un golden que no existe: SIN DATOS (2)', rc == 2 and 'no lo encuentro' in out, out[:300])
    escribir(dec, '# Decisiones\n\n## DEC-004 — Refactor o migración\n\n**Estado:** ⚠ a decidir.\n')
    escribir(mod, TABLA % ('paridad', 'Persona de prueba', 'red', 'Persona de prueba'))
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', par)
    caso('DEC-004 sin confirmar: HALLAZGO', rc == 1 and 'FALTA DEC-004' in out, out[:400])
    escribir(dec, '# Decisiones\n\n## DEC-004 — Refactor o migración\n\n**Estado:** **Confirmado.**\n')
    rc, out = correr('corte', mod, '--slice', 'reservas', '--paridad', os.path.join(tmp, 'no.json'))
    caso('sin resultado de paridad: SIN DATOS (2), no OK', rc == 2)
    rc, out = correr('corte', mod, '--slice', 'reservas')
    caso('migracion sin --paridad: SIN DATOS (2) y dice que hace falta', rc == 2 and 'paridad' in out)
    rc, out = correr('corte', mod, '--slice', 'noexiste', '--paridad', par)
    caso('slice que no esta en la tabla: SIN DATOS (2)', rc == 2)
    # refactor en el lugar: el corte se prueba con el VEREDICTO del verificador
    escribir(mod, TABLA % ('paridad', 'Persona de prueba', 'paridad', 'Persona de prueba'))
    ver = os.path.join(tmp, 'veredicto.md')
    escribir(ver, '```\nVEREDICTO-INICIO\n5        verificar-tdd   : OK   -- script: OK (modo caracterizacion), criterio: ok\n5-bis    code-review     : OK\n5-ter    auditar-codigo  : OK\n5-quater C1..C8          : C1 OK\nBLOQUEANTES: 0   SIN DATOS (no se pudo mirar): 0   SIN DATOS (pendiente declarado): 0\nVerificado por: Claude Code\nVEREDICTO-FIN\n```\n')
    rc, out = correr('corte', mod, '--slice', 'usuarios', '--veredicto', ver)
    caso('refactor con veredicto en OK y caracterizacion: OK (0), 8 de 8', rc == 0 and '8 de 8' in out, out[:500])
    rc, out = correr('corte', mod, '--slice', 'reservas', '--veredicto', ver)
    caso('migracion con --veredicto y sin --paridad: SIN DATOS (2), el veredicto no reemplaza a la paridad', rc == 2 and 'paridad' in out, out[:300])
    rc, out = correr('corte', mod, '--slice', 'usuarios')
    caso('refactor sin --veredicto: SIN DATOS (2)', rc == 2 and 'veredicto' in out)
    escribir(ver, '```\nVEREDICTO-INICIO\n5        verificar-tdd   : HALLAZGO\nBLOQUEANTES: 1\nVEREDICTO-FIN\n```\n')
    rc, out = correr('corte', mod, '--slice', 'usuarios', '--veredicto', ver)
    caso('refactor con verificar-tdd en HALLAZGO: HALLAZGO (1)', rc == 1 and 'FALTA verificar-tdd dio OK' in out, out[:400])
    escribir(mod, '# sin tabla\n')
    rc, out = correr('ver', mod)
    caso('archivo sin la tabla: SIN DATOS (2)', rc == 2)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
