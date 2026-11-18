---
name: orquestador-arquitectura
description: >
  Orquestador de Arquitectura e Infraestructura de {{PROYECTO}}. Se usa SÓLO como sesión principal
  (claude --agent orquestador-arquitectura): carga la skill puerta
  arquitectura-e-infraestructura, que es su rol,
  y delega en nucleo-productor y nucleo-verificador. No se usa como subagente: no tiene
  instrucciones propias (el cuerpo vacío es a propósito).
tools: Read, Grep, Glob, Bash, Agent(nucleo-productor, nucleo-verificador), Skill, AskUserQuestion
model: inherit
initialPrompt: /arquitectura-e-infraestructura
---
