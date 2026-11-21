from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import (
    Product, Category, Wishlist, Order, OrderItem, ProductVariant
)
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required


def get_cart_data(request):
    cart = request.session.get('cart', {})

    cart_items = []
    cart_total = 0
    cart_count = 0

    for cart_key, quantity in cart.items():
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            continue

        if quantity <= 0:
            continue

        if cart_key.startswith('v_'):
            try:
                variant_id = int(cart_key[2:])
                variant = ProductVariant.objects.select_related(
                    'colour__product'
                ).get(id=variant_id)

                product = variant.colour.product

            except (ValueError, ProductVariant.DoesNotExist):
                continue

            colour_name = variant.colour.colour_name
            size = variant.size

        else:
            try:
                product = Product.objects.get(id=int(cart_key))
            except (ValueError, Product.DoesNotExist):
                continue

            variant = None
            colour_name = ''
            size = ''

        subtotal = product.price * quantity

        cart_items.append({
            'product': product,
            'variant': variant,
            'colour_name': colour_name,
            'size': size,
            'quantity': quantity,
            'subtotal': subtotal,
        })

        cart_total += subtotal
        cart_count += quantity

    return cart_items, cart_total, cart_count

def index(request):
    products = Product.objects.filter(show_on_homepage=True)
    main_categories = Category.objects.filter(parent=None)

    daily_sales_category = Category.objects.filter(
        name__iexact='Daily Sales',
        parent=None
    ).first()

    cart = request.session.get('cart', {})
    cart_items, cart_total, cart_count = get_cart_data(request)

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

    for product in products:
        product.cart_quantity = cart.get(str(product.id), 0)
        product.homepage_colours = []

        for colour in product.colours.prefetch_related('variants').all():
            variants = []

            for variant in colour.variants.all():
                variants.append({
                    'id': variant.id,
                    'size': variant.size,
                    'stock': variant.stock,
                })

            product.homepage_colours.append({
                'id': colour.id,
                'name': colour.colour_name,
                'variants': variants,
            })

    return render(request, 'core/index.html', {
        'products': products,
        'main_categories': main_categories,
        'daily_sales_category': daily_sales_category,
        'cart': cart,
        'wishlist_product_ids': wishlist_product_ids,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
    })

def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    subcategories = category.subcategories.all()

    if category.parent:
        category_filters = category.parent.subcategories.all()
    else:
        category_filters = subcategories

    products = Product.objects.filter(
        category=category
    ).prefetch_related(
        'colours__variants',
        'colours__images'
    )

    cart_items, cart_total, cart_count = get_cart_data(request)

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

    return render(request, 'core/category.html', {
        'category': category,
        'subcategories': subcategories,
        'category_filters': category_filters,
        'products': products,
        'product_count': products.count(),
        'wishlist_product_ids': wishlist_product_ids,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
    })


def product_list(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)

    return render(request, 'core/products.html', {
        'category': category,
        'products': products,
    })


def search_products(request):
    query = request.GET.get('q', '').strip()

    products = Product.objects.filter(
        name__icontains=query
    ) if query else Product.objects.none()

    return render(request, 'core/search_results.html', {
        'products': products,
        'query': query,
    })

def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'colours__images',
            'colours__variants'
        ),
        id=product_id
    )

    colour_data = []

    for colour in product.colours.all():
        images = []

        for image in colour.images.all():
            if image.image:
                images.append({
                    'view': image.view,
                    'url': image.image.url,
                })

        variants = []

        for variant in colour.variants.all():
            variants.append({
                'id': variant.id,
                'size': variant.size,
                'stock': variant.stock,
            })

        colour_data.append({
            'id': colour.id,
            'name': colour.colour_name,
            'images': images,
            'variants': variants,
        })

    # Keep this OUTSIDE the colour loop
    cart_items, cart_total, cart_count = get_cart_data(request)

    return render(request, 'core/product_detail.html', {
        'product': product,
        'colour_data': colour_data,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
    })


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    variant_id = request.POST.get('variant_id')
    cart = request.session.get('cart', {})

    variant = None

    if variant_id:
        variant = get_object_or_404(
            ProductVariant,
            id=variant_id,
            colour__product=product
        )

        if variant.stock <= 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'This variant is out of stock.'
                }, status=400)

            return redirect(request.META.get('HTTP_REFERER', 'core:index'))

        cart_key = f'v_{variant.id}'

    else:
        if product.colours.filter(variants__isnull=False).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Please select a colour and size first.'
                }, status=400)

            return redirect(request.META.get('HTTP_REFERER', 'core:index'))

        cart_key = str(product.id)

    current_quantity = int(cart.get(cart_key, 0))

    if variant and current_quantity >= variant.stock:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Not enough stock available.'
            }, status=400)

        return redirect(request.META.get('HTTP_REFERER', 'core:index'))

    cart[cart_key] = current_quantity + 1

    request.session['cart'] = cart
    request.session.modified = True

    # Return JSON for homepage AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_items, cart_total, cart_count = get_cart_data(request)

        cart_html = render_to_string('partials/cart_items.html', {
            'cart_items': cart_items,
            'cart_total': cart_total,
        })

        return JsonResponse({
            'success': True,
            'quantity': cart[cart_key],
            'cart_count': cart_count,
            'cart_html': cart_html,
        })

    # Normal redirect for regular form submissions
    return redirect(request.META.get('HTTP_REFERER', 'core:index'))

