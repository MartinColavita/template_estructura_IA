"""Las lineas que agrega un diff unificado de git: el lector que comparten atajos.py (--base) y auditar-diff.py.

Cada bloque @@ -a,b +c,d @@ anuncia cuantas lineas del archivo nuevo trae (d): mientras falten, nada es cabecera,
aunque una linea agregada empiece con "++ " (se ve como "+++ ..."). Fuera de un bloque solo hay cabeceras y lineas
borradas, y una borrada empieza con "-": un comentario SQL borrado ("--- ...") no se toma por cabecera. Antes,
auditar-diff tomaba esas lineas por el nombre de otro archivo. Las lineas de contexto cuentan para el numero de linea
del archivo nuevo; las borradas, no. Solo biblioteca estandar. ASCII puro.
"""

import re

_HUNK = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')


def lineas_agregadas(diff):
    """[(archivo, nro, texto)] de cada linea '+' del diff, con su numero en el archivo nuevo."""
    res, archivo, nro, nuevas = [], None, 0, 0
    # solo \n corta: splitlines() corta tambien en un salto de pagina o un U+2028 del contenido, el bloque se
    # descuenta de mas y las lineas que siguen se pierden (un secreto despues de un \f pasaba como OK)
    for l in diff.split('\n'):
        l = l[:-1] if l.endswith('\r') else l
        if nuevas > 0:   # adentro de un bloque: faltan lineas del archivo nuevo
            if l.startswith('+'):
                nuevas, nro = nuevas - 1, nro + 1
                if archivo is not None:
                    res.append((archivo, nro, l[1:]))
            elif not l.startswith(('-', '\\')):   # contexto ("\ No newline at end of file" no cuenta)
                nuevas, nro = nuevas - 1, nro + 1
            continue
        m = _HUNK.match(l)
        if m:
            nuevas = int(m.group(2)) if m.group(2) is not None else 1
            nro = int(m.group(1)) - (1 if nuevas else 0)
        elif l.startswith('+++ '):
            destino = l[4:].strip()
            archivo = None if destino == '/dev/null' else (destino[2:] if destino.startswith('b/') else destino)
    return res
