#!/bin/sh
# colector-salud -- reporte de salud del servidor, de SOLO LECTURA, para bin/salud-host.py.
#
# Lo instala UNA PERSONA, una sola vez, en /usr/local/sbin/colector-salud (duenio root, modo 0755), y lo ata a
# la identidad de lectura de la IA como comando forzado en su authorized_keys:
#     restrict,command="/usr/local/sbin/colector-salud",from="<bastion>" <clave publica de ia-lectura>
# Con eso, esa clave solo puede correr este archivo: sin terminal, sin reenvios y sin comandos libres. Lo que
# el cliente pida por ssh se ignora (sshd lo deja en una variable que este script no lee).
#
# Reglas de este archivo (las verifica bin/probar-salud-host.py):
# - sh POSIX, sin argumentos, ASCII puro, saltos de linea de Unix.
# - No escribe en ningun archivo, no cambia nada y no imprime el entorno, los procesos ni nada que pueda
#   traer un secreto: solo cifras, nombres de montajes, nombres de unidades y estados.
# - Cada seccion se imprime siempre. Si algo no se pudo medir, la seccion dice sin_dato=<motivo>: un
#   dato que falta es SIN DATOS para quien lee, nunca un OK.
# - El formato es el contrato con bin/salud-host.py (formato=1). Cambiarlo es cambiar los dos.
#
# Contenido: [sistema] [disco] [inodos] [memoria] [carga] [servicios] [reinicio] [reloj] [journal] [fin].
# Detalle y como se instala: references/acceso.md y references/diagnosticar.md de la skill.

if [ "$#" -ne 0 ]; then
    echo 'colector-salud: no acepta argumentos' >&2
    exit 2
fi
PATH=/usr/sbin:/usr/bin:/sbin:/bin
LC_ALL=C
export PATH LC_ALL

hay() { command -v "$1" >/dev/null 2>&1; }

# Corre una orden con tope de tiempo si existe timeout: un montaje colgado no puede trabar el reporte.
con_tope() {
    if hay timeout; then timeout 10 "$@"; else "$@"; fi
}

# Del formato de df -P con tipo (sistema, tipo, total, usados, libres, porcentaje, montaje) a
# tipo|total|usados|porcentaje|montaje. El montaje puede tener espacios.
filas_df() {
    awk 'NR != 1 && !(NF < 7) { m = $7; for (i = 8; i <= NF; i++) m = m " " $i; p = $6; sub(/%$/, "", p);
         print $2 "|" $3 "|" $4 "|" p "|" m }'
}

echo 'colector-salud formato=1'

echo '[sistema]'
echo "fecha_epoch=$(date +%s)"
if [ -r /proc/uptime ]; then
    echo "arranque_epoch=$(awk -v ahora="$(date +%s)" '{ printf "%d\n", ahora - $1 }' /proc/uptime)"
