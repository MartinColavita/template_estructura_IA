#!/usr/bin/env python3
"""Prueba de bin/generar-documentacion.py con un Cerebro de mentira y una app de mentira en una carpeta temporal.
Se corre:  python -B bin/probar-generar-documentacion.py   -> OK o FALLA, con el detalle de cada caso."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'generar-documentacion.py')
ESPERADOS = []


def caso(nombre, ok, detalle=''):
    ESPERADOS.append((nombre, ok, detalle))
    print('  %s %s%s' % ('ok  ' if ok else 'FALLA', nombre, ('  -- ' + detalle) if (detalle and not ok) else ''))


def escribir(raiz, rel, texto):
    p = os.path.join(raiz, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as h:
        h.write(texto)


def correr(*args):
    r = subprocess.run([sys.executable, '-I', SCRIPT] + list(args), capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


class Contador(HTMLParser):
    def __init__(self):
        super().__init__()
        self.abiertos, self.secciones, self.svgs, self.errores = [], 0, 0, 0
        self.vacios = {'meta', 'br', 'hr', 'img', 'input', 'link', 'path', 'line', 'rect', 'polygon', 'circle'}

    def handle_starttag(self, tag, attrs):
        if tag == 'section':
            self.secciones += 1
        if tag == 'svg':
            self.svgs += 1
        if tag not in self.vacios:
            self.abiertos.append(tag)

    def handle_endtag(self, tag):
        if tag in self.vacios:
            return
        if self.abiertos and self.abiertos[-1] == tag:
            self.abiertos.pop()
        else:
            self.errores += 1


def armar(raiz):
    escribir(raiz, 'cerebro-digital/contexto.md', '---\nid: contexto\ntipo: contexto\n---\n# Contexto\n\n## Propósito del sistema\n\nReservar salas sin pisarse.\n\n## Integraciones con sistemas externos\n\n| Sistema | Rol | Tipo |\n|---|---|---|\n| Calendario | agenda | consulta |\n')
    escribir(raiz, 'cerebro-digital/log.md', '---\nid: log\ntipo: log\n---\n# Historial\n\n## 2026-11-01 (Primera ficha)\n- Se cargo la ficha de reservas.\n- Validado por: martin\n')
    escribir(raiz, 'cerebro-digital/m/funcional/index.md', '---\nid: i\ntipo: indice\n---\n# i\n')
    escribir(raiz, 'cerebro-digital/m/funcional/plantilla-ficha-flujo.md', '---\nid: p\ntipo: flujo\n---\n# plantilla\n\n## Flujo\n\n1. <Paso 1>\n')
    escribir(raiz, 'cerebro-digital/m/funcional/crear-reserva.md', '---\nid: crear-reserva\ntipo: flujo\nestado: F-Verified\nmodulo: m\ntitle: "Crear una reserva"\nfuente_maqueta: "entregables/disenos/crear-reserva.png"\n---\n'
             '# Crear una reserva\n\n## Propósito\n\nQue una persona reserve una sala libre.\n\n## Glosario\n\n| Término | Definición |\n|---|---|\n| Sala | Espacio reservable |\n\n## Reglas de negocio\n\n### RN-MOD-001 — Sin solapamiento\n\nDos reservas no pueden pisarse en la misma sala.\n\n_Últ. modif.: 2026-11-01 — @martin — alta_\n\n'
             '## Flujo\n\n1. La persona elige la sala y el horario.\n2. El sistema valida que este libre.\n3. Confirma y recibe el comprobante.\n\n## Pantalla\n\n- **Maqueta vigente:** `entregables/disenos/crear-reserva.png`\n')
    escribir(raiz, 'cerebro-digital/m/funcional/cancelar-reserva.md', '---\nid: cancelar\ntipo: flujo\nestado: F-Draft\nmodulo: m\ntitle: "Cancelar una reserva"\nfuente_maqueta: ""\n---\n# Cancelar\n\n## Propósito\n\nLiberar la sala.\n\n## Flujo\n\n1. Abrir la reserva.\n2. Cancelar.\n')
    escribir(raiz, 'cerebro-digital/m/arquitectura/decisiones.md', '---\nid: d\ntipo: decisiones\n---\n# Decisiones\n\n## DEC-001 — El codigo vive afuera\n\n**Estado:** Confirmado\n\n## DEC-002 — Modulos\n\n**Estado:** ⚠ a confirmar\n')
    escribir(raiz, 'cerebro-digital/m/aplicacion/mapa.md', '---\nid: mapa\ntipo: aplicacion\n---\n# Mapa\n\n## Módulos de código\n\n| Módulo | Repo | Qué hace |\n|---|---|---|\n| reservas | back | crea reservas |\n')
    escribir(raiz, 'cerebro-digital/m/aplicacion/aprendizajes.md', '---\nid: ap\ntipo: aplicacion\n---\n# AP\n\n| # | Fecha | Tipo | Qué | Causa | Fuente | Qué cambió |\n|---|---|---|---|---|---|---|\n| AP-001 | 2026-11-01 | bug | fecha mal | zona horaria | #3 | test nuevo |\n')
    escribir(raiz, 'cerebro-digital/m/aplicacion/deuda.md', '---\nid: dt\ntipo: aplicacion\n---\n# DT\n\n## Abiertas\n\n| # | Qué | Dónde | Por qué | Riesgo | Cuándo | Fuente |\n|---|---|---|---|---|---|---|\n| DT-001 | sin indice | reservas | apuro | lento | sprint 2 | Doctor |\n')
    escribir(raiz, 'cerebro-digital/m/pendientes.md', '---\nid: pen\ntipo: pendientes\n---\n# Pendientes\n\n## Abiertas\n\n| # | Pregunta | Responsable | Origen |\n|---|---|---|---|\n| P-002 | ¿Se puede reservar fin de semana? | funcional | reunion |\n\n## Resueltas\n\n| # | Pregunta | Respuesta (resumen) | Dónde quedó | Fecha |\n|---|---|---|---|---|\n| P-001 | ¿Cuántas salas? | Tres por ahora | contexto | 2026-11-01 |\n')
    escribir(raiz, 'cerebro-digital/m/backlog/0003-crear-una-reserva.md', '---\nid: 3\ntipo: Historia\nestado: Closed\ntitulo: "Crear una reserva"\nactualizado: 2026-11-01\n---\n# #3\n')
    escribir(raiz, 'entregables/disenos/crear-reserva.png', 'png de mentira')
    app = os.path.join(raiz, 'app')
    escribir(app, 'src/reservas/api/ReservaResource.java', 'package x.reservas.api;\n@Path("/reservas")\npublic class R {\n  @GET\n  public void listar() {}\n}\n')
    escribir(app, 'db/migrations/V1.sql', 'CREATE TABLE reserva (id int, sala_id int, FOREIGN KEY (sala_id) REFERENCES sala(id));\nCREATE TABLE sala (id int);\n')
    return app


def main():
    print('== generar-documentacion')
    tmp = tempfile.mkdtemp(prefix='probar-doc-')
    app = armar(tmp)
    rc, out = correr('--tipo', 'manual', '--raiz', tmp, '--modulo', 'm', '--salida', os.path.join(tmp, 'out', 'guia.html'))
    guia = open(os.path.join(tmp, 'out', 'guia.html'), encoding='utf-8').read() if rc == 0 else ''
    caso('manual: se escribe (0)', rc == 0 and guia, out[:300])
    if guia:
        c = Contador(); c.feed(guia)
        caso('manual: HTML balanceado, con indice y 6 secciones (empezar + 2 flujos + glosario + faq + ayuda)', c.errores == 0 and c.secciones == 6 and guia.count('href="#') >= 6, 'secciones=%d errores=%d' % (c.secciones, c.errores))
        caso('manual: empezar usa los pasos de la primera ficha y los dibuja', 'Empezar en pocos pasos' in guia and 'elige la sala' in guia and c.svgs >= 3)
        caso('manual: la pantalla PNG citada en fuente_maqueta se embebe con ruta relativa', 'src="../entregables/disenos/crear-reserva.png"' in guia)
        caso('manual: ficha sin maqueta queda marcada <completar> (Stitch)', 'exportar de Stitch' in guia)
        caso('manual: reglas en criollo, glosario y FAQ de pendientes resueltas', 'Sin solapamiento' in guia and 'Espacio reservable' in guia and 'Tres por ahora' in guia)
        caso('manual: no toma la plantilla ni el index', 'plantilla' not in guia.lower().split('<main>')[1] if '<main>' in guia else False)
    rc, out = correr('--tipo', 'tecnica', '--raiz', tmp, '--modulo', 'm', '--app', app, '--salida', os.path.join(tmp, 'out', 'tecnica.html'))
    tec = open(os.path.join(tmp, 'out', 'tecnica.html'), encoding='utf-8').read() if rc == 0 else ''
    caso('tecnica: se escribe con radiografia (0)', rc == 0 and tec and 'sin radiografia' not in out, out[:300])
    if tec:
        c = Contador(); c.feed(tec)
        caso('tecnica: 14 secciones, HTML balanceado', c.secciones == 14 and c.errores == 0, 'secciones=%d errores=%d' % (c.secciones, c.errores))
        caso('tecnica: modulos, ER y API salen de la radiografia', 'aria-label="modulos"' in tec and 'aria-label="modelo de datos"' in tec and '/reservas' in tec and 'RESERVA' in tec.upper())
        caso('tecnica: catalogo de reglas, decisiones, mapa, AP, DT, pendientes', 'RN-MOD-001' in tec and 'DEC-002' in tec and 'crea reservas' in tec and 'AP-001' in tec and 'DT-001' in tec and 'fin de semana' in tec)
        caso('tecnica: bitacora con log.md y el tablero local', 'Primera ficha' in tec and '1 cerrados' in tec)
        caso('tecnica: cuenta lo que falta y lo marca', re.search(r'\d+ marca\(s\) <completar>', out) is not None and 'class="completar"' in tec)
    rc, out = correr('--tipo', 'manual', '--raiz', os.path.join(tmp, 'nada'))
    caso('sin Cerebro: SIN DATOS (2)', rc == 2)
    shutil.rmtree(tmp, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
