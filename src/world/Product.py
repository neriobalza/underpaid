"""Tipo de producto que puede almacenarse en una repisa."""


class Product:
    def __init__(self, product_type: int, name: str = "") -> None:
        if type(product_type) is not int or product_type < 0:
            raise ValueError("El tipo de producto debe ser un entero no negativo")
        if not isinstance(name, str):
            raise ValueError("El nombre del producto debe ser texto")
        self._product_type = product_type
        self.name = name.strip() or f"Producto {product_type}"

    @property
    def product_type(self) -> int:
        return self._product_type
