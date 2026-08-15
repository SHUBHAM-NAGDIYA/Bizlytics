import pytest
from datetime import date
from ..models import Product, Sales
from ..services.analytics import get_sales_insights


@pytest.mark.django_db
def test_total_revenue_calculation():
    product = Product.objects.create(
        ProductID="P1",
        ProductName="Soap",
        Category="Hygiene",
        Quantity=100,
        UnitPrice=50
    )

    Sales.objects.create(
        ProductID=product,
        Date=date(2025, 1, 1),
        QuantitySold=2,
        PriceAtSale=50
    )

    Sales.objects.create(
        ProductID=product,
        Date=date(2025, 1, 1),
        QuantitySold=3,
        PriceAtSale=50
    )

    data = get_sales_insights()

    assert data["total_revenue"] == 250
