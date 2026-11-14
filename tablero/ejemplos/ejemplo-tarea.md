---
id: ejemplo-tarea
tipo: ejemplo
estado: F-Draft
modulo: integracion-azure-devops
title: "Ejemplo — de tarea pobre a tarea profesional"
author: equipo
tags: [azure-devops, ejemplo, tarea, antes-despues]
last_updated: 2026-08-26
---

# Ejemplo: de tarea pobre a tarea profesional

*Muestra la transformación completa (ANTES → DESPUÉS) de una Tarea cuya descripción es solo un link de Figma, para que la IA aprenda a escribir el alcance real, subtareas, entregable y Definición de terminado; caso inspirado en tarjetas reales del tablero (parafraseado, sin datos reales).*

---

## Contexto del caso

En el tablero aparece una **Tarea** titulada *"Pantalla de inicio de sesión"* cuya única descripción es un enlace de Figma con la nota *"Adjunto el link de Figma que contiene las tareas a realizar"*. Es el patrón clásico de "el diseño lo dice todo": nadie escribió el alcance, así que cada quien interpreta lo que ve y el resultado depende de la memoria de quien la agarre.

---

## ANTES (tal cual está hoy)

> **Tipo:** Tarea
> **Título:** Pantalla de inicio de sesión
>
> **Descripción:**
> Adjunto el link de Figma que contiene las tareas a realizar.
> https://www.figma.com/file/XXXX/Login
>
> **Esfuerzo original:** *(vacío)*
> **Actividad:** *(vacío)*
> **Enlace a Historia padre:** *(ninguno)*

---

## Qué le falta (diagnóstico)

- **Alcance = un link.** El Figma **acompaña**, no reemplaza. La tarjeta no dice qué hay que construir, con qué tecnología, ni qué estados de la pantalla entran (campos, validaciones, error de login, "recordarme", etc.).
- **No dice que el login es federado (inicio de sesión corporativo).** El inicio de sesión no es un formulario de usuario/clave propio: la autenticación la hace el proveedor de identidad de la organización. Sin aclararlo, se puede construir algo que no va.
- **Sin subtareas ni entregable claro.** No se sabe si el "hecho" es maquetar, integrar el inicio de sesión federado, o ambos; no hay forma de cortar el trabajo ni de estimarlo (`Esfuerzo original` y `Actividad` vacíos).
- **Sin Historia padre.** Queda huérfana, sin trazabilidad al valor que persigue.
- **⚠ PHI y credenciales:** una pantalla de login toca datos sensibles; hay que dejar por escrito que en pruebas y capturas no se usan credenciales reales.

---

## DESPUÉS (reescrito como corresponde)

### Campo: Título

```
[Login] Implementar la pantalla de inicio de sesión (front) integrada con el inicio de sesión corporativo federado
```

*(Prefijo de módulo consistente, sin typos, y aclara capa e integración desde el título.)*

### Campo: Descripción (HTML enriquecido)

**Objetivo.** Construir la pantalla de inicio de sesión del sistema (la aplicación de front) según el diseño de Figma referenciado, integrada con la **autenticación federada corporativa** (no es un login de usuario/clave propio del sistema).

**Alcance escrito (lo que entra en esta tarea):**
- Maquetar la pantalla según el Figma: layout, logo, textos, botón de ingreso, estados visuales (normal, cargando, error).
- Disparar el flujo de autenticación federada contra el proveedor de identidad al presionar "Ingresar" y manejar el retorno (callback) con el token.
- Estado de **error de autenticación**: mensaje claro cuando el proveedor de identidad rechaza el ingreso, sin exponer detalles técnicos.
- Estado de **sesión expirada / sin sesión**: redirigir al inicio de sesión.
- Responsivo según los breakpoints del diseño; textos en español.
- Accesibilidad mínima: campos y botón navegables por teclado, foco visible.

**Fuera de alcance (para evitar el "yo pensé que también…"):**
- Alta/recuperación de usuario o cambio de contraseña (lo gestiona el proveedor de identidad, no el sistema).
- Permisos por rol una vez adentro (es de otra historia/tarea).

**Diseño de apoyo (referencia, no alcance):**
- Figma: `https://www.figma.com/file/XXXX/Login` — pantalla *Login* y sus estados (normal / cargando / error).

**⚠ Datos a confirmar:**
- ⚠ El detalle del flujo de autenticación (parámetros, direcciones del proveedor de identidad, renovación del token) · recomendación: tomarlo de la documentación de autenticación del proyecto (`<doc-autenticacion>`), sin inventar la configuración · lo define quien administra la autenticación. La subtarea de integración depende de esto.
- ⚠ El Esfuerzo original · recomendación: estimarlo en el planning, por partes (maquetado e integración) · mientras
  tanto el campo va en `0`, no vacío.
