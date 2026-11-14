---
id: redaccion-tickets-definicion-preparado-terminado
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: Definición de Preparado (DoR) y Terminado (DoD)
author: equipo
tags: [dor, dod, definition-of-ready, definition-of-done, sprint, checklist]
last_updated: 2026-08-26
---

# Definición de Preparado (DoR) y Definición de Terminado (DoD)

Las dos listas de control que un ítem del backlog debe cumplir para ENTRAR a un sprint (Preparado) y para poder cerrarse (Terminado). Úsalas como semáforo objetivo, no como opinión. Método agnóstico; el aterrizaje al stack real del equipo va rotulado.

---

## Qué son y por qué importan

- **DoR = Definición de Preparado** (*Definition of Ready*): el conjunto de condiciones que una historia, tarea o bug debe cumplir **ANTES** de que el equipo lo comprometa en un sprint. Si no las cumple, no entra: se devuelve al autor para completarlo.
- **DoD = Definición de Terminado** (*Definition of Done*): el conjunto de condiciones que deben cumplirse para mover el ítem a **Closed** (Cerrado). No es "el código compila": es "está en producción o listo para producción, verificado y sin deuda oculta".

Estas dos definiciones atacan de raíz el problema recurrente del tablero: historias sin criterios de aceptación, descripciones que son solo un link, bugs que dicen "Ver adjunto", y campos (Puntos de historia, Gravedad) vacíos. El DoR frena eso en la entrada; el DoD frena que se cierre algo a medias.

> Regla de casa: **el DoR y el DoD no se negocian por presión de fecha.** Si un ítem no está Preparado, se prepara antes; no se mete "a ver si sale".

---

## DEFINICIÓN DE PREPARADO (DoR)

### Común a TODO ítem (historia, tarea, bug)

- [ ] **Título claro y con prefijo de módulo** consistente, **sin errores de tipeo**.
- [ ] **Tipo de work item correcto**: es una Historia si aporta valor al usuario; es una Tarea si es trabajo técnico hijo de una historia; es un Bug si es un defecto. (Una "reestructuración de módulo" es Tarea/Feature técnica, **no** una Historia de usuario disfrazada.)
- [ ] **Alcance escrito en la propia tarjeta**, no solo un enlace. Un link a un diseño o a un repositorio **acompaña**, no reemplaza, la descripción del alcance.
- [ ] **Dependencias identificadas** (otros ítems, otro equipo, otro módulo, datos, definiciones funcionales) y **sin bloqueos abiertos**.
- [ ] **Estimado** con Puntos de historia (los calcula la IA por complejidad a nivel sistema + tokens de resolver/investigar, y el humano puede ajustar), o el ítem es lo bastante chico y claro que no necesita estimación. Ver [[estimacion-y-priorizacion]].
- [ ] **Ruta de iteración y Área** decididas (a qué sprint apunta, a qué área de valor).
- [ ] **Etiqueta** puesta: **una sola, temática**, sin prefijo y siempre escrita igual. **Techo duro: ninguna más.** Nunca el nombre del producto/repo (`<producto>`, `<repositorio>`), nunca la versión, nunca el slice (el slice es la Épica). Si hace falta dejar asentada la versión o el componente, va como **campo de contenido** de la tarjeta, no como etiqueta. Ver [[organizacion-y-trazabilidad]] §1.
- [ ] **Sin PHI**: no hay datos personales reales (personas, documentos, teléfonos, diagnósticos, credenciales) escritos en la tarjeta. Si hacen falta datos de prueba, se referencian por estructura o por marcador (`<persona>`, `<documento>`), no por valor real.

### Adicional para HISTORIA DE USUARIO

- [ ] **Rol / necesidad / beneficio** explícito: "Como `<rol>` quiero `<necesidad>` para `<beneficio>`". Se ve el valor de negocio.
- [ ] **Criterios de aceptación ESCRITOS** (no vacíos), verificables, idealmente en Gherkin español (Dado / Cuando / Entonces). Debe poder responderse "¿cuándo está hecha?". Ver [[criterios-aceptacion-gherkin]].
- [ ] **Contexto de dominio referenciado** cuando aplica: módulo del flujo troncal, tipo de operación, estados involucrados, canal. (El dominio concreto lo define [[contexto-proyecto]].)
- [ ] **Diseño referenciado** si toca UI, con el link y una nota de qué pantalla/estado cubre.
- [ ] **Cumple INVEST**: Independiente, Negociable, Valiosa, Estimable, pequeña (*Small*) y Testeable. Si no es *Small*, se parte. Ver [[historias-de-usuario]].

### Adicional para TAREA (trabajo técnico)

- [ ] **Enlazada a su Historia padre** (Primario/Parent), salvo que sea tarea técnica pura sin historia (migración/reestructuración): en ese caso, el objetivo técnico está escrito.
- [ ] **Objetivo técnico concreto**: qué repo/módulo se toca, qué rama, qué se espera al terminar. Para reestructuración: origen, destino y alcance.
- [ ] **Esfuerzo original** estimado en horas (campo de la Tarea) si el equipo trabaja con horas.
- [ ] **Actividad** definida (Development / Testing / Documentation / Deployment...).
- [ ] **Lista para desarrollar**: las cuatro piezas de [[redactar-tarea]] §3.1 (capa `api`, `application` o `domain`;
  las exenciones de otras capas, ahí), con lo dudoso declarado en **«⚠ Datos a confirmar»**. Lo cuenta
  `bin/auditar-tarea.py`.

