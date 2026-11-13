#!/usr/bin/env python3
"""La guarda de encoding del hook pre-commit y del CI: BOM UTF-8 y caracteres de control invisibles. SOLO LECTURA.

    python -I bin/verificar-staged.py [--repo <carpeta>]          (lo que esta en stage: lo que se va a commitear)
    python -I bin/verificar-staged.py [--repo <carpeta>] --todo   (todo lo versionado: para el CI)

Tres estados, nunca dos:  0 = OK   1 = HALLAZGO (BOM o caracter de control)   2 = SIN DATOS (no es un repo, o git
                          no pudo leer un archivo)

QUE MIRA. En los archivos de texto (por extension), el BLOB del indice -lo que se va a commitear, no el disco-: un BOM
UTF-8 al principio (el proyecto usa UTF-8 SIN BOM; excepcion declarada: .ps1, .psm1, .psd1, .bat y .cmd, que PowerShell
5.1 y cmd leen mal sin el) y los caracteres BEL, BS, VT y FF, que un \\a \\b \\f interpretado como escape mete en silencio.
Entran los agregados, copiados, modificados, renombrados y los que cambiaron de tipo. Un proceso de git para la lista y
otro para todos los contenidos, pedidos por su id de blob (no por nombre: un nombre con salto de linea no los desarma).

QUE NO MIRA. Submodulos (modo 160000) ni enlaces simbolicos (120000): no tienen contenido de texto propio. Solo
biblioteca estandar.
"""

import argparse
import subprocess
import sys

OK, HALLAZGO, SIN_DATOS = 0, 1, 2
TEXTO = ('.md', '.markdown', '.mdx', '.html', '.htm', '.css', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.json',
         '.yaml', '.yml', '.txt', '.csv', '.sh', '.bash', '.ps1', '.psm1', '.psd1', '.bat', '.cmd', '.py', '.sql',
         '.java', '.kt', '.cs', '.xml', '.svg', '.toml', '.ini', '.cfg', '.conf', '.properties')
NOMBRES = ('.gitignore', '.gitattributes', 'Dockerfile')
BOM_PERMITIDO = ('.ps1', '.psm1', '.psd1', '.bat', '.cmd')
CONTROL = (b'\x07', b'\x08', b'\x0b', b'\x0c')
SIN_CONTENIDO = ('160000', '120000')   # submodulo y enlace simbolico


def es_texto(ruta):
    nombre = ruta.rsplit('/', 1)[-1]
    return ruta.lower().endswith(TEXTO) or nombre in NOMBRES or ruta.startswith('.githooks/')


def git(repo, args, entrada=None):
    r = subprocess.run(['git', '-C', repo] + args, input=entrada, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def listar(repo, todo):
    """[(ruta, id_del_blob)] de lo que hay que mirar, o None si git no pudo."""
    res = []
    if todo:
        crudo = git(repo, ['ls-files', '-s', '-z'])
        if crudo is None:
            return None
        for entrada in crudo.split(b'\0'):
            if not entrada:
                continue
            cabeza, ruta = entrada.split(b'\t', 1)
            modo, blob, _ = cabeza.decode().split(' ')
            if modo not in SIN_CONTENIDO:
                res.append((ruta.decode('utf-8', 'replace'), blob))
        return res
    crudo = git(repo, ['diff', '--cached', '--raw', '-z', '--no-abbrev', '--diff-filter=ACMRT'])
    if crudo is None:
        return None
    partes = crudo.split(b'\0')
    i = 0
    while i < len(partes) and partes[i]:
        cabeza = partes[i].decode().lstrip(':').split(' ')   # modo_viejo modo_nuevo blob_viejo blob_nuevo estado
        modo, blob, estado = cabeza[1], cabeza[3], cabeza[4]
        if estado[0] in 'RC':          # renombre o copia: vienen la ruta vieja y la nueva
            ruta, i = partes[i + 2], i + 3
        else:
            ruta, i = partes[i + 1], i + 2
        if modo not in SIN_CONTENIDO:
            res.append((ruta.decode('utf-8', 'replace'), blob))
    return res


def contenidos(repo, blobs):
    """{id: bytes} en UN proceso (git cat-file --batch), pedidos por id de blob."""
    if not blobs:
        return {}
    datos = git(repo, ['cat-file', '--batch'], ''.join(b + '\n' for b in blobs).encode())
    if datos is None:
        return None
    res, i = {}, 0
    for b in blobs:
        fin = datos.index(b'\n', i)
        cabecera = datos[i:fin].split(b' ')
        i = fin + 1
        if len(cabecera) < 3 or cabecera[-1] == b'missing':
            continue
        n = int(cabecera[2])
        res[b] = datos[i:i + n]
        i += n + 1
    return res


def main():
    ap = argparse.ArgumentParser(description='BOM y caracteres de control en lo que se va a commitear (o en todo).')
    ap.add_argument('--repo', default='.')
    ap.add_argument('--todo', action='store_true', help='todo lo versionado, no solo lo que esta en stage (para el CI)')
    a = ap.parse_args()

    entradas = listar(a.repo, a.todo)
    if entradas is None:
        print('SIN DATOS -- git no pudo listar los archivos de %s (¿es un repositorio?)' % a.repo)
        return SIN_DATOS
    entradas = [(r, b) for r, b in entradas if es_texto(r)]
    if not entradas:
        print('OK -- ningun archivo de texto %s.' % ('versionado' if a.todo else 'en stage'))
        return OK
    blobs = contenidos(a.repo, sorted(set(b for _, b in entradas)))
    if blobs is None:
        print('SIN DATOS -- git no pudo leer el contenido de los archivos.')
        return SIN_DATOS

    boms, control, sin_leer = [], [], []
    for ruta, blob in entradas:
        datos = blobs.get(blob)
        if datos is None:
            sin_leer.append(ruta)
            continue
        if datos.startswith(b'\xef\xbb\xbf') and not ruta.lower().endswith(BOM_PERMITIDO):
            boms.append(ruta)
        if any(c in datos for c in CONTROL):
            control.append(ruta)

    if boms:
        print('HALLAZGO -- archivos con BOM UTF-8 (el proyecto usa UTF-8 SIN BOM):')
        print('\n'.join('  - ' + r for r in boms))
        print('  Sacalo y volve a commitear.')
    if control:
        print('HALLAZGO -- caracteres de control invisibles (BEL/BS/VT/FF) en:')
        print('\n'.join('  - ' + r for r in control))
        print('  Suelen venir de un \\a \\b \\f interpretado como escape. Para ubicarlos:  grep -n $\'[\\x07\\x08\\x0B\\x0C]\' <archivo>')
    if sin_leer:
        # nunca decir OK sobre algo que no se pudo mirar
        print('SIN DATOS -- no se pudo leer el contenido de: ' + ', '.join(sin_leer[:10]))
    if boms or control:
        return HALLAZGO
    if sin_leer:
        return SIN_DATOS
    print('OK -- %d archivo(s) de texto %s, sin BOM ni caracteres de control.' % (len(entradas), 'versionados' if a.todo else 'en stage'))
    return OK


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    try:
        sys.exit(main())
    except Exception as e:
        print('SIN DATOS -- error del script: %s: %s' % (type(e).__name__, e))
        sys.exit(SIN_DATOS)
