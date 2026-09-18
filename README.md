# Underpaid

Base de videojuego con Gale y Pygame: menú principal, configuración de
pantalla, selección de dos jugadores con mandos o mando y teclado, y movimiento independiente.
Usa dependencias propias del proyecto y la fuente incluida en Pygame.

## Ejecutar

Desde la raíz del repositorio, con el entorno virtual activado:

```bash
python -m pip install -r requirements.txt
python main.py
```

## Pantalla

La resolución virtual permanece en **640 × 480**. Gale escala el contenido a
la resolución de ventana elegida, conservando la proporción **4:3**:

| Índice | Resolución de ventana |
|--------|-----------------------|
| 0 | 640 × 480 |
| 1 | 960 × 720 |
| 2 | 1280 × 960 |
| 3 | 1920 × 1440 |

Edita `DEFAULT_RESOLUTION_INDEX` en `settings.py` para elegir la resolución
al iniciar. Durante la ejecución, abre **Configuración**, selecciona una
resolución y pulsa **Aplicar**. Los cambios del menú duran durante esa sesión;
volver sin aplicar descarta la selección pendiente.

Para jugar en pantalla completa, cambia **Modo** a **Pantalla completa** y
pulsa **Aplicar**. Para regresar a la ventana, selecciona **Ventana** y aplica.
La pantalla completa utiliza el tamaño del escritorio y mantiene el contenido
en 4:3, con bandas negras cuando la proporción del monitor es distinta.
La resolución de ventana seleccionada se conserva para cuando vuelvas a ese modo.
Puedes iniciar en pantalla completa configurando `FULLSCREEN = True` en `settings.py`.

## Controles

- Flechas arriba/abajo o W/S: seleccionar una opción.
- Enter o Espacio: activar la opción seleccionada.
- Flechas izquierda/derecha o A/D: cambiar la resolución o el modo seleccionado.
- Ratón: seleccionar y activar opciones; pulsar la resolución recorre la lista.
- Esc: volver al menú desde configuración o desde la partida.
- Salir: cerrar el juego desde el menú principal.

## Archivos principales

- `main.py`: punto de entrada.
- `settings.py`: resolución inicial, pantalla virtual, controles y colores.
- `src/Underpaid.py`: juego, máquina de estados y cambio de ventana.
- `src/gui/Menu.py`: menú compartido por las pantallas.
- `src/states/game/MainMenuState.py`: menú principal.
- `src/states/game/SettingsState.py`: configuración de resolución.
- `src/states/game/PlayerSelectState.py`: entrada con A y elección exclusiva de lado.
- `src/states/game/PlayState.py`: movimiento independiente de los dos jugadores.
- `src/entity/Player.py`: personaje y vínculo exclusivo con su mando o teclado.
- `src/input/ControllerManager.py`: inicialización de mandos y detección de conexiones.
- `src/input/commands.py`: comandos de movimiento del teclado con Gale.
- `src/states/game/GameOverState.py`: resumen diario y condición de derrota.

## Dos jugadores

Conecta dos mandos Xbox (u otros mandos reconocidos por el mapeo de SDL).
También puedes utilizar **un mando y el teclado**; cada método de entrada puede
elegir Player 1 o Player 2. Se admiten dos participantes, cada uno con una entrada diferente.
El menú principal se puede manejar con cruceta y A, o con flechas y Enter;
**Jugar** abre la selección. La pulsación que abre esa pantalla no registra
un jugador: pulsa A o Enter de nuevo para entrar en el centro.

| Acción | Mando | Teclado |
|--------|-------|---------|
| Entrar en selección / confirmar | A | Enter |
| Recorrer izquierda, centro y derecha | Joystick izquierdo | Flechas izquierda/derecha |
| Cancelar confirmación | B | Delete (también Backspace) |
| Mover el personaje en la partida | Joystick izquierdo | W/A/S/D |
| Levantar / colocar una caja en la partida | A | Enter |

1. Pulsa **A en el mando o Enter en el teclado** para aparecer en el centro.
2. Usa el joystick izquierdo o las flechas para recorrer **Player 1 ↔ centro ↔ Player 2**.
   Suelta el joystick o la tecla entre pasos. Puedes cambiar de lado mientras exploras.
3. Pulsa **A o Enter de nuevo** sobre un personaje para confirmarlo. Desde el centro
   no se confirma ningún personaje. Sólo la confirmación reserva el lado.
4. Pulsa **B o Delete** para cancelar tu confirmación, liberar el personaje y seguir
   escogiendo. Un personaje confirmado por el otro jugador no puede seleccionarse.
5. Cuando ambos jugadores confirmen personajes diferentes, se abre la pantalla
   de juego con **dos personajes animados**.

