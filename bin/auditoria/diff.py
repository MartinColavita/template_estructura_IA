"""El lector de un diff unificado de git: el que comparten atajos.py (--base), auditar-diff.py y
clasificar-migraciones.py.

Cada bloque @@ -a,b +c,d @@ anuncia cuantas lineas del archivo viejo (b) y del nuevo (d) trae: mientras falten,
nada es cabecera, aunque una linea agregada empiece con "++ " (se ve como "+++ ...") o una borrada sea un comentario
SQL ("--- ..."). Antes, auditar-diff tomaba esas lineas por el nombre de otro archivo. Las lineas de contexto cuentan
para el numero de linea del archivo nuevo; las borradas, no. Solo biblioteca estandar. ASCII puro.
"""

import re

_HUNK = re.compile(r'^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


def sin_prefijo(ruta):
    r = (ruta or '').strip().strip('"')
    return r[2:] if r.startswith(('a/', 'b/')) else r


def ruta_de_cabecera(linea):
    """La ruta de 'diff --git a/X b/X' (las dos mitades iguales; si no, la de despues del ultimo ' b/')."""
    resto = linea[len('diff --git '):].strip().strip('"')
    k = (len(resto) - 5) // 2
    if resto.startswith('a/') and resto[2 + k:5 + k] == ' b/' and resto[2:2 + k] == resto[5 + k:]:
        return resto[2:2 + k]
    return sin_prefijo(resto.rsplit(' b/', 1)[-1]) if ' b/' in resto else sin_prefijo(resto)


def archivos(diff):
    """[{ruta, nueva, borrada, lineas: [(nro, texto)]}] de cada archivo del diff, en orden. lineas: las agregadas,
    con su numero en el archivo nuevo. Un archivo sin lineas agregadas (borrado, binario) tambien figura."""
    res, actual, desde = [], None, None
    viejas = nuevas = nro = 0
    # solo \n corta: splitlines() corta tambien en un salto de pagina o un U+2028 del contenido, el bloque se
    # descuenta de mas y las lineas que siguen se pierden (un secreto despues de un \f pasaba como OK)
    for l in diff.split('\n'):
        l = l[:-1] if l.endswith('\r') else l
        if viejas > 0 or nuevas > 0:   # adentro de un bloque
            if l.startswith('+'):
                nuevas, nro = nuevas - 1, nro + 1
                if actual is not None and not actual['borrada']:
                    actual['lineas'].append((nro, l[1:]))
            elif l.startswith('-'):
                viejas -= 1
            elif not l.startswith('\\'):   # contexto ("\ No newline at end of file" no cuenta)
                viejas, nuevas, nro = viejas - 1, nuevas - 1, nro + 1
            continue
        m = _HUNK.match(l)
        if m:
            viejas = int(m.group(1)) if m.group(1) is not None else 1
            nuevas = int(m.group(3)) if m.group(3) is not None else 1
            nro = int(m.group(2)) - (1 if nuevas else 0)
        elif l.startswith('diff --git '):
            actual = {'ruta': ruta_de_cabecera(l), 'nueva': False, 'borrada': False, 'lineas': [], 'mas': False}
            res.append(actual)
            desde = None
        elif l.startswith('new file mode') and actual is not None:
            actual['nueva'] = True
        elif l.startswith('deleted file mode') and actual is not None:
            actual['borrada'] = True
        elif l.startswith('--- '):
            desde = l[4:].strip()
        elif l.startswith('+++ '):
            destino = l[4:].strip()
            if actual is None or actual['mas']:   # un diff sin cabeceras 'diff --git'
                actual = {'ruta': '', 'nueva': False, 'borrada': False, 'lineas': [], 'mas': False}
                res.append(actual)
            actual['mas'] = True
            if destino == '/dev/null':
                actual['borrada'] = True
                actual['ruta'] = sin_prefijo(desde)
            else:
                actual['ruta'] = sin_prefijo(destino)
                if desde == '/dev/null':
                    actual['nueva'] = True
    return [a for a in res if a['ruta']]


def lineas_agregadas(diff):
    """[(archivo, nro, texto)] de cada linea '+' del diff, con su numero en el archivo nuevo."""
    return [(a['ruta'], nro, texto) for a in archivos(diff) for nro, texto in a['lineas']]
