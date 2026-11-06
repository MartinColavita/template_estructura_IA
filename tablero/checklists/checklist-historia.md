---
id: checklist-historia
tipo: checklist
estado: F-Draft
modulo: integracion-azure-devops
title: "Checklist de calidad — Historias de usuario y Tareas"
author: equipo
tags: [azure-devops, checklist, calidad, historia-de-usuario, tarea, invest, dor]
last_updated: 2026-08-26
---

# Checklist de calidad — Historias de usuario y Tareas

Lista accionable para verificar, antes de pegar en Azure DevOps, que una Historia de usuario o Tarea está bien escrita, es verificable y no arrastra los vicios típicos del tablero. Es agnóstica de dominio; el recuadro final "Ejemplo (genérico)" es solo ilustrativo.

Relacionados: [[historia-de-usuario]] · [[tarea]] · [[habilitador-tecnico]] · [[mapa-campos-azure]]

---

## Cómo usar este checklist

1. Pegá tu historia/tarea POBRE junto con este checklist y el conocimiento de dominio del toolkit.
2. Recorré cada casilla. Todo lo que quede `[ ]` (sin marcar) es un hueco que hay que completar **antes** de crear el work item.
3. Si un dato no lo sabés con certeza, **no lo inventes**: dejá una marca **(pendiente)** visible y una pregunta concreta para el referente funcional/técnico.
4. Antes de pegar en Azure, cruzá con [[mapa-campos-azure]] para saber en qué campo va cada bloque.

> **Regla previa:** primero decidí **qué tipo de work item es**. Si describe una necesidad de un usuario con valor de negocio → **Historia de usuario**. Si es trabajo técnico interno sin cara de usuario (reestructurar un servicio, mover una rama, actualizar una dependencia) → **Tarea** hija de una Historia/Feature. No disfraces una Tarea técnica de Historia (es el error número 1 de los tableros reales).

---

## 1. Título

- [ ] Empieza con el **prefijo de módulo/dominio** cuando aplica.
- [ ] Es una **frase corta y específica** que se entiende sin abrir la tarjeta (no "Ajustes varios", no "Pantalla de login" a secas).
- [ ] **Sin typos** ni abreviaturas caseras. Prefijo de módulo **consistente** con el resto del tablero.
- [ ] Para Historia: describe **la capacidad**, no la solución técnica.
- [ ] Para Tarea técnica: describe **la acción concreta** (p.ej. "ms-reservas - Reestructurar a estructura api+impl y mover rama develop").

## 2. Rol / necesidad / beneficio (Historia) o alcance técnico (Tarea)

- [ ] **Historia**: tiene la forma **"Como `<rol>`, quiero `<necesidad>`, para `<beneficio>`"** con un rol REAL del sistema (operador, supervisor, administrador, usuario final...), no "como usuario" genérico.
- [ ] El **beneficio** es un valor real (reduce tiempo, evita error, cumple un requisito), no relleno.
- [ ] **Tarea técnica**: en lugar de rol/beneficio, tiene **objetivo técnico + motivo** ("para homogenizar la estructura según el plan de migración", "porque el servicio expone un endpoint nuevo").

## 3. Contexto y problema

- [ ] Explica **el estado actual** y **por qué** se necesita el cambio (qué duele hoy, qué falta, qué está mal).
- [ ] Menciona el **origen** si lo tiene: número de bug relacionado, spec funcional, decisión de arquitectura, pedido del negocio.
- [ ] Si venía como "un link y nada más" (Figma, GitLab), el **alcance está escrito en prosa**: el link es apoyo, no el contenido.

## 4. Alcance y fuera de alcance

- [ ] Está claro **qué entra** (pantallas, endpoints, servicios, estados, canales afectados).
- [ ] Está claro **qué NO entra** (fuera de alcance explícito) para evitar que crezca sola.
- [ ] Identifica el/los **módulos** y **servicios/componentes** tocados.
- [ ] Aclara la **capa**: frontend (el stack de front documentado en el Cerebro), backend (los servicios de back con su lógica y base de datos propia), integración o infra.