### Adicional para BUG

- [ ] **Ambiente** identificado y **uno solo por bug** (por ejemplo DESA / TEST / PREPROD / PROD). No se mezclan ambientes en una misma tarjeta.
- [ ] **Versión** afectada (frontend y/o backend).
- [ ] **Pasos para reproducir numerados**, en frío, que otra persona pueda seguir.
- [ ] **Resultado esperado** y **Resultado obtenido** claramente **separados**, más **por qué es un error**. Ver [[bugs-y-defectos]].
- [ ] **Evidencia** adjunta (captura/video/log) — y si el log tiene PHI, redactado.
- [ ] **Gravedad y Prioridad** puestas con criterio (ver [[estimacion-y-priorizacion]]).
- [ ] **Reproducible o con hipótesis**: o se reproduce, o queda anotado que es intermitente/no reproducido y qué se intentó.

---

## DEFINICIÓN DE TERMINADO (DoD)

> **Aterrizaje al proyecto.** Ajustar al stack real del equipo, que se documenta en `cerebro-digital/modulo-ejemplo/arquitectura/esqueleto-proyectos.md`: lenguajes y frameworks de back y de front, gates de seguridad (SAST/SCA) y de calidad de código (cobertura, duplicación, complejidad, code smells), autenticación corporativa, repositorio de código, registry por ambiente, plataforma de despliegue y escalera de ambientes (p. ej. **DESA → TEST → PREPROD → PROD**). Los ítems de abajo nombran los conceptos; los nombres concretos los pone el Cerebro.

### Común a TODO ítem

- [ ] **Todos los Criterios de aceptación / Resultado esperado verificados** (uno por uno), no "en general funciona".
- [ ] **Estado actualizado** en Azure siguiendo el flujo real (por ejemplo New → Active → Design → Review → QA → Closed) y con el **Historial** completado para la validación de QA.
- [ ] **Sin PHI en el resultado**: ni en logs, ni en la tarjeta, ni en capturas de evidencia; datos personales reales redactados.
- [ ] **Documentación mínima** hecha: si cambió comportamiento del sistema, se refleja donde corresponda (documentación de la API, ficha del módulo, o nota funcional). Un cambio que altera el conocimiento del dominio se anota.

### Adicional para HISTORIA / TAREA de desarrollo (backend)

- [ ] **Código en la rama correcta** y con Merge Request abierto contra su destino (por defecto `develop`), un MR por repo (poli-repo).
- [ ] **Respeta la arquitectura del proyecto**: la lógica vive donde debe (el servicio de back con su capa de negocio y datos propia), siguiendo los patrones y convenciones del equipo.
- [ ] **Tests**: unitarios y/o de integración/aprobación según corresponda, en verde.
- [ ] **Compila y levanta** en dev mode sin romper referencias a librerías compartidas ni a la configuración de build común.
- [ ] **Merge Request revisado y aprobado** según la rúbrica de revisión del equipo.
- [ ] **Pasa el análisis de seguridad** (SAST/SCA) cuando aplica: sin flaws nuevos en nuestro código. Los flaws en librerías legacy se escalan/baseline, no bloquean el cierre.
- [ ] **Pasa el gate de calidad de código** cuando aplica: cobertura, duplicación, complejidad y code smells dentro del umbral que fija el pipeline del equipo.
- [ ] **Desplegado y validado en ambiente**: al menos verificado en **<ambientes de prueba>**; el ascenso a PREPROD/PROD sigue el circuito de DevOps. Servicio sano tras el despliegue.
- [ ] **QA lo validó** (pasó por el estado QA con evidencia en el Historial).

### Adicional para FRONTEND

- [ ] Criterios de aceptación verificados en el navegador contra el diseño referenciado, respetando el design system del proyecto (sus componentes y tokens; nunca valores escritos a mano).
- [ ] MR revisado y mergeado a la rama que corresponda; versión reflejada en la etiqueta del frontend.
- [ ] Validado en el ambiente objetivo detrás del inicio de sesión corporativo.

### Adicional para BUG

- [ ] **Causa raíz identificada** y anotada: ¿en qué capa estaba (front, servicio de back, base de datos, integración externa, sistema legacy)?
- [ ] **Corrección verificada reproduciendo los Pasos originales**: el Resultado obtenido ahora coincide con el Resultado esperado.
- [ ] **Sin regresiones** en el flujo afectado.
- [ ] **Validado por QA** en el ambiente donde se reportó (o en el que corresponda tras el fix), con evidencia en el Historial.
- [ ] **Registro técnico** generado si el bug dejó conocimiento útil.

---

## Cómo usar estas listas al redactar un ticket

1. Antes de tomar un ítem para desarrollarlo, pasalo por el **DoR** (Definición de Preparado). Si algo no está tildado, ese es exactamente el texto que falta escribir.
2. Al cerrar, pasalo por el **DoD**. Si algo no está tildado, **no está Terminado**, por más que "ya anda".
3. Cuando la IA reescribe un ticket pobre, debe **apuntar a dejarlo DoR-completo** (o marcar "(pendiente)" lo que el autor todavía tiene que aportar y no se puede inventar).

---

## Ver también

- Historias de usuario e INVEST: [[historias-de-usuario]]
- Criterios de aceptación: [[criterios-aceptacion-gherkin]]
- Estimación, Gravedad y Prioridad: [[estimacion-y-priorizacion]]
- Bugs y defectos: [[bugs-y-defectos]]
