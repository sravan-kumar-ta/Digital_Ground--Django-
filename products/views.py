from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
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


def cart(request):
    cart_obj = list()
    total_price = 0
    context = {}

    if request.user.is_authenticated:
        products = Cart.objects.filter(user=request.user)
        for i in products:
            total = int(i.item_total())
            product = get_object_or_404(Product, id=i.product.id)
            temp = {
                'product': product,
                'qty': i.quantity,
                'total': total
            }
            total_price += total
            cart_obj.append(temp)
        request.session['cart_length'] = Cart.objects.filter(user=request.user).count()
        addresses = Address.objects.filter(user=request.user)
        context = {'addresses': addresses}

    else:
        # request.session.flush()
        if 'cart' in request.session:
            session_cart = request.session['cart']
            for i in session_cart:
                item = session_cart[i]
                product = get_object_or_404(Product, id=i)
                quantity = item['qty']
                total = product.price * int(quantity)
                temp = {
                    'product': product,
                    'qty': quantity,
                    'total': total
                }
                total_price += total
                cart_obj.append(temp)

            request.session['cart_length'] = len(request.session['cart'])

    if len(cart_obj) < 1:
        context = None
    else:
        tax = total_price * 3 / 100  # 3% tax
        shipping_charge = 40
        discount = total_price * 2 / 100  # 2% discount
        grand_total = total_price + tax + shipping_charge - discount

        context['cart_obj'] = cart_obj
        context['total_price'] = total_price
        context['tax'] = tax
        context['shipping_charge'] = shipping_charge
        context['discount'] = discount
        context['grand_total'] = grand_total

    return render(request, 'products/cart.html', {'cart_products': context})


def total_price(price):
    tax = price * 3 / 100  # 3% tax
    shipping_charge = 40
    discount = price * 2 / 100  # 2% discount
    grand_total = price + tax + shipping_charge - discount
    context = {
        "sub_total": round(price, 2),
        "tax": round(tax, 2),
        "shipping_charge": round(shipping_charge, 2),
        "discount": round(discount, 2),
        "grand_total": round(grand_total, 2)
    }
    return context


def add_to_cart(request):
    prod_id = request.GET.get('prod_id')
    qty = int(request.GET.get('quantity', 1))
    product = get_object_or_404(Product, id=prod_id)
    context = {}

    if request.user.is_authenticated:
        item, created = Cart.objects.get_or_create(
            product=product,
            user=request.user
        )
        item.quantity += qty
        qty = item.quantity
        item.save()
        price = item.item_total()

        total_prz = 0
        products = Cart.objects.filter(user=request.user)
        for i in products:
            total = int(i.item_total())
            total_prz += total

        context = total_price(total_prz)

    else:
        session_cart = request.session.get('cart', {})
        session_cart[prod_id] = {'qty': session_cart.get(prod_id, {'qty': 0})['qty'] + qty}
        qty = session_cart[prod_id]['qty']
        request.session['cart'] = session_cart
        price = product.price * qty

        total_prz = 0
        for i in session_cart:
            item = session_cart[i]
            product = get_object_or_404(Product, id=i)
            quantity = item['qty']
            total = product.price * int(quantity)
            total_prz += total

        context = total_price(total_prz)

    context.update({"prod_id": prod_id, "qty": qty, "price": price})

    return JsonResponse(context)


def minus_from_cart(request):
    prod_id = request.GET['prod_id']
    product = get_object_or_404(Product, id=prod_id)
    qty = price = 0
    context = {}
    try:
        if request.user.is_authenticated:
            item = Cart.objects.get(product=prod_id, user=request.user)
            item.quantity -= 1
            qty = item.quantity
            item.save()
            price = item.item_total()
            if item.quantity < 1:
                item.delete()
                price = 0

            total_prz = 0
            products = Cart.objects.filter(user=request.user)
            for i in products:
                total = int(i.item_total())
                total_prz += total

            context = total_price(total_prz)

        else:
            session_cart = request.session['cart']
            qty_in_session = int(session_cart[prod_id]['qty'])
            # session_cart[prod_id] = {'qty': qty_in_session - 1}
            session_cart[prod_id]['qty'] = qty_in_session - 1
            qty = session_cart[prod_id]['qty']
            price = product.price * qty
            if session_cart[prod_id]['qty'] < 1:
                del session_cart[prod_id]
                price = 0
            request.session['cart'] = session_cart

            total_prz = 0
            for i in session_cart:
                item = session_cart[i]
                product = get_object_or_404(Product, id=i)
                quantity = item['qty']
                total = product.price * int(quantity)
                total_prz += total

            context = total_price(total_prz)
    except:
        pass

    context.update({"prod_id": prod_id, "qty": qty, "price": price})

    return JsonResponse(context)


def remove_from_cart(request):
    prod_id = request.GET['prod_id']
    if request.user.is_authenticated:
        item = Cart.objects.get(product=prod_id, user=request.user)
        item.delete()

        total_prz = 0
        products = Cart.objects.filter(user=request.user)
        for i in products:
            total = int(i.item_total())
            total_prz += total

        context = total_price(total_prz)
    else:
        session_cart = request.session['cart']
        del session_cart[prod_id]
        request.session['cart'] = session_cart

        total_prz = 0
        for i in session_cart:
            item = session_cart[i]
            product = get_object_or_404(Product, id=i)
            quantity = item['qty']
            total = product.price * int(quantity)
            total_prz += total

        context = total_price(total_prz)

    context.update({"prod_id": prod_id})

    return JsonResponse(context)
