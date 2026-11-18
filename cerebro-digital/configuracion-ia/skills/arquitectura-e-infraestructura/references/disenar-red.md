# Diseñar la red de una aplicación por ambiente, y escribirla como código

La red es parte de la infraestructura y, escrita como código, **entra por [[desarrollo]]** (G2) con el ciclo de
[armar-infraestructura.md](armar-infraestructura.md): rama, test primero, Merge Request, verificador distinto,
nada se aplica desde la máquina. Acá está **sólo lo propio de la red**: qué flujos existen, en qué zonas vive cada
cosa, qué se expone y a quién, DNS, TLS, la salida a internet y el acceso administrativo. Diagnosticar una red que
ya corre es de [[operacion-de-servidores]]; los protocolos y cifrados de TLS y escanear lo expuesto, de [[seguridad]].

Las ideas vienen de las guías de red de AWS y Microsoft, de NIST SP 800-41 y 800-207, de la documentación de
Kubernetes y de OWASP (bibliografía: `cerebro-digital/networking/fuentes.md`).

## Antes de dibujar nada

1. **`DEC-007`**: la plataforma, la herramienta de infraestructura como código y los temas de red (zonas por
   ambiente, acceso administrativo, dónde termina TLS, quién administra el DNS, salida a internet). **Lo que esté en
   `⚠` se pregunta antes de escribir**; no se elige por el equipo (G3).
2. **Las fichas**: [[red]] (lo concreto de la red por ambiente), [[infraestructura]] (los recursos y la vista de
   despliegue), [[ambientes]] (la lista de ambientes). Un ambiente que no está en [[ambientes]] no tiene red.
3. **Qué habla con qué**: la vista de contenedores o de despliegue ([disenar-arquitectura.md](disenar-arquitectura.md)).
   Cada regla de red sale de un flujo de esa vista; un flujo que no está en la vista es una pregunta.

## Primero los flujos, después las reglas

Cada flujo, una fila: **origen, destino, puerto y protocolo, motivo**. Se separa lo que cruza el borde (entra o sale
de internet, «norte-sur») de lo que va entre piezas propias («este-oeste»). Un puerto abierto sin un flujo que lo
pida no se abre: se pregunta para qué es. La tabla final vive en [[red]].

## Zonas por ambiente

| Zona | Qué vive | Quién le habla | Salida a internet |
|---|---|---|---|
| **Borde** (pública) | El balanceador o el proxy inverso; el firewall de aplicaciones web si `DEC-007` lo pide | Internet, sólo en 443 (y 80 para redirigir) | No hace falta |
| **Aplicación** (privada) | La aplicación, sus trabajos en segundo plano | Sólo el borde, por el puerto de la aplicación | Por un punto de salida controlado, si la aplicación llama afuera |
| **Datos** (privada) | Bases, colas, caché, almacenamiento | Sólo la zona de aplicación, por el puerto de cada servicio | **Ninguna** |
| **Administración** | El bastión o el acceso administrado, los agentes de construcción si corren adentro | Quien opera, con identidad | La que pida la herramienta |

- **Una red por ambiente**, y producción sin conexión directa con desarrollo ni con prueba (sin emparejamiento de
  redes), salvo lo que `DEC-007` fije con su motivo.
- **Nada de la zona de datos tiene dirección pública.** Un servicio administrado de la nube se usa por su punto de
  acceso privado cuando la plataforma lo tiene, y con su firewall propio encendido.
- **Las reglas apuntan a grupos, no a direcciones sueltas**: «la aplicación acepta desde el grupo del balanceador»
  sigue valiendo cuando cambian las máquinas; cada regla lleva su descripción (el motivo).
- **Kubernetes**: los Pods no están aislados hasta que una NetworkPolicy los elige. Por espacio de nombres va una
  política que niega todo por defecto (entrada y salida) y una por cada flujo permitido; si se cierra la salida, se
  permite el DNS del cluster (53, UDP y TCP) o deja de resolver. **Sin un plugin de red que las aplique, las
  NetworkPolicy no hacen nada**: eso es `SIN DATOS` hasta que `DEC-007` diga cuál es.

## Exposición mínima

- **Se niega por defecto, en las dos direcciones** (NIST SP 800-41): lo que no está permitido por una regla escrita
  no pasa.
- **A todo internet se abre sólo el borde**, en 443 (y 80 para redirigir a HTTPS). **Nunca a todo internet**: SSH
  (22), escritorio remoto (3389) ni una base o una caché (3306, 5432, 1433, 27017, 6379, 9200), ni un rango que los
  incluya, ni «todos los puertos». Lo cuenta `bin/auditar-iac.py` con la regla `RED-ABIERTA`.
- **Un `Service` de Kubernetes `LoadBalancer` abre a todo internet por defecto.** Lo público entra por un Ingress o un
  Gateway; si hace falta un `LoadBalancer`, lleva `loadBalancerSourceRanges` escrito (aunque sea `0.0.0.0/0`, para que
  la exposición sea una decisión a la vista) o va interno, con la anotación de la plataforma.
- **Los servidores detrás del balanceador sólo aceptan tráfico del balanceador**, y la aplicación confía en la
  cabecera de la dirección del cliente (`X-Forwarded-For`) sólo si viene de él.

## Salida a internet, controlada

En muchas plataformas la salida está abierta por defecto. La zona de datos no sale; la de aplicación sale por un
punto controlado (traducción de direcciones o firewall de salida) y, si `DEC-007` lo pide, sólo a una lista de
destinos con nombre. El DNS se consulta sólo al resolvedor propio: un 53 abierto a cualquier destino también sirve
para sacar datos.