fi
if [ -r /etc/os-release ]; then
    echo "so=$(awk -F= '$1 == "ID" { gsub(/"/, "", $2); i = $2 } $1 == "VERSION_ID" { gsub(/"/, "", $2); v = $2 }
                       END { print i " " v }' /etc/os-release)"
fi
echo "nucleo=$(uname -r)"
echo "cpus=$(getconf _NPROCESSORS_ONLN 2>/dev/null)"

echo '[disco]'
filas=$(con_tope df -P -T -k -l 2>/dev/null | filas_df)
if [ -n "$filas" ]; then printf '%s\n' "$filas"; else echo 'sin_dato=df no informo ningun sistema de archivos'; fi

echo '[inodos]'
filas=$(con_tope df -P -T -i -l 2>/dev/null | filas_df)
if [ -n "$filas" ]; then printf '%s\n' "$filas"; else echo 'sin_dato=df no informo los inodos'; fi

echo '[memoria]'
if [ -r /proc/meminfo ]; then
    awk '$1 == "MemTotal:" { print "total_kb=" $2 } $1 == "MemAvailable:" { print "disponible_kb=" $2 }
         $1 == "SwapTotal:" { print "swap_total_kb=" $2 } $1 == "SwapFree:" { print "swap_libre_kb=" $2 }' /proc/meminfo
else
    echo 'sin_dato=no hay /proc/meminfo'
fi

echo '[carga]'
if [ -r /proc/loadavg ]; then
    awk '{ print "uno=" $1; print "cinco=" $2; print "quince=" $3 }' /proc/loadavg
else
    echo 'sin_dato=no hay /proc/loadavg'
fi

echo '[servicios]'
if hay systemctl; then
    caidas=$(con_tope systemctl list-units --state=failed --plain --no-legend --no-pager 2>/dev/null)
    lista=$?
    if [ "$lista" -eq 0 ]; then
        estado=$(con_tope systemctl is-system-running 2>/dev/null)
        echo "estado=${estado:-desconocido}"
        unidades=$(printf '%s\n' "$caidas" | awk 'NF != 0 { u = $1; if (u == "*" || u == "x") u = $2; print u }')
        if [ -n "$unidades" ]; then
            echo "caidas=$(printf '%s\n' "$unidades" | awk 'END { print NR }')"
            printf '%s\n' "$unidades" | awk '{ print "caida=" $0 }'
        else
            echo 'caidas=0'
        fi
    else
        echo 'sin_dato=no se pudieron listar las unidades de systemd (sin systemd o sin acceso)'
    fi
else
    echo 'sin_dato=no hay systemd en este servidor'
fi

echo '[reinicio]'
archivo=''
for f in /run/reboot-required /var/run/reboot-required; do
    if [ -z "$archivo" ] && [ -e "$f" ]; then archivo=$f; fi
done
if [ -n "$archivo" ]; then
    echo 'pendiente=si'
    echo "desde_epoch=$(date -r "$archivo" +%s 2>/dev/null || echo desconocido)"
    echo 'metodo=archivo'
elif hay needs-restarting; then
    con_tope needs-restarting -r >/dev/null 2>&1
    pide=$?
    if [ "$pide" -eq 0 ]; then echo 'pendiente=no'
    elif [ "$pide" -eq 1 ]; then echo 'pendiente=si'; echo 'desde_epoch=desconocido'
    else echo 'pendiente=desconocido'
    fi
    echo 'metodo=needs-restarting'
elif [ -d /lib/modules ]; then
    nuevo=$(ls /lib/modules 2>/dev/null | sort -V 2>/dev/null | awk 'END { print $0 }')
    if [ -z "$nuevo" ]; then echo 'pendiente=desconocido'
    elif [ "$nuevo" = "$(uname -r)" ]; then echo 'pendiente=no'
    else echo 'pendiente=si'; echo "desde_epoch=$(date -r "/lib/modules/$nuevo" +%s 2>/dev/null || echo desconocido)"
    fi
    echo 'metodo=nucleo'
else
    echo 'pendiente=desconocido'
    echo 'metodo=ninguno'
fi

echo '[reloj]'
sinc=''
if hay timedatectl; then
    sinc=$(con_tope timedatectl show -p NTPSynchronized --value 2>/dev/null)
    if [ -z "$sinc" ]; then
        sinc=$(con_tope timedatectl status 2>/dev/null | awk -F: '/synchronized/ { gsub(/ /, "", $2); print $2; exit }')
    fi
fi
case "$sinc" in
    yes) echo 'sincronizado=si' ;;
    no) echo 'sincronizado=no' ;;
    *) echo 'sincronizado=desconocido' ;;
esac

echo '[journal]'
uso=''
if hay journalctl; then
    uso=$(con_tope journalctl --disk-usage 2>/dev/null | sed -n 's/.*take up \([^ ]*\) .*/\1/p')
fi
if [ -n "$uso" ]; then echo "uso=$uso"; else echo 'sin_dato=journalctl no informo el uso'; fi

echo '[fin]'
