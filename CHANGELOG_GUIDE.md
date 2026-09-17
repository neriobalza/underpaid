# Guía para actualizar el Changelog

Para mantener el archivo `CHANGELOG.md` limpio y fácil de leer para cualquier persona, sigue estos pasos al registrar un nuevo cambio:

### 1. Ubicación
Siempre añade tus cambios recientes en la parte superior del archivo, justo debajo del encabezado `## [Unreleased]`.

### 2. Categorías
Agrupa tus cambios debajo de la categoría que corresponda (créala si no existe):
- **Added**: Para características o mecánicas completamente nuevas.
- **Changed**: Para cambios en mecánicas o funciones que ya existían.
- **Deprecated**: Para cosas que pronto se van a eliminar.
- **Removed**: Para características que ya fueron eliminadas.
- **Fixed**: Para correcciones de bugs o errores.

### 3. Redacción para Humanos (No Máquinas)
- **Evita jerga técnica:** No menciones nombres de archivos, funciones, variables o clases (ej. no pongas "Cambiado `Room.py` para usar `move_and_collide`").
- **Enfócate en la experiencia:** Describe cómo afecta el cambio al jugador (ej. "Las paredes del almacén ahora bloquean físicamente a los personajes").

### 4. Consistencia
- Trata de empezar cada punto con una estructura similar. Por ejemplo, descripciones directas ("Nueva zona de...", "Soporte para...") o verbos en participio ("Corregido el error...", "Mejorada la velocidad...").
- Sé conciso y no escribas un manual de instrucciones; solo resume la novedad.

### 5. Lanzamiento de Versiones (Release)
Cuando el juego tenga una actualización pública grande, simplemente cambia el título `## [Unreleased]` por el número de la versión y la fecha de hoy, por ejemplo:
`## [1.0.0] - 2026-10-01`
Y debajo de eso, crea un nuevo bloque vacío `## [Unreleased]` para los siguientes cambios.
