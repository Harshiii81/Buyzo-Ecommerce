from .models import Wishlist


def wishlist_count(request):
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(
            user=request.user
        ).count()
    else:
        count = 0

    return {
        'wishlist_count': count
    }


def cart_context(request):
    cart = request.session.get('cart', {})

    cart_count = sum(
        int(quantity) for quantity in cart.values()
    )

    return {
        'cart_count': cart_count
    }