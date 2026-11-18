# Acceso — cómo llega la IA a un servidor sin tener una shell

> **La barrera vive en el servidor.** Las reglas del cliente de IA las aplica el programa, no el modelo, y una regla
> sobre comandos de terminal no es una frontera de seguridad: el mismo programa se puede invocar de otra forma. Por
> eso la identidad que usa la IA **no puede** hacer lo que no debe, aunque se lo pidan. Todo lo de esta página lo
> instala y lo cambia **una persona**: tocar accesos es N3 ([[AGENTS]]).

## Las tres identidades

| Identidad | Para qué | Cómo se restringe | Quién la habilita |
|---|---|---|---|
| **De lectura** (`ia-lectura`) | N0: el diagnóstico | Una clave que **sólo** puede correr el colector: comando forzado, sin terminal, sin reenvíos, desde un solo origen | Una persona, una vez por servidor, con revisión |
| **De cambio** (`ia-cambio`) | N1 y N2, dentro de la ventana | Un **certificado SSH de vida corta** (una hora) que firma una persona al abrir la ventana, y del lado del servidor `sudo` con **comandos exactos**, sin comodines, con registro de entrada y salida | La persona que dio el «sí», en cada ventana |
| **De emergencia** | Lo que ninguna de las dos alcanza | Sólo personas, vigilado | — |

Sin root interactivo, sin `sudo` libre y nunca la clave personal de quien administra: una sesión SSH abierta expone
todo el sistema y se audita mal.

## Lo que instala una persona, una sola vez

### 1. El colector

[assets/colector-salud.sh](../assets/colector-salud.sh) es un script de `sh`, fijo, sin argumentos y de sólo
lectura. Se copia como `/usr/local/sbin/colector-salud`, dueño `root`, permisos `0755`, y se prueba a mano:

```sh
/usr/local/sbin/colector-salud > salud-<alias>.txt
```

En la máquina de la IA, `python -I bin/salud-host.py --archivo salud-<alias>.txt --horas-reporte 0` tiene que leerlo
entero (sin «le falta la sección…»). Si el servidor no tiene systemd, esas secciones dicen `sin_dato`: el colector
no inventa.

### 2. La identidad de lectura

Un usuario `ia-lectura` sin contraseña, sin `sudo` y sin grupos de administración. En su `authorized_keys`, una
sola línea:

```
restrict,command="/usr/local/sbin/colector-salud",from="<bastión>" <clave pública de ia-lectura>
```

- `restrict` apaga el reenvío de puertos, del agente y de X11, la terminal y el `~/.ssh/rc`, incluidas las
  restricciones que agreguen versiones futuras.
- `command=` hace que esa clave corra **siempre** el colector: el comando que pida el cliente se ignora.
- `from=` limita desde dónde se puede usar. Si se quiere que venza, `expiry-time=`.
- Para que vea los servicios y el journal del sistema, alcanza con el grupo de lectura del journal
  (`systemd-journal` o `adm`, según la distribución); nunca `sudo`.

### 3. La máquina de la IA

En la configuración de SSH de la máquina (fuera del repositorio), un alias por servidor con su usuario, su clave y
`IdentitiesOnly yes`. Ese alias es el que va en la columna **Destino** del inventario: un nombre solo, sin usuario,
sin espacios y sin opciones (si no, `bin/salud-host.py` no se conecta). La **primera** conexión, la que acepta la
clave del servidor, la hace una persona: el script nunca acepta una clave de servidor nueva ni pide contraseña.

### 4. La prueba de que la barrera está en el servidor

```sh
ssh <alias-de-lectura> id
```

Tiene que imprimir **el reporte del colector**, no el usuario: el `id` se ignoró. Si imprime otra cosa, la clave
no está restringida y no se usa hasta arreglarlo. Después, `python -I bin/salud-host.py --ssh <alias>` en OK (o con
HALLAZGO reales), nunca con «no es un reporte del colector».

### 5. La identidad de cambio (sólo si se va a operar en N1 o N2)

- Una autoridad de certificados SSH propia: el servidor confía en ella (`TrustedUserCAKeys`) y sólo acepta el
  principal `ia-cambio` para ese usuario.
- `sudoers` con la lista **exacta** de comandos que los planes usan (por ejemplo
  `/usr/bin/systemctl restart cola.service`), sin comodines en los argumentos (un comodín también calza espacios),
  con `log_input` y `log_output` para que quede qué entró y qué salió.
- Al abrir una ventana, la persona firma la clave de la IA con validez corta y origen fijo:

```sh
ssh-keygen -s <clave-de-la-autoridad> -I <ventana-AAAA-MM-DD> -n ia-cambio -V +1h -O source-address=<bastión> <clave-de-la-ia>.pub
```

Sin `-V`, un certificado vale para siempre: la validez se pone siempre. La clave de la autoridad nunca está en la
máquina de la IA.

## Lo que la IA no hace nunca

Instalar o cambiar el colector, tocar `authorized_keys`, `sudoers`, usuarios, la configuración de SSH o el
firewall de administración, firmar un certificado o tener la clave de la autoridad, ni leer variables de entorno o
archivos de credenciales «para diagnosticar». Lo que hace es **armar el resumen exacto** (qué línea, en qué
servidor, por qué) para que lo haga la persona.

## Sin identidades instaladas

La operación queda en **N0 con reportes que trae una persona** (`--archivo`), y los cambios N1 o N2 los corre la
persona con el plan a la vista. Es más lento, y es lo correcto hasta que estén las identidades: sin ellas, ninguna
regla escrita impide que una sesión con más permisos haga de más.

## Registro y secretos

- **Lo que queda en el servidor**: el registro de SSH (quién entró, con qué clave o certificado) y el de `sudo`
  (qué se corrió, con su entrada y su salida). Dónde se guarda y cuánto tiempo, `DEC-008`.
- **Los secretos** (contraseñas de los repositorios de respaldo, tokens) viven en el gestor que fije `DEC-008`:
  nunca en el repositorio, en el chat ni en un plan. El colector no imprime ninguno.
- **Las herramientas de observabilidad**, en sólo lectura: un MCP de tableros o de alertas se conecta con la
  escritura apagada (por ejemplo, el de Grafana con `--disable-write`).

## Cómo entra en el veredicto

```
identidad de lectura : OK si "ssh <alias-de-lectura> id" devuelve el reporte; HALLAZGO si devuelve otra cosa
colector             : OK si salud-host.py lo lee entero; SIN DATOS si no está o llega cortado
identidad de cambio  : SIN DATOS mientras no esté: N1 y N2 los corre la persona
```
