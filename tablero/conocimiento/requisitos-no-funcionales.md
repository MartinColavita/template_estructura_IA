---
id: redaccion-tickets-requisitos-no-funcionales
tipo: guia
estado: F-Draft
modulo: integracion-azure-devops
title: Requisitos no funcionales en un ticket
author: equipo
tags: [rnf, seguridad, phi, rendimiento, disponibilidad, auditoria, usabilidad]
last_updated: 2026-08-26
---

# Requisitos no funcionales en un ticket

Guía para que un ticket contemple —cuando corresponda— seguridad, rendimiento, disponibilidad, auditoría, compatibilidad y usabilidad, con criterios redactados en forma medible. Método agnóstico; los ejemplos concretos van rotulados **Ejemplo (genérico)**.

Un requisito funcional dice **qué hace** el sistema; un requisito no funcional (RNF) dice **con qué calidad lo hace**: qué tan seguro, qué tan rápido, qué tan tolerante a fallos. En un producto donde un usuario atiende en tiempo real, los RNF no son "extras": muchas veces son la parte del ticket que evita un incidente en producción.

**Regla práctica:** no metas RNF de relleno en todos los tickets. Metelos **cuando el cambio los toca**. Una historia que agrega un campo de solo lectura no necesita un criterio de rendimiento; una que llama a una integración externa o muestra datos de la persona, sí.

Cada RNF se redacta como **criterio de aceptación medible**, no como deseo. Mal: "que sea seguro". Bien: "el documento de la persona se enmascara en el log del servicio dejando visibles solo los últimos 3 dígitos".

---

## 1. Seguridad y PHI — la categoría estrella cuando hay datos personales

Un producto que maneja datos de personas maneja **PHI**: la sigla viene de *Protected Health Information* y acá se usa para **cualquier dato personal sensible real** — nombre, documento, identificador, teléfono, dato sensible, motivo de la solicitud. Esta categoría aplica a **casi todo ticket que toque datos de la persona o del registro**.

**Qué preguntarse**
- ¿El cambio muestra, guarda, loguea o transmite datos de la persona (PHI)?
- ¿Qué roles pueden ver o ejecutar esto? ¿El backend valida el rol o solo lo esconde la interfaz?
- ¿Algún dato sensible viaja por la URL (parámetro de consulta o path)?
- ¿Los logs, mensajes de error o notificaciones emergentes (*toasters*) podrían filtrar un dato real?
- ¿La respuesta de error enmascara la causa técnica en lugar de exponer el detalle interno?

**Cómo redactarlo (criterios de ejemplo)**
- "Los datos de la persona (`<documento>`, `<identificador>`, `<dato-sensible>`) **no se escriben en logs** del servicio; si hace falta trazar, se registra el identificador interno del registro, no el dato personal sensible."
- "El endpoint valida el rol en el backend; ocultar el botón en la interfaz **no** alcanza como control de seguridad."
- "Ningún dato de PHI viaja en la URL ni en la cadena de consulta (*query string*); los datos sensibles van en el cuerpo (*body*) de la petición."
- "Ante error interno, el mensaje al usuario es genérico y **no expone** la traza de error (*stack trace*), SQL ni datos de la persona."
- "El acceso a la pantalla/acción queda restringido a los roles `<rol A>` / `<rol B>`; un rol sin permiso recibe 403 y no ve la opción."

> Regla de oro del proyecto: **nunca** pongas datos personales reales en el ticket. Usá marcadores: `<persona>`, `<documento>`, `<identificador>`, `<telefono>`, `<dato-sensible>`. Describí la estructura del dato, no el dato.

> **Aterrizaje al proyecto.** Ajustar al stack real del equipo, que se documenta en `cerebro-digital/modulo-ejemplo/arquitectura/esqueleto-proyectos.md`: cuál es la autenticación corporativa y cómo se valida el rol en el backend (nunca solo en el front). Los gates de seguridad del pipeline (SAST/SCA) atrapan varias de estas fallas (datos en URL, secretos, catch vacío) antes del deploy, pero el criterio de aceptación las deja explícitas para QA.

---

## 2. Rendimiento

El usuario trabaja contra reloj: una operación lenta traba la atención. Pero **no todo tiene que ser instantáneo**: algunas operaciones son lentas por diseño (integraciones externas) y el ticket tiene que decir qué se espera y cómo se le avisa al usuario.

