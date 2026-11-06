# Escritorio, móvil, línea de comandos y API — cuando no hay navegador

> Referencia de [[automatizar-e2e]]. El esqueleto de `bin/armar-e2e.py` con `--motor proceso` o `--motor http`
> es el molde; cada tipo lo adapta como dice abajo. La traza `Historia #<id> · Escenario: <título>` y la
> regla «un Escenario, una prueba» no cambian.

## Escritorio con webview (Tauri, Wails) — los flujos que tocan el sistema

- **`tauri-driver`** expone la app por **WebDriver**; se maneja con el cliente WebDriver del stack
  (`webdriverio` o `selenium`) sobre la ventana real. Sirve para lo que el front en navegador no
  puede probar: diálogos de archivo, permisos de micrófono, bandeja, atajos del sistema.
- Pocas pruebas y lentas: el grueso de los Escenarios de pantalla va por Playwright en navegador
  ([playwright.md](playwright.md)).
- Para una app de grabación de reuniones, por ejemplo: «empieza a grabar y aparece el archivo» va
  por WebDriver; «la lista de reuniones muestra el estado» va por Playwright con la API simulada.

## Escritorio nativo (Windows, macOS, Linux)

- **Windows**: WinAppDriver (WebDriver sobre UI Automation) o `pywinauto`; se busca por **nombre de
  automatización** (`AutomationId`), que es el identificador estable de esta plataforma.
- **macOS**: XCUITest; **Linux**: AT-SPI (`dogtail`).
- El esqueleto `proceso` arranca la aplicación con `subprocess` y la prueba la maneja por el cliente de
  automatización; el `Entonces` se observa en la ventana, en un archivo o en el código de salida.

## Móvil

- **Appium** (WebDriver sobre Android e iOS) o **Maestro** (flujos en YAML, más simples).
- Se busca por **accessibility id**; el front móvil lo expone igual que un `data-testid`.
- Corre contra un emulador o un dispositivo declarado en `DEC-003`; nunca contra la tienda.

## Línea de comandos

- El esqueleto `proceso` corre el ejecutable con `subprocess.run`, con entrada por argumentos o por
  `stdin`, y afirma sobre **código de salida, salida estándar y archivos producidos**.
- Cada Escenario arranca con una carpeta temporal limpia (estado conocido); los archivos de entrada
  salen de `datos/`, sin datos de personas.

## API sin pantalla

- El esqueleto `http` usa `urllib` contra `E2E_BASE_URL`; con un cliente del stack queda igual.
- Cada Escenario: una petición (el `Cuando`), una afirmación sobre estado y cuerpo (el `Entonces`), con
  la siembra previa por la API de prueba del ambiente (el `Dado`).
- Las diferencias contra una versión anterior se miden con `bin/paridad.py`, no a mano.

## Lo que es igual en todos

| Regla | Por qué |
|---|---|
| Traza fija por Escenario | `bin/cobertura-e2e.py` la cuenta; sin traza, el Escenario figura sin prueba |
| Estado conocido al empezar | Una prueba que depende de la anterior falla sola y nadie sabe por qué |
| Esperar estados, no segundos | Igual que en web: lento cuando pasa, frágil cuando falla |
| Sin datos de personas, sin secretos en archivos | Van por variable de entorno; las capturas y los videos también se revisan antes de versionar |
