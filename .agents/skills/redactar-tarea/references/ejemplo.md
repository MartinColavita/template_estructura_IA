# Ejemplo de redacción (genérico)

Parte de la skill `redactar-tarea`: se lee cuando hace falta ver cómo queda un ticket pobre convertido en uno pegable.

---

### Ejemplo (genérico)

> Entrada pobre en el tablero: *"Un listado tira error,
> ver adjunto"*. La skill clasifica como **Bug**, y redacta:
> **Esperado:** al abrir un listado se muestran los resultados del filtro.
> **Obtenido:** error técnico 500 al aplicar el filtro por `<documento>`.
> **Por qué / pasos:** 1) entrar al listado; 2) filtrar por documento;
> 3) se corta con 500. Ambiente TEST, versión FE_x.y.z. Gravedad `2-High`.
> ⚠ pendiente: ¿el error es con cualquier documento o solo con uno puntual?
>
> Los datos reales de la persona se enmascaran con `<documento>` (PHI). El ticket queda
> pegable en los campos del board (*Pasos para reproducir*, *Gravedad*), sin tocar
> Azure hasta que el humano confirme.
