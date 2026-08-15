import pytest
from ..services.inventory import get_low_stock_alerts
from ..models import Product, Sales
from django.utils.timezone import now


@pytest.mark.django_db
def test_low_stock_alert_returns_only_low_items():
    product1 = Product.objects.create(
        ProductID="P1",
        ProductName="Rice",
        Category="Food",
        Quantity=100,
        UnitPrice=50
    )

    product2 = Product.objects.create(
        ProductID="P2",
        ProductName="Sugar",
        Category="Food",
        Quantity=30,
        UnitPrice=40
    )

    Sales.objects.create(ProductID=product1, QuantitySold=20, PriceAtSale=50, Date=now())
    Sales.objects.create(ProductID=product2, QuantitySold=20, PriceAtSale=50, Date=now())

    alerts = get_low_stock_alerts(threshold=50)

    assert len(alerts) == 1
    assert alerts[0]["product"] == "Sugar"
    assert alerts[0]["remaining"] == 10


@pytest.mark.django_db
def test_low_stock_severity_levels():
    product = Product.objects.create(
        ProductID="P3",
        ProductName="Oil",
        Category="Food",
        Quantity=100,
        UnitPrice=120
    )

    Sales.objects.create(ProductID=product, QuantitySold=90, PriceAtSale=50, Date=now())

    alerts = get_low_stock_alerts(threshold=50, critical_threshold=20)

    assert alerts[0]["severity"] == "critical"
