import pytest
from datetime import date
from ..models import Product, Sales
from ..services.forecasting import get_product_velocity


@pytest.mark.django_db
def test_velocity_calculation():
    product = Product.objects.create(
        ProductID="P10",
        ProductName="Milk",
        Category="Dairy",
        Quantity=100,
        UnitPrice=60
    )

    Sales.objects.create(ProductID=product, QuantitySold=10, PriceAtSale=50, Date=date(2026, 1, 1))
    Sales.objects.create(ProductID=product, QuantitySold=20, PriceAtSale=50, Date=date(2026, 1, 2))

    result = get_product_velocity()
    velocity_data = list(result["velocity"])
    assert velocity_data[0]['avg_daily_sales'] == 15

  
