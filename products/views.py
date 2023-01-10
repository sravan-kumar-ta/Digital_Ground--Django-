from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
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
    products = args[0]

    if len(selected_brands) != 0:
        selected_brands_objs = list()
        for brand in selected_brands:
            selected_brands_objs.append(get_object_or_404(Brand, name=brand))
        products = products.filter(brand__in=selected_brands_objs)

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
    products = Product.objects.filter(Q(category=category) & Q(stock__gte=1))
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
    paginator = Paginator(products, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context.update({
        'category': category,
        'page_obj': page_obj,
        'brands': brands
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
                print(cart_obj)

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


def add_to_cart(request):
    prod_id = request.POST['prod_id']
    try:
        qty = request.POST['quantity']
    except:
        qty = 1

    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=prod_id)
        if Cart.objects.filter(product=prod_id, user=request.user).exists():
            item = Cart.objects.get(product=prod_id, user=request.user)
            item.quantity += int(qty)
        else:
            item = Cart.objects.create(
                product=product,
                user=request.user,
                quantity=int(qty)
            )
        item.save()

    else:
        item = dict()
        item[prod_id] = {
            'qty': qty
        }

        if 'cart' in request.session:
            session_cart = request.session['cart']
            if prod_id in request.session['cart']:
                qty_in_session = int(session_cart[prod_id]['qty'])
                session_cart[prod_id]['qty'] = qty_in_session + int(qty)
                request.session['cart'] = session_cart
            else:
                session_cart.update(item)
                request.session['cart'] = session_cart
        else:
            request.session['cart'] = item

        request.session['cart_length'] = len(request.session['cart'])

    messages.success(request, 'Item added to the cart.')
    return redirect('products:cart')


def minus_from_cart(request):
    try:
        prod_id = request.POST['prod_id']
        if request.user.is_authenticated:
            item = Cart.objects.get(product=prod_id, user=request.user)
            item.quantity -= 1
            item.save()
            if item.quantity < 1:
                item.delete()

        else:
            session_cart = request.session['cart']
            qty_in_session = int(session_cart[prod_id]['qty'])
            session_cart[prod_id]['qty'] = qty_in_session - 1
            if session_cart[prod_id]['qty'] < 1:
                del session_cart[prod_id]
            request.session['cart'] = session_cart
    except:
        pass

    return redirect('products:cart')


def remove_from_cart(request, p_id):
    if request.user.is_authenticated:
        item = Cart.objects.get(product=p_id, user=request.user)
        item.delete()
    else:
        session_cart = request.session['cart']
        del session_cart[p_id]
        request.session['cart'] = session_cart
    messages.error(request, 'Item remove from your cart.')
    return redirect('products:cart')
