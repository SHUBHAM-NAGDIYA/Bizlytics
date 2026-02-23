# ml/stock_engine.py
from django.db.models import Sum
from django.db import transaction
from django.db.models.functions import Coalesce
from ..models import Sales, Product, StockRecommendation

SAFETY_BUFFER_PERCENT = 0.2


def classify_risk(current_stock, forecast_7_days):
    if current_stock <= 0:
        return "out_of_stock"
    elif current_stock < 0.5 * forecast_7_days:
        return "critical"
    elif current_stock < forecast_7_days:
        return "warning"
    else:
        return "safe"


def generate_reason(risk_level):
    if risk_level == "out_of_stock":
        return "Product already out of stock"
    elif risk_level == "critical":
        return "Immediate restocking required due to high demand"
    elif risk_level == "warning":
        return "Stock may run out soon based on forecast"
    else:
        return "Stock level is sufficient"


def generate_stock_recommendations(forecast_dict, store):

    if not forecast_dict:
        return []

    recommendations = []
    product_ids = list(forecast_dict.keys())

    # Filter products by store
    products = Product.objects.filter(
        store=store,
        ProductID__in=product_ids
    )

    products_map = {p.ProductID: p for p in products}

    # Aggregate total sales per product
    sales_data = (
        Sales.objects
        .filter(store=store, ProductID__ProductID__in=product_ids)
        .values('ProductID__ProductID')
        .annotate(total_sold=Coalesce(Sum('QuantitySold'), 0))
    )

    sales_map = {
        item['ProductID__ProductID']: item['total_sold']
        for item in sales_data
    }

    with transaction.atomic():

        # Delete old recommendations for this store only
        StockRecommendation.objects.filter(
            store=store,
            ProductID__ProductID__in=product_ids
        ).delete()

        for product_id, forecast_data in forecast_dict.items():

            product = products_map.get(product_id)
            if not product:
                continue

            total_sold = sales_map.get(product_id, 0)

            current_stock = product.Quantity - total_sold
            forecast_7_days = forecast_data.get("forecast_7_days", 0)

            safety_buffer = forecast_7_days * SAFETY_BUFFER_PERCENT
            required_stock = forecast_7_days + safety_buffer

            recommended_order = max(required_stock - current_stock, 0)

            risk_level = classify_risk(current_stock, forecast_7_days)
            reason = generate_reason(risk_level)

            # ✅ FIXED FIELD NAME HERE
            StockRecommendation.objects.create(
                store=store,
                ProductID=product,
                CurrentStock=current_stock,
                ForecastSevendays=forecast_7_days,  # ✅ corrected
                RecommendedOrder=recommended_order,
                RiskLevel=risk_level,
                Confidence=forecast_data.get("confidence")
            )

            recommendations.append({
                "product_id": product.ProductID,
                "product_name": product.ProductName,
                "current_stock": round(current_stock, 2),
                "forecast_7_days": round(forecast_7_days, 2),
                "recommended_order": round(recommended_order, 2),
                "risk_level": risk_level,
                "confidence": forecast_data.get("confidence"),
                "reason": reason
            })

    return recommendations