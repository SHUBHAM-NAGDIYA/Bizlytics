from django.db.models import Sum, F, FloatField, ExpressionWrapper
from ..models import Sales

def get_sales_insights(store):
    # revenue per row = qty * price, computed at the DB level so we're not
    # pulling every sale into Python just to multiply two numbers
    revenue_expression = ExpressionWrapper(
        F('QuantitySold') * F('PriceAtSale'),
        output_field=FloatField()
    )

    # this is the shared queryset both "top" and "least" sellers are built from
    base_qs = (
        Sales.objects
        .filter(store=store)
        .values('ProductID__ProductName')
        .annotate(
            total_sold=Sum('QuantitySold'),
            product_revenue=Sum(revenue_expression)
        )
    )

    top_products = list(
        base_qs.order_by('-total_sold')[:5]
    )

    least_products = list(
        base_qs.order_by('total_sold')[:5]
    )

    total_sold_products = (
        Sales.objects
        .filter(store=store)
        .aggregate(total=Sum('QuantitySold'))['total'] or 0
    )

    total_revenue = (
        Sales.objects
        .filter(store=store)
        .aggregate(total=Sum(revenue_expression))['total'] or 0
    )

    return {
        "top_products": top_products,
        "least_products": least_products,
        "total_sold_products": total_sold_products,
        "total_revenue": round(total_revenue, 2),
    }
