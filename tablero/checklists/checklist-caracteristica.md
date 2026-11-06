---
id: checklist-caracteristica
tipo: checklist
estado: F-Draft
modulo: integracion-azure-devops
title: "Checklist — Característica (Feature)"
author: equipo
tags: [azure-devops, feature, caracteristica, checklist, calidad]
last_updated: 2026-09-11
---

# Checklist — Característica (Feature)

Antes existían checklists de Historia, Bug y Habilitador, y **ninguno de Feature ni de Épica**. Eso dejaba un paso vacío: [[cargar-a-azure]] §1c manda «correr el checklist del tipo» al reutilizar un nodo que ya existe, y la Feature es —junto con la Épica— **el nodo que más se reutiliza** (en toda re-sincronización se marca YA EXISTE). El paso se evaporaba justo donde más corría.

Relacionados: [[checklist-historia]] · [[plantillas/caracteristica]] · [[definicion-preparado-terminado]]

---

## Contenido propio

- [ ] **Título** con prefijo de módulo consistente, sin typos, describiendo una **capacidad**, no una pantalla ni una tarea técnica.
- [ ] **Qué es** y **Valor para el negocio** escritos: se entiende qué capacidad entrega y a quién le sirve, sin leer las Historias hijas.
- [ ] **Alcance** y **Fuera de alcance**, los dos. El «fuera de alcance» es el que evita que la Feature crezca sola.
- [ ] **Criterios de aceptación de alto nivel** presentes y **verificables**: se puede decir si se cumplieron o no. Sin «funciona bien», «es usable», «mejora la experiencia».
- [ ] **Métricas de éxito** medibles (con unidad y valor), o declaradas explícitamente como no aplicables. Una métrica sin número no es una métrica.
- [ ] **Dependencias** identificadas.
- [ ] **Área de valor** y **Riesgo** puestos.
- [ ] **Una sola etiqueta temática**, la misma de toda la descendencia — sin prefijo, sin versión, sin producto/repo, sin slice ([[organizacion-y-trazabilidad]] §1).
- [ ] **Parent = la Épica del slice**, y la tabla **Historias que agrupa** presente.

## Vocabulario compartido con las hijas (lo que faltaba pedir)

Las Historias hijas heredan el vocabulario de su Feature. Si la Feature no lo fija, **cada Historia elige el suyo** y después los `Como <rol>` y los `Entonces <estado>` no coinciden entre hermanas — y nada lo detecta, porque cada Historia es internamente coherente.

- [ ] **Roles** que intervienen, nombrados **igual que en el Cerebro**. Son los que las Historias hijas van a usar en su «Como `<rol>`».
- [ ] **Estados** del dominio que la Feature toca, con su nombre exacto y de dónde salen. Son los que las hijas van a usar en sus `Entonces`.
- [ ] Si un rol o un estado **no existe todavía en el Cerebro**, va `⚠` y se pregunta. **No se inventa un nombre** para poder seguir: un nombre inventado acá se propaga a todas las hijas y a sus tests.

## Cierre contra las hijas

- [ ] **Cada criterio de alto nivel queda cubierto** por al menos una Historia hija, o está declarado como pendiente de una Historia futura. Es el equivalente, un nivel arriba, de lo que [[analizar-tareas]] hace entre Historia y Tareas — y hasta ahora **nadie lo miraba**: una Feature con 3 criterios y 2 Historias que cubren uno solo pasaba todos los controles del repo.
- [ ] **La tabla «Historias que agrupa» coincide con las Historias realmente creadas** (por `#ID`). Una fila sin Historia es alcance prometido y no entregado; una Historia hija que no está en la tabla es alcance que nadie declaró.
- [ ] **Cada Historia hija rastrea a un `[C-nn]`/`[F-nn]`** de la ficha fuente.

## Trazabilidad

- [ ] **Documento fuente** como link, nunca el contenido copiado.
- [ ] **Fila en [[historial/INDICE]]**. Es habitual que las Épicas y Features creadas queden sin fila, contra la regla de «una fila por ticket».

---

## Veredicto

| Resultado | Qué habilita |
|---|---|
| Todas tildadas | La Feature está en condiciones de recibir Historias |
| Falta contenido propio o vocabulario | **Se completa antes de crear las Historias hijas** — lo que falte acá se multiplica por cada hija |
| Falta cierre contra las hijas | Se puede seguir, pero queda como hallazgo: hay alcance declarado que nadie entrega |

> Este checklist **no reemplaza** a [[auditar-historia]], que, si se pide, audita cada Historia hija en su
> propio turno y con otro agente. Acá se mira la Feature; allá, sus hijas.
