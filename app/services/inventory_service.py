from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    unit_price: float
    stock: int


PRODUCTS: dict[str, Product] = {
    "F-200": Product("F-200", "Industrial Filter", 120.0, 80),
    "PV-10": Product("PV-10", "Pressure Valve", 75.0, 15),
    "P-500": Product("P-500", "Industrial Pump", 850.0, 8),
}


def get_product(sku: str) -> Product | None:
    return PRODUCTS.get(sku.upper())