**Qué preguntarse**
- ¿Cuál es el tiempo de respuesta aceptable para esta acción?
- ¿El proceso llama a una integración externa o a un cálculo pesado (normalización de dirección, georreferenciación, mensajería)?
- ¿Corre en primer plano (el usuario espera) o en segundo plano (asíncrono)?
- ¿Qué ve el usuario mientras espera? ¿Puede seguir trabajando?
- ¿Qué pasa si la operación supera su tiempo máximo de espera (*timeout*)?

> **Ejemplo (genérico) — normalización/georreferenciación de dirección:** corre en **segundo plano con timeouts largos** (del orden de dos etapas encadenadas). Es asíncrona a propósito: el operador **no debe quedar bloqueado** esperando a que la dirección se normalice; la solicitud se puede seguir cargando mientras tanto.

**Cómo redactarlo (criterios de ejemplo)**
- "La respuesta del listado `<pantalla>` se muestra en **≤ 2 s** en condiciones normales."
- "La normalización de dirección corre en **segundo plano**; el usuario puede continuar con la carga sin esperar el resultado."
- "Si la operación no responde dentro del *timeout*, el trabajo **no se bloquea**: se guarda el dato tal como fue ingresado y se marca como *pendiente*."
- "La llamada a `<integración externa>` es **asíncrona**; mientras se resuelve, la interfaz muestra un indicador de carga y no congela el resto del formulario."

> Consejo: si no conocés el número exacto de *timeout*/SLA, escribí el criterio con la forma medible y marcá el umbral "(pendiente)" para que lo confirme el equipo, en lugar de omitir el criterio.

---

## 3. Disponibilidad y manejo de errores

En una operación crítica, **el peor error es el que rompe el flujo sin decir por qué**. El sistema depende de capas que pueden caer: el backend propio, un sistema legacy en migración, y las **integraciones externas**. El ticket debe decir cómo se comporta cuando algo de eso falla.

**Qué preguntarse**
- Si el backend o una integración no responde, ¿qué ve el usuario?
- ¿El mensaje de error es claro y accionable, o es un código técnico?
- ¿El fallo **corta el flujo** o se puede seguir con una alternativa/reintento?
- ¿Se puede reintentar sin duplicar el registro?

**Cómo redactarlo (criterios de ejemplo)**
- "Ante caída del backend, el usuario ve un *toaster* claro (`<mensaje sin jerga técnica>`) y **no** una pantalla en blanco ni un 500 crudo."
- "Si `<integración>` no responde, la carga **continúa**: el dato que aportaría esa integración queda pendiente y se puede completar/reintentar después, sin recargar todo."
- "El mensaje distingue entre 'reintentá en unos segundos' (fallo transitorio) y 'contactá a soporte' (fallo persistente)."
- "Un reintento de la acción **no genera un registro duplicado**."

> Estándar típico: los errores se comunican con ***toasters*** (avisos no bloqueantes en pantalla). El criterio debe apuntar a un *toaster* comprensible, no a un código de excepción.

---

## 4. Auditoría y trazabilidad

Un registro puede tener implicancias legales o de auditoría. Muchas acciones deben quedar **registradas en el historial del registro**: quién hizo qué y cuándo.

**Qué preguntarse**
- ¿Esta acción cambia el estado del registro o de la solicitud? ¿Queda registrada?
- ¿Se puede saber **qué usuario** ejecutó la acción y en qué momento?
- ¿Una cancelación, rechazo o reasignación deja rastro de motivo?
- ¿El historial es visible para el rol que lo necesita (supervisor/monitoreo)?

**Cómo redactarlo (criterios de ejemplo)**
- "El cambio de estado queda registrado en el **historial del registro** con usuario, fecha/hora y estado anterior → nuevo."
- "La cancelación/rechazo registra el **motivo** seleccionado y el usuario que la realizó."
- "El historial muestra la acción `<X>` de forma legible para el rol `<supervisor/monitoreo>`."

> Ojo con el nombre: el campo **Historial (System.History)** del work item en Azure DevOps se usa para la validación de QA; no lo confundas con el historial funcional del registro dentro de la aplicación. Ambos importan, pero son cosas distintas.

---

## 5. Compatibilidad

El producto corre en un entorno operativo acotado y conocido. El ticket debe respetar esos límites, sobre todo si toca la interfaz o el manejo de sesiones/solapas.

