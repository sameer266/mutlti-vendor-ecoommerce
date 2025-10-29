from dashboard.models import Cart, Category,Organization,VendorPayoutRequest,Vendor,Order

def global_context(request):
    """
    Provides cart item count and active categories globally.
    Works for both authenticated and guest users.
    """
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')

    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_items = Cart.objects.filter(session_key=session_key)

    cart_count = sum(item.quantity for item in cart_items)
    organization=Organization.objects.first()
    total_pending_payouts=VendorPayoutRequest.objects.filter(status='pending').count()
    
    # Vendor 
    total_vendor_pending_orders=0
    total_vendor_pending_payouts=0
    if request.user.is_authenticated and  request.user.role.role == 'vendor':
        vendor=Vendor.objects.get(user=request.user)
        total_vendor_pending_payouts=VendorPayoutRequest.objects.filter(vendor=vendor,status="pending").count()
        total_vendor_pending_orders=Order.objects.filter(items__vendor=vendor,status='pending').count()
    

    return {
        'cart_count': cart_count,
        'categories': categories,
        'organization':organization,
        'total_pending_payouts':total_pending_payouts,
        # vendor
        'total_vendor_pending_orders':total_vendor_pending_orders,
        'total_vendor_pending_payouts':total_vendor_pending_payouts,
       
    }
