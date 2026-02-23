import pandas as pd
import hashlib
import logging

from django.db import transaction
from ..models import Product, Sales, UploadedFileLog, StockRecommendation

logger = logging.getLogger(__name__)


def generate_file_hash(file):
    hasher = hashlib.sha256()
    for chunk in file.chunks():
        hasher.update(chunk)
    file.seek(0)
    return hasher.hexdigest()


logger = logging.getLogger(__name__)


def process_sales_upload(file, store):

    if not file:
        return {"error": "No file uploaded"}, 400

    file_hash = generate_file_hash(file)

    # Prevent duplicate file upload per store
    if UploadedFileLog.objects.filter(store=store, FileHash=file_hash).exists():
        return {"error": "This file was already uploaded"}, 400

    try:
        filename = file.name.lower()

        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return {"error": "Unsupported file type"}, 400

    except Exception:
        return {"error": "File reading failed"}, 400

    required_columns = [
        'ProductID', 'ProductName', 'Category',
        'Date', 'Quantity', 'QuantitySold',
        'UnitPrice', 'PriceAtSale'
    ]

    if not all(col in df.columns for col in required_columns):
        return {"error": "Missing required columns"}, 400

    df = df[required_columns].dropna(how='all')

    df['ProductID'] = df['ProductID'].astype(str).str.strip()
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['QuantitySold'] = pd.to_numeric(df['QuantitySold'], errors='coerce')
    df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
    df['PriceAtSale'] = pd.to_numeric(df['PriceAtSale'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    df = df.dropna(subset=[
        'ProductID', 'ProductName', 'Category',
        'Date', 'QuantitySold', 'PriceAtSale'
    ])

    df = df[(df['QuantitySold'] > 0) & (df['PriceAtSale'] > 0)]

    if df.empty:
        return {"error": "No valid sales rows found"}, 400

    valid_rows = len(df)

    with transaction.atomic():

        uploaded_products = (
            df[['ProductID', 'ProductName', 'Category', 'Quantity', 'UnitPrice']]
            .drop_duplicates(subset=['ProductID'])
        )

        # 🔥 Use get_or_create instead of bulk_create
        product_map = {}

        for _, row in uploaded_products.iterrows():

            product, created = Product.objects.get_or_create(
                store=store,
                ProductID=row['ProductID'],
                defaults={
                    'ProductName': row['ProductName'],
                    'Category': row['Category'],
                    'Quantity': row['Quantity'],
                    'UnitPrice': row['UnitPrice']
                }
            )

            # Validate metadata if product already exists
            if not created:
                if (
                    product.ProductName != row['ProductName'] or
                    product.Category != row['Category'] or
                    float(product.UnitPrice) != float(row['UnitPrice'])
                ):
                    return {
                        "error": f"Product metadata mismatch for {row['ProductID']}"
                    }, 400

            product_map[row['ProductID']] = product

        # Create sales records
        sales_list = []

        for _, row in df.iterrows():
            product = product_map.get(row['ProductID'])

            sales_list.append(Sales(
                store=store,
                ProductID=product,
                QuantitySold=row['QuantitySold'],
                Date=row['Date'],
                PriceAtSale=row['PriceAtSale']
            ))

        Sales.objects.bulk_create(sales_list)

        UploadedFileLog.objects.create(
            store=store,
            FileHash=file_hash
        )

    return {
        "message": "File processed successfully",
        "records_inserted": len(sales_list),
        "valid_rows": valid_rows
    }, 200

def delete_uploaded_data():
    UploadedFileLog.objects.all().delete()
    StockRecommendation.objects.all().delete()
    Sales.objects.all().delete()
    Product.objects.all().delete()
    return None
