"""Punto de entrada de Underpaid."""

import sys

import pygame

from src.Underpaid import Underpaid


if __name__ == "__main__":
    try:
        game = Underpaid()
        game.exec()
    except (pygame.error, OSError, ValueError) as error:
        print(f"No se pudo ejecutar Underpaid: {error}", file=sys.stderr)
        raise SystemExit(1) from error
