from app.services.catalog import Catalog


def test_register_and_price():
    catalog = Catalog()
    catalog.register("Blue Mug", 9)
    assert catalog.price_of("blue mug") == 9


def test_count():
    catalog = Catalog()
    catalog.register("a", 1)
    catalog.register("b", 2)
    assert catalog.count() == 2