- ⚠ La Historia padre · recomendación: enlazar la del acceso al sistema; si no existe, crearla antes o escribir acá el
  objetivo funcional · lo confirma quien arma el backlog.
- ⚠ El sprint · recomendación: el que fije el planning · lo define el planning.

### Subtareas (checklist de trabajo)

- [ ] Maquetar la pantalla de login según Figma (estructura + estilos + responsive).
- [ ] Integrar el disparo del flujo de autenticación federada y el manejo del callback/token.
- [ ] Implementar el estado de error de autenticación con mensaje en español.
- [ ] Manejar redirección por sesión expirada / sin sesión.
- [ ] Revisión de accesibilidad básica (teclado + foco visible).
- [ ] Pruebas manuales del flujo completo en el ambiente objetivo detrás del inicio de sesión corporativo.

### Entregable

La pantalla de inicio de sesión funcionando en el ambiente objetivo: el operador llega a la aplicación, es redirigido al proveedor de identidad, se autentica y vuelve autenticado; ante credenciales inválidas ve un error claro. Código en la rama correspondiente del repo frontend (`<repo-frontend>`), con Merge Request abierto.

### Definición de terminado (DoD) de esta tarea

- [ ] La pantalla coincide con el Figma referenciado en sus estados (normal / cargando / error).
- [ ] El flujo de autenticación federada funciona de punta a punta en <ambientes de prueba> (ingreso exitoso y rechazo).
- [ ] Mensajes y textos en español; sin cadenas en inglés en la interfaz.
- [ ] Merge Request revisado y mergeado a la rama que corresponda.
- [ ] **Sin PHI ni credenciales reales** en el código, logs, pruebas ni capturas de evidencia: se usan usuarios de prueba del ambiente y marcadores (`<usuario>`, `<identificador>`), nunca valores reales.
- [ ] Validado en el navegador contra el diseño en el ambiente objetivo.

### Campo: Actividad

`Development` — (las subtareas de prueba manual pueden registrarse como `Testing` si el equipo separa tareas por actividad).

### Campo: Esfuerzo original

`0` hasta que el equipo la estime en horas (por ejemplo, maquetado ~X h + integración de la autenticación ~Y h); la pregunta está en «⚠ Datos a confirmar». No se completa a ojo.

### Campo: Prioridad

`2` — Alta. El login es puerta de entrada al sistema; bloquea validar cualquier otra pantalla en el ambiente.

### Campo: Enlace a Historia padre

Enlace **Primario/Parent** a la Historia de usuario del alta de acceso/login del sistema (⚠ declarado en «Datos a confirmar»: una tarea no debería quedar huérfana).

### Campo: Etiquetas

`login` (una sola etiqueta temática)

### Campo: Ruta de iteración

`<Proyecto>\<Equipo> - Sprint NN` (⚠ declarado en «Datos a confirmar»).

---

## Mapeo a campos de Azure DevOps

| Campo visible (español) | Referencia interna | Qué se cargó |
|---|---|---|
| Título | `System.Title` | `[Login] Implementar la pantalla de inicio de sesión (front) integrada con el inicio de sesión corporativo federado` |
| Descripción | `System.Description` (HTML) | Objetivo + alcance escrito + fuera de alcance + Figma como apoyo + subtareas + entregable + DoD |
| Actividad | `Microsoft.VSTS.Common.Activity` | `Development` |
| Esfuerzo original | `Microsoft.VSTS.Scheduling.OriginalEstimate` | `0` (⚠ declarado) |
| Prioridad | `Microsoft.VSTS.Common.Priority` | `2` (Alta) |
| Enlace Primario/Parent | `System.LinkTypes.Hierarchy-Reverse` | Historia padre del acceso/login ⚠ |
| Etiquetas | `System.Tags` | `login` |
| Ruta de iteración | `System.IterationPath` | `<Proyecto>\<Equipo> - Sprint NN` ⚠ |

---

## Qué aprender de este ejemplo

1. **El Figma se cita como apoyo; el alcance se escribe.** La IA debe convertir "el diseño lo dice todo" en un alcance textual con estados, fuera de alcance y entregable.
2. **Contexto de dominio que cambia el trabajo:** el login del sistema es **federado (proveedor de identidad corporativo)**, no usuario/clave propio. Nombrarlo evita construir lo que no va.
3. **Subtareas + Definición de terminado hacen la tarea estimable y cerrable.** Sin ellas, "hecho" es una opinión.
4. **PHI y credenciales:** toda tarjeta que roce datos sensibles deja por escrito que en pruebas/capturas se usan marcadores y usuarios de prueba, nunca valores reales.
5. **Lo desconocido se marca con ⚠** (config exacta de la autenticación, versión de frontend, esfuerzo, sprint, historia padre), no se inventa.

Ver también: [[definicion-preparado-terminado]] · [[ejemplo-habilitador]].
