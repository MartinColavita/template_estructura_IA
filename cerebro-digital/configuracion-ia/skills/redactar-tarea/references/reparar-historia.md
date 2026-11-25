# Reparar una Historia existente

Parte de la skill `redactar-tarea`: se lee cuando hay que cerrar el Gherkin, los *Casos de uso* o los *Datos y estados* de una Historia ya creada que [[auditar-historia]] marcó CON HUECOS (§3.2 de la skill).

### 3.2 Reparar una Historia existente (cuando [[auditar-historia]] la marcó CON HUECOS)

Esta skill es también la que **cierra el Gherkin de una Historia ya creada**. Es un caso de
uso propio, no un efecto colateral: un veredicto que bloquea y **no tiene destinatario**
termina en que alguien inventa los Escenarios para desbloquear — exactamente lo que todo
este aparato viene a impedir.

- Se toma la Historia por su `#ID` (lectura) más el **reporte de la auditoría**, y se
  reescriben **solo** los bloques observados: Criterios de aceptación, *Casos de uso*,
  *Datos y estados*.
- **Lo que la IA no puede saber NO se completa:** una regla que no está en el Cerebro, un
  comportamiento ambiguo o un estado sin nombre salen como **pregunta `⚠`**. Proponer la
  regla que falta para destrabar es el defecto que la auditoría persigue.
- Se entrega pegable; escribirlo en el board es otro turno ([[cargar-a-azure]]). El sello
  anterior queda vencido, porque cambiaron sus Criterios de aceptación; volver a auditarla es
  opcional.
