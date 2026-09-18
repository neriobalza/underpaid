"""Pila de Gale con transiciones por nombre y limpieza de escenas."""

from gale.state import StateStack


class SceneStack(StateStack):
    def __init__(self, factories, on_change):
        super().__init__()
        self.factories = factories
        self.on_change = on_change

    @property
    def current(self):
        return self.states[-1] if self.states else None

    def push(self, state, *args, **kwargs) -> None:
        try:
            super().push(state, *args, **kwargs)
        except Exception:
            # Gale agrega la escena antes de enter(); retirarla si falla.
            super().pop()
            raise
        finally:
            self.on_change()

    def pop(self) -> None:
        try:
            super().pop()
        finally:
            self.on_change()

    def clear(self) -> None:
        # StateStack.clear() descarta la pila sin llamar a exit().
        while self.states:
            self.pop()

    def change(self, name, *args, **kwargs) -> None:
        factory = self.factories[name]
        self.clear()
        self.push(factory(self), *args, **kwargs)