Cada personaje se mueve en todas las direcciones únicamente con el método de entrada
que confirmó ese personaje, dentro de los límites de la pantalla. En el teclado,
**W** mueve arriba, **A** a la izquierda, **S** abajo y **D** a la derecha;
las flechas se utilizan para la selección y los menús.
El movimiento diagonal está normalizado: su velocidad máxima es la misma que
al moverse por un solo eje. El joystick conserva la velocidad proporcional
a su inclinación cuando el vector de entrada tiene longitud menor que uno.
Hay una zona muerta para evitar movimiento por pequeñas desviaciones del joystick.
Al desconectar un mando se vuelve a selección, conservando el jugador conectado (o el teclado) y
dejando libre el lado del desconectado. Un mando reconectado debe pulsar A y elegir
el lado libre y confirmarlo con A.

Ambos jugadores utilizan `assets/graphics/player_walk.png`, con fotogramas de
32 × 64 píxeles y cuatro fotogramas por dirección. Caminan mirando en la dirección
del movimiento y permanecen quietos mirando hacia su última dirección al detenerse.
Cada jugador mantiene su propio estado de animación. `PLAYER_FRAME_INTERVAL` en
`settings.py` permite ajustar la duración de cada fotograma.

## Escenario

La partida transcurre en una sala basada en `06-princess`, con sus mismos
tiles de suelo, paredes y esquinas. El tilesheet se incluye como una copia
local en `assets/graphics/tilesheet.png`, por lo que Underpaid puede ejecutarse
sin depender de la carpeta del otro proyecto.

`src/world/Room.py` construye la sala de 20 × 14 tiles. Comienza 32 píxeles más abajo
para reservar una franja blanca superior para el reloj, y llega hasta el borde inferior
de la pantalla virtual de 640 × 480. Los tiles originales
de 16 × 16 píxeles se dibujan a 32 × 32 para mantener la escala de los personajes.
Ambos jugadores aparecen dentro de la sala y las paredes delimitan su movimiento.
La colisión utiliza la mitad inferior del personaje, donde apoya los pies, para
alcanzar todos los tiles de suelo junto a las paredes. La cabeza y el torso pueden
superponerse a la pared superior, dando perspectiva sin atravesar los límites del suelo.
Los personajes tampoco pueden atravesarse: cada uno bloquea al otro con un collider
de 32 × 32 píxeles en la mitad inferior del cuerpo. Cabeza y torso pueden
superponerse visualmente cuando los pies están separados. Las colisiones se
resuelven por eje para poder deslizarse junto al compañero, incluso cargando cajas.

## Duración de la partida

Cada partida dura **8 minutos**. El reloj aparece arriba, centrado sobre una
franja blanca de un tile de alto, y avanza desde **8:00 AM** hasta **4:00 PM**,
como un horario de trabajo. Cada minuto real equivale a una hora del juego:
tras cuatro minutos reales marca **12:00 PM**.
Se implementa con `gale.timer.Timer.tween`, actualizado por el bucle de Gale.
Cuando termina el tiempo se abre el resumen de jornada. Salir de la partida cancela
su reloj; una nueva partida comienza a las **8:00 AM**.
`CLOCK_START_HOUR`, `CLOCK_END_HOUR` y `SECONDS_PER_GAME_HOUR` en `settings.py`
definen el horario y la velocidad del reloj; `MATCH_DURATION` calcula la duración
en segundos reales.

## Puntuación y derrota

El prototipo comienza con **5 estrellas**. La zona de despacho es el rectángulo
amarillo junto a la pared derecha. Coloca las cajas de pedidos (medianas y pequeñas)
antes de las **4:00 PM**. Al finalizar la jornada se cuentan únicamente las cajas de pedidos
en el suelo y completamente dentro de esa zona; cargar uno sobre la cabeza no lo entrega.

Cada caja de pedido entregada suma un punto al total acumulado. Si falta al menos una,
el almacén pierde una estrella; entregar todos los pedidos conserva las estrellas.
El resumen permite empezar otra jornada mientras queden estrellas, sin límite de
días ni de puntos. **Perder las cinco estrellas termina el juego**. Elegir Jugar
desde el menú inicia una sesión nueva con cinco estrellas y cero puntos.

Las cajas grandes representan la recepción de productos y no cuentan como pedidos
entregados. La generación de pedidos, el empaquetado y los camiones todavía no están implementados. La desconexión de
un mando conserva al participante conectado y vuelve a selección; al confirmar
de nuevo se reinicia la jornada, manteniendo la puntuación de la sesión.

## Integración con Gale

`Underpaid` hereda de `gale.game.Game`, que controla el bucle, escala la superficie
virtual, despacha las entradas y actualiza `Timer` una sola vez por frame. Las
cinco escenas heredan de `BaseState` y se crean con fábricas de `StateMachine`.
El reloj se cancela en `PlayState.exit()`, incluso al cerrar la ventana.

`ControllerManager` llama a `InputHandler.init_gamepads()` al iniciar, conserva
los controladores SDL para recibir eventos `CONTROLLER*` y reconcilia los IDs de
instancia con `InputHandler.gamepads`. Los errores de desconexión durante la
enumeración o el cierre no interrumpen esa limpieza. Cada personaje filtra su
entrada por propietario antes de ejecutar los comandos de `CommandBindings` o
leer los ejes analógicos; sus animaciones de Gale son independientes.

