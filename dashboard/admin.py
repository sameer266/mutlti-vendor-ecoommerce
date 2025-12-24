from django.contrib import admin
from .models import *

# Register all models
admin.site.register(UserRole)
admin.site.register(UserProfile)
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


admin.site.register(Slider)
admin.site.register(Banner)

admin.site.register(Supplier)
admin.site.register(Purchase)
admin.site.register(PurchaseItem)
admin.site.register(PurchaseInvoice)
admin.site.register(PurchaseInvoiceItem)

admin.site.register(OTPVerification)
admin.site.register(TaxCost)
