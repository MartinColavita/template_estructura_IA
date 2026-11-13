#!/usr/bin/env python3
"""Prueba de doctor/comparar.py: el reporte de arreglos del Doctor (--comparar) y el panel «como venimos».
Compara dos corridas sonda por sonda; con la huella de cada fila, hallazgo por hallazgo (M-026).
Se corre:  python -B bin/probar-doctor-comparar.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'doctor'))
import comparar  # noqa: E402

ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def sonda(sid, estado, filas):
    """Una sonda como la guarda el Doctor: estado, cantidad de filas y la huella de cada una."""
    return {'id': sid, 'titulo': sid, 'estado': estado, 'resumen': '', 'filas': len(filas),
            'claves': comparar.claves_de({'tabla': (['que', 'detalle'], [[f, 'x'] for f in filas])})}


def veredicto(antes, ahora):
    cuenta, filas = comparar.comparar({'sondas': [antes]}, {'sondas': [ahora]})
    return filas[0]


def main():
    print('== doctor: comparar dos corridas')
    f = veredicto(sonda('wikilinks', 'HALLAZGO', ['a.md', 'b.md']), sonda('wikilinks', 'HALLAZGO', ['a.md', 'c.md']))
    caso('mismas filas, uno arreglado y otro nuevo: EMPEORO (antes decia "sin cambios")', f['veredicto'] == 'empeoro', str(f))
    caso('la fila dice cuantos se resolvieron y cuantos aparecieron', f.get('resueltos') == 1 and f.get('nuevos') == 1, str(f))

    f = veredicto(sonda('wikilinks', 'HALLAZGO', ['a.md', 'b.md', 'c.md']), sonda('wikilinks', 'HALLAZGO', ['a.md', 'd.md']))
    caso('menos filas pero un hallazgo nuevo: EMPEORO (antes decia "arreglado")', f['veredicto'] == 'empeoro', str(f))

    f = veredicto(sonda('wikilinks', 'HALLAZGO', ['a.md', 'b.md']), sonda('wikilinks', 'HALLAZGO', ['a.md']))
    caso('uno arreglado y ninguno nuevo: ARREGLADO', f['veredicto'] == 'arreglado' and f.get('resueltos') == 1, str(f))

    f = veredicto(sonda('wikilinks', 'HALLAZGO', ['a.md', 'b.md']), sonda('wikilinks', 'HALLAZGO', ['b.md', 'a.md']))
    caso('las mismas filas en otro orden: SIN CAMBIOS', f['veredicto'] == 'igual', str(f))

    f = veredicto(sonda('deuda', 'HALLAZGO', ['x.py', 'x.py']), sonda('deuda', 'HALLAZGO', ['x.py']))
    caso('dos filas con la misma clave y se arregla una: ARREGLADO (cuenta repetidas)', f['veredicto'] == 'arreglado', str(f))

    viejo = {'id': 'wikilinks', 'titulo': 'w', 'estado': 'HALLAZGO', 'resumen': '', 'filas': 3}
    f = veredicto(viejo, sonda('wikilinks', 'HALLAZGO', ['a.md']))
    caso('corrida vieja sin huellas: se compara por cantidad de filas, como antes', f['veredicto'] == 'arreglado', str(f))

    f = veredicto(sonda('espejos', 'HALLAZGO', ['a']), sonda('espejos', 'OK', []))
    caso('HALLAZGO -> OK: ARREGLADO', f['veredicto'] == 'arreglado', str(f))
    f = veredicto(sonda('espejos', 'OK', []), sonda('espejos', 'HALLAZGO', ['a']))
    caso('OK -> HALLAZGO: EMPEORO', f['veredicto'] == 'empeoro', str(f))

    cuenta, filas = comparar.comparar({'sondas': [sonda('tendencia', 'OK', [])]}, {'sondas': [sonda('tendencia', 'HALLAZGO', ['x'])]})
    caso('las sondas que miran el informe (tendencia) no se comparan', filas == [], str(filas))

    caso('la huella es la primera columna de cada fila', comparar.claves_de({'tabla': (['a', 'b'], [['uno', 1], ['dos', 2]])}) == ['dos', 'uno'])
    caso('sin tabla, sin huellas', comparar.claves_de({}) == [])
    con_estado = {'tabla': (['Skill', 'Tokens', 'Estado'], [['grande', '9000', 'HALLAZGO'], ['chica', '100', 'OK']])}
    caso('con columna Estado, solo las filas en HALLAZGO son hallazgos', comparar.claves_de(con_estado) == ['grande'], str(comparar.claves_de(con_estado)))

    def tam(filas):
        return {'id': 'tamano', 'titulo': 't', 'estado': 'HALLAZGO', 'resumen': '', 'filas': len(filas),
                'claves': comparar.claves_de({'tabla': (['Skill', 'Tokens', 'Estado'], filas)})}
    f = veredicto(tam([['a', '9000', 'HALLAZGO'], ['b', '9000', 'HALLAZGO']]),
                  tam([['a', '100', 'OK'], ['a2', '100', 'OK'], ['b', '9000', 'HALLAZGO']]))
    caso('se parte una skill grande: su fila pasa a OK y es ARREGLADO, no "sin cambios"', f['veredicto'] == 'arreglado', str(f))
    f = veredicto(tam([['a', '9000', 'HALLAZGO']]), tam([['a', '9000', 'HALLAZGO'], ['nueva', '50', 'OK']]))
    caso('se agrega una fila en OK: SIN CAMBIOS, no "empeoro"', f['veredicto'] == 'igual', str(f))

    caso('si la sonda trae su huella (la calculo antes de cortar la tabla), se usa esa',
         comparar.claves_de({'claves': ['x.md | a', 'x.md | b'], 'tabla': (['Archivo', 'Enlace'], [['x.md', 'a']])}) == ['x.md | a', 'x.md | b'])

    def wl(claves):
        return {'id': 'wikilinks', 'titulo': 'w', 'estado': 'HALLAZGO', 'resumen': '', 'filas': min(len(claves), 40), 'claves': claves}
    f = veredicto(wl(['x.md | a']), wl(['x.md | b']))
    caso('en el mismo archivo se arregla un enlace y se rompe otro: EMPEORO', f['veredicto'] == 'empeoro', str(f))
    viejos = ['f%02d.md | e' % i for i in range(45)]
    f = veredicto(wl(viejos), wl(viejos[1:]))
    caso('45 rotos con la tabla cortada en 40: arreglar uno es ARREGLADO (no entra el 41 como nuevo)', f['veredicto'] == 'arreglado', str(f))

    antes = {'sondas': [sonda('wikilinks', 'HALLAZGO', ['a.md', 'b.md'])]}
    ahora = {'sondas': [sonda('wikilinks', 'HALLAZGO', ['a.md', 'c.md'])]}
    cuenta, filas = comparar.comparar(antes, ahora)
    html = comparar.render(antes, ahora, cuenta, filas)
    caso('el reporte dice que se resolvio 1 y aparecio 1', 'Se resolvió 1' in html and 'apareció 1' in html, html[:200])

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
