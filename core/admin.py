
from django.contrib import admin
from .models import (
    Product, Wishlist, Category, Order, OrderItem, SavedAddress,
    ProductColour, ProductImage, ProductVariant
)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'id')
    list_filter = ('parent',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'show_on_homepage')
    list_filter = ('category', 'show_on_homepage')
    search_fields = ('name',)
    list_editable = ('show_on_homepage',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'full_name', 'phone',
        'total_amount', 'payment_method',
        'payment_status', 'status', 'created_at'
    )
    list_filter = ('status', 'payment_status', 'payment_method')
    search_fields = ('full_name', 'email', 'phone')
    inlines = [OrderItemInline]

@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
        'phone',
        'city',
        'state',
        'pincode',
        'is_default'
    )

    list_filter = ('is_default', 'state', 'city')
    search_fields = ('user__username', 'full_name', 'phone')

@admin.register(ProductColour)
class ProductColourAdmin(admin.ModelAdmin):
    list_display = ('product', 'colour_name')
    list_filter = ('colour_name',)
    search_fields = ('product__name', 'colour_name')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('colour', 'view', 'image')
    list_filter = ('view',)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('colour', 'size', 'stock')
    list_filter = ('size',)
    search_fields = ('colour__product__name', 'colour__colour_name')