from django.contrib import admin
from products.models import *


# Register your models here.
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'slug')


class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('id', 'title', 'brand', 'category', 'price', 'stock')
    list_editable = ('price', 'stock')
    list_filter = ('category',)


class CartAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'quantity')
    list_filter = ('product', 'user')


admin.site.register(Brand, BrandAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Wishlist)