**Qué preguntarse**
- ¿El cambio funciona en el navegador soportado?
- ¿Afecta el manejo de **solapas simultáneas** o de sesión?
- ¿Interactúa con un canal o integración (telefonía, mensajería, apps externas)?
- ¿Depende de una versión concreta de frontend/backend?

> **Ejemplo (genérico).** El navegador soportado es Chrome; hay un límite de solapas simultáneas por cliente (configurable); interactúa con un sistema de telefonía y uno de mensajería, entre otros canales.

**Cómo redactarlo (criterios de ejemplo)**
- "El comportamiento se verifica en `<navegador soportado>`; no se garantiza en otros navegadores."
- "El cambio respeta el límite de solapas simultáneas; abrir una de más muestra el aviso correspondiente y no rompe la sesión."
- "La integración con `<canal>` sigue funcionando como hoy; el cambio no altera su comportamiento."
- "El cambio es compatible con la versión `<frontend>` / `<backend>` indicada en las Etiquetas."

---

## 6. Accesibilidad y usabilidad (básicas)

No se pide una auditoría WCAG completa, pero sí que la interfaz sea usable bajo presión: el usuario no puede pelear con la pantalla mientras atiende.

**Qué preguntarse**
- ¿La acción principal se alcanza con pocos clics y sin pasos ambiguos?
- ¿Los mensajes (validación, error, éxito) son claros y en español?
- ¿Los campos obligatorios y los errores de validación se señalan de forma visible?
- ¿Se puede operar con teclado en los formularios de carga intensiva?
- ¿El texto y los estados (cargando, deshabilitado, error) se distinguen bien?

**Cómo redactarlo (criterios de ejemplo)**
- "Los mensajes de validación aparecen junto al campo correspondiente, en español y describiendo la corrección esperada."
- "Los campos obligatorios se marcan visualmente; al faltar uno, el foco va al primer campo con error."
- "El botón de la acción principal muestra estado *cargando* mientras se procesa y se **deshabilita** para evitar doble envío."
- "El formulario permite navegar entre campos con teclado (Tab) en el orden lógico de la pantalla."

> **Aterrizaje al proyecto.** Ajustar al stack real del equipo, que se documenta en `cerebro-digital/modulo-ejemplo/arquitectura/esqueleto-proyectos.md`: con qué se construye el front y cuál es su design system. Reusar los componentes y tokens de ese design system, en lugar de estilos ad-hoc (nunca valores escritos a mano), es parte de la usabilidad y la coherencia visual.

---

## Mini-checklist: ¿qué requisitos no funcionales aplican a este ticket?

Marcá los que apliquen; para cada uno marcado, agregá al menos **un criterio de aceptación medible**. Si no aplica, dejalo sin marcar (no inventes RNF de relleno).

- [ ] **Seguridad / PHI** — ¿muestra, guarda, loguea o transmite datos de la persona? ¿valida rol en backend? ¿nada sensible en la URL? *(casi siempre aplica si hay datos de la persona)*
- [ ] **Rendimiento** — ¿llama a integración externa o cálculo pesado? ¿corre en segundo plano? ¿tiempo de respuesta esperado? ¿*timeout*?
- [ ] **Disponibilidad / errores** — ¿qué ve el usuario si cae el backend o una integración? ¿mensaje claro (*toaster*)? ¿no rompe el flujo? ¿reintento sin duplicar?
- [ ] **Auditoría / trazabilidad** — ¿cambia estado del registro/solicitud? ¿queda en el historial con usuario + fecha/hora? ¿motivo en cancelación/rechazo?
- [ ] **Compatibilidad** — ¿navegador soportado? ¿respeta el límite de solapas/sesión? ¿toca un canal/integración? ¿versión frontend/backend?
- [ ] **Accesibilidad / usabilidad** — ¿mensajes claros en español? ¿obligatorios y errores visibles? ¿evita doble envío? ¿operable con teclado? ¿usa el design system del proyecto?

> Si dudás de un umbral (segundos, versión, rol exacto), escribí igual el criterio en forma medible y marcá el valor "(pendiente)" para que lo confirme el equipo. Un criterio con un número a confirmar es infinitamente mejor que un "que ande bien".

---

## Ver también

- Criterios de aceptación (cómo redactarlos): [[criterios-aceptacion-gherkin]]
- Definición de Terminado (los gates entran acá): [[definicion-preparado-terminado]]
- Dominio del proyecto: [[contexto-proyecto]]
