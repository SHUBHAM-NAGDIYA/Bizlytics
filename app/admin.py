from django.contrib import admin
from .models import StoreOwneres,Sales,Product

# exposed in /admin mainly for poking at the data during development
admin.site.register(StoreOwneres)
admin.site.register(Product)
admin.site.register(Sales)
