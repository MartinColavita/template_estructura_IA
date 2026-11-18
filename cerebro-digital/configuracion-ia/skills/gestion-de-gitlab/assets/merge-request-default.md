<!--
Molde de la descripción de Merge Request. En el repositorio de código va como
.gitlab/merge_request_templates/Default.md (entra por la skill desarrollo).
Sin acciones rápidas (ninguna línea empieza con barra) y sin palabras de cierre delante de un número de issue:
mergear no cambia ninguna tarjeta; la mueve su GATE. Sin datos de personas: marcadores.
Antes de guardarla en GitLab, desde el repositorio del Cerebro: python -I bin/auditar-gitlab.py texto <archivo>
-->

## Tarea

Related to #<ID>

<!-- Si el tablero es Azure Boards: AB#<ID>, sin verbo delante (enlaza sin cerrar). -->

## Qué hace

<Dos o tres líneas en criollo: qué cambia para quien usa el sistema.>

## Qué módulo modifica

<Uno. Si usa otro (por su application), cuál.>

## Cómo se probó

<Los tests que se agregaron, y la evidencia del rojo y del verde (rama evidencia/<ID>).>

## Contrato

<Si cambió el contrato de la API: qué cambió y si rompe a alguien. Si no, «sin cambios».>

## Cambios que rompen

<Explícito. Si no hay, «ninguno».>

## Dependencias nuevas

<Cuáles, por qué y si están en la lista aprobada del proyecto. Si no hay, «ninguna».>

## Lo que quedó afuera

<Lo que se decidió no hacer, con el motivo.>

## Lo que no se pudo mirar

<Lo que quedó SIN DATOS en la verificación, con su motivo. Si no hay, «nada».>
