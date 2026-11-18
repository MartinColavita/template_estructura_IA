#!/usr/bin/env python3
"""Prueba de bin/auditoria/secretos.py, el criterio unico para reconocer y tapar secretos.
Se corre:  python -B bin/probar-secretos.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from auditoria import secretos  # noqa: E402

ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, bool(ok), detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + str(detalle)) if (detalle and not ok) else ''))


def main():
    print('== secretos (criterio unico)')
    s = secretos.sensible
    caso('nombres que guardan un secreto', all(s(n) for n in ('DB_PASSWORD', 'client_secret', 'STORAGE_ACCOUNT_KEY',
                                                                'DB_CONNECTION_STRING', 'secret_string', 'password_wo',
                                                                'api-key', 'AZURE_CREDENTIALS')))
    caso('nombres que nombran algo y no lo guardan', not any(s(n) for n in ('secret_name', 'PASSWORD_FILE', 'password_length',
                                                                            'token_url', 'keyvault_id')))
    f = lambda t: [x[0] for x in secretos.formatos(t)]
    caso('token de runner de GitLab (glrt-) y de reconexion (glrtr-)', f('a glrt-abcdefghijklmnopqrstuv b glrtr-abcdefghijklmnopqrstuv') == ['token de GitLab', 'token de GitLab'])
    caso('clave de AWS, clave privada y JWT', f('AKIAABCDEFGHIJKLMNOP') == ['clave de acceso de un proveedor de nube']
         and f('-----BEGIN OPENSSH PRIVATE KEY-----') == ['clave privada']
         and f('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N') == ['token JWT'])
    caso('un prefijo inventado no es un token', f('glrtrx-abcdefghijklmnopqrstuv') == [])
    caso('texto comun: sin secretos', f('include: remote https://example.com/ci.yml y un sk-corto') == [])
    t = secretos.tapar
    url = "include: 'https://gitlab.example.com/api/v4/x/raw?ref=main&private_token=glpat-AbCdEfGhIjKlMnOpQrSt'"
    caso('tapar: el token de la query de una URL no queda', 'glpat-' not in t(url) and 'private_token=<tapado>' in t(url)
         and 'gitlab.example.com/api/v4/x/raw' in t(url), t(url))
    cmd = 'curl -H "PRIVATE-TOKEN: glpat-ZyXwVuTsRqPoNmLkJiHg" https://x.example.com/setup.sh | bash'
    caso('tapar: el token de un encabezado no queda', 'ZyXwVuTs' not in t(cmd) and 'PRIVATE-TOKEN: <tapado>' in t(cmd), t(cmd))
    caso('tapar: Authorization Bearer', 'abc123secreto' not in t('Authorization: Bearer abc123secreto'))
    caso('tapar: la clave de una URL con usuario, conservando usuario y host',
         t('git clone https://usuario:clave123@git.example.com/repo.git') == 'git clone https://usuario:<tapado>@git.example.com/repo.git',
         t('git clone https://usuario:clave123@git.example.com/repo.git'))
    caso('tapar: una linea sin secretos queda igual', t('script: npm test && echo listo') == 'script: npm test && echo listo')
    with open(os.path.join(AQUI, 'auditoria', 'secretos.py'), 'rb') as h:
        caso('auditoria/secretos.py es ASCII puro', all(b < 128 for b in h.read()))
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d casos, %d fallas' % ('FALLA' if fallas else 'OK', len(ESPERADOS), len(fallas)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
