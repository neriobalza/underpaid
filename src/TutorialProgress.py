"""Persistencia local del progreso del tutorial."""

from pathlib import Path


class TutorialProgress:
    COMPLETED_VALUE = "tutorial_completed=true"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> bool:
        """Indica si el tutorial fue completado; un archivo inválido es pendiente."""
        try:
            value = self.path.read_text(encoding="utf-8").strip().lower()
        except (OSError, UnicodeError):
            return False
        return value == self.COMPLETED_VALUE

    def save_completed(self) -> None:
        """Guarda el progreso mediante reemplazo para evitar archivos parciales."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            temporary_path.write_text(f"{self.COMPLETED_VALUE}\n", encoding="utf-8")
            temporary_path.replace(self.path)
        except OSError:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
