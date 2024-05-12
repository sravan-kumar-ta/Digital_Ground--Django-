from django.urls import path
from django.views.generic import TemplateView

from products import views

app_name = 'products'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('categories/', TemplateView.as_view(template_name='products/categories.html'), name='category'),
    path('category/<slug:category_slug>/', views.product_list, name='products-list'),
    path('product/<slug:c_slug>/<slug:p_slug>/', views.details_of_product, name='category'),
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('minus-from-cart/', views.minus_from_cart, name='minus_from_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
]
