from django.contrib import admin

from orders.models import Order


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'grand_total', 'order_status', 'payment_status')


admin.site.register(Order, OrderAdmin)
