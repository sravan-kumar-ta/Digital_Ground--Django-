from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView

from account.models import Address
from products.models import Category, Product, Brand, Cart


class HomeView(TemplateView):
    template_name = 'products/home.html'

    def get_context_data(self, **kwargs):
        context = {
            'categories': Category.objects.all().order_by('?')[:3],  # fetching 3 random objects
            'products': Product.objects.all().order_by('?')[:8]
        }
        return context


class ProductListView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'products/category_products.html'
    category = None

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs.get('slug'))
        return super().get_queryset().filter(Q(category=self.category) & Q(stock__gte=1))  # stock >= 1

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['category'] = self.category
        context['brands'] = Brand.objects.filter(category=self.category)
        return context


def product_filter(*args, **kwargs):
    selected_brands = kwargs['data']['selected_brands']
    sort_method = kwargs['data']['sort_method']
    min_price = kwargs['data']['min_price']
    max_price = kwargs['data']['max_price']
    category_id = kwargs['data']['cat_id']
    products = args[0]

    if len(selected_brands) != 0:
        products = products.filter(brand__name__in=selected_brands, brand__category=category_id)

    if sort_method:
        if sort_method == '1':
            products = products.order_by('price')
        elif sort_method == '2':
            products = products.order_by('-price')

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    return products


def product_list(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category, stock__gte=1)
    brands = Brand.objects.filter(category=category)
    category_id = category.id

    context = dict()

    # filtering the products
    if request.method == 'POST':
        selected_brands = request.POST.getlist('brands')
        sort_method = request.POST['sort']
        min_price = request.POST['min']
        max_price = request.POST['max']

        prod_filter = {
            'cat_id': category_id,
            'selected_brands': selected_brands,
            'sort_method': sort_method,
            'min_price': min_price,
            'max_price': max_price
        }
        context.update(prod_filter)

        # filtering the products
        products = product_filter(products, data=prod_filter)
        request.session['prod_filter'] = prod_filter

    # this block is used to filter the data when pagination is occurs...(when changing pages)
    if request.method == 'GET':
        if 'prod_filter' in request.session:
            if request.session['prod_filter']['cat_id'] == category_id:
                prod_filter = request.session['prod_filter']
                context.update(prod_filter)
                # filtering the products
                products = product_filter(products, data=prod_filter)
            else:
                del request.session['prod_filter']
        try:
            if request.GET['clear_filter'] == '1':
                # clearing filter and reset to default products fetching
                request.session.flush()
                context.pop('cat_id')
                context.pop('selected_brands')
                context.pop('sort_method')
                context.pop('min_price')
                context.pop('max_price')
                products = Product.objects.filter(Q(category=category) & Q(stock__gte=1))
        except:
            pass

    # Pagination
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context.update({
        'category': category,
        'page_obj': page_obj,
        'brands': brands,
        'total_pr': products.count()
    })
    return render(request, 'products/category_products.html', context)


def details_of_product(request, c_slug, p_slug):
    product = get_object_or_404(Product, slug=p_slug)
    related_products = Product.objects.exclude(id=product.id).filter(category__slug=c_slug)

    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'products/detail.html', context)


def get_cart_context(request):
    cart_obj = []
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user).order_by('-id')
        cart_length = cart_items.count()
        addresses = Address.objects.filter(user=request.user, is_available=True)
        for item in cart_items:
            cart_obj.append({
                'product': item.product,
                'qty': item.quantity,
                'total': item.item_total()
            })
    else:
        session_cart = request.session.get('cart', {})
        cart_length = len(session_cart)
        product_ids = session_cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            qty = session_cart[str(product.id)]['qty']
            total = product.price * qty
            cart_obj.append({
                'product': product,
                'qty': qty,
                'total': total
            })

    sub_total = float(sum(item['total'] for item in cart_obj))
    shipping_charge = 40
    tax = sub_total * 0.03  # 3% tax
    discount = sub_total * 0.02  # 2% discount
    grand_total = sub_total + tax + shipping_charge - discount

    context = {
        'cart_obj': cart_obj,
        'cart_length': cart_length,
        'sub_total': sub_total,
        'shipping_charge': shipping_charge,
        'tax': tax,
        'discount': discount,
        'grand_total': grand_total
    }

    if request.user.is_authenticated:
        context['addresses'] = addresses
    return context


def cart(request):
    return render(request, 'products/cart.html', {'cart_products': get_cart_context(request)})


def update_cart_context(request, prod_id):
    context = get_cart_context(request)
    product = get_object_or_404(Product, id=prod_id)
    qty = next((item['qty'] for item in context['cart_obj'] if item['product'].id == int(prod_id)), 0)
    price = product.price * qty

    context.update({
        "prod_id": prod_id,
        "qty": qty,
        "price": price
    })
    context.pop('cart_obj', None)
    context.pop('addresses', None)
    return context


def modify_cart(request, prod_id, qty_change):
    product = get_object_or_404(Product, id=prod_id)
    if request.user.is_authenticated:
        item, created = Cart.objects.get_or_create(product=product, user=request.user)
        item.quantity += qty_change
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()
    else:
        session_cart = request.session.get('cart', {})
        if prod_id in session_cart:
            session_cart[prod_id]['qty'] += qty_change
            if session_cart[prod_id]['qty'] <= 0:
                del session_cart[prod_id]
        else:
            if qty_change > 0:
                session_cart[prod_id] = {'qty': qty_change}
        request.session['cart'] = session_cart

    context = update_cart_context(request, prod_id)
    return JsonResponse(context)


def add_to_cart(request):
    prod_id = request.GET.get('prod_id')
    qty = int(request.GET.get('quantity', 1))
    return modify_cart(request, prod_id, qty)


def minus_from_cart(request):
    prod_id = request.GET.get('prod_id')
    return modify_cart(request, prod_id, -1)


def remove_from_cart(request):
    prod_id = request.GET.get('prod_id')
    product = get_object_or_404(Product, id=prod_id)

    if request.user.is_authenticated:
        Cart.objects.filter(product=product, user=request.user).delete()
    else:
        session_cart = request.session.get('cart', {})
        if prod_id in session_cart:
            del session_cart[prod_id]
            request.session['cart'] = session_cart

    context = update_cart_context(request, prod_id)
    return JsonResponse(context)