Referencias: [entradas y mandos](https://r3mmurd.github.io/Gale/examples/input_handler.html),
[máquina de estados](https://r3mmurd.github.io/Gale/examples/state.html) y los proyectos
locales `projects/01-pong` a `projects/08-throw_a_bird`, especialmente `06-princess`.

## Objetos levantables

La sala comienza sin cajas; no se generan al iniciar ni al pasar a otra jornada.
Los tres tipos siguen disponibles en `src/world/Box.py` para futuras mecánicas de recepción y pedidos.
Cada tipo usa su propio sprite de `assets/graphics/`, escalado sin suavizado para conservar el pixel art.

| Tipo (`box_type`) | Tamaño | Sprite | Uso |
|-------------------|--------|--------|-----|
| `large` | 64 × 64 píxeles | `big_box.png` | Recepción de productos |
| `medium` | 32 × 32 píxeles | `medium_box.png` | Pedidos medianos |
| `small` | 16 × 16 píxeles | `small_box.png` | Pedidos pequeños |

`Box(x, y, box_type="medium")` permite crear cada tipo; los tipos desconocidos se rechazan.
La colisión ocupa el tamaño de la caja y se calcula contra la mitad inferior de los personajes. Los jugadores
pueden deslizarse junto a los objetos sin atravesarlos.

Acércate a una caja, mira hacia ella y pulsa **A en el mando o Enter en el teclado**
para levantarla. Durante los 0,3 segundos del levantamiento el personaje permanece
quieto; después puede caminar llevando el objeto sobre la cabeza. La caja levantada
deja de bloquear el suelo y sólo puede pertenecer a un jugador. Cada personaje puede
cargar un objeto a la vez.
Mientras carga, la velocidad es de **90 píxeles/s con una caja grande**,
**120 píxeles/s con una mediana** y **180 píxeles/s con una pequeña**
(la velocidad normal). Colocar la caja restaura la velocidad normal.
Estos límites se aplican también a las diagonales; el joystick conserva
el movimiento proporcional a su inclinación.
Al cargar, el personaje utiliza `assets/graphics/player_pot_walk.png` para caminar
con los brazos levantados. Cada jugador mantiene su propia animación de carga.

Mientras cargas una caja, pulsa **A o Enter de nuevo** para colocarla en el suelo
delante del personaje. Las cajas medianas y grandes se alinean a la cuadrícula
de tiles de 32 × 32 píxeles. Las pequeñas se alinean a una cuadrícula de
16 × 16: caben cuatro en un tile, distribuidas en dos filas y dos columnas.
Muévete frente a la subcasilla que quieres ocupar antes de colocarla.
Sólo se muestra el área que ocupa la caja en la dirección que miras mientras cargas: verde si
puedes colocarla y roja si está bloqueada o todavía estás levantándola.
Si hay una pared, otra caja o un jugador en ese lugar, conservas
la caja sobre la cabeza hasta encontrar espacio. Al colocarla vuelve a bloquear
el paso y cualquiera de los dos jugadores puede levantarla de nuevo.
La colocación consulta la capa de paredes del mapa de Tiled para toda el área
de la caja; también bloquea la segunda fila de la pared superior y los
solapamientos parciales de cajas grandes o subcasillas pequeñas.

## Repisas y productos

Las repisas se crean desde la capa de objetos `shelfs` del mapa `day1.json`.
Cada objeto define su posición, dimensiones y una propiedad entera `type`
que identifica el único tipo de producto admitido. Comienzan vacías y son
obstáculos fijos: no pueden levantarse ni colocarse cajas encima.

`Product(product_type, name="")` describe un tipo de producto. Cada `Shelf`
mantiene el producto almacenado y la cantidad disponible. `add(product, quantity=1)`
agrega existencias y `remove(quantity=1)` las retira, devolviendo el producto.
Los tipos incompatibles, cantidades no positivas y retiros superiores al stock
se rechazan sin cambiar las existencias.

Las repisas usan `assets/graphics/shelf.png`: el primer fotograma cuando están
vacías y el segundo cuando tienen al menos una unidad. Al retirar la última
unidad vuelve a mostrarse el primero. Los fotogramas se recortan con Gale y
se escalan a las dimensiones indicadas por el mapa.

Ejemplo de abastecimiento desde código:

```python
from src.world.Product import Product

shelf = room.shelves[0]
shelf.add(Product(shelf.product_type, "Libro"), quantity=3)
shelf.remove(quantity=1)
```

La interacción de jugadores para abastecer o retirar productos queda pendiente.

## Verificación

Las pruebas utilizan eventos de teclado y eventos SDL con mandos simulados. Desde la raíz del proyecto,
con el entorno virtual activado:

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py settings.py src tests
```
