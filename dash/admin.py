from django.contrib import admin
from dash.models import (
    Profile,
    Category,
    Inventory,
    Supplier,
    Delivery,
    DeliveryItem,
    PaymentMethod,
    TodaysDeal,
    Unit,
    LowStockThreshold,
    Transaction,
    HomePageSession,
)


admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(Inventory)
admin.site.register(Supplier)
admin.site.register(Delivery)
admin.site.register(DeliveryItem)
admin.site.register(PaymentMethod)
admin.site.register(TodaysDeal)
admin.site.register(Unit)
admin.site.register(LowStockThreshold)
admin.site.register(Transaction)
admin.site.register(HomePageSession)
