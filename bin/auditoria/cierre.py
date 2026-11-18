"""Lo que, escrito en un commit o en un Merge Request, cambia una tarjeta POR AFUERA de sus GATEs.

Por que existe. "Fixes AB#123" en un mensaje de commit pasa la tarjeta de Azure Boards a su estado terminal al
mergear; "Closes #12" cierra el issue de GitLab al mergear; y una linea de una descripcion o de un comentario de
GitLab que empieza con /merge o /approve es una accion rapida que se ejecuta. Las tres saltean los GATEs del tablero
y el de despliegue (AGENTS.md). Enlazar sin cerrar es "AB#123" o "Related to #12".

Lo usan auditar-diff.py (los mensajes de commit de la rama) y auditar-gitlab.py (un texto antes de escribirlo en
GitLab), para que las dos digan lo mismo. Solo biblioteca estandar. ASCII puro.

Fuentes: docs.gitlab.com, "Managing issues" (closing patterns) y "GitLab quick actions"; learn.microsoft.com,
"Link GitHub commits... to Azure Boards" (Fixes AB#).
"""

import re

# Los verbos del patron de cierre de GitLab (que incluye los de Azure Boards y GitHub) en todas sus formas.
VERBOS = r'(?:clos(?:e|es|ed|ing)|fix(?:es|ed|ing)?|resolv(?:e|es|ed|ing)|implement(?:s|ed|ing)?)'
# A que puede apuntar: una tarjeta de Azure (AB#123), un issue del mismo proyecto o de otro (#12, grupo/proyecto#12)
# o la URL de un issue o de un work item.
REFERENCIA = r'(?:AB#\d+|[\w.\-/]*#\d+|https?://\S+?/(?:-/)?(?:issues|work_items)/\d+)'
# "Closes issue #12" y "Fixes issues #12 and #13" tambien cierran: la palabra issue puede ir en el medio.
CIERRE = re.compile(r'(?i)\b' + VERBOS + r'\b:?\s+(?:issues?\s+)?' + REFERENCIA)
# Una accion rapida: la linea empieza con / y una palabra en minusculas seguida de espacio o fin de linea
# ("/ruta/a/un/archivo" no lo es: sigue una barra).
ACCION_RAPIDA = re.compile(r'^\s*/[a-z][a-z_]*(?=\s|$)')


def cierres(texto):
    """[(numero de linea, lo que se encontro)]: cada palabra de cierre seguida de una referencia."""
    return [(n, m.group(0)) for n, linea in enumerate(texto.split('\n'), 1) for m in CIERRE.finditer(linea)]


def acciones_rapidas(texto):
    """[(numero de linea, la accion)]: cada linea que GitLab ejecutaria como accion rapida."""
    res = []
    for n, linea in enumerate(texto.split('\n'), 1):
        m = ACCION_RAPIDA.match(linea)
        if m:
            res.append((n, m.group(0).strip()))
    return res
