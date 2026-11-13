#!/usr/bin/env python3
"""Prueba de bin/arrancar-proyecto.py sobre una COPIA temporal del template (sin archify ni espejos, para que sea rapida)
y un proyecto existente de mentira. Necesita git.
Se corre:  python -B bin/probar-arrancar-proyecto.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ESPERADOS = []
SALTEADOS = []   # lo que no corrio se dice en la ultima linea: no es OK


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def escribir(raiz, rel, texto):
    p = os.path.join(raiz, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)


def probar_firma(tmp, plantilla):
    """La firma de DEC-005 sobre copias minimas (instanciar.py y decisiones.md): sin la marca no se firma nada."""
    def mini(nombre):
        raiz = os.path.join(tmp, nombre)
        escribir(raiz, 'cerebro-digital/modulo-ejemplo/arquitectura/decisiones.md', open(plantilla, encoding='utf-8').read())
        os.makedirs(os.path.join(raiz, 'bin'), exist_ok=True)
        shutil.copy(os.path.join(AQUI, 'instanciar.py'), os.path.join(raiz, 'bin', 'instanciar.py'))
        return raiz

    def instanciar(raiz, *extra, env=None):
        return subprocess.run([sys.executable, '-I', os.path.join(raiz, 'bin', 'instanciar.py'), '--proyecto', 'X', '--producto', 'Y',
                               '--organizacion', 'Z', '--modulo', 'm', '--tablero', 'local', '--sin-espejos'] + list(extra),
                              capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, cwd=tmp)

    def dec(raiz):
        return open(os.path.join(raiz, 'cerebro-digital', 'm', 'arquitectura', 'decisiones.md'), encoding='utf-8').read()

    t = open(plantilla, encoding='utf-8').read()
    caso('el template trae DEC-005 sin firmar', 'Sin firmar' in t and 'Confirmado para el modo solo' not in t)
    sin = mini('sin-marca')
    r = instanciar(sin, '--modo', 'solo', '--autor', 'ana')
    caso('modo solo SIN --desatendido: DEC-005 sigue sin firmar y lo dice', r.returncode == 0 and 'Sin firmar' in dec(sin)
         and 'Confirmado para el modo solo' not in dec(sin) and 'sin firmar' in r.stdout, (r.stdout + r.stderr)[-300:])
    escribir(sin, 'cerebro-digital/m/nota.md', '---\nlast_updated: 2020-01-01\n---\n# nota\n')
    r = instanciar(sin, '--modo', 'solo', '--desatendido', '--autor', 'ana')
    caso('una segunda corrida con --desatendido la firma, con el nombre y el pie de la decision',
         r.returncode == 0 and 'firmado por ana' in dec(sin) and '@ana — firmada para el modo solo' in dec(sin), (r.stdout + r.stderr)[-300:])
    caso('esa segunda corrida no vuelve a fechar los .md del proyecto',
         'last_updated: 2020-01-01' in open(os.path.join(sin, 'cerebro-digital', 'm', 'nota.md'), encoding='utf-8').read())
    roto = mini('roto')
    p = os.path.join(roto, 'cerebro-digital', 'modulo-ejemplo', 'arquitectura', 'decisiones.md')
    escribir(roto, 'cerebro-digital/modulo-ejemplo/arquitectura/decisiones.md', open(p, encoding='utf-8').read().replace('Sin firmar', 'Sin firma'))
    r = instanciar(roto, '--modo', 'solo', '--desatendido', '--autor', 'ana')
    caso('sin la marca de DEC-005 donde firmar: sale 1 antes de tocar nada (el modulo no se renombra)',
         r.returncode == 1 and os.path.isdir(os.path.join(roto, 'cerebro-digital', 'modulo-ejemplo')), (r.stdout + r.stderr)[-300:])
    eq = mini('equipo')
    instanciar(eq, '--modo', 'equipo', '--autor', 'ana')
    r = instanciar(eq, '--modo', 'solo', '--desatendido', '--autor', 'ana')
    caso('proyecto que quedo en modo equipo (DEC-006): --desatendido sale 1 y no firma', r.returncode == 1 and 'Confirmado para el modo solo' not in dec(eq), (r.stdout + r.stderr)[-300:])
    vacio = os.path.join(tmp, 'gitconfig-vacio')
    escribir(tmp, 'gitconfig-vacio', '')
    env = dict(os.environ, GIT_CONFIG_GLOBAL=vacio, GIT_CONFIG_NOSYSTEM='1')
    r = instanciar(mini('sin-autor'), '--modo', 'solo', '--desatendido', '--dry-run', env=env)
    caso('--desatendido sin un nombre que firme: sale 1', r.returncode == 1 and 'autor' in r.stdout, (r.stdout + r.stderr)[-300:])


def main():
    print('== arrancar-proyecto')
    if shutil.which('git') is None:
        print('SIN DATOS -- no hay git en el PATH.')
        return 2
    tmp = tempfile.mkdtemp(prefix='probar-arrancar-')
    copia = os.path.join(tmp, 'nucleo')
    shutil.copytree(RAIZ, copia, ignore=shutil.ignore_patterns('.git', 'archify', 'borrador', 'salida', '__pycache__', 'INFORME-ESQUELETO.html'))
    app = os.path.join(tmp, 'mi-app')
    escribir(app, 'CLAUDE.md', '# mi-app\n\n```bash\nnpm test\n```\n')
    escribir(app, 'src/server.js', "const app = require('express')();\napp.get('/salud', (q, r) => r.send('ok'));\n")
    base = [sys.executable, '-I', os.path.join(copia, 'bin', 'arrancar-proyecto.py'), '--proyecto', 'Gestion de Reservas', '--producto', 'ReservaWeb',
            '--organizacion', 'Acme', '--modulo', 'reservas', '--modo', 'solo', '--desatendido', '--autor', 'martin', '--existente', app, '--como', 'back', '--importar-reglas', '--sin-informe']
    plantilla = os.path.join(copia, 'cerebro-digital', 'modulo-ejemplo', 'arquitectura', 'decisiones.md')
    if os.path.isfile(plantilla):
        probar_firma(tmp, plantilla)
    else:
        SALTEADOS.append('la firma de DEC-005 (el nucleo ya esta instanciado: no hay template que firmar)')
        print('  SALTEADO %s' % SALTEADOS[-1])
    r = subprocess.run(base + ['--dry-run'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    caso('dry-run termina en 0 y no instancia', r.returncode == 0 and os.path.isdir(os.path.join(copia, 'cerebro-digital', 'modulo-ejemplo')), (r.stdout + r.stderr)[-400:])
    r = subprocess.run(base, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    caso('corrida real termina en 0', r.returncode == 0, out[-600:])
    caso('instancio el modulo y el modo (DEC-006)', os.path.isdir(os.path.join(copia, 'cerebro-digital', 'reservas')) and 'modo solo' in open(os.path.join(copia, 'cerebro-digital', 'reservas', 'arquitectura', 'decisiones.md'), encoding='utf-8').read())
    dec_reservas = os.path.join(copia, 'cerebro-digital', 'reservas', 'arquitectura', 'decisiones.md')
    if os.path.isfile(plantilla) or os.path.isfile(dec_reservas):
        dec = open(dec_reservas, encoding='utf-8').read()
        caso('con --desatendido, arrancar deja DEC-005 firmada por quien arranca', 'Confirmado para el modo solo (' in dec and 'firmado por martin' in dec and 'Sin firmar' not in dec)
    caso('hizo git init en develop', subprocess.run(['git', '-C', copia, 'branch', '--show-current'], capture_output=True, text=True).stdout.strip() == 'develop')
    caso('dejo el hook activo (instalar)', subprocess.run(['git', '-C', copia, 'config', '--get', 'core.hooksPath'], capture_output=True, text=True).stdout.strip() == '.githooks')
    caso('enchufo el proyecto en back/ y dejo los informes', os.path.isdir(os.path.join(copia, 'back', 'mi-app')) and any(d.endswith('-mi-app') for d in os.listdir(os.path.join(copia, 'borrador', 'adopcion'))))
    caso('importo la linea de reglas en el CLAUDE.md del proyecto', 'AGENTS.md' in open(os.path.join(app, 'CLAUDE.md'), encoding='utf-8').read())
    caso('dice lo que sigue', 'LISTO' in out and 'modo documentar' in out)
    r = subprocess.run(base, capture_output=True, text=True, encoding='utf-8', errors='replace')
    caso('segunda corrida: idempotente (ya instanciado, ya repo, ya enchufado) y 0', r.returncode == 0 and 'ya estaba instanciado' in r.stdout and 'ya es un repositorio' in r.stdout and 'ya estaba enchufado' in r.stdout, (r.stdout + r.stderr)[-400:])
    r = subprocess.run([sys.executable, '-I', os.path.join(copia, 'bin', 'arrancar-proyecto.py'), '--proyecto', 'X', '--producto', 'Y', '--organizacion', 'Z', '--modulo', 'otro', '--modo', 'equipo', '--tablero', 'azure', '--sin-informe'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    r2 = subprocess.run([sys.executable, '-I', os.path.join(copia, 'bin', 'instanciar.py'), '--proyecto', 'X', '--producto', 'Y', '--organizacion', 'Z', '--modulo', 'otro', '--modo', 'equipo', '--desatendido', '--tablero', 'local', '--dry-run'],
                        capture_output=True, text=True, encoding='utf-8', errors='replace')
    caso('--desatendido en modo equipo: no firma nada y sale 1', r2.returncode == 1 and 'desatendido' in r2.stdout, (r2.stdout + r2.stderr)[-300:])
    caso('modo equipo con azure sin datos del tablero: FRENA (1) en instanciar', r.returncode == 1 and 'FRENA' in r.stdout, (r.stdout + r.stderr)[-300:])
    enlace = os.path.join(copia, 'back', 'mi-app')
    try:
        if os.name == 'nt':
            os.rmdir(enlace)
        else:
            os.unlink(enlace)
    except OSError:
        pass
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.%s' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS),
                                                         (' SALTEADOS: ' + '; '.join(SALTEADOS)) if SALTEADOS else ''))
    return 1 if fallas else 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        # el detalle de un caso que falla puede traer acentos o el signo de alerta: que se vea, no que tire la prueba
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
