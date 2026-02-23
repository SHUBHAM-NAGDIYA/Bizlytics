from django.db import models
from django.contrib.auth.models import User


class StoreOwneres(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    storename = models.CharField(max_length=100)
    ownername = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.storename


class Product(models.Model):
    store = models.ForeignKey(StoreOwneres, on_delete=models.CASCADE)
    ProductID = models.CharField(max_length=50)
    ProductName = models.CharField(max_length=200)
    Category = models.CharField(max_length=100)
    Quantity = models.IntegerField()
    UnitPrice = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('store', 'ProductID')

    def __str__(self):
        return f"{self.ProductName} ({self.store.storename})"


class Sales(models.Model):
    store = models.ForeignKey(StoreOwneres, on_delete=models.CASCADE)
    ProductID = models.ForeignKey(Product, on_delete=models.CASCADE)
    Date = models.DateField()
    QuantitySold = models.IntegerField()
    PriceAtSale = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.ProductID.ProductName} - {self.Date}"


class UploadedFileLog(models.Model):
    store = models.ForeignKey(StoreOwneres, on_delete=models.CASCADE)
    FileHash = models.CharField(max_length=255)
    UploadedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('store', 'FileHash')

    def __str__(self):
        return f"{self.store.storename} - {self.FileHash}"


class StockRecommendation(models.Model):
    store = models.ForeignKey(StoreOwneres, on_delete=models.CASCADE)
    ProductID = models.ForeignKey(Product, on_delete=models.CASCADE)
    CurrentStock = models.IntegerField()
    ForecastSevendays = models.FloatField()
    RecommendedOrder = models.FloatField()
    RiskLevel = models.CharField(max_length=20)
    Confidence = models.FloatField(null=True, blank=True)
    GeneratedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ProductID.ProductName} - {self.RiskLevel}"