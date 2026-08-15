# Bizlytics

Bizlytics is a Django web app that gives small store owners a lightweight analytics dashboard: upload a sales spreadsheet and get revenue insights, demand forecasts, low-stock alerts, and AI-generated restocking recommendations.

## Features

- **Sales ingestion** — upload sales data as `.csv`, `.xlsx`, or `.xls`. Files are validated, deduplicated (via file hash), and parsed with pandas before being written to the database.
- **Sales insights** — top and least selling products, total units sold, and total revenue per store.
- **Revenue forecasting** — daily and weekly revenue trends with growth direction (up/down/flat), best/worst week, and per-product revenue contribution.
- **Product velocity** — estimates how many days of stock remain for each product based on its average daily sales.
- **Demand forecasting (ML)** — a per-product linear regression model (scikit-learn) trained on historical sales to predict demand for the next 7 days, with accuracy metrics (MAE, RMSE, confidence).
- **Stock recommendations** — combines the demand forecast with current stock to classify each product's risk level (`safe`, `warning`, `critical`, `out_of_stock`) and recommend how much to reorder.
- **Multi-store support** — every model is scoped to a `StoreOwneres` record, so each store's data, forecasts, and recommendations stay isolated.

## Tech Stack

- **Backend:** Django 6
- **Data processing:** pandas, NumPy
- **Machine learning:** scikit-learn (Linear Regression)
- **Database:** PostgreSQL (via `dj-database-url` / `psycopg2`)
- **Static files:** WhiteNoise
- **Server:** Gunicorn
- **Testing:** pytest + `pytest-django`

## Project Structure

```
main/
├── app/
│   ├── models.py               # StoreOwneres, Product, Sales, UploadedFileLog, StockRecommendation
│   ├── views.py                 # page views + JSON API endpoints
│   ├── urls.py
│   ├── admin.py
│   ├── services/
│   │   ├── ingestion.py          # file upload parsing & validation
│   │   ├── analytics.py           # sales insights (top/least sellers, totals)
│   │   ├── forecasting.py          # revenue trends & product velocity
│   │   ├── forecasting_engine.py    # ML demand forecasting (linear regression)
│   │   ├── stock_recommendation_engine.py  # risk classification & reorder amounts
│   │   └── inventory.py             # low stock alerts
│   └── tests/                    # pytest test suite
├── Templates/                  # landing, auth, dashboard, upload pages
├── main/                        # Django project settings, urls, wsgi/asgi
├── manage.py
├── build.sh                     # install deps, collectstatic, migrate
├── pytest.ini
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL

### Setup

```bash
cd main
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Set a `DATABASE_URL` environment variable (used by `dj-database-url`):

```env
DATABASE_URL=postgres://user:password@localhost:5432/bizlytics
```

Run migrations and start the server:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

### Running Tests

```bash
pytest
```

### Deployment

`build.sh` handles the standard deploy steps (install dependencies, collect static files, run migrations) and can be used as a build command on platforms like Render or Railway. Gunicorn is included as the production WSGI server.

## How It Works

1. **Sign up / sign in** — each user is linked to a `StoreOwneres` profile (store name, owner name, city).
2. **Upload sales data** — a spreadsheet with columns `ProductID`, `ProductName`, `Category`, `Date`, `Quantity`, `QuantitySold`, `UnitPrice`, `PriceAtSale` is validated and imported.
3. **Dashboard** — pulls together sales insights, revenue forecasts, low-stock alerts, and product velocity into one view.
4. **AI engine** — `run_full_inventory_ai_engine` runs the demand forecast model for every product, then generates stock recommendations (risk level + suggested reorder quantity) in one call.
5. **Sign out** — for this project, uploaded data is cleared on logout rather than persisted indefinitely.

## Key API Endpoints

| Endpoint | Description |
|---|---|
| `POST /upload_sales/` | Upload and process a sales file |
| `GET /get_insights/` | Sales insights (top/least sellers, totals) |
| `GET /forecast_demand/` | Revenue forecast metrics |
| `GET /low_stock_alert/` | Low stock alerts |
| `GET /run_full_inventory_ai_engine/` | Full demand forecast + stock recommendations |

## Notes

- `SECRET_KEY` and `DEBUG` in `main/settings.py` are set for local development — override them with environment variables before deploying.
- No license specified yet — consider adding one (e.g., MIT) if you plan to open-source this project.
