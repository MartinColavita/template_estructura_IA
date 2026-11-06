# Playwright — web, Electron y el front de una app con webview

> Referencia de [[automatizar-e2e]]. Lo que es común a toda prueba de aceptación (traza, datos, ambiente)
> está en la skill; acá va lo propio del motor.

## Instalar, por proyecto y con la persona

```bash
npm.cmd init -y                              # si la carpeta qa/<app>-e2e/ todavía no es un paquete
npm.cmd i -D @playwright/test typescript
npx.cmd playwright install                   # descarga los navegadores; con Edge instalado se puede evitar: channel 'msedge'
```

`playwright.config.ts` mínimo, con el ambiente por variable de entorno y el identificador estable que
fija `DEC-003`:

```ts
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:3000',
    testIdAttribute: 'data-testid',        // o 'automation-id': lo que diga DEC-003
    channel: process.env.E2E_CHANNEL,      // 'msedge' usa el Edge instalado y evita la descarga
    trace: 'retain-on-failure',
  },
  timeout: 30_000,
});
```

## Cómo se escribe cada Escenario

- **Buscar como una persona**: `getByRole('button', { name: 'Reservar' })`, `getByLabel`, `getByText`; y
  `getByTestId('lista-reservas')` sólo donde el front expone el identificador estable.
- **Esperar estados, no segundos**: `await expect(locator).toBeVisible()`, `toHaveAttribute('data-estado', 'cancelada')`;
  nunca `waitForTimeout`.
- **Un Escenario, una prueba, un resultado observable** (el `Entonces`). El `Dado` se arma con la
  siembra de datos o con la API de prueba del ambiente, no clicando veinte pantallas.
- **Login una sola vez** por corrida: `storageState` guardado en un `globalSetup`, con las credenciales
  del entorno (`E2E_USUARIO`, `E2E_CLAVE`); el estado guardado **no se versiona**.
- **Objetos de página** en `objetos/`: uno por pantalla, con sus localizadores y acciones con nombre
  de negocio (`reservar()`, `cancelar(id)`); las pruebas leen como el Gherkin.

## Electron

Playwright lo lanza directo: `_electron.launch({ args: ['.'] })` y `app.firstWindow()`; el resto es igual
que web. La traza y la estructura no cambian.

## Escritorio con webview (Tauri, Wails)

Dos capas, con el mismo Gherkin:

1. **El front, en navegador**: se sirve la interfaz con su servidor de desarrollo y se prueba con
   Playwright; las llamadas a la API nativa (`invoke` de Tauri) se **simulan** con un doble que
   responde lo que el contrato dice. Cubre casi todos los Escenarios de pantalla.
2. **Los flujos que tocan el sistema** (archivos, audio, bandeja): con `tauri-driver` por WebDriver
   ([otros-tipos.md](otros-tipos.md)), pocos y lentos.

## Windows con Git Bash

`npx` y `npm test -- …` pueden fallar con *«"C:\Program" no se reconoce»* cuando el PATH tiene espacios:
usar `npm.cmd` / `npx.cmd`, y para un solo test `npx.cmd playwright test -g "<título>"`.

## Lo que frena

| Freno | Por qué |
|---|---|
| Selector por clase de estilo o por posición en el árbol | Se rompe con cada cambio visual; pedir el identificador estable al front |
| `waitForTimeout` | Una prueba que duerme es lenta cuando pasa y frágil cuando falla |
| Un paso que el Gherkin no dice | Es un hueco de la Historia: pregunta, no invento |
| Datos de personas en fixtures o capturas | Quedan en el repositorio para siempre |
