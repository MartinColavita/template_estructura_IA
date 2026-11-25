# Formato del preview: tag y HTML

Parte de la skill `cargar-a-azure`: se lee cuando se arma el preview (§2), antes de mostrar la Descripción y los Criterios.

- Incluir el **tag temático — uno solo, techo duro** (sin tag de slice, sin tag de
  producto/repo) — y verificar que la **Descripción** Y los **Criterios de aceptación**
  van en **HTML** válido (no markdown crudo). Los Criterios (Gherkin) llevan **todas las
  keywords en negrita** (`Dado`/`Cuando`/`Entonces`/`Y`/`Pero`), pasos sangrados y un
  `<p>` por escenario — si no, se ven como un muro. Esqueleto: [[checklists/mapa-campos-azure]].
