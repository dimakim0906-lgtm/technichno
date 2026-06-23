from django.contrib import admin
from .models import Order, OrderStatus, OrderWork, OrderHistory


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'sort_order']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'device_brand', 'device_model', 'status', 'received_at']
    list_filter = ['status']
    search_fields = ['client__full_name', 'device_model', 'imei']


@admin.register(OrderWork)
class OrderWorkAdmin(admin.ModelAdmin):
    list_display = ['order', 'description', 'cost', 'master', 'performed_at']


admin.site.register(OrderHistory)