## DNS

- **Dos zonas si hace falta**: lo interno resuelve en una zona privada y **no se publica** en la pública. Se publican
  la menor cantidad de nombres que se pueda.
- **Un cambio seguro**: se baja el TTL (por ejemplo a 300 segundos) **un TTL viejo antes** del cambio, se cambia, se
  verifica y recién después se sube. Se anota el valor anterior: es la vuelta atrás.
- **Un registro `CAA`** dice qué autoridades pueden emitir certificados para el dominio.
- **Los registros son código** cuando el proveedor de DNS lo permite (en el repositorio de infraestructura); si la
  zona la administra otro equipo, se le pide con el registro exacto. Cambiar uno de producción es **N2**; los
  servidores de nombres, el registrador o borrar una zona, **N3** ([[AGENTS]]).

## TLS

- **Dónde termina**, por ambiente, escrito en [[red]]: en el borde (balanceador o proxy) y, si viajan datos de
  personas o lo pide `DEC-007`, **re-cifrado** hasta la aplicación. HTTP sólo para redirigir.
- **Los certificados se renuevan solos** (ACME o el gestor de certificados de la plataforma). La clave privada nunca
  va al repositorio (lo cuenta `SECRETO-FORMATO`). La vigencia la mide `bin/vigencia-certificados.py`
  ([[operacion-de-servidores]]); protocolos y cifrados, [[seguridad]].

## Acceso administrativo

En este orden de preferencia, y lo elige `DEC-007`:

1. **Sin puerto abierto**: el acceso administrado de la plataforma (una sesión que abre la identidad de la persona,
   con registro), en la línea de confianza cero de NIST SP 800-207: la sesión se autoriza por identidad, no por estar
   «adentro» de la red.
2. **Un bastión** en la zona de administración, con origen acotado al rango de la organización y registro de
   sesiones.
3. **Una VPN**, con identidad por persona.

Nunca SSH ni escritorio remoto abiertos a todo internet. Configurar quién entra es **tocar accesos: N3**, lo hace una
persona; la IA escribe el código y arma el resumen.

## Escribirla como código

El orden del repositorio, el estado y las pruebas sin nube están en
[armar-infraestructura.md](armar-infraestructura.md). Lo propio de la red:

- **Un módulo `red`** por capacidad: la red del ambiente, sus subredes por zona, los grupos o reglas de firewall, la
  salida y el DNS. Las direcciones y los rangos entran por variable, con `description`; en el código y en las fichas
  van alias y `<rango>`, nunca direcciones reales de la organización.
- **Una regla, un recurso, con su descripción.** En AWS, la documentación del proveedor recomienda
  `aws_vpc_security_group_ingress_rule` y `..._egress_rule` antes que los bloques en línea, y no mezclar las dos
  formas. En Azure, `azurerm_network_security_rule` con prioridades separadas; en Google Cloud,
  `google_compute_firewall` apuntando a etiquetas o cuentas de servicio.
- **Sin `dynamic` ni `for_each` para armar reglas desde una lista que llega por variable**: `RED-ABIERTA` no la ve y
  queda para el criterio del verificador. Si hace falta, el test del módulo (`terraform test` con proveedor
  simulado) afirma que ninguna regla de ingreso abre un puerto sensible a `0.0.0.0/0`.
- **Aplicar la red real lo hace el pipeline** (GATE de INFRAESTRUCTURA): la IA no corre `plan` contra un ambiente
  ni `apply`.

## Qué se decide en una DEC y qué va a la ficha

| Qué | Dónde |
|---|---|
| La política: zonas por ambiente, acceso administrativo, dónde termina TLS, quién administra el DNS, salida a internet | `DEC-007`, por `cerebro-curator` con el «sí» |
| Lo concreto de cada ambiente: zonas, puertos abiertos con su motivo, registros, dónde termina TLS, cómo se administra | [[red]], por `cerebro-curator` con el «sí» |
| Los recursos que lo implementan y la vista de despliegue | [[infraestructura]] |
| Los servidores y las URL que la IA puede tocar | [[inventario]] |
| El código | Su repositorio, por [[desarrollo]] |

## Cómo lo revisa el verificador

Primero el script, después el criterio:

```
RED-ABIERTA            : lo que diga bin/auditar-iac.py (sus avisos -- puerto, origen o direccion por variable, reglas dynamic o como atributo que no se leen -- a mano)
flujos                 : criterio -- cada regla de ingreso tiene su flujo y su motivo en la ficha red; sin flujo, HALLAZGO
datos sin exposicion   : criterio -- nada de la zona de datos con direccion publica ni salida a internet
administracion         : criterio -- ningun puerto de administracion publico; la via elegida es la de DEC-007
salida                 : criterio -- la salida sale por el punto controlado; SIN DATOS si DEC-007 esta en ⚠
Kubernetes             : criterio -- negar por defecto por espacio de nombres y DNS permitido; SIN DATOS sin plugin que aplique
DNS y TLS              : criterio -- lo interno no esta en la zona publica; TLS termina donde dice la ficha red
```

Lo que depende de un tema de `DEC-007` en `⚠` es `SIN DATOS (pendiente declarado)`. Un chequeo que no corrió es
`SIN DATOS`, no OK.

## Lo que entrega quien produce

- La tabla de flujos y lo que cambia en [[red]], para que lo valide la persona.
- El código en la rama de la Tarea, con la salida de `bin/auditar-iac.py` tal cual.
- Lo que no se pudo probar sin la nube, como `SIN DATOS`, y los temas de red de `DEC-007` que siguen en `⚠`.
