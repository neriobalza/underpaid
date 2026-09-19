"""Pedidos procedurales por jugador y comprobación exacta de su contenido."""

from collections import Counter
import random

import settings
from src.world.Product import Product


class Order:
    def __init__(self, number: int, owner: int, requirements, truck_id: int = 1) -> None:
        if type(number) is not int or number <= 0 or type(owner) is not int or owner not in (1, 2):
            raise ValueError("El pedido requiere un número positivo y un jugador válido")
        self.number = number
        self.owner = owner
        self.truck_id = truck_id
        self._requirements = Counter(requirements)
        for product_type, quantity in self._requirements.items():
            Product(product_type)
            if type(quantity) is not int or quantity <= 0:
                raise ValueError("Las cantidades del pedido deben ser enteros positivos")
        if not settings.ORDER_MIN_PRODUCTS <= self.quantity <= settings.ORDER_MAX_PRODUCTS:
            raise ValueError("Cada pedido debe contener entre 2 y 5 productos")

    @property
    def requirements(self) -> Counter:
        return self._requirements.copy()

    @property
    def quantity(self) -> int:
        return sum(self._requirements.values())

    @property
    def box_type(self) -> str:
        return "medium" if self.quantity >= 4 else "small"

    def matches(self, box) -> bool:
        return box.box_type == self.box_type and self.matches_contents(box)

    def matches_contents(self, box) -> bool:
        return getattr(box, "contents", None) == self._requirements


def generate_orders(rng=None, num_trucks: int = 1,
                    orders_per_player: int | None = None) -> list[Order]:
    rng = rng or random.Random()
    if orders_per_player is None:
        orders_per_player = settings.ORDERS_PER_PLAYER
    if type(orders_per_player) is not int or orders_per_player <= 0:
        raise ValueError("La cantidad de pedidos por jugador debe ser positiva")
    if type(num_trucks) is not int or num_trucks <= 0:
        raise ValueError("La cantidad de camiones debe ser positiva")
    total_orders = 2 * orders_per_player
    num_trucks = min(num_trucks, total_orders)
    
    truck_assignments = list(range(1, num_trucks + 1))
    while len(truck_assignments) < total_orders:
        truck_assignments.append(rng.randint(1, num_trucks))
    rng.shuffle(truck_assignments)
    
    orders = []
    for owner in (1, 2):
        for _ in range(orders_per_player):
            quantity = rng.randint(settings.ORDER_MIN_PRODUCTS, settings.ORDER_MAX_PRODUCTS)
            requirements = Counter(rng.randrange(len(settings.PRODUCT_NAMES)) for _ in range(quantity))
            truck_id = truck_assignments.pop()
            orders.append(Order(len(orders) + 1, owner, requirements, truck_id))
    return orders