@require_POST
def update_cart_quantity(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})
    cart_key = request.POST.get('cart_key', str(product.id))

    if cart_key.startswith('v_'):
        try:
            variant = ProductVariant.objects.get(
                id=int(cart_key[2:]),
                colour__product=product
            )
        except (ValueError, ProductVariant.DoesNotExist):
            return JsonResponse({'success': False}, status=404)
    elif cart_key == str(product.id):
        variant = None
    else:
        return JsonResponse({'success': False}, status=400)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        return JsonResponse({'success': False}, status=400)

    if quantity <= 0:
        cart.pop(cart_key, None)
    else:
        if variant and quantity > variant.stock:
            return JsonResponse({
                'success': False,
                'message': 'Not enough stock available.'
            }, status=400)

        cart[cart_key] = quantity

    request.session['cart'] = cart
    request.session.modified = True

    cart_items, cart_total, cart_count = get_cart_data(request)

    cart_html = render_to_string('partials/cart_items.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
    })

    return JsonResponse({
        'success': True,
        'quantity': cart.get(cart_key, 0),
        'cart_count': cart_count,
        'cart_html': cart_html,
    })
@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart_key = request.POST.get('cart_key', str(product_id))

    if cart_key == str(product_id) or cart_key.startswith('v_'):
        cart.pop(cart_key, None)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect(request.META.get('HTTP_REFERER', 'core:cart'))
def cart_detail(request):
    cart_items, total, cart_count = get_cart_data(request)

    return render(request, 'core/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
    })


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    )

    if wishlist_item.exists():
        wishlist_item.delete()
        added = False
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product
        )
        added = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'added': added
        })

    return redirect(
        request.META.get('HTTP_REFERER', 'core:index')
    )


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product')

    print("LOGGED IN USER:", request.user)
    print("WISHLIST COUNT:", wishlist_items.count())
    print("WISHLIST ITEMS:", list(wishlist_items))

    return render(request, 'core/wishlist.html', {
        'wishlist_items': wishlist_items
    })



def checkout_view(request):
    cart = request.session.get('cart', {})

    cart_items, total, cart_count = get_cart_data(request)

    if not cart_items:
        return redirect('core:cart')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        house_address = request.POST.get('house_address', '').strip()
        street_address = request.POST.get('street_address', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()

        payment_method = request.POST.get('payment_method', '')

        valid_methods = [
            'upi', 'phonepe', 'paytm', 'card', 'cod'
        ]

        if not all([
            full_name, email, phone,
            house_address, street_address,
            city, state, pincode
        ]):
            error = "Please fill in all required fields."

        elif not phone.isdigit() or len(phone) != 10:
            error = "Please enter a valid 10-digit mobile number."

        elif not pincode.isdigit() or len(pincode) != 6:
            error = "Please enter a valid 6-digit PIN code."

        elif payment_method not in valid_methods:
            error = "Please select a valid payment method."

        else:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    house_address=house_address,
                    street_address=street_address,
                    landmark=landmark,
                    city=city,
                    state=state,
                    pincode=pincode,
                    payment_method=payment_method,
                    payment_status='pending',
                    status='pending',
                    total_amount=total,
                )

                for item in cart_items:
                    OrderItem.objects.create(
        order=order,
        product=item['product'],
        variant=item['variant'],
        colour_name=item['colour_name'],
        size=item['size'],
        product_name=item['product'].name,
        price=item['product'].price,
        quantity=item['quantity'],
    )
            request.session.pop('cart', None)
            request.session.modified = True

            return render(request, 'core/order_success.html', {
                'order': order
            })

    else:
        error = None

    return render(request, 'core/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'error': error,
    })
