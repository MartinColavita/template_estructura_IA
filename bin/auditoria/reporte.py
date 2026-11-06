"""Reporte comun de las auditorias mecanicas: niveles, salida y codigo de salida.

Niveles de cada renglon:
- HALLAZGO      algo que falta o sobra, contado contra un insumo. Bloquea (codigo 1).
- NO_AUDITABLE  el insumo de ese chequeo no esta o vino vacio. Bloquea (codigo 1): nunca
                se da por cumplido lo que no se pudo mirar.
- AVISO         senal para el auditor (el modelo) o para quien lee; no bloquea.
- OK            el chequeo corrio y paso; se lista para que se vea que se miro.

Codigo de salida: 2 si el insumo principal no se pudo leer (SIN DATOS), 1 si hay algun
HALLAZGO o NO_AUDITABLE, 0 si no. Igual que verificar-sello y probar-reglas.
"""

import io
import json
import sys

OK, HALLAZGOS, SIN_DATOS = 0, 1, 2
NIVELES = ('HALLAZGO', 'NO_AUDITABLE', 'AVISO', 'OK')


class Reporte(object):

    def __init__(self, herramienta, insumo):
        self.herramienta = herramienta
        self.insumo = insumo
        self.renglones = []          # (nivel, chequeo, detalle, evidencia)
        self.para_el_auditor = []    # chequeos que el script NO mira: los mira el modelo
        self.sin_datos = None        # motivo, si el insumo principal no se pudo leer
        self.datos = {}              # numeros utiles (tests, escenarios, largo...) para el json

    def _agregar(self, nivel, chequeo, detalle, evidencia=''):
        self.renglones.append((nivel, str(chequeo), detalle, evidencia))

    def hallazgo(self, chequeo, detalle, evidencia=''):
        self._agregar('HALLAZGO', chequeo, detalle, evidencia)

    def no_auditable(self, chequeo, detalle, evidencia=''):
        self._agregar('NO_AUDITABLE', chequeo, detalle, evidencia)

    def aviso(self, chequeo, detalle, evidencia=''):
        self._agregar('AVISO', chequeo, detalle, evidencia)

    def ok(self, chequeo, detalle, evidencia=''):
        self._agregar('OK', chequeo, detalle, evidencia)

    def falta_insumo(self, motivo):
        """El insumo principal no se pudo leer: SIN DATOS, y no se corre nada mas."""
        self.sin_datos = motivo

    def codigo(self):
        if self.sin_datos:
            return SIN_DATOS
        if any(n in ('HALLAZGO', 'NO_AUDITABLE') for n, _, _, _ in self.renglones):
            return HALLAZGOS
        return OK

    def veredicto(self):
        return {OK: 'SIN HALLAZGOS', HALLAZGOS: 'CON HALLAZGOS', SIN_DATOS: 'SIN DATOS'}[self.codigo()]

    def contar(self, nivel):
        return sum(1 for n, _, _, _ in self.renglones if n == nivel)

    def como_dict(self):
        return {
            'herramienta': self.herramienta,
            'insumo': self.insumo,
            'veredicto': self.veredicto(),
            'codigo': self.codigo(),
            'sin_datos': self.sin_datos,
            'datos': self.datos,
            'renglones': [{'nivel': n, 'chequeo': c, 'detalle': d, 'evidencia': e}
                          for n, c, d, e in self.renglones],
            'para_el_auditor': self.para_el_auditor,
        }

    def markdown(self):
        o = ['## %s - %s' % (self.herramienta, self.insumo), '']
        if self.sin_datos:
            o += ['**SIN DATOS** - %s' % self.sin_datos, '']
            return '\n'.join(o)
        o.append('**Veredicto mecanico:** %s (%d hallazgos, %d no auditables, %d avisos)'
                 % (self.veredicto(), self.contar('HALLAZGO'), self.contar('NO_AUDITABLE'),
                    self.contar('AVISO')))
        if self.datos:
            o.append('')
            o.append('Datos: ' + ' - '.join('%s: %s' % (k, v) for k, v in self.datos.items()))
        for nivel in NIVELES:
            filas = [r for r in self.renglones if r[0] == nivel]
            if not filas:
                continue
            o += ['', '### %s (%d)' % (nivel, len(filas)), '']
            for _, c, d, e in filas:
                o.append('- [%s] %s%s' % (c, d, (' -- ' + e) if e else ''))
        if self.para_el_auditor:
            o += ['', '### Lo que este script NO mira (lo mira el auditor, con criterio)', '']
            o += ['- %s' % x for x in self.para_el_auditor]
        o.append('')
        return '\n'.join(o)


def emitir(reporte, como_json=False, salida=None):
    """Imprime el reporte (y lo guarda si se pidio). Devuelve el codigo de salida."""
    texto = (json.dumps(reporte.como_dict(), ensure_ascii=False, indent=2) if como_json
             else reporte.markdown())
    if salida:
        with io.open(salida, 'w', encoding='utf-8', newline='\n') as f:
            f.write(texto + ('\n' if not texto.endswith('\n') else ''))
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    print(texto)
    return reporte.codigo()
