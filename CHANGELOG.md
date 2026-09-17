# Changelog

Los cambios relevantes de Underpaid se documentan en este archivo.
El formato sigue [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
El proyecto todavía no tiene versiones publicadas; los hitos históricos se
registran con su fecha y los cambios pendientes de publicación en `Unreleased`.

## [Unreleased]

### Added

- Tres tipos de cajas: grandes de recepción (64 × 64), medianas para pedidos
  (32 × 32) y pequeñas para pedidos (16 × 16), con el sprite local `big_box.png`.
- Dos cajas grandes, una mediana y una pequeña al iniciar cada jornada.
- Resumen de jornada como quinta escena de Gale, con continuación mientras queden estrellas.
- Zona de despacho para los objetos actuales, puntuación acumulada sin límite de jornadas
  y derrota al perder las cinco estrellas. Cada jornada incompleta resta una estrella.
- Validación de fuentes de entrada y de los dos personajes requeridos para iniciar una partida.
- Pruebas de despacho, derrota, continuidad entre jornadas, conexiones SDL y limpieza al cerrar.
- Este historial de cambios y documentación de la integración con Gale.

### Changed

- Las cajas sustituyen las vasijas; colisión y vista previa de colocación usan
  el tamaño de cada tipo. Sólo las cajas medianas y pequeñas cuentan en despacho.
- Movimiento del teclado mediante `gale.command.CommandBindings` y comandos reutilizables,
  siguiendo el patrón del proyecto de referencia `06-princess`.
- La interacción con objetos se procesa en el personaje y la escena resuelve sus efectos.
- `ControllerManager` inicializa los mandos con `InputHandler.init_gamepads()` y mantiene
  las referencias de Gale junto con los controladores SDL.
- Al terminar el reloj se muestra el resultado de la jornada en lugar de regresar directamente al menú.

### Fixed

- Cerrar la ventana o elegir Salir cancela el reloj, libera los objetos cargados,
  cierra los dispositivos y desregistra el juego de `InputHandler`.
- La limpieza tolera dispositivos desconectados o ya cerrados y puede repetirse.
- Un fallo de inicialización desregistra el listener de Gale y libera Pygame;
  el punto de entrada informa los errores de SDL, archivos o configuración.
- Instrucciones de ejecución actualizadas para la raíz del proyecto independiente.

## Hito: proyecto independiente - 2026-09-17

Este hito corresponde al estado importado en el commit `65d2654`; no representa
una versión publicada. No se dispone del historial anterior en este repositorio.

### Added

- Juego independiente con Pygame y Gale, recursos locales y dependencias propias.
- Menú principal, configuración, selección de dos jugadores y escena de juego.
- Controles exclusivos por personaje con dos mandos o un mando y teclado,
  selección de lado y recuperación tras desconexión.
- Sala con paredes, colisiones, personajes animados y objetos levantables y colocables.
- Reloj de jornada de ocho minutos mediante `gale.timer.Timer.tween`.
- Base de 50 pruebas de regresión con entradas de teclado y mandos simulados.
