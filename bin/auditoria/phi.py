"""Datos personales (PHI) en el texto de una tarjeta, para auditar-tarea y auditar-historia; auditar-diff usa el mismo
reconocimiento de emails (cada script con su severidad).

Lo INEQUIVOCO frena (HALLAZGO): un email de un dominio real o un CUIT/CUIL de persona (prefijo 20, 23, 24 o 27) con su
digito verificador valido, escrito con guiones (sin guiones puede ser una fecha u otro numero: avisa). Lo AMBIGUO avisa (AVISO), porque la heuristica no distingue un dato
de una persona de otra cosa: un CUIT de empresa o con el verificador mal, un DNI con puntos, un numero de 7 u 8 cifras, un
telefono, un email de un dominio de ejemplo. No es un email una version de paquete (react@18.3.1) ni el usuario de una
URL o de un remoto de git (git@github.com:org/x.git, https://org@dev.azure.com/...). Lo que la heuristica no ve
(nombres, direcciones, diagnosticos) lo lee el auditor.
"""

import re

from . import texto

# El dominio termina en letras (no es una version) y lo que sigue no es parte de una URL ni de un remoto.
_EMAIL = re.compile(r'(?<![\w.+\-/@])([\w.+\-]+)@((?:[\w\-]+\.)+[A-Za-z]{2,})(?![\w\-/@]|:[\w~/]|\.[\w\-])')
# logo@2x.png o foo@next.js no son emails: el "dominio" termina en una extension de archivo
_EXTENSION = re.compile(r'\.(png|jpe?g|gif|svg|webp|ico|bmp|js|mjs|cjs|ts|tsx|jsx|css|scss|less|map|json|ya?ml|xml|txt|md|html?|py|java|kt|cs)$', re.I)
_CUIT = re.compile(r'(?<![\w\-.])(\d{2})-?(\d{8})-?(\d)(?![\w\-]|\.\d)')   # un punto final de oracion no lo corta
_AMBIGUOS = [
    ('un DNI con puntos', re.compile(r'(?<![\w.])\d{1,2}\.\d{3}\.\d{3}(?![\w]|\.\d)')),
    ('un numero de 7 u 8 cifras (documento?)', re.compile(r'(?<![\w#/.\-:])\d{7,8}(?![\w/.\-])')),
    ('un telefono', re.compile(r'(?<![\w\-])(?:\+?54[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-])?'
                               r'(?:15[\s\-]?)?\d{4}-\d{4}(?![\w\-])')),
]


def es_de_ejemplo(dominio):
    """Dominios reservados para ejemplos (RFC 2606/6761) y el que usa el template."""
    d = dominio.lower()
    return (d in ('example.com', 'example.net', 'example.org', 'ejemplo.com', 'localhost')
            or d.endswith(('.example.com', '.example.net', '.example.org', '.example', '.test', '.invalid', '.localhost')))


def emails(fragmento):
    """[(email, real)] del texto (incluidos los de un mailto:), sin repetir."""
    res = []
    for m in _EMAIL.finditer(fragmento or ''):
        # .py y .md son tambien paises: solo es una extension si el "dominio" tiene un unico punto (2x.png, next.js)
        if m.group(2).count('.') == 1 and _EXTENSION.search(m.group(2)):
            continue
        e = m.group(0)
        if e not in [x for x, _ in res]:
            res.append((e, not es_de_ejemplo(m.group(2))))
    return res


def cuit_valido(prefijo, numero, verificador):
    digitos = [int(c) for c in prefijo + numero]
    s = sum(d * w for d, w in zip(digitos, (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)))
    dv = 11 - s % 11
    dv = 0 if dv == 11 else (9 if dv == 10 else dv)
    return dv == int(verificador)


def _unicos(xs):
    res = []
    for x in xs:
        if x not in res:
            res.append(x)
    return res


def revisar(rep, chequeo, fragmento, donde=''):
    """Agrega al reporte lo que encuentra; devuelve cuantos hallazgos y avisos dejo. `donde` dice que se miro."""
    plano = texto.texto_plano(fragmento or '')
    todos = emails(plano + '\n' + (fragmento or ''))
    reales = [e for e, real in todos if real]
    de_ejemplo = [e for e, real in todos if not real]
    personas, otros_cuit = [], []
    for m in _CUIT.finditer(plano):
        p, n, v = m.groups()
        # con guiones y verificador valido es un CUIT/CUIL de persona; sin guiones puede ser una fecha u otro numero
        (personas if '-' in m.group(0) and p in ('20', '23', '24', '27') and cuit_valido(p, n, v)
         else otros_cuit).append(m.group(0))
    marcados = 0
    if reales:
        rep.hallazgo(chequeo, 'PHI: un email de un dominio real', ', '.join(reales[:5]) + ' -- va <persona> o un dominio de ejemplo (example.com)')
        marcados += 1
    if personas:
        rep.hallazgo(chequeo, 'PHI: un CUIT o CUIL de persona', ', '.join(_unicos(personas)[:5]) + ' -- va <documento>')
        marcados += 1
    if de_ejemplo:
        rep.aviso(chequeo, 'posible PHI: un email', ', '.join(de_ejemplo[:5]) + ' -- es de un dominio de ejemplo; revisar que no sea de alguien')
        marcados += 1
    if otros_cuit:
        rep.aviso(chequeo, 'posible PHI: un numero con forma de CUIT', ', '.join(_unicos(otros_cuit)[:5]) +
                  ' -- de empresa o con el verificador mal; si es de una persona, va <documento>')
        marcados += 1
    sin_cuit = _CUIT.sub(' ', plano)
    for nombre, rx in _AMBIGUOS:
        hall = _unicos(x for x in rx.findall(sin_cuit)
                       if not (nombre == 'un telefono' and re.match(r'^(19|20)\d\d-(19|20)\d\d$', x.strip())))
        if hall:
            rep.aviso(chequeo, 'posible PHI: %s' % nombre, ', '.join(hall[:5]) +
                      ' -- revisar; si es un dato real, va un marcador (<documento>, <telefono>)')
            marcados += 1
    if not marcados:
        rep.ok(chequeo, 'sin emails, CUIT ni numeros con forma de documento o telefono (heuristica)' + (' en ' + donde if donde else ''))
    return marcados
