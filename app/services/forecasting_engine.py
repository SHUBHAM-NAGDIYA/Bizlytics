import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from django.db.models import Sum
from ..models import Sales, Product


FORECAST_DAYS = 7
MINIMUM_DATA_POINTS = 10


def generate_demand_forecast(store):
    # simple linear regression per product - nothing fancy, but it's enough
    # to give store owners a directional 7-day demand number
    forecast_results = {}

    product_ids = (
        Sales.objects
        .filter(store=store)
        .values_list('ProductID', flat=True)
        .distinct()
    )

    for product_id in product_ids:
        # always scope by store + product together, never just product_id,
        # otherwise two stores selling the same ProductID would bleed into
        # each other's numbers
        base_qs = (
            Sales.objects
            .filter(store=store, ProductID=product_id)
            .values('Date')
            .annotate(total_sold=Sum('QuantitySold'))
            .order_by('Date')
        )

        df = pd.DataFrame(list(base_qs))

        # skip products that don't have enough sales history to fit a
        # meaningful trend line
        if df.empty or len(df) < MINIMUM_DATA_POINTS:
            continue

        df['Date'] = pd.to_datetime(df['Date'])

        daily_sales = (
            df.set_index('Date')['total_sold']
        )

        # a product might not have sold every single day, but for the model
        # to make sense the timeline can't have gaps - fill missing days
        # with zero sales
        full_range = pd.date_range(
            start=daily_sales.index.min(),
            end=daily_sales.index.max()
        )

        daily_sales = daily_sales.reindex(full_range, fill_value=0)

        daily_sales = daily_sales.reset_index()
        daily_sales.columns = ['Date', 'QuantitySold']
        daily_sales['DayIndex'] = range(len(daily_sales))

        # 80/20 train/test split so we can sanity-check accuracy before
        # trusting the forecast
        split_index = int(len(daily_sales) * 0.8)

        X = daily_sales['DayIndex'].values.reshape(-1, 1)
        y = daily_sales['QuantitySold'].values

        X_train = X[:split_index]
        y_train = y[:split_index]
        X_test = X[split_index:]
        y_test = y[split_index:]

        model = LinearRegression()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        # rough confidence score - the smaller the error relative to average
        # demand, the closer this gets to 1
        confidence = max(0, 1 - (rmse / (np.mean(y) + 1)))

        last_index = daily_sales['DayIndex'].max()

        future_indices = np.array(
            [[last_index + i] for i in range(1, FORECAST_DAYS + 1)]
        )

        future_predictions = model.predict(future_indices)
        # a linear model can predict negative sales, which doesn't make
        # sense here, so floor everything at zero
        future_predictions = np.maximum(future_predictions, 0)

        total_forecast = float(np.sum(future_predictions))

        product = Product.objects.get(pk=product_id)

        forecast_results[product.ProductID] = {
            "product_name": product.ProductName,
            "forecast_7_days": round(total_forecast, 2),
            "confidence": round(confidence, 2),
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2)
        }

    return forecast_results
