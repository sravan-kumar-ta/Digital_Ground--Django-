from io import BytesIO

import razorpay
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa

from account.models import Address
from core_folder import settings
from orders.models import Order, ProductInOrder
from products.models import Cart, Product

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_ID, settings.RAZORPAY_KEY))


@login_required(login_url='login')
def checkout(request):
    address_id = request.GET['address']
    address = get_object_or_404(Address, id=address_id)
    cart_objs = Cart.objects.filter(user=request.user)

    sub_total = 0
    for i in cart_objs:
        sub_total += i.item_total()

    tax = sub_total * 3 / 100  # 3% tax
    shipping_charge = 40
    discount = sub_total * 2 / 100  # 2% discount
    grand_total = sub_total + tax + shipping_charge - discount

    notes = {'order-type': "basic order from the website", 'key': 'value'}
    razorpay_order = razorpay_client.order.create(dict(amount=int(grand_total * 100), notes=notes, currency="INR"))

    Order.objects.create(
        user=request.user,
        address=address,
        sub_total=sub_total,
        tax=tax,
        shipping_charge=shipping_charge,
        discount=discount,
        grand_total=grand_total,
        razorpay_order_id=razorpay_order['id']
    ).save()

    context = {
        'address': address,
        'cart_objs': cart_objs,
        'sub_total': sub_total,
        'tax': tax,
        'shipping_charge': shipping_charge,
        'discount': discount,
        'grand_total': grand_total,
        'razorpay_id': settings.RAZORPAY_ID,
        'order_id': razorpay_order['id'],
        'currency': razorpay_order['currency'],
    }
    return render(request, 'orders/checkout.html', context)


@login_required(login_url='login')
@csrf_exempt
def handle_request(request):
    if request.method == 'POST':
        try:
            params_dict = {
                'razorpay_order_id': request.POST['razorpay_order_id'],
                'razorpay_payment_id': request.POST['razorpay_payment_id'],
                'razorpay_signature': request.POST['razorpay_signature'],
            }
            razorpay_client.utility.verify_payment_signature(params_dict)

            order = get_object_or_404(Order, razorpay_order_id=params_dict['razorpay_order_id'])
            order.razorpay_payment_id = params_dict['razorpay_payment_id']
            order.razorpay_signature = params_dict['razorpay_signature']
            order.payment_status = 1  # 1 for success status
            order.save()

            cart_item = Cart.objects.filter(user=request.user)
            for item in cart_item:
                ProductInOrder.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                ).save()

                product = get_object_or_404(Product, id=item.product.id)
                product.stock -= item.quantity
                product.save()

            cart_item.delete()

            context = {
                'status': True,
                'order': order,
            }

            return render(request, 'orders/payment_status.html', context)
        except:
            return render(request, 'orders/payment_status.html', {'status': False})
    else:
        return redirect('products:cart')


@login_required(login_url='login')
def orders(request):
    return render(request, 'orders/orders.html', {'orders': Order.objects.filter(user=request.user, payment_status=1)})


@login_required(login_url='login')
def order_detail(request, o_id):
    order = get_object_or_404(Order, id=o_id)
    context = {
        'order': order,
        'products': ProductInOrder.objects.filter(order=order)
    }
    return render(request, 'orders/order_detail.html', context)


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


@login_required(login_url='login')
def generate_invoice(request, o_id):
    try:
        order = Order.objects.get(id=o_id, user=request.user, payment_status=1)
    except:
        return HttpResponse("<h1>505 Not Found</h1>")

    data = {
        'order_id': order.order_id,
        'order': order,
        'date': order.datetime_of_payment.strftime("%b %d %Y"),
        'transaction_id': order.razorpay_payment_id,
    }

    pdf = render_to_pdf('orders/invoice.html', data)
    return HttpResponse(pdf, content_type='application/pdf')
