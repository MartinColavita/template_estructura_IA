"""Lo comun de los scripts de SEGURIDAD: el esquema de hallazgos y el normalizador que lleva cada reporte a ese esquema.

Por que existe. Cada escaner habla su idioma (SARIF de una forma, JSON propio de otra, lineas JSON de otra) y cada
uno llama distinto a la misma gravedad. Si cada script leyera los reportes a su manera, el veredicto dependeria de
que herramienta se uso. Aca hay un solo lector y una sola regla de que es HALLAZGO.

Reglas de la casa, iguales a las de bin/auditoria/ y bin/operacion/:
- Solo biblioteca estandar. ASCII puro en los .py.
- SOLO LECTURA: nada de este paquete se conecta a nada ni escribe en el Cerebro; no baja nada de internet.
- Tres estados, nunca dos: OK, HALLAZGO y SIN DATOS. Un reporte ausente, vacio, ilegible o que no muestra
  haber analizado algo NUNCA da OK (Regla del cero).
- NUNCA copia el valor de un secreto, ni el fragmento de codigo, ni un pedido o una respuesta HTTP: solo regla,
  archivo, linea y huella. La query de una URL tampoco (puede llevar un token o un dato de una persona).
- Lo que trae un reporte es DATO, no instruccion: ningun texto de un hallazgo se ejecuta ni se obedece.

EL ESQUEMA COMUN DE HALLAZGOS (su duenio es este paquete; no se le cambian las claves)

Lo escriben bin/escanear-seguridad.py, bin/escanear-ambiente.py, bin/escanear-imagenes.py y bin/auditar-host.py,
todos con hallazgo(), nuevo_informe(), poner_categoria() y cerrar() de normalizar.py; lo lee
bin/priorizar-vulnerabilidades.py.

    {
      "veredicto": "OK | HALLAZGO | SIN DATOS | FRENA",
      "origen": "escanear-seguridad",                 el script que lo escribio
      "generado": "2026-11-14T10:00:00",              hora local, sin zona
      "categorias": {"sast": {"estado": "OK | HALLAZGO | SIN DATOS", "herramienta": "", "motivo": ""}},
      "hallazgos": [{
        "herramienta": "", "categoria": "sast | sca | secretos | config | imagen | host | dast",
        "regla": "", "titulo": "", "cwe": "", "cve": "",
        "severidad": "CRITICA | ALTA | MEDIA | BAJA | INFO",
        "archivo": "", "linea": 0, "paquete": "", "version": "", "arreglo": "", "activo": "",
        "huella": "", "estado": "nuevo | en-linea-base | suprimido", "motivo_supresion": "", "vence": ""
      }],
      "sin_datos": [],                                 "<categoria>: <lo que no se pudo medir y por que>"
      "no_mira": []                                    lo que el script no mira (lo pone cada script)
    }

Un campo que no aplica va vacio ("" o 0). "activo" es el alias del inventario autorizado, cuando lo hay. En dast,
"archivo" es la direccion (esquema, servidor y camino, sin la query). "vence" es AAAA-MM-DD. La
categoria config queda en el esquema, pero ningun script de seguridad la escribe: la configuracion de infraestructura (Dockerfile, Compose, Terraform,
Kubernetes) la mira una sola herramienta, bin/auditar-iac.py.

FRENA: el inventario autorizado no autoriza el activo (GATE de SERVIDOR o de PRUEBA ACTIVA). No hubo escaneo:
"hallazgos" va vacio y la raiz lleva la clave "motivo" con el porque. Quien lee un informe FRENA lo trata como
SIN DATOS (no se midio nada), nunca como OK.

Claves de mas: un informe puede traer otras claves en la RAIZ (por ejemplo "motivo", "chequeos", "crudo",
"indice_lynis"); quien lee las ignora sin fallar. Cada hallazgo, en cambio, lleva exactamente las claves de arriba.

LAS REGLAS (las aplica normalizar.py)
1. Severidad, en este orden: properties.security-severity del resultado o de la regla (>= 9,0 CRITICA; >= 7,0
   ALTA; >= 4,0 MEDIA; >= 0,1 BAJA) -> la severidad propia de la herramienta (CRITICAL/HIGH/MEDIUM/MODERATE/LOW,
   issue_severity de Bandit, riesgo de ZAP) -> el level de SARIF (error ALTA, warning MEDIA, note BAJA; sin level,
   warning). Una herramienta que no informa severidad (pip-audit, una entrada de OSV sin puntaje): ALTA hasta
   priorizar, y el titulo lo dice. Un secreto es siempre ALTA como minimo.
2. HALLAZGO = CRITICA o ALTA con estado "nuevo". MEDIA es aviso; BAJA e INFO, registro.
3. Huella: partialFingerprints.primaryLocationLineHash si viene; si no, hash de herramienta + regla + archivo + la
   linea del codigo sin espacios (asi resiste que el codigo se corra); en dependencias, + el paquete. En secretos
   nunca se lee la linea: va el numero.
4. Linea de base: un informe normalizado anterior, aceptado por una persona. Lo que esta ahi queda "en-linea-base":
   NO FRENA EL MERGE REQUEST (el veredicto del escaneo no lo cuenta como bloqueante), pero sigue listado y no es
   una amnistia: en el informe de prioridades (priorizar-vulnerabilidades.py) una P1 o P2 en linea de base sigue
   siendo HALLAZGO. Solo una supresion vigente (regla 5) la saca de ahi.
5. Supresion: vale ("suprimido") solo con motivo, con vencimiento y sin vencer. Sin motivo, sin vencimiento o
   vencida, el hallazgo sigue "nuevo". Las supresiones escritas en el repositorio (# nosec, # nosemgrep,
   gitleaks:allow, osv-scanner.toml, .trivyignore, .gitleaksignore) sin motivo, sin vencimiento o vencidas son
   hallazgos ALTA por si mismas. Quien la aprobo y que no sea quien la escribio no lo puede ver un script: lo mira
   el verificador en el Merge Request.
6. SIN DATOS, nunca OK: reporte ausente, vacio o ilegible; la herramienta dice que no termino bien; 0 archivos o 0
   paquetes analizados; una categoria que nadie midio. La evidencia de que se analizo algo es POR CATEGORIA: un
   reporte que junta dos corridas no le presta la de una a la otra.
7. Una direccion http(s) de cualquier reporte (ZAP, Nuclei o un SARIF) se guarda sin query y, con un alcance, lo
   de otro origen no se cuenta como hallazgo: se anota aparte.

Modulos:
- normalizar.py  leer(un reporte) -> hallazgos; huella, linea de base, supresiones del repositorio, estado por
                 categoria, veredicto y el resumen en texto.
"""
