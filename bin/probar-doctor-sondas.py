#!/usr/bin/env python3
"""Prueba de sondas del Doctor que no pueden dar OK sin haber mirado: si git no responde, o si una guarda del hook
sólo aparece nombrada en un comentario. Carga doctor/doctor.py y le cambia lo que lee (git, la raíz) por casos armados.
Se corre:  python -B bin/probar-doctor-sondas.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import shutil
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'doctor'))
sys.argv = [sys.argv[0]]
import doctor  # noqa: E402

ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def main():
    print('== doctor: sondas que no dan OK sin mirar')
    git_real, raiz_real = doctor.git, doctor.ROOT
    caso('git() de verdad, con un comando que falla: devuelve None (no "", que se leia como "nada")',
         doctor.git('comando-que-no-existe-xyz') is None)
    try:
        doctor.git = lambda *a: None   # git no respondio
        r = doctor.sonda_andamiaje()
        caso('andamiaje con git que no responde: SIN DATOS, no OK', r['estado'] == 'SIN DATOS', r['estado'] + ' ' + r['resumen'][:120])
        r = doctor.sonda_guardarrailes()
        caso('guardarrailes con git que no responde: SIN DATOS (no "sin configurar")', r['estado'] == 'SIN DATOS', r['estado'])
        caso('fechas_git con git que no responde: None (no un diccionario vacio)', doctor.fechas_git() is None)
        r = doctor.sonda_deuda()
        caso('deuda sin historial de git: dice que lo que nadie toca quedo SIN DATOS', 'SIN DATOS' in r['resumen'], r['resumen'][:200])
        doctor.git = lambda *a: None if a[:2] == ('config', 'core.hooksPath') else '.git'
        r = doctor.sonda_guardarrailes()
        fila = [f for f in r['tabla'][1] if f[0] == 'core.hooksPath configurado']
        caso('git anda pero la clave no existe: "sin configurar" es HALLAZGO', fila and fila[0][2] == 'HALLAZGO', str(fila))
        doctor.git = lambda *a: '.gitkeep\n' if a == ('ls-files',) else None
        r = doctor.sonda_andamiaje()
        caso('un .gitkeep cuya carpeta git no pudo listar: SIN DATOS, no "carpeta vacia"',
             r['tabla'] and r['tabla'][1][0][3] == 'SIN DATOS', str(r.get('tabla')))

        tmp = tempfile.mkdtemp(prefix='probar-doctor-')
        os.makedirs(os.path.join(tmp, '.githooks'))
        guardas = ['check_mirror', 'check_pair', 'check_control_chars', 'check_skills_spec']
        cuerpo = '#!/usr/bin/env bash\n'
        for g in guardas[:3]:
            cuerpo += '%s() {\n  return 0\n}\n' % g
        cuerpo += 'function %s {\n  return 0\n}\n' % guardas[3]      # definida con "function", sin ()
        cuerpo += '%s || FALLO=1\n' % guardas[1]
        cuerpo += 'if ! %s; then FALLO=1; fi\n' % guardas[2]
        cuerpo += 'if ! %s; then FALLO=1; fi\n' % guardas[3]        # llamada dentro de un if
        cuerpo += '# check_mirror ya no se llama: quedo solo nombrado en este comentario\n'
        with open(os.path.join(tmp, '.githooks', 'pre-commit'), 'w', encoding='utf-8', newline='\n') as h:
            h.write(cuerpo)
        doctor.ROOT = tmp.replace('\\', '/')
        doctor.git = lambda *a: '.githooks' if a[:2] == ('config', 'core.hooksPath') else ''
        r = doctor.sonda_guardarrailes()
        fila = [f for f in r['tabla'][1] if f[0] == 'Guarda check_mirror']
        caso('una guarda definida pero que nadie llama (sólo nombrada en un comentario): HALLAZGO',
             fila and fila[0][2] == 'HALLAZGO', str(fila))
        otras = [f for f in r['tabla'][1] if f[0].startswith('Guarda ') and f[0] != 'Guarda check_mirror']
        caso('las guardas definidas y llamadas: OK', otras and all(f[2] == 'OK' for f in otras), str(otras))
        for modo, esperado in (('100644', 'HALLAZGO'), ('100755', 'OK')):
            doctor.git = lambda *a, m=modo: ('.githooks' if a[:2] == ('config', 'core.hooksPath') else
                                             ('%s abc 0\t.githooks/pre-commit\n' % m if a[:2] == ('ls-files', '-s') else ''))
            fila = [f for f in doctor.sonda_guardarrailes()['tabla'][1] if f[0].startswith('Hook ejecutable')]
            caso('hook con modo %s en git: %s (Linux y macOS ignoran un hook sin permiso de ejecucion)' % (modo, esperado),
                 fila and fila[0][2] == esperado, str(fila))
        shutil.rmtree(tmp, ignore_errors=True)
    finally:
        doctor.git, doctor.ROOT = git_real, raiz_real

    argv = sys.argv
    try:
        sys.argv = ['doctor.py', '--help']
        rc = doctor.main()
        sys.argv = ['doctor.py', '--solo', 'espejos', 'conteos']
        rc2 = doctor.main()
    finally:
        sys.argv = argv
    caso('un argumento que no conoce (--help): sale 2 sin correr ni escribir nada', rc == 2, str(rc))
    caso('un argumento suelto (--solo espejos conteos, separado con espacio): sale 2', rc2 == 2, str(rc2))

    medidas = doctor.medidas_de([{'id': 'x', 'titulo': 'X', 'estado': 'HALLAZGO', 'resumen': '',
                                  'tabla': (['Que', 'Estado'], [['roto.md', 'HALLAZGO'], ['sano.md', 'OK']])}], '2026-01-01')
    caso('las medidas que guarda el Doctor llevan la huella de cada hallazgo (para comparar hallazgo por hallazgo)',
         medidas['sondas'][0].get('claves') == ['roto.md'], str(medidas))

    raiz_vieja = (doctor.ROOT, doctor.SRC_SKILLS, doctor.git)
    tmp2 = tempfile.mkdtemp(prefix='probar-doctor-espejos-')
    try:
        for base in ('cerebro-digital/configuracion-ia/skills', '.agents/skills', '.claude/skills'):
            for rel, texto in (('una/SKILL.md', 'una\n'), ('una/references/guia.md', 'guia\n')):
                p = os.path.join(tmp2, base, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, 'w', encoding='utf-8', newline='\n') as h:
                    h.write(texto)
        with open(os.path.join(tmp2, '.claude/skills/una/references/guia.md'), 'a', encoding='utf-8') as h:
            h.write('una linea que solo esta en el espejo\n')
        doctor.ROOT = tmp2.replace('\\', '/')
        doctor.SRC_SKILLS = doctor.ROOT + '/cerebro-digital/configuracion-ia/skills'
        r = doctor.sonda_espejos()
        caso('espejos: un archivo de references/ distinto en el espejo es HALLAZGO (no solo el SKILL.md)',
             r['estado'] == 'HALLAZGO' and any('una' in f[2] for f in r['tabla'][1] if f[0] == '.claude/skills'), str(r.get('tabla')))
        doctor.git = lambda *a: ('.githooks' if a[:2] == ('config', 'core.hooksPath') else
                                 ('100755 abc 0\t.githooks/pre-commit\n' if a == ('ls-files', '-s', '--', '.githooks/pre-commit') else
                                  ('100644 abc 0\tbin/sync-skills.sh\n100755 abc 0\tbin/lote.sh\n' if a[:2] == ('ls-files', '-s') else '')))
        os.makedirs(os.path.join(tmp2, '.githooks'), exist_ok=True)
        with open(os.path.join(tmp2, '.githooks', 'pre-commit'), 'w', encoding='utf-8', newline='\n') as h:
            h.write('#!/usr/bin/env bash\n')
        r = doctor.sonda_guardarrailes()
        fila = [f for f in r['tabla'][1] if f[0].startswith('Scripts .sh')]
        caso('un .sh sin permiso de ejecucion en git: HALLAZGO y lo nombra', fila and fila[0][2] == 'HALLAZGO'
             and 'sync-skills.sh' in fila[0][1] and 'lote.sh' not in fila[0][1], str(fila))
    finally:
        doctor.ROOT, doctor.SRC_SKILLS, doctor.git = raiz_vieja
        shutil.rmtree(tmp2, ignore_errors=True)

    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    try:
        sys.exit(main())
    except Exception as e:
        print('FALLA -- la prueba exploto: %s: %s' % (type(e).__name__, e))
        sys.exit(1)
