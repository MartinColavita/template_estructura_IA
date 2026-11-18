---
name: orquestador-operacion
description: >
  Orquestador de Operación de Servidores de {{PROYECTO}}. Se usa SÓLO como sesión principal
  (claude --agent orquestador-operacion): carga la skill puerta operacion-de-servidores, que es su rol,
  y delega en nucleo-productor y nucleo-verificador. No se usa como subagente: no tiene
  instrucciones propias (el cuerpo vacío es a propósito).
tools: Read, Grep, Glob, Bash, Agent(nucleo-productor, nucleo-verificador), Skill, AskUserQuestion
model: inherit
initialPrompt: /operacion-de-servidores
---
