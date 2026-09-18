# Changelog

Los cambios relevantes de Underpaid se documentan en este archivo.
El formato sigue [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
El proyecto todavía no tiene versiones publicadas; los hitos históricos se
registran con su fecha y los cambios pendientes de publicación en `Unreleased`.

## [Unreleased]

### Added

- Panel de pedidos unificado y centrado que pausa el juego para ambos jugadores al abrirse, e incluye los horarios exactos de llegada de los camiones de despacho.
- Lógica de la jornada reestructurada para analizar la demanda temprana y tardía, garantizando de forma matemática que los productos siempre sean entregados al almacén antes del horario exigido.
- La cantidad de cajas grandes por entrega de abastecimiento se fijó exactamente a 4 por cada camión (8 en total por jornada).

- Patrón Strategy (`DaySchedule`) para controlar los tiempos de llegada y salida de los camiones, agregando un 30% de margen a los productos necesarios y distribuyéndolos en cajas de hasta 10 elementos.
- Llegada de camiones de entrega dividida en 2 lotes durante la jornada (inicio y mitad del día).
- Múltiples camiones de despacho que llegan en intervalos, recogiendo paquetes específicos usando `truck_id`.
- Interfaz gráfica (`OrdersPanel`) actualizada para indicar el camión correspondiente a cada pedido.
- Animación de texto flotante que aparece sobre el último jugador que transportó una caja cuando se envía incorrectamente, restando 5 centavos de su salario base (200¢).

- Pedidos procedurales de dos a cinco productos para cada jugador, con listas
  personales que se consultan con Q en teclado o X en mando.
- Cinco productos identificables: camisas, audífonos, pantalones, teléfonos y zapatos.
- Llegada de cajas grandes a las 8 AM con los productos necesarios para todos
  los pedidos, descarga por unidad a sus repisas y eliminación de cajas vacías.
- Cajas pequeñas y medianas como contenedores, puestos para obtener cajas
  vacías y empaquetado por unidad en las mesas de trabajo.
- Transporte de un único producto en mano y devolución a las repisas de todos
  los artículos de un tipo para corregir el contenido de una caja.
- Fin anticipado de la jornada al entregar todos los pedidos y descuento de
  puntos al finalizar por paquetes incorrectos o duplicados.
- Mesas de trabajo de 64 píxeles de ancho por 32 de alto con el sprite completo
  `table.png`, una por cada pareja de espacios de la capa `table` del mapa,
  con colisiones y una superficie para preparar pedidos.
- Pausa con `Esc` o Start del mando mediante una pila de estados de Gale,
  con panel semitransparente y botones para continuar o volver al menú principal.
- Reloj, personajes y diálogos detenidos durante la pausa, conservando la
  jornada al continuar y limpiando las entradas pendientes.
- Repisas en las zonas del almacén definidas por el mapa, dedicadas a un único
  tipo de producto y con control de existencias.
- Apariencia de repisa vacía o abastecida según su contenido, con bloqueo del
  paso de personajes y de la colocación de cajas sobre ella.

### Removed

- Generación de cajas sueltas sin contenido al iniciar cada jornada; ahora
  sólo llegan cajas de abastecimiento con productos para los pedidos.

### Changed

- Aviso de descarga más claro: muestra el producto, la repisa de destino, el
  botón de acción y las unidades restantes, indicando una unidad por pulsación.
- La cuadrícula se muestra en amarillo sólo cuando se pueden descargar productos
  en una repisa; las posiciones de colocación bloqueadas conservan el rojo.
- Las entregas requieren el tamaño de caja y las cantidades exactas de cada
  producto: un pedido correcto suma 100 puntos y un paquete incorrecto resta 50.
- Las cajas pequeñas admiten hasta tres productos y las medianas hasta cinco.
  Consultar pedidos mantiene el reloj corriendo; la pausa sigue deteniéndolo.

### Fixed

- Repisas superpuestas y asignadas al mismo producto en el mapa: ahora los
  cinco productos tienen su propio espacio de almacenamiento.
- Aparición de personajes en posiciones ocupadas por muebles o cajas.
- Pruebas de colisiones y entregas adaptadas al suelo actual y a los paquetes con contenido.

## [0.2.0] - 2026-09-17

### Added

- Sistema de cuadros de diálogo flotantes interactivos con retratos animados, voces procedurales estilo 8-bits y un evento matutino del jefe.

## [0.1.0] - 2026-09-17

### Added

- Colisiones entre personajes usando el collider de 32 × 32 de la mitad
  inferior del cuerpo, con deslizamiento por eje y bloqueo durante la carga de cajas.
- Zonas visuales dedicadas en el suelo del almacén: área gris para recepción de paquetes y área amarilla para despachos.
- Nuevo mapa estructural del almacén con soporte para paredes físicas.
- Tres tipos de cajas: grandes de recepción (64 × 64), medianas para pedidos
  (32 × 32) y pequeñas para pedidos (16 × 16), con sprites locales para cada tipo.
- Dos cajas grandes, una mediana y una pequeña al iniciar cada jornada.
- Resumen de jornada como quinta escena de Gale, con continuación mientras queden estrellas.
- Zona de despacho para los objetos actuales, puntuación acumulada sin límite de jornadas
  y derrota al perder las cinco estrellas. Cada jornada incompleta resta una estrella.
- Validación de fuentes de entrada y de los dos personajes requeridos para iniciar una partida.
- Pruebas de despacho, derrota, continuidad entre jornadas, conexiones SDL y limpieza al cerrar.
- Este historial de cambios y documentación de la integración con Gale.

### Changed

- La delimitación del área de juego ahora usa obstáculos físicos (paredes) en lugar de una barrera invisible en los bordes de la pantalla.
- Cargar una caja grande reduce la velocidad a la mitad y una mediana a dos
  tercios; las pequeñas conservan la velocidad normal. Colocarla restaura la
  velocidad, tanto con teclado como con mando y en movimiento diagonal.
- Las cajas medianas usan `medium_box.png` y las pequeñas `small_box.png`;
  las grandes conservan `big_box.png`. Cada imagen se carga y escala una sola vez.
- Las cajas sustituyen las vasijas; colisión y vista previa de colocación usan
  el tamaño de cada tipo. Sólo las cajas medianas y pequeñas cuentan en despacho.
- Movimiento del teclado mediante `gale.command.CommandBindings` y comandos reutilizables,
  siguiendo el patrón del proyecto de referencia `06-princess`.
- La interacción con objetos se procesa en el personaje y la escena resuelve sus efectos.
- `ControllerManager` inicializa los mandos con `InputHandler.init_gamepads()` y mantiene
  las referencias de Gale junto con los controladores SDL.
- Al terminar el reloj se muestra el resultado de la jornada en lugar de regresar directamente al menú.

### Fixed

- La colocación comprueba todos los tiles de pared que ocupa una caja,
  bloqueando la segunda fila de la pared superior y cualquier solapamiento
  parcial. La vista previa muestra esas posiciones en rojo.
- El movimiento conserva las coordenadas decimales al consultar las paredes de Gale,
  evitando desplazamientos por redondeo al detenerse. El eje vertical se calcula
  después de resolver el horizontal contra cajas y personajes.
- Las cajas pequeñas se colocan en una cuadrícula de 16 × 16, permitiendo
  cuatro por tile de 32 × 32. La vista previa y la colisión respetan cada
  subcasilla y rechazan las posiciones ocupadas.
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
