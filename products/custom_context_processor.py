from django.db.models import Min, Max

from products.models import Category, Product, Wishlist, Cart


def categories(request):
    return {'categories_obj': Category.objects.all()}


def get_filters(request):
    minMaxPrice = Product.objects.aggregate(Min('price'), Max('price'))
    data = {
        'minMaxPrice': minMaxPrice,
    }
    return data


def get_wishlist(request):
    count = 0
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    return {'wishlist_len': count}


def cart_count(request):
    if request.user.is_authenticated:
        cart_length = Cart.objects.filter(user=request.user).count()
    else:
        session_cart = request.session.get('cart', {})
        cart_length = len(session_cart)
    return {'cart_length': cart_length}
