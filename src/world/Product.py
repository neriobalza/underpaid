"""Tipo de producto que puede almacenarse en una repisa."""

import settings


class Product:
    def __init__(self, product_type: int, name: str = "") -> None:
        if type(product_type) is not int or not 0 <= product_type < len(settings.PRODUCT_NAMES):
            raise ValueError("El tipo de producto debe estar entre 0 y 4")
        if not isinstance(name, str):
            raise ValueError("El nombre del producto debe ser texto")
        self._product_type = product_type
        self.name = name.strip() or settings.PRODUCT_NAMES[product_type]

    @property
    def product_type(self) -> int:
        return self._product_type

    @property
    def image(self):
        return settings.load_product_frames()[self.product_type]
