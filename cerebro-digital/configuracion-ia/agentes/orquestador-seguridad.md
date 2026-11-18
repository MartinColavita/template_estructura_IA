---
name: orquestador-seguridad
description: >
  Orquestador de Seguridad de {{PROYECTO}}. Se usa SÓLO como sesión principal
  (claude --agent orquestador-seguridad): carga la skill puerta seguridad, que es su rol,
  y delega en nucleo-productor y nucleo-verificador. No se usa como subagente: no tiene
  instrucciones propias (el cuerpo vacío es a propósito).
tools: Read, Grep, Glob, Bash, Agent(nucleo-productor, nucleo-verificador), Skill, AskUserQuestion
model: inherit
initialPrompt: /seguridad
---
