from django.contrib import admin
from .models import *

# Register all models
admin.site.register(UserRole)
admin.site.register(UserProfile)
admin.site.register(Vendor)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductVariant)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Coupon)
admin.site.register(CouponUsage)
admin.site.register(Organization)
admin.site.register(Newsletter)
admin.site.register(Contact)
admin.site.register(Notification)
admin.site.register(VendorCommission)

admin.site.register(VendorPayoutRequest)
admin.site.register(VendorWallet)

admin.site.register(Slider)
admin.site.register(Banner)
