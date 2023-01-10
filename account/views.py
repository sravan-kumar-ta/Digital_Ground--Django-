import requests
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, FormView, ListView

from account.CustomBackend import CustomAuth
from account.forms import CustomUserCreationForm, LoginForm, ChangePasswordForm, ResetPasswordForm, VerifyForm
from account.models import CustomUser, Address
from account.twilio import _send_otp, _verify_otp
from orders.models import Order
from products.models import Product, Cart, Wishlist, Category, Brand


class RegistrationView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "account/register.html"
    success_url = reverse_lazy("login")


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'account/login.html'

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = CustomAuth.authenticate(self.request, username=username, password=password)

        if user:
            if not user.is_active:
                self.request.session['phone_number'] = user.phone_number
                messages.error(self.request, "You have not activated your account.")
                messages.success(self.request, "OTP sent your phone number")
                _send_otp(user.phone_number)
                return redirect('verify')

            if 'cart' in self.request.session:
                session_cart = self.request.session['cart']
                for i in session_cart:
                    item = session_cart[i]
                    product = get_object_or_404(Product, id=i)
                    quantity = item['qty']
                    cart_item = Cart.objects.create(product=product, user=user, quantity=quantity)
                    cart_item.save()

            login(request=self.request, user=user)
            self.request.session['cart_length'] = Cart.objects.filter(user=self.request.user).count()
            messages.success(self.request, 'Successfully logged in')

            # If url have next page
            url = self.request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('products:home')

        else:
            messages.error(self.request, "Invalid credentials..!")
            return redirect('login')

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid Credentials')
        return redirect('login')


def verify_otp(request):
    if request.method == 'POST':
        form = VerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('code')
            phone_number = request.session['phone_number']

            if _verify_otp(phone_number, code):
                user = CustomUser.objects.get(phone_number=phone_number)
                user.is_active = True
                user.save()
                messages.success(request, 'Your account has been verified successfully.')
                return redirect('login')
            else:
                messages.error(request, 'Enter the correct OTP')
                return redirect('verify')
    else:
        form = VerifyForm()
        return render(request, 'account/otp_verification.html', {'form': form})


@login_required(login_url='login')
def profile(request):
    addresses = Address.objects.filter(user=request.user, is_available=True)
    orders = Order.objects.filter(user=request.user, payment_status=1)

    context = {
        'addresses': addresses,
        'orders': orders
    }
    return render(request, 'account/profile.html', context)


@method_decorator(login_required(login_url='login'), name='dispatch')
class WishlistView(ListView):
    model = Wishlist
    context_object_name = 'wishlist'
    template_name = 'account/wishlist.html'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


def add_to_wishlist(request):
    p_id = request.GET['prod_id']
    product = get_object_or_404(Product, id=p_id)
    try:
        obj = Wishlist.objects.create(product=product, user=request.user)
        obj.save()
        messages.success(request, 'Item added to your wishlist.')
    except:
        data = 0
    else:
        data = 1

    # The data will be checked in ajax. If 1, redirect to wishlist page.
    return JsonResponse({'data': data})


@login_required(login_url='login')
def remove_from_wishlist(request, p_id):
    product = get_object_or_404(Product, id=p_id)
    obj = Wishlist.objects.get(product=product, user=request.user)
    obj.delete()
    messages.error(request, 'Item remove from your wishlist.')
    return redirect('wishlist')


@login_required(login_url='login')
def add_address(request):
    if request.method == 'POST':
        try:
            pin_code = request.POST['pin']
            state = request.POST['state']
            district = request.POST['district']
            locality = request.POST['locality']
            phone = request.POST['phone']
            address = Address.objects.create(
                pin_code=pin_code,
                state=state,
                district=district,
                locality=locality,
                phone_number=phone,
                user=request.user
            )
            address.save()
            messages.success(request, 'Successfully added your address.')
            return redirect('profile')
        except:
            messages.error(request, 'Please enter your valid address..')

    return render(request, 'account/add_address.html')


@login_required(login_url='login')
def remove_address(request, id):
    address = get_object_or_404(Address, user=request.user, id=id)
    address.is_available = False
    address.save()
    messages.success(request, "Address removed.")
    return redirect('profile')


@login_required(login_url='login')
def find_locality(request):
    pin_code = request.GET['pin_code']

    url = "https://api.postalpincode.in/pincode/" + str(pin_code)
    response = requests.get(url)
    data = response.json()

    post_offices = data[0]['PostOffice']
    locality = [i['Name'] for i in post_offices]

    locality = render_to_string('partials/_localities.html', {'localities': locality})
    data = {
        'state': data[0]['PostOffice'][0]['State'],
        'district': data[0]['PostOffice'][0]['District'],
        'phone': request.user.phone_number,
        'locality': locality
    }
    return JsonResponse({'data': data})


class ChangePasswordView(PasswordChangeView):
    template_name = 'account/change_password.html'
    form_class = ChangePasswordForm


class ResetPasswordView(PasswordResetView):
    template_name = 'account/password_reset.html'
    form_class = ResetPasswordForm


def dashboard(request):
    users = CustomUser.objects.filter(is_staff=False, is_active=True).count()
    orders = Order.objects.all().count()
    brands = Brand.objects.all().count()
    categories = Category.objects.all()
    categories_count = categories.count()

    products_dict = {}
    for category in categories:
        count = Product.objects.filter(category=category).count()
        products_dict[category.title] = count

    context = {
        'title': 'Site administration',
        'users': users,
        'orders': orders,
        'brands': brands,
        'categories_count': categories_count,
        'products': products_dict
    }
    return render(request, 'admin/custom_dashboard.html', context)


def handle_not_fount(request, exception):
    return render(request, 'error_404.html')
