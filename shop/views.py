from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.conf import settings as django_settings
from api.models import Product, CustomUser, Order, OrderItem
import json
import urllib.request
import urllib.error
from django.db import transaction
from django.core.cache import cache
from django.core.signing import TimestampSigner
from django.core.mail import send_mail
from django_ratelimit.decorators import ratelimit
from .forms import UserRegistrationForm, CheckoutForm
from api.views import signer


def home(request):
    """Головна сторінка з hero-банером і рекомендованими товарами."""
    featured_products = Product.objects.filter(stock__gt=0).order_by('-created_at')[:6]
    total_products = Product.objects.count()
    return render(request, 'shop/home.html', {
        'featured_products': featured_products,
        'total_products': total_products,
    })


def catalog(request):
    """Каталог товарів з пошуком та сортуванням."""
    products = Product.objects.all()

    # Пошук
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Сортування
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at')

    return render(request, 'shop/catalog.html', {
        'products': products,
        'query': query,
        'sort': sort,
    })


def product_detail(request, pk):
    """Деталі окремого товару."""
    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.exclude(pk=pk).filter(stock__gt=0).order_by('?')[:4]
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })


def cart_view(request):
    """Сторінка кошика."""
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    product_ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]
    products = Product.objects.in_bulk(product_ids)

    for product_id, item_data in cart.items():
        try:
            product = products.get(int(product_id))
            if not product:
                continue
            quantity = item_data.get('quantity', 1)
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except ValueError:
            continue

    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total': total,
    })


@require_POST
def cart_add(request):
    """Додати товар до кошика (AJAX)."""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': 'Невірні дані'}, status=400)

    try:
        product = Product.objects.get(pk=int(product_id))
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Товар не знайдено'}, status=404)

    cart = request.session.get('cart', {})

    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {'quantity': quantity}

    # Не більше, ніж є на складі
    if cart[product_id]['quantity'] > product.stock:
        cart[product_id]['quantity'] = product.stock

    request.session['cart'] = cart
    request.session.modified = True

    cart_count = sum(item.get('quantity', 0) for item in cart.values())
    return JsonResponse({
        'success': True,
        'cart_count': cart_count,
        'message': f'«{product.name}» додано до кошика!',
    })


@require_POST
def cart_update(request):
    """Оновити кількість товару в кошику (AJAX)."""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': 'Невірні дані'}, status=400)

    cart = request.session.get('cart', {})

    if product_id in cart:
        if quantity <= 0:
            del cart[product_id]
        else:
            try:
                product = Product.objects.get(pk=int(product_id))
                cart[product_id]['quantity'] = min(quantity, product.stock)
            except Product.DoesNotExist:
                del cart[product_id]

    request.session['cart'] = cart
    request.session.modified = True

    cart_count = sum(item.get('quantity', 0) for item in cart.values())
    return JsonResponse({'success': True, 'cart_count': cart_count})


@require_POST
def cart_remove(request):
    """Видалити товар з кошика (AJAX)."""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': 'Невірні дані'}, status=400)

    cart = request.session.get('cart', {})
    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart
    request.session.modified = True

    cart_count = sum(item.get('quantity', 0) for item in cart.values())
    return JsonResponse({'success': True, 'cart_count': cart_count})


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register_view(request):
    """Сторінка реєстрації."""
    if request.user.is_authenticated:
        return redirect('shop:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_email_verified = False  # Require email verification
            user.save()
            
            # Send verification email
            token = signer.sign(user.email)
            verification_url = f"{request.scheme}://{request.get_host()}/api/auth/verify-email/?token={token}"
            
            subject = "Підтвердження реєстрації — 3D Store"
            message = (
                f"Вітаємо, {user.first_name or 'користувачу'}!\n\n"
                "Дякуємо за реєстрацію в нашому інтернет-магазині 3D-друкованих фігурок.\n"
                "Щоб завершити реєстрацію та підтвердити email, перейдіть за посиланням нижче:\n"
                f"{verification_url}\n\n"
                "Це посилання дійсне протягом 24 годин."
            )
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Реєстрація успішна! Перевірте електронну пошту для підтвердження.')
            except Exception:
                messages.warning(request, 'Реєстрація успішна, але не вдалося надіслати лист для підтвердження.')

            return redirect('shop:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request, 'shop/register.html')

    return render(request, 'shop/register.html')


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def login_view(request):
    """Сторінка входу."""
    if request.user.is_authenticated:
        return redirect('shop:home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, 'msg.login.error.invalid')
            return render(request, 'shop/login.html', {'email': email})

        if not user.check_password(password):
            messages.error(request, 'msg.login.error.invalid')
            return render(request, 'shop/login.html', {'email': email})

        if not user.is_active:
            messages.error(request, 'msg.login.error.inactive')
            return render(request, 'shop/login.html', {'email': email})

        login(request, user)
        messages.success(request, 'msg.login.success')

        next_url = request.GET.get('next', '')
        if next_url:
            return redirect(next_url)
        return redirect('shop:home')

    return render(request, 'shop/login.html')


def logout_view(request):
    """Вихід з системи."""
    logout(request)
    messages.info(request, 'msg.logout.success')
    return redirect('shop:home')


@login_required
def profile_view(request):
    """Профіль користувача."""
    return render(request, 'shop/profile.html')


def checkout_view(request):
    """Сторінка оформлення замовлення."""
    cart = request.session.get('cart', {})

    if not cart:
        messages.warning(request, 'msg.checkout.empty')
        return redirect('shop:cart')

    # Підготовка товарів кошика
    cart_items = []
    total = 0
    product_ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]
    products = Product.objects.in_bulk(product_ids)

    for product_id, item_data in cart.items():
        try:
            product = products.get(int(product_id))
            if not product:
                continue
            quantity = item_data.get('quantity', 1)
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except ValueError:
            continue

    if not cart_items:
        messages.warning(request, 'msg.checkout.not_found')
        return redirect('shop:cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Створюємо замовлення
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    first_name=cd['first_name'],
                    last_name=cd['last_name'],
                    phone=cd['phone'],
                    email=cd['email'],
                    delivery_service=cd['delivery_service'],
                    payment_method=cd['payment_method'],
                    np_city=cd.get('np_city', ''),
                    np_city_ref=cd.get('np_city_ref', ''),
                    np_warehouse=cd.get('np_warehouse', ''),
                    np_warehouse_ref=cd.get('np_warehouse_ref', ''),
                    ppl_city=cd.get('ppl_city', ''),
                    ppl_point=cd.get('ppl_point', ''),
                    meest_country=cd.get('meest_country', ''),
                    meest_city=cd.get('meest_city', ''),
                    meest_address=cd.get('meest_address', ''),
                    total_price=total,
                    comment=cd.get('comment', ''),
                )

                # Додаємо товари до замовлення
                order_items_to_create = []
                products_to_update = []
                for item in cart_items:
                    order_items_to_create.append(
                        OrderItem(
                            order=order,
                            product=item['product'],
                            quantity=item['quantity'],
                            price=item['product'].price,
                        )
                    )
                    # Зменшуємо кількість на складі
                    product = item['product']
                    product.stock = max(0, product.stock - item['quantity'])
                    products_to_update.append(product)
                
                OrderItem.objects.bulk_create(order_items_to_create)
                Product.objects.bulk_update(products_to_update, ['stock'])

            # Очищаємо кошик
            request.session['cart'] = {}
            request.session.modified = True

            return redirect('shop:payment', order_id=order.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request, 'shop/checkout.html', {
                'cart_items': cart_items,
                'total': total,
                'form_data': request.POST,
            })

    # Передаємо дані користувача для автозаповнення
    form_data = {}
    if request.user.is_authenticated:
        form_data = {
            'first_name': request.user.first_name,
            'email': request.user.email,
        }

    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'form_data': form_data,
    })


