from ..models import Sales,Product
from django.db.models import Sum, F
from django.db.models.functions import Coalesce


def get_low_stock_alerts(store, threshold=50, critical_threshold=20):

    products = (
        Product.objects
        .filter(store=store)
        .annotate(
            total_sold=Coalesce(Sum('sales__QuantitySold'), 0)
        )
        .annotate(
            remaining=F('Quantity') - F('total_sold')
        )
        .filter(remaining__lt=threshold)
        .order_by('remaining')
    )

    alerts = []

    for product in products:
        remaining = product.remaining

        alerts.append({
            "product": product.ProductName,
            "remaining": remaining,
            "severity": "critical" if remaining < critical_threshold else "warning"
        })

    return alerts