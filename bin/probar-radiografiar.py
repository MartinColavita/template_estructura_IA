#!/usr/bin/env python3
"""Prueba de bin/radiografiar-codigo.py sobre una aplicacion de mentira (Java JAX-RS + Spring, Express,
Flask, React, SQL, YAML) en una carpeta temporal.
Se corre:  python -B bin/probar-radiografiar.py   -> OK o FALLA, con el detalle de cada caso."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(AQUI, 'radiografiar-codigo.py')
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


def armar(app):
    escribir(app, 'src/main/java/com/acme/reservas/api/ReservaResource.java', '''package com.acme.reservas.api;
import com.acme.salas.application.SalaService;
import com.acme.salas.infra.SalaRepositoryImpl;
import javax.ws.rs.*;

@Path("/reservas")
public class ReservaResource {
    static final int MAX_DIAS = 30;

    @GET
    @RolesAllowed("OPERADOR")
    public List<Reserva> listar() { return servicio.listar(); }

    @POST
    @Path("/{id}/confirmar")
    public Reserva confirmar(@PathParam("id") Long id, int dias) {
        if (dias > MAX_DIAS) {
            throw new ReservaInvalidaException("La reserva no puede superar 30 dias");
        }
        reserva.setEstado(EstadoReserva.CONFIRMADA);
        return reserva;
    }

    private BigDecimal calcularImporte(Reserva r) { return BigDecimal.ZERO; }
}
''')
    escribir(app, 'src/main/java/com/acme/reservas/domain/Reserva.java', '''package com.acme.reservas.domain;
import javax.persistence.*;
import javax.validation.constraints.NotNull;

@Entity
@Table(name = "reserva")
public class Reserva {
    @NotNull
    private Long id;
    @ManyToOne
    private Sala sala;
    private EstadoReserva estado;
}
''')
    escribir(app, 'src/main/java/com/acme/reservas/domain/EstadoReserva.java', 'package com.acme.reservas.domain;\npublic enum EstadoReserva { PENDIENTE, CONFIRMADA, CANCELADA }\n')
    escribir(app, 'src/main/java/com/acme/salas/application/SalaService.java', '''package com.acme.salas.application;
import org.springframework.web.client.RestTemplate;
import org.springframework.scheduling.annotation.Scheduled;

public class SalaService {
    private final RestTemplate rest = new RestTemplate();

    @Scheduled(cron = "0 0 * * * *")
    public void sincronizar() { rest.getForObject(url, String.class); }
}
''')
    escribir(app, 'src/main/resources/application.yml', '''proveedor:
  url: https://api.proveedor.example.org/v1
  password: supersecreta
datasource:
  url: jdbc:postgresql://db:5432/reservas
''')
    escribir(app, 'db/migrations/V1__init.sql', 'CREATE TABLE reserva (id bigint primary key, sala_id bigint, FOREIGN KEY (sala_id) REFERENCES sala(id));\nCREATE TABLE sala (id bigint primary key);\n')
    escribir(app, 'front/src/routes.tsx', 'import { Route } from "react-router-dom";\nimport ReservasPage from "./pages/ReservasPage";\nexport const rutas = (<Route path="/reservas" element={<ReservasPage/>}/>);\n')
    escribir(app, 'front/src/pages/ReservasPage.tsx', 'import axios from "axios";\nexport default function ReservasPage() { return axios.get("/api/reservas"); }\n')
    escribir(app, 'front/src/server.js', "const app = require('express')();\napp.get('/health', (req, res) => res.send('ok'));\n")
    escribir(app, 'api/openapi.yaml', 'openapi: 3.0.0\npaths:\n  /reservas:\n    get: {}\n  /salas:\n    get: {}\n')
    escribir(app, 'okf/modelo.md', '# Modelo\n\n```sql\nCREATE TABLE meeting (id int primary key);\nCREATE TABLE segmento (id int, meeting_id int, FOREIGN KEY (meeting_id) REFERENCES meeting(id));\n```\n\n```mermaid\nstateDiagram-v2\n  [*] --> Grabando\n  Grabando --> Transcribiendo\n  Transcribiendo --> Listo\n```\n')
    escribir(app, 'tools/data.py', 'ADRS = [dict(id=1, estado="Propuesta"), dict(id=2, estado="Aceptada")]\n')
    escribir(app, 'crates/app/src/main.rs', '#[tauri::command]\nfn grabar_reunion(x: i32) -> i32 { x }\n')
    escribir(app, 'app.py', '''from flask import Flask
app = Flask(__name__)

@app.route('/salud', methods=['GET'])
def salud():
    if importe < 0:
        raise ValueError("Importe negativo")
    return "ok"
''')


def main():
    print('== radiografiar-codigo')
    app = tempfile.mkdtemp(prefix='probar-radiografia-')
    armar(app)
    rc, out = correr(app, '--json')
    try:
        d = json.loads(out)
    except ValueError:
        d = None
    caso('corre y devuelve JSON (0)', rc == 0 and d is not None, out[:300])
    if d:
        rutas = set((x['metodo'], x['ruta']) for x in d['api'])
        caso('endpoints JAX-RS con el @Path de la clase y del metodo', ('GET', '/reservas') in rutas and ('POST', '/reservas/{id}/confirmar') in rutas, str(sorted(rutas)))
        caso('endpoints Express y Flask', ('GET', '/health') in rutas and ('GET', '/salud') in rutas, str(sorted(rutas)))
        caso('rutas del contrato openapi', sorted(x['ruta'] for x in d['contrato']) == ['/reservas', '/salas'])
        mo = d['modelo']
        caso('entidad JPA con su tabla', any(e['valor'] == 'Reserva' for e in mo['entidades']) and any(t['valor'] == 'reserva' and t['origen'] == 'orm' for t in mo['tablas']))
        caso('tablas del DDL y su FOREIGN KEY', sorted(t['valor'] for t in mo['tablas'] if t['origen'] == 'ddl') == ['meeting', 'reserva', 'sala', 'segmento'] and any(r['tipo'] == 'FOREIGN KEY' for r in mo['relaciones']))
        caso('enum y campo de estado', any(e['valor'] == 'EstadoReserva' for e in mo['enums']) and any(c['valor'] == 'estado' for c in mo['campos_estado']))
        caso('relacion ManyToOne', any(r['tipo'] == 'ManyToOne' for r in mo['relaciones']))
        caso('ruta y componente del front', any(p['valor'] == '/reservas' for p in d['pantallas']) and any(p['valor'] == 'ReservasPage' for p in d['pantallas']))
        tipos = {}
        for r in d['reglas_candidatas']:
            tipos.setdefault(r['tipo'], []).append(r)
        caso('regla candidata: constante con nombre', any(r['valor'] == 'MAX_DIAS = 30' for r in tipos.get('constante con nombre', [])))
        frena = tipos.get('condicion que frena', [])
        caso('regla candidata: condicion que frena, con su if', any('30 dias' in r['valor'] and 'MAX_DIAS' in r.get('condicion', '') for r in frena) and any('negativo' in r['valor'] for r in frena), str(frena)[:300])
        caso('regla candidata: validacion, cambio de estado y calculo', 'validacion declarativa' in tipos and 'cambio de estado' in tipos and any(r['valor'] == 'calcularImporte' for r in tipos.get('funcion de calculo', [])))
        integ = {}
        for i in d['integraciones']:
            integ.setdefault(i['tipo'], []).append(i['valor'])
        caso('integraciones: cliente HTTP, URL de config, conexion, tarea programada', 'RestTemplate' in integ.get('cliente HTTP', []) and 'axios' in integ.get('cliente HTTP', [])
             and any('api.proveedor' in v for v in integ.get('url en configuracion', [])) and any('jdbc:postgresql' in v for v in integ.get('conexion a base o broker', []))
             and integ.get('tarea programada'), str(integ)[:400])
        caso('el password de la configuracion no se copia', 'supersecreta' not in out)
        caso('permisos con el rol literal', any('OPERADOR' in p['roles'] for p in d['permisos']))
        dep = d['dependencias']
        caso('arista reservas -> salas y cruce de capa infra', any(a['de'] == 'reservas' and a['a'] == 'salas' for a in dep['aristas']) and any(c['capa'] == 'infra' for c in dep['cruces_de_capa']), str(dep)[:300])
        caso('todo hecho trae archivo y linea', all('archivo' in x and 'linea' in x for x in d['api'] + d['reglas_candidatas'] + d['integraciones'] + d['permisos']))
        caso('lee el DDL y el stateDiagram que viven dentro de un .md', any(t['valor'] == 'meeting' and t['archivo'].endswith('okf/modelo.md') for t in mo['tablas']) and any(e['valor'].startswith('stateDiagram: Grabando') for e in mo['enums']))
        caso('estado= dentro de un dict NO es un cambio de estado', not any('data.py' in r['archivo'] for r in tipos.get('cambio de estado', [])), str(tipos.get('cambio de estado'))[:200])
        caso('reconoce un comando de Tauri como entrada de la API', ('CMD', 'grabar_reunion') in rutas)
    rc, out = correr(app)
    caso('en texto imprime la RADIOGRAFIA con sus secciones', rc == 0 and 'RADIOGRAFIA' in out and 'Reglas CANDIDATAS' in out and 'CRUCE DE CAPA' in out, out[:300])
    rc, out = correr(app, '--mermaid')
    caso('--mermaid dibuja modulos, el cruce de capa y el ER del DDL', rc == 0 and 'flowchart LR' in out and 'reservas -.' in out and 'CRUCE DE CAPA' in out and 'erDiagram' in out and 'RESERVA }o--|| SALA' in out, out[:400])
    vacio = tempfile.mkdtemp(prefix='probar-radiografia-vacio-')
    rc, out = correr(vacio)
    caso('carpeta vacia: SIN DATOS (2)', rc == 2)
    for d_ in (app, vacio):
        shutil.rmtree(d_, ignore_errors=True)
    fallas = [n for n, ok, _ in ESPERADOS if not ok]
    print()
    print('%s -- %d de %d casos dieron lo esperado.' % ('OK' if not fallas else 'FALLA', len(ESPERADOS) - len(fallas), len(ESPERADOS)))
    return 1 if fallas else 0


if __name__ == '__main__':
    sys.exit(main())