def checkout_success(request):
    """Сторінка успішного оформлення замовлення."""
    return render(request, 'shop/checkout_success.html')


def np_search_cities(request):
    """Proxy API для пошуку міст Нової Пошти."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'cities': []})

    cache_key = f"np_cities_{query.lower()}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse({'cities': cached_data})

    api_key = django_settings.NOVA_POSHTA_API_KEY

    payload = json.dumps({
        'apiKey': api_key,
        'modelName': 'AddressGeneral',
        'calledMethod': 'searchSettlements',
        'methodProperties': {
            'CityName': query,
            'Limit': '20',
            'Page': '1',
        }
    }).encode('utf-8')

    try:
        req = urllib.request.Request(
            'https://api.novaposhta.ua/v2.0/json/',
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        cities = []
        if data.get('success') and data.get('data'):
            for entry in data['data']:
                for addr in entry.get('Addresses', []):
                    cities.append({
                        'ref': addr.get('DeliveryCity', ''),
                        'name': addr.get('Present', ''),
                    })
        cache.set(cache_key, cities, timeout=86400)
        return JsonResponse({'cities': cities})
    except (urllib.error.URLError, json.JSONDecodeError, Exception):
        return JsonResponse({'cities': [], 'error': 'Помилка з\'єднання з API'})


def np_search_warehouses(request):
    """Proxy API для пошуку відділень Нової Пошти за містом."""
    city_ref = request.GET.get('city_ref', '').strip()
    search = request.GET.get('q', '').strip()

    if not city_ref:
        return JsonResponse({'warehouses': []})

    cache_key = f"np_warehouses_{city_ref}_{search.lower()}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse({'warehouses': cached_data})

    api_key = django_settings.NOVA_POSHTA_API_KEY

    method_properties = {
        'CityRef': city_ref,
        'Limit': '50',
        'Page': '1',
    }
    if search:
        method_properties['FindByString'] = search

    payload = json.dumps({
        'apiKey': api_key,
        'modelName': 'Address',
        'calledMethod': 'getWarehouses',
        'methodProperties': method_properties,
    }).encode('utf-8')

    try:
        req = urllib.request.Request(
            'https://api.novaposhta.ua/v2.0/json/',
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        warehouses = []
        if data.get('success') and data.get('data'):
            for w in data['data']:
                warehouses.append({
                    'ref': w.get('Ref', ''),
                    'name': w.get('Description', ''),
                    'short_address': w.get('ShortAddress', ''),
                    'number': w.get('Number', ''),
                })
        cache.set(cache_key, warehouses, timeout=86400)
        return JsonResponse({'warehouses': warehouses})
    except (urllib.error.URLError, json.JSONDecodeError, Exception):
        return JsonResponse({'warehouses': [], 'error': 'Помилка з\'єднання з API'})

def payment_view(request, order_id):
    """Сторінка імітації оплати."""
    order = get_object_or_404(Order, id=order_id)
    
    # If already paid/processing, redirect to success
    if order.status != 'new':
        return redirect('shop:checkout_success')
        
    return render(request, 'shop/payment.html', {'order': order})


def payment_process(request, order_id):
    """Обробка результату імітації оплати."""
    if request.method != 'POST':
        return redirect('shop:checkout')
        
    order = get_object_or_404(Order, id=order_id)
    
    # Simulate payment success
    order.status = 'processing'
    order.save()
    
    messages.success(request, 'msg.checkout.success')
    return redirect('shop:checkout_success')
