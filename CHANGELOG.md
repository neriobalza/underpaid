# Changelog

Todos los cambios relevantes de Underpaid se documentan en este archivo.
El formato sigue [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
y las versiones numeradas siguen [Semantic Versioning](https://semver.org/).
Las versiones y los hitos se presentan del más reciente al más antiguo; los
cambios pendientes de publicación se registran en `Unreleased`.

## [Unreleased]

### Added

- Guardado persistente de la jornada pausada, incluyendo reloj, puntuación,
  jugadores, salarios, inventario, pedidos, cajas, muebles y eventos pendientes.
- Opción **Continuar partida** en el menú principal, con reasignación de controles
  si los mandos usados al guardar ya no están conectados.
- Persistencia local para recordar que el tutorial fue completado y una opción
  **Tutorial** en el menú para volver a jugarlo.
- Menú principal con el almacén como fondo y un empleado animado que recoge
  productos, prepara cajas en la mesa y las lleva a despacho, bajo un panel
  semitransparente con los botones y la guía de controles.
- Música continua para el menú, el tutorial y las jornadas, además de una pieza
  especial al superar el día con estrellas restantes.
- Nivel Tutorial (Día 0) guiado por diálogos y objetivos secuenciales para
  enseñar movimiento, descarga, empaquetado y despacho sin límite de tiempo.
- Sistema de deducción de salario con avisos flotantes sobre el responsable de
  un pedido erróneo o sobre un jugador al azar cuando un pedido no se entrega.
- Etiqueta roja **NO ENTREGADO** para identificar los pedidos perdidos.
- Consulta de pedidos con Q para el Teclado 1 y Retroceso para el Teclado 2.
- Recuperación ante la desconexión de un mando mediante el regreso a la
  selección de personajes con un mensaje explicativo.
- Soporte simultáneo para dos jugadores de teclado, conservando la
  compatibilidad con mandos.
- Estrategias de jornada y tutorial para controlar la dificultad y la secuencia
  de eventos de cada día.
- Dos entregas de abastecimiento por jornada y varios camiones de despacho con
  horarios y pedidos asignados.
- Pedidos procedurales de dos a cinco productos para cada jugador, con listas
  personales que se consultan con Q en teclado o X en mando.
- Cinco productos identificables: camisas, audífonos, pantalones, teléfonos y
  zapatos.
- Llegada de cajas grandes a las 8 AM con los productos necesarios para todos
  los pedidos, descarga por unidad a sus repisas y eliminación de cajas vacías.
- Cajas pequeñas y medianas como contenedores, puestos para obtener cajas
  vacías y empaquetado por unidad en las mesas de trabajo.
- Transporte de un único producto en mano y devolución a las repisas de todos
  los artículos de un tipo para corregir el contenido de una caja.
- Fin anticipado de la jornada al entregar todos los pedidos y descuento de
  puntos al finalizar por paquetes incorrectos o duplicados.
- Mesas de trabajo de 64 píxeles de ancho por 32 de alto, colocadas cada dos
  espacios, con colisiones y una superficie para preparar pedidos.
- Pausa con `Esc` o Start del mando mediante una pila de estados de Gale,
  con panel semitransparente, reloj detenido y opciones para continuar o salir.
- Repisas en las zonas del almacén definidas por el mapa, dedicadas a un único
  tipo de producto, con control de existencias y apariencia distinta cuando
  están vacías o abastecidas; también bloquean el paso y la colocación de cajas.
- Pruebas automatizadas para el tutorial, los controles, las colisiones y las
  entregas de pedidos.

### Changed

- El botón **Menú principal** de la pausa fue sustituido por **Guardar y salir**;
  los camiones que estaban animándose reintentan únicamente su evento pendiente
  al cargar la partida.
- El selector identifica al Jugador 1 en rojo y al Jugador 2 en azul; el segundo
  jugador utiliza sus sprites propios al caminar y al cargar cajas.
- La estrategia de cada jornada aumenta la dificultad sin reiniciar el mapa:
  cada día añade un pedido por jugador y un camión de despacho respecto al día
  anterior, repartiendo las nuevas órdenes entre todos sus horarios.
- El encabezado del menú principal ahora muestra el lema
  “tlabaja, tiene que tlabajal”.
- **Jugar** inicia el tutorial sólo en la primera partida; después comienza
  directamente en la primera jornada con reloj.
- El panel de pedidos ahora está centrado, agrupa las entregas por camión, las
  ordena por hora de salida y muestra los horarios de despacho.
- El movimiento y las entradas de ambos jugadores ahora usan los eventos y
  comandos lógicos de Gale de forma uniforme.
- La jornada calcula la demanda temprana y tardía para garantizar que los
  productos lleguen antes de su despacho; cada camión de abastecimiento entrega
  cuatro cajas grandes con un margen adicional de productos.
- Aviso de descarga más claro: muestra el producto, la repisa de destino, el
  botón de acción y las unidades restantes, indicando una unidad por pulsación.
- La cuadrícula se muestra en amarillo sólo cuando se pueden descargar productos
  en una repisa; las posiciones de colocación bloqueadas conservan el rojo.
- Las entregas requieren el tamaño de caja y las cantidades exactas de cada
  producto: un pedido correcto suma 100 puntos y un paquete incorrecto resta 50.
- Las cajas pequeñas admiten hasta tres productos y las medianas hasta cinco.
  Consultar pedidos mantiene el reloj corriendo; la pausa sigue deteniéndolo.

### Removed

- Generación de cajas sueltas sin contenido al iniciar cada jornada; ahora
  sólo llegan cajas de abastecimiento con productos para los pedidos.

### Fixed

- La tecla `Esc` vuelve correctamente al menú principal desde la selección de
  personajes, aunque el primer teclado todavía no se haya unido a la partida.
- Los pedidos con productos y cantidades correctos en una caja del tamaño
  equivocado ahora se marcan como entregados, muestran el error de caja sin un
  estado rojo de pedido perdido y descuentan $1 al responsable.
- Repisas superpuestas y asignadas al mismo producto en el mapa: ahora los
  cinco productos tienen su propio espacio de almacenamiento.
- Aparición de personajes en posiciones ocupadas por muebles o cajas.

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
