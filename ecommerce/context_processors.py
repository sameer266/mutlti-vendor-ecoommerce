from dashboard.models import Cart, Category

def global_context(request):
    """
    Provides cart item count and active categories globally.
    Works for both authenticated and guest users.
    """
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')

    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        # For guest users, use session_key
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_items = Cart.objects.filter(session_key=session_key)

    cart_count = sum(item.quantity for item in cart_items)

    return {
        'cart_count': cart_count,
        'categories': categories,
    }
