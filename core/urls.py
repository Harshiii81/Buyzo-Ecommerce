from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
        path("search/", views.search_products, name="search_products"),
    path(
        "category/<int:category_id>/",
        views.category_detail,
        name="category_detail"
    ),

    path(
    "wishlist/toggle/<int:product_id>/",
    views.toggle_wishlist,
    name="toggle_wishlist"
),

path("wishlist/", views.wishlist_view, name="wishlist"),

    path(
        "products/<int:category_id>/",
        views.product_list,
        name="product_list"
    ),
    path(
    "product/<int:product_id>/",
    views.product_detail,
    name="product_detail"
),
path(
    "cart/add/<int:product_id>/",
    views.add_to_cart,
    name="add_to_cart"
),

path(
    "cart/remove/<int:product_id>/",
    views.remove_from_cart,
    name="remove_from_cart"
),
path(
    "cart/",
    views.cart_detail,
    name="cart"
),
path(
    "cart/update/<int:product_id>/",
    views.update_cart_quantity,
    name="update_cart_quantity"
),

path("checkout/", views.checkout_view, name="checkout"),

]