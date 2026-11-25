# Tabla de precedencia

Parte de la skill `desarrollo`: se lee cuando una guía externa o un estándar corporativo y este proyecto dicen cosas distintas (G3), y cuando el equipo la completa.

⚠ **A completar por el equipo** si la organización publica un estándar corporativo. Mientras no
haya estándar externo, gana el proyecto en todo y la tabla queda como molde. Los temas que casi
siempre chocan:

| Tema | El estándar externo dice | Nosotros decimos | Gana |
|---|---|---|---|
| Estructura de paquetes del back | <completar> | **Paquete por módulo de dominio** con 4 capas + `exceptions/` + `shared/` ([[decisiones#DEC-002]]); entre módulos sólo por la `application` del otro | **NOSOTROS** (salvo que el equipo cambie DEC-002) |
| Framework y estructura del front | <completar> | Lo que fije `DEC-003` | ⚠ a decidir |
| Test primero | <completar> | Lo mismo, **más evidencia**: el test tiene que haber fallado **en su aserción**, y lo verifica un agente distinto del que escribió el código | **LOS DOS** (el nuestro es más exigente) |
| Publicar en el repositorio del estándar | <completar> | Nada sale sin un "sí" explícito (G4) | **NOSOTROS** |
| Extensiones/librerías obligatorias, registry interno, dependencias aprobadas, autenticación y roles | <completar> | Si la organización lo define, se toma tal cual | **EL ESTÁNDAR** (si existe) |
| **Design tokens** | <completar> | Design system propio (`diseno/diseno-sistema.md` y `cerebro-mockup-design`); nunca hexadecimales a mano | ⚠ **se pregunta** si hay dos paletas |
| Cobertura mínima | <completar> | ⚠ umbral a definir por el equipo (`DEC-003`) | ⚠ a decidir |
