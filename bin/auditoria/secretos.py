"""Como se reconoce un secreto: UN solo criterio para todos los scripts.

Por que existe. Cuatro scripts tenian su propia lista (auditar-diff.py, auditar-iac.py, verificar-pipeline.py y
auditar-gitlab.py) y ya daban resultados distintos sobre lo mismo: un token de runner de GitLab en un .tf no se veia,
una STORAGE_ACCOUNT_KEY en las variables de un pipeline tampoco. Aca estan los formatos de token conocidos, los nombres
de clave que guardan un secreto, y como se tapa un valor antes de imprimir una linea.

Lo usan: auditar-diff.py, auditar-iac.py, verificar-pipeline.py y auditar-gitlab.py. Solo biblioteca estandar. ASCII.
Fuentes de los formatos: docs.gitlab.com/security/tokens/ (prefijos de GitLab), docs.github.com (ghp_, github_pat_),
docs.aws.amazon.com (AKIA), learn.microsoft.com (AccountKey=, firma de acceso compartido sig=).
"""

import re

TAPADO = '<tapado>'

# (nombre para el informe, expresion). Un formato conocido es secreto aunque la clave no lo diga.
FORMATOS = (
    ('clave privada', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA |ENCRYPTED )?PRIVATE KEY')),
    ('token JWT', re.compile(r'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}')),
    ('clave de acceso de un proveedor de nube', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('token de GitHub', re.compile(r'\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})')),
    ('token de GitLab', re.compile(r'\bgl(?:pat|oas|dt|rt|rtr|cbt|ptt|ft|imt|agent|wt|soat|ffct)-[A-Za-z0-9_-]{20,}')),
    ('token de un chat', re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}')),
    ('clave de API de un servicio de IA', re.compile(r'\bsk-[A-Za-z0-9_-]{32,}')),
    ('cadena de conexion con su clave', re.compile(r'AccountKey=[A-Za-z0-9+/]{40,}={0,2}')),
    ('firma de acceso compartido', re.compile(r'[?&]sig=[A-Za-z0-9%+/]{30,}')),
    ('URL con usuario y clave', re.compile(r'[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]{3,}@')),
)

# Un nombre es sensible si, sin separadores y en minusculas, TERMINA en una de estas palabras (secret_name, *_FILE o
# password_length nombran algo, no lo guardan).
SENSIBLES = ('password', 'passwd', 'pwd', 'secret', 'token', 'apikey', 'accesskey', 'secretkey', 'privatekey',
             'connectionstring', 'accountkey', 'sastoken', 'secretstring', 'passwordwo', 'secretvalue', 'clientsecret',
             'credentials', 'credential')

# Lo que hay que tapar en una linea antes de imprimirla, ademas de los formatos: el valor de un parametro o de un
# encabezado que lleva un token, y la clave de una URL con usuario.
_TAPAR = (
    re.compile(r'(?i)((?:private_token|access_token|token|apikey|api_key|key|sig|password)=)[^&\s"\'#]+'),
    re.compile(r'(?i)((?:PRIVATE-TOKEN|JOB-TOKEN|Authorization|X-Api-Key|X-Goog-Api-Key)\s*:\s*(?:Bearer\s+|Basic\s+|token\s+)?)[^\s"\']+'),
    re.compile(r'([a-z][a-z0-9+.-]*://[^/\s:@]+:)[^/\s@]+(@)'),
)


def sensible(nombre):
    """True si el nombre de una clave o de una variable dice que guarda un secreto."""
    return re.sub(r'[^a-z0-9]', '', str(nombre).lower()).endswith(SENSIBLES)


def formatos(texto):
    """[(nombre del formato, inicio, fin)] de cada secreto con formato conocido en el texto."""
    res = []
    for nombre, rx in FORMATOS:
        for m in rx.finditer(texto):
            res.append((nombre, m.start(), m.end()))
    return sorted(res, key=lambda x: x[1])


def tapar(texto):
    """El texto con todo valor de secreto reconocible reemplazado por <tapado>: para imprimir una linea sin filtrarlo."""
    t = str(texto)
    t = _TAPAR[2].sub(lambda m: m.group(1) + TAPADO + m.group(2), t)   # la URL conserva esquema, usuario y host
    t = _TAPAR[0].sub(lambda m: m.group(1) + TAPADO, t)
    t = _TAPAR[1].sub(lambda m: m.group(1) + TAPADO, t)
    for nombre, rx in FORMATOS:
        if nombre != 'URL con usuario y clave':
            t = rx.sub(TAPADO, t)
    return t
