---
name: orquestador-despliegue
description: >
  Orquestador de CI/CD y Despliegue de {{PROYECTO}}. Se usa SÓLO como sesión principal
  (claude --agent orquestador-despliegue): carga la skill puerta despliegue-continuo, que es su rol,
  y delega en nucleo-productor y nucleo-verificador. No se usa como subagente: no tiene
  instrucciones propias (el cuerpo vacío es a propósito).
tools: Read, Grep, Glob, Bash, Agent(nucleo-productor, nucleo-verificador), Skill, AskUserQuestion
model: inherit
initialPrompt: /despliegue-continuo
---
