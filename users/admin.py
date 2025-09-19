from django.contrib import admin
from .models import (
    User,
    VendorUser,
    KYC,
    Category,
    SubCategory,
    AttributeCategory,
    Attribute,
    ProductAttribute,
    Product,
    ProductImage,
    ShippingOption,
    FlashSale,

    Banner,
    Cart,
    CartItem,
    ShippingAddress,
    Order
)

# Simple registration of all models
admin.site.register(User)
admin.site.register(VendorUser)
admin.site.register(KYC)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(AttributeCategory)
admin.site.register(Attribute)
admin.site.register(ProductAttribute)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ShippingOption)
admin.site.register(FlashSale)
admin.site.register(Banner)

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ShippingAddress)
admin.site.register(Order)