## 5. Reglas de negocio

- [ ] Lista las **reglas de negocio** que aplican, con el vocabulario del dominio.
- [ ] Cada regla está **numerada `[RN-<TEMA>-NN]`** para poder referenciarla en los criterios (ver [[organizacion-y-trazabilidad]] §4).
- [ ] Cada `[RN-…]` indica su **referencia al OKF** (ruta#ancla del Cerebro Digital) para poder consultarla — enlazar, no copiar.
- [ ] Cubre **casos de excepción** y validaciones (qué pasa si falta un dato, si el registro no existe, si el estado no aplica, permisos por rol).
- [ ] No contradice las specs; si hay desvío observado, se anota **(pendiente) spec dice X / observado Y**.

## 6. Criterios de aceptación (Gherkin en español, verificables)

- [ ] Existen criterios de aceptación (**no vacíos** — es el vicio número 1 del tablero).
- [ ] Están en **Gherkin en español**: `Característica`, `Antecedentes`, `Escenario` / `Esquema del escenario` + `Ejemplos`, y los pasos `Dado` / `Cuando` / `Entonces` / `Y` / `Pero`. **Cero** Given/When/Then/Feature/Scenario.
- [ ] Cada escenario es **verificable objetivamente** (QA puede decir "pasa/no pasa" sin interpretar).
- [ ] Cubren: **camino feliz**, **casos borde** y al menos un **caso de error/negativo**.
- [ ] Los datos de ejemplo usan **marcadores** (`<persona>`, `<documento>`, `<identificador>`, `<dato-sensible>`), nunca PHI real.
- [ ] Cada escenario **referencia la regla que verifica** (`[RN-<TEMA>-NN]` en el nombre o como comentario).
- [ ] Definen implícita o explícitamente el **"Hecho" (DoD)**: cuándo la historia se considera terminada.

Ejemplo de forma correcta (dominio genérico):

```gherkin
Característica: Visualización del estado de una solicitud

  Antecedentes:
    Dado que soy un operador con una solicitud abierta
    Y la solicitud es de tipo <tipo>

  Escenario: La solicitud avanza de estado
    Cuando el sistema registra el avance
    Entonces el detalle muestra el estado nuevo con su fecha y hora
    Y el estado aparece en la línea de tiempo de la solicitud

  Escenario: El avance no aplica a un tipo sin ese paso
    Dado que la solicitud es de tipo <otro-tipo>
    Cuando consulto el detalle
    Entonces ese estado no se ofrece como transición posible
```

## 6b. Casos de uso (alcance de pruebas)

- [ ] Existe el bloque **Casos de uso** que delimita el **alcance de las pruebas** (no son los Criterios: son el inventario de flujos a cubrir por Testing).
- [ ] Cubre **camino feliz + alternativos + borde/negativos + permisos por rol**.
- [ ] Cada caso se **mapea a un `[RN-…]`** y se cubre con **≥1 escenario Gherkin** de la sección 6.

## 6c. Datos y estados (funcional)

- [ ] Si la historia toca datos o estados, existe el bloque **Datos y estados**: **campos/datos** (obligatorio/catálogo/default/formato, con su `[RN-…]`) y **estados y transiciones** (permitidas/bloqueadas).
- [ ] Es **funcional, no técnico**: nombres de negocio y catálogos, **no** tipos/columnas/endpoints (eso va en la Tarea — Contrato técnico).

## 7. Dependencias

- [ ] Lista **dependencias** con otras historias/tareas, otros servicios, integraciones externas, infra, o equipos.
- [ ] Indica **bloqueos** (qué tiene que estar listo antes) y **enlace Primario/Parent** si es Tarea hija de una Historia/Feature.
- [ ] Aclara si requiere cambios coordinados **cross-repo** (poly-repo: un commit por repo).

## 8. Estimación

- [ ] Tiene **Puntos de historia (Story Points)** en Historia, o **Esfuerzo original en horas** en Tarea (no vacío).
- [ ] La estimación es **coherente** con el alcance (una historia vaga no puede estar bien estimada: primero se define, después se estima).
- [ ] Si no se puede estimar todavía por falta de definición, se marca **(pendiente)** y se dice qué falta.

## 9. Prioridad

- [ ] Tiene **Prioridad (1–4)** asignada y coherente con el impacto operativo.
- [ ] Si aplica, tiene **Riesgo** y **Área de valor** (Business / Architectural — las reestructuraciones suelen ser Architectural).

## 10. INVEST

- [ ] **I**ndependiente: se puede trabajar sin depender de otra a medio hacer (o la dependencia está declarada).
- [ ] **N**egociable: describe el **qué/por qué**, deja margen al **cómo**.
- [ ] **V**aliosa: aporta valor visible a un rol o a la iniciativa técnica.
- [ ] **E**stimable: hay suficiente definición para ponerle puntos.
- [ ] **S**mall (pequeña): entra en un sprint; si es un monstruo, se parte.
- [ ] **T**esteable: tiene criterios de aceptación verificables (ver sección 6).

## 11. DoR — Definición de Preparado (Definition of Ready)

- [ ] Título, rol/necesidad/beneficio (o alcance técnico), contexto y criterios de aceptación **completos**.
- [ ] Dependencias identificadas y no bloqueantes (o el bloqueo está declarado).
- [ ] Estimada y priorizada.
- [ ] Sin ambigüedades abiertas críticas (las dudas menores están marcadas con **(pendiente)**).
- [ ] El equipo entendería qué hacer **sin** preguntar al autor.

## 12. Idioma y PHI (reglas de oro — no negociables)

- [ ] **Todo en español (Argentina).** Cero inglés en prosa, títulos, viñetas o Gherkin. Siglas técnicas (INVEST, DoR, DoD, Gherkin) van como nombre propio con explicación en español al lado.
- [ ] **Sin PHI**: ningún dato personal sensible/personal real (persona, documento, teléfono, identificador, dato sensible del dominio, nombre). Solo marcadores `<...>` y descripción de estructura.

## 13. Organización y trazabilidad (tags · relaciones · documento fuente)

- [ ] **Etiqueta temática** presente (`<tema>`, **sin prefijo**) y escrita **igual** que en el resto de los tickets del mismo tema (ver [[organizacion-y-trazabilidad]] §1).
- [ ] Bloque **Relaciones / Enlaces**: **Parent** (Feature/Épica madre) y **Related** (otras UH del mismo tema) propuestos; los `#ID` reales marcados `⚠` a confirmar o resueltos por MCP.
- [ ] **Documento fuente** enlazado como **ruta/link** (no se copió el contenido).
- [ ] Reglas numeradas `[RN-…]` y referenciadas en los criterios (ver secciones 5 y 6).

---

## Veredicto rápido

> Si **todas** las casillas de las secciones 6 (criterios), 10 (INVEST), 11 (DoR) y 12 (idioma/PHI) están marcadas, la historia está lista para Azure. Si **cualquiera** de esas queda vacía, **no la crees todavía**: es exactamente uno de los vicios que este toolkit viene a eliminar.

---

## Ejemplo (genérico)

> Recuadro ilustrativo. El vocabulario de dominio que un checklist de sección 5 esperaría ver, con placeholders neutros: tipos de registro (`<tipo>`), clasificaciones (`<clasificacion>`), estados del ciclo de vida (Estado1→Estado2→…→cierre), unidades/sedes (`<unidad>`), canales (`<canal>`). En cada proyecto, cambiá estos placeholders por el vocabulario del dominio propio.
