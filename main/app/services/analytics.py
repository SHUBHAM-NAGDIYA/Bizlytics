from django.db.models import Sum, F, FloatField, ExpressionWrapper
from ..models import Sales

def get_sales_insights(store):

    # Revenue expression
    revenue_expression = ExpressionWrapper(
        F('QuantitySold') * F('PriceAtSale'),
        output_field=FloatField()
    )

    # Group by product
    base_qs = (
        Sales.objects
        .filter(store=store)
        .values('ProductID__ProductName')
        .annotate(
            total_sold=Sum('QuantitySold'),
            product_revenue=Sum(revenue_expression)
        )
    )

    # Top 5 best selling
    top_products = list(
        base_qs.order_by('-total_sold')[:5]
    )

    # Bottom 5 least selling
    least_products = list(
        base_qs.order_by('total_sold')[:5]
    )

    # Total sold items for this store
    total_sold_products = (
        Sales.objects
        .filter(store=store)
        .aggregate(total=Sum('QuantitySold'))['total'] or 0
    )

    # Total revenue for this store
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

