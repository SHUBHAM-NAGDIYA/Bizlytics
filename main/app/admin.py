from django.contrib import admin
from .models import StoreOwneres,Sales,Product

# Register your models here.
admin.site.register(StoreOwneres)
admin.site.register(Product)
admin.site.register(Sales)
