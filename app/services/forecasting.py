from django.db.models import Sum, F, Count, FloatField, Case, When, Value
from django.db.models.functions import TruncWeek, TruncDate
from datetime import timedelta
from ..models import Sales
import logging
logger = logging.getLogger(__name__)

def get_revenue_forecast_metrics(store):
    # day-by-day revenue for the store, oldest first
    daily_revenue = list(
        Sales.objects.filter(store=store)
        .values('Date')
        .annotate(daily_revenue=Sum(F('QuantitySold') * F('PriceAtSale')))
        .order_by('Date')
    )

    total_revenue = sum(row['daily_revenue'] or 0 for row in daily_revenue)

    # walk the days in order and tag each one with how it moved vs the
    # previous day - keeping both the % change and a simple up/down/flat label
    # makes the frontend's job a lot easier
    prev = None
    for row in daily_revenue:
        curr = row['daily_revenue'] or 0

        if prev and prev != 0:
            row['daily_growth_percent'] = round(((curr - prev) / prev) * 100, 2)
        else:
            row['daily_growth_percent'] = None

        if prev is None:
            row['daily_growth_percent'] = 'neutral'
        elif curr > prev:
            row['daily_growth_percent'] = 'upwards'
        elif curr < prev:
            row['daily_growth_percent'] = 'downwards'
        else:
            row['daily_growth_percent'] = 'neutral'

        prev = curr

    # how much of total revenue each product is responsible for
    product_revenue = list(
        Sales.objects
        .values('ProductID__ProductName')
        .annotate(product_revenue=Sum(F('QuantitySold') * F('PriceAtSale')))
        .order_by('-product_revenue')
    )

    revenue_contribution = []
    for row in product_revenue:
        percent = (row['product_revenue'] * 100 / total_revenue) if total_revenue else 0
        revenue_contribution.append({
            'ProductID__ProductName': row['ProductID__ProductName'],
            'product_revenue': row['product_revenue'],
            'revenue_contribution_percent': round(percent, 2)
        })

    # only care about the top 5 for the dashboard card
    revenue_contribution = revenue_contribution[:5]

    # same idea as daily revenue, just rolled up to weeks
    weekly_revenue = list(
        Sales.objects
        .annotate(week=TruncWeek('Date'))
        .values('week')
        .annotate(weekly_revenue=Sum(F('QuantitySold') * F('PriceAtSale')))
        .order_by('week')
    )

    best_week = max(weekly_revenue, key=lambda x: x['weekly_revenue'], default=None)
    worst_week = min(weekly_revenue, key=lambda x: x['weekly_revenue'], default=None)

    prev = None
    for row in weekly_revenue:
        curr = row['weekly_revenue'] or 0
        start = row['week']
        end = start + timedelta(days=6)
        # human-friendly label like "12 Jan - 18 Jan" instead of raw dates
        row['week_name'] = f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"

        if prev and prev != 0:
            row['weekly_growth_percent'] = round(((curr - prev) / prev) * 100, 2)
        else:
            row['weekly_growth_percent'] = None

        if prev is None:
            row['weekly_growth_trend'] = 'neutral'
        elif curr > prev:
            row['weekly_growth_trend'] = 'upwards'
        elif curr < prev:
            row['weekly_growth_trend'] = 'downwards'
        else:
            row['weekly_growth_trend'] = 'neutral'

        prev = curr

    logger.info("Forecast demand endpoint triggered")
    return {
        "daily_revenue": daily_revenue,
        "weekly_revenue": weekly_revenue,
        "best_week": best_week,
        "worst_week": worst_week,
        "total_revenue": total_revenue,
        "revenue_contribution": revenue_contribution,
    }


def get_product_velocity():
    # "velocity" = how fast a product sells and, from that, roughly how many
    # days of stock are left at the current pace
    velocity = (
        Sales.objects
        .annotate(day=TruncDate('Date'))
        .values('ProductID__ProductName', 'ProductID__Quantity')
        .annotate(
            total_sold=Sum('QuantitySold'),
            active_days=Count('day', distinct=True)
        )
        .annotate(
            avg_daily_sales=Case(
                When(active_days__gt=0, then=F('total_sold') * 1.0 / F('active_days')),
                default=Value(0),
                output_field=FloatField()
            ),
            current_stock=F('ProductID__Quantity') - F('total_sold')
        )
        .annotate(
            # guard against divide-by-zero when a product hasn't sold at all yet
            estimated_stock_out_days=Case(
                When(avg_daily_sales__gt=0, then=F('current_stock') * 1.0 / F('avg_daily_sales')),
                default=None,
                output_field=FloatField()
            )
        )
        .order_by('estimated_stock_out_days')
    )

    return {"velocity": velocity}
