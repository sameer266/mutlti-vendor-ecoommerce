from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from .models import (
    UserRole, UserProfile, Vendor, Category, Product, ProductImage, ProductVariant, Order, OrderItem, 
    Review, Coupon, ShippingZone, Organization, Newsletter, Contact, 
    Notification, Slider, Banner, HomeCategory, VendorPayout, VendorCommission, VendorPayoutRequest
)

# Helper decorator to check admin access
def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role') or not request.user.role.is_admin():
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

# Admin Dashboard
@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    customers_count = UserRole.objects.filter(role='customer').count()
    vendors_count = UserRole.objects.filter(role='vendor').count()
    admins_count = UserRole.objects.filter(role='admin').count()
    total_vendors = Vendor.objects.count()
    verified_vendors = Vendor.objects.filter(verification_status='verified').count()
    pending_vendors = Vendor.objects.filter(verification_status='pending').count()
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(stock__lte=5, stock__gt=0).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(Sum('total'))['total__sum'] or 0
    active_sliders = Slider.objects.filter(is_active=True).count()
    active_banners = Banner.objects.filter(is_active=True).count()
    active_home_categories = HomeCategory.objects.filter(is_active=True).count()
    total_reviews = Review.objects.count()
    unread_contacts = Contact.objects.filter(is_read=False).count()
    newsletter_subscribers = Newsletter.objects.filter(is_active=True).count()
    unread_notifications = Notification.objects.filter(is_read=False).count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    recent_products = Product.objects.order_by('-created_at')[:5]
    recent_sliders = Slider.objects.order_by('-created_at')[:5]
    recent_banners = Banner.objects.order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'customers_count': customers_count,
        'vendors_count': vendors_count,
        'admins_count': admins_count,
        'total_vendors': total_vendors,
        'verified_vendors': verified_vendors,
        'pending_vendors': pending_vendors,
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'active_sliders': active_sliders,
        'active_banners': active_banners,
        'active_home_categories': active_home_categories,
        'total_reviews': total_reviews,
        'unread_contacts': unread_contacts,
        'newsletter_subscribers': newsletter_subscribers,
        'unread_notifications': unread_notifications,
        'recent_orders': recent_orders,
        'recent_products': recent_products,
        'recent_sliders': recent_sliders,
        'recent_banners': recent_banners,
    }
    return render(request, 'dashboard/pages/dashboard.html', context)

# User Management
@admin_required
def admin_users_list(request):
    search = request.GET.get('search', '')
    role = request.GET.get('role', '')
    users = User.objects.all().select_related('role').order_by('-date_joined')

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )

    if role in ['customer', 'vendor', 'admin']:
        users = users.filter(role__role=role)

    return render(request, 'dashboard/pages/users/users_list.html', {
        'users': users,
    })

@admin_required
def admin_user_add(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        user = User.objects.create_user(username=username, email=email, password=password)
        UserRole.objects.create(user=user, role=role)
        return redirect('admin_users_list')
    return render(request, 'dashboard/pages/users/user_add.html')

@admin_required
def admin_user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name=request.POST.get('first_name')
        user.last_name=request.POST.get('last_name')
        user.save()      
        return redirect('admin_users_list')
    return render(request, 'dashboard/pages/users/edit_user.html', {'user': user})

@admin_required
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk != request.user.pk:  # Prevent self-deletion
        user.delete()
    return redirect('admin_users_list')

# Vendor Management
@admin_required
def admin_vendors_list(request):
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    vendors = Vendor.objects.all().order_by('-created_at')

    if search:
        vendors = vendors.filter(
            Q(shop_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(user__username__icontains=search)
        )

    if status_filter:
        vendors = vendors.filter(verification_status=status_filter)

    return render(request, 'dashboard/pages/vendor/vendors_list.html', {'vendors': vendors})

@admin_required
def admin_vendors_pending_kyc(request):
    vendors = Vendor.objects.filter(verification_status='pending').order_by('-created_at')
    return render(request, 'dashboard/pages/vendor/pending_vendors.html', {'vendors': vendors})

@admin_required
def admin_vendors_verified_kyc(request):
    vendors = Vendor.objects.filter(verification_status='verified').order_by('-created_at')
    return render(request, 'dashboard/pages/vendor/verified_vendors.html', {'vendors': vendors})

@admin_required
def admin_vendor_add(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        user = get_object_or_404(User, pk=user_id)
        vendor = Vendor.objects.create(
            user=user,
            shop_name=request.POST.get('shop_name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            province=request.POST.get('province'),
            pan_number=request.POST.get('pan_number'),
            citizenship_number=request.POST.get('citizenship_number', ''),
            bank_name=request.POST.get('bank_name', ''),
            bank_account_number=request.POST.get('bank_account_number', ''),
            bank_account_holder=request.POST.get('bank_account_holder', ''),
            verification_status=request.POST.get('verification_status', 'pending')
        )
        if request.FILES.get('shop_logo'):
            vendor.shop_logo = request.FILES['shop_logo']
        if request.FILES.get('shop_banner'):
            vendor.shop_banner = request.FILES['shop_banner']
        if request.FILES.get('pan_document'):
            vendor.pan_document = request.FILES['pan_document']
        if request.FILES.get('citizenship_front'):
            vendor.citizenship_front = request.FILES['citizenship_front']
        if request.FILES.get('citizenship_back'):
            vendor.citizenship_back = request.FILES['citizenship_back']
        if request.FILES.get('company_registration'):
            vendor.company_registration = request.FILES['company_registration']
        vendor.save()
        return redirect('admin_vendors_list')
    users = User.objects.all()
    provinces = Vendor.PROVINCE_CHOICES
    return render(request, 'dashboard/pages/vendor/add_vendor.html', {'users': users, 'provinces': provinces})

@admin_required
def admin_vendor_update(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.shop_name = request.POST.get('shop_name')
        vendor.phone = request.POST.get('phone')
        vendor.email = request.POST.get('email')
        vendor.address = request.POST.get('address')
        vendor.city = request.POST.get('city')
        vendor.province = request.POST.get('province')
        vendor.pan_number = request.POST.get('pan_number')
        vendor.citizenship_number = request.POST.get('citizenship_number', '')
        vendor.bank_name = request.POST.get('bank_name', '')
        vendor.bank_account_number = request.POST.get('bank_account_number', '')
        vendor.bank_account_holder = request.POST.get('bank_account_holder', '')
        vendor.verification_status = request.POST.get('verification_status')
        vendor.rejection_reason = request.POST.get('rejection_reason', '')
        if request.FILES.get('shop_logo'):
            vendor.shop_logo = request.FILES['shop_logo']
        if request.FILES.get('shop_banner'):
            vendor.shop_banner = request.FILES['shop_banner']
        if request.FILES.get('pan_document'):
            vendor.pan_document = request.FILES['pan_document']
        if request.FILES.get('citizenship_front'):
            vendor.citizenship_front = request.FILES['citizenship_front']
        if request.FILES.get('citizenship_back'):
            vendor.citizenship_back = request.FILES['citizenship_back']
        if request.FILES.get('company_registration'):
            vendor.company_registration = request.FILES['company_registration']
        vendor.save()
        return redirect('admin_vendors_list')
    provinces = Vendor.PROVINCE_CHOICES
    return render(request, 'dashboard/pages/vendor/edit_vendor.html', {'vendor': vendor, 'provinces': provinces})

@admin_required
def admin_vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.delete()
    return redirect('admin_vendors_list')

@admin_required
def admin_vendor_change_status(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    vendor = get_object_or_404(Vendor, pk=pk)
    new_status = request.POST.get('status')
    if new_status not in ['pending', 'verified', 'rejected']:
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    vendor.verification_status = new_status
    if new_status == 'verified':
        vendor.verified_at = timezone.now()
        vendor.is_active = True
    else:
        vendor.is_active = False
    if new_status != 'rejected':
        vendor.rejection_reason = ''
    vendor.save()
    return JsonResponse({
        'success': True,
        'vendor_id': vendor.id,
        'verification_status': vendor.verification_status,
        'verified_at': vendor.verified_at.isoformat() if vendor.verified_at else None,
        'is_active': vendor.is_active,
    })

# Product Management
@admin_required
def admin_products_list(request):
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    vendor_id = request.GET.get('vendor', '')
    products = Product.objects.all().order_by('-created_at')

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(brand__icontains=search) |
            Q(sku__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if vendor_id:
        products = products.filter(vendor_id=vendor_id)

    categories = Category.objects.filter(is_active=True)
    vendors = Vendor.objects.filter(is_active=True)

    return render(request, 'dashboard/pages/product/products_list.html', {
        'products': products,
        'categories': categories,
        'vendors': vendors
    })

@admin_required
def admin_products_featured(request):
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    vendor_id = request.GET.get('vendor', '')
    products = Product.objects.filter(is_featured=True).order_by('-created_at')

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(brand__icontains=search) |
            Q(sku__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if vendor_id:
        products = products.filter(vendor_id=vendor_id)

    categories = Category.objects.filter(is_active=True)
    vendors = Vendor.objects.filter(is_active=True)

    return render(request, 'dashboard/pages/product/featured_products.html', {
        'products': products,
        'categories': categories,
        'vendors': vendors
    })

@admin_required
def admin_products_low_stock(request):
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    vendor_id = request.GET.get('vendor', '')
    products = Product.objects.filter(stock__gt=0, stock__lte=F('low_stock_alert')).order_by('stock')

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(brand__icontains=search) |
            Q(sku__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if vendor_id:
        products = products.filter(vendor_id=vendor_id)

    categories = Category.objects.filter(is_active=True)
    vendors = Vendor.objects.filter(is_active=True)

    return render(request, 'dashboard/pages/product/low_stock_products.html', {
        'products': products,
        'categories': categories,
        'vendors': vendors
    })

@admin_required
def admin_product_add(request):
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor')
        category_id = request.POST.get('category')
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        category = get_object_or_404(Category, pk=category_id)
        product = Product.objects.create(
            vendor=vendor,
            category=category,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            price=Decimal(request.POST.get('price')),
            cost_price=Decimal(request.POST.get('cost_price')) if request.POST.get('cost_price') else None,
            stock=int(request.POST.get('stock', 0)),
            low_stock_alert=int(request.POST.get('low_stock_alert', 5)),
            brand=request.POST.get('brand', ''),
            weight=Decimal(request.POST.get('weight')) if request.POST.get('weight') else None,
            is_featured=True if request.POST.get('is_featured') == 'on' else False,
        )
        if request.FILES.get('main_image'):
            product.main_image = request.FILES['main_image']
            product.save()
        else:
            product.save()

        # Handle gallery images (multiple)
        for img in request.FILES.getlist('gallery_images'):
            ProductImage.objects.create(product=product, image=img)

        # Handle variants: expect arrays variant_type[], variant_name[], variant_price_adjustment[], variant_stock[], variant_sku[]
        variant_types = request.POST.getlist('variant_type[]')
        variant_names = request.POST.getlist('variant_name[]')
        variant_price_adjustments = request.POST.getlist('variant_price_adjustment[]')
        

        for i in range(len(variant_names)):
            name = variant_names[i].strip()
            if not name:
                continue
            ProductVariant.objects.create(
                product=product,
                variant_type=variant_types[i] if i < len(variant_types) and variant_types[i] else 'other',
                name=name,
                price_adjustment=Decimal(variant_price_adjustments[i]) if i < len(variant_price_adjustments) and variant_price_adjustments[i] else 0,
            )

        return redirect('admin_products_list')
    categories = Category.objects.filter(is_active=True)
    vendors = Vendor.objects.filter(is_active=True)
    return render(request, 'dashboard/pages/product/add_product.html', {'categories': categories, 'vendors': vendors})

@admin_required
def admin_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor')
        category_id = request.POST.get('category')
        product.vendor = get_object_or_404(Vendor, pk=vendor_id)
        product.category = get_object_or_404(Category, pk=category_id)
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = Decimal(request.POST.get('price'))
        product.cost_price = Decimal(request.POST.get('cost_price')) if request.POST.get('cost_price') else None
        product.stock = int(request.POST.get('stock', 0))
        product.low_stock_alert = int(request.POST.get('low_stock_alert', 5))
        product.brand = request.POST.get('brand', '')
        product.weight = Decimal(request.POST.get('weight')) if request.POST.get('weight') else None
        product.is_featured = True if request.POST.get('is_featured') == 'on' else False

        if request.FILES.get('main_image'):
            product.main_image = request.FILES['main_image']
        product.save()

        # Append new gallery images if any
        for img in request.FILES.getlist('gallery_images'):
            ProductImage.objects.create(product=product, image=img)

        # Update existing variants and optionally delete
        existing_ids = request.POST.getlist('existing_variant_id[]')
        existing_types = request.POST.getlist('existing_variant_type[]')
        existing_names = request.POST.getlist('existing_variant_name[]')
        existing_price_adjustments = request.POST.getlist('existing_variant_price_adjustment[]')
        
        delete_ids = set(request.POST.getlist('existing_variant_delete[]'))

        for idx in range(len(existing_ids)):
            variant_id = existing_ids[idx]
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                continue

            if variant_id in delete_ids:
                variant.delete()
                continue

            name_val = existing_names[idx].strip() if idx < len(existing_names) else variant.name
            if not name_val:
                # skip empty names to avoid unique_together issues
                continue
            variant.variant_type = existing_types[idx] if idx < len(existing_types) and existing_types[idx] else variant.variant_type
            variant.name = name_val
            variant.price_adjustment = Decimal(existing_price_adjustments[idx]) if idx < len(existing_price_adjustments) and existing_price_adjustments[idx] else Decimal('0')
            try:
                variant.save()
            except Exception:
                # Silently ignore unique constraint conflicts for now
                pass

        # Append new variants from form
        variant_types = request.POST.getlist('variant_type[]')
        variant_names = request.POST.getlist('variant_name[]')
        variant_price_adjustments = request.POST.getlist('variant_price_adjustment[]')
        

        for i in range(len(variant_names)):
            name = variant_names[i].strip()
            if not name:
                continue
            try:
                ProductVariant.objects.create(
                    product=product,
                    variant_type=variant_types[i] if i < len(variant_types) and variant_types[i] else 'other',
                    name=name,
                    price_adjustment=Decimal(variant_price_adjustments[i]) if i < len(variant_price_adjustments) and variant_price_adjustments[i] else 0,
                )
            except Exception:
                # Ignore duplicates violating unique_together
                pass
        return redirect('admin_products_list')
    categories = Category.objects.filter(is_active=True)
    vendors = Vendor.objects.filter(is_active=True)
    return render(request, 'dashboard/pages/product/edit_product.html', {
        'product': product,
        'categories': categories,
        'vendors': vendors,
    })

@admin_required
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('admin_products_list')

# Category Management
@admin_required
def admin_categories_list(request):
    categories = Category.objects.all().order_by('order', 'name')
    return render(request, 'dashboard/pages/category/categories_list.html', {'categories': categories})

@admin_required
def admin_category_add(request):
    if request.method == 'POST':

        category = Category.objects.create(
            name=request.POST.get('name'),
        
            order=int(request.POST.get('order', 0)),
            is_featured=True if request.POST.get('is_featured') == 'on' else False
        )
        if request.FILES.get('image'):
            category.image = request.FILES['image']
        category.save()
        return redirect('admin_categories_list')
    return render(request, 'dashboard/pages/category/add_category.html')

@admin_required
def admin_category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.order = int(request.POST.get('order', 0))
        category.is_featured = True if request.POST.get('is_featured') == 'on' else False
        if request.FILES.get('image'):
            category.image = request.FILES['image']
        category.save()
        return redirect('admin_categories_list')
    return render(request, 'dashboard/pages/category/edit_category.html', {'category': category})

@admin_required
def admin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('admin_categories_list')

# Order Management
@admin_required
def admin_orders_list(request):
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    payment_status = request.GET.get('payment_status', '')
    orders = Order.objects.all().order_by('-created_at')

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    if payment_status:
        orders = orders.filter(payment_status=payment_status)

    return render(request, 'dashboard/pages/order/orders_list.html', {
        'orders': orders,
        'order_model': Order,
    })

# Payments Overview
@admin_required
def admin_payments_overview(request):
    search = request.GET.get('search', '')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    vendors = Vendor.objects.all().order_by('shop_name')
    if search:
        vendors = vendors.filter(shop_name__icontains=search)

    orders = OrderItem.objects.select_related('order', 'vendor').all()
    if date_from:
        orders = orders.filter(order__created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(order__created_at__date__lte=date_to)

    # Default Commission if none configured
    DEFAULT_COMMISSION = Decimal('0.10')

    vendor_rows = []
    total_platform_revenue = Decimal('0')
    total_vendor_earnings = Decimal('0')
    total_payouts = Decimal('0')

    vendor_id_to_vendor_earning = {}
    vendor_id_to_admin_commission = {}
    vendor_id_to_gross = {}
    for oi in orders:
        amount = Decimal(oi.get_total())
        rate = DEFAULT_COMMISSION
        # If vendor-specific commission exists, use the latest active
        vc = VendorCommission.objects.filter(vendor_id=oi.vendor_id, active=True).order_by('-effective_from', '-created_at').first()
        if vc and vc.rate is not None:
            rate = Decimal(vc.rate)
        admin_commission = (amount * rate).quantize(Decimal('0.01'))
        vendor_earning = (amount - admin_commission).quantize(Decimal('0.01'))
        total_platform_revenue += admin_commission
        total_vendor_earnings += vendor_earning
        vendor_id_to_vendor_earning[oi.vendor_id] = vendor_id_to_vendor_earning.get(oi.vendor_id, Decimal('0')) + vendor_earning
        vendor_id_to_admin_commission[oi.vendor_id] = vendor_id_to_admin_commission.get(oi.vendor_id, Decimal('0')) + admin_commission
        vendor_id_to_gross[oi.vendor_id] = vendor_id_to_gross.get(oi.vendor_id, Decimal('0')) + amount

    for v in vendors:
        gross = vendor_id_to_gross.get(v.id, Decimal('0'))
        admin_commission_sum = vendor_id_to_admin_commission.get(v.id, Decimal('0'))
        vendor_earning_sum = vendor_id_to_vendor_earning.get(v.id, Decimal('0'))
        vendor_paid = sum((p.amount for p in v.payouts.all()), Decimal('0'))
        pending = (vendor_earning_sum - vendor_paid).quantize(Decimal('0.01'))
        total_payouts += vendor_paid
        vendor_rows.append({
            'vendor': v,
            'total_revenue': gross,
            'admin_commission': admin_commission_sum,
            'vendor_earning': vendor_earning_sum,
            'paid': vendor_paid,
            'pending': pending,
        })

    context = {
        'vendor_rows': vendor_rows,
        'total_platform_revenue': total_platform_revenue,
        'total_vendor_earnings': total_vendor_earnings,
        'total_payouts': total_payouts,
        'pending_total': (total_vendor_earnings - total_payouts).quantize(Decimal('0.01')),
    }
    return render(request, 'dashboard/pages/vendor/overview.html', context)

@admin_required
def admin_vendor_payments_detail(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    DEFAULT_COMMISSION = Decimal('0.10')

    order_items = OrderItem.objects.filter(vendor=vendor).select_related('order').order_by('-order__created_at')
    payouts = vendor.payouts.all().order_by('-created_at')

    total_earning = Decimal('0')
    total_commission = Decimal('0')
    orders_data = []
    for oi in order_items:
        amount = Decimal(oi.get_total())
        vc = VendorCommission.objects.filter(vendor_id=vendor.id, active=True).order_by('-effective_from', '-created_at').first()
        rate = Decimal(vc.rate) if vc and vc.rate is not None else DEFAULT_COMMISSION
        admin_commission = (amount * rate).quantize(Decimal('0.01'))
        vendor_earning = (amount - admin_commission).quantize(Decimal('0.01'))
        total_earning += vendor_earning
        total_commission += admin_commission
        orders_data.append({
            'order': oi.order,
            'order_item': oi,
            'amount': amount,
            'admin_commission': admin_commission,
            'vendor_earning': vendor_earning,
            'payment_status': oi.order.payment_status,
        })

    paid_out = sum((p.amount for p in payouts), Decimal('0'))
    remaining = (total_earning - paid_out).quantize(Decimal('0.01'))

    context = {
        'vendor': vendor,
        'orders_data': orders_data,
        'payouts': payouts,
        'total_earning': total_earning,
        'total_commission': total_commission,
        'paid_out': paid_out,
        'remaining': remaining,
    }
    return render(request, 'dashboard/pages/vendor/vendor_detail.html', context)

# Payout Requests
@admin_required
def admin_payout_requests_list(request):
    status_filter = request.GET.get('status', '').strip()
    requests_qs = VendorPayoutRequest.objects.select_related('vendor').all().order_by('-created_at')
    if status_filter in ['pending', 'approved', 'rejected', 'paid']:
        requests_qs = requests_qs.filter(status=status_filter)
    totals = {
        'pending': VendorPayoutRequest.objects.filter(status='pending').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'approved': VendorPayoutRequest.objects.filter(status='approved').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'rejected': VendorPayoutRequest.objects.filter(status='rejected').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'paid': VendorPayoutRequest.objects.filter(status='paid').aggregate(total=Sum('requested_amount'))['total'] or 0,
    }
    return render(request, 'dashboard/pages/payout/requests_list.html', {'requests': requests_qs, 'totals': totals})

@admin_required
def admin_payout_requests_pending(request):
    status_filter = request.GET.get('status', '').strip() or 'pending'
    if status_filter not in ['pending', 'approved', 'rejected', 'paid']:
        status_filter = 'pending'
    requests_qs = VendorPayoutRequest.objects.select_related('vendor').filter(status=status_filter).order_by('-created_at')
    totals = {
        'pending': VendorPayoutRequest.objects.filter(status='pending').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'approved': VendorPayoutRequest.objects.filter(status='approved').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'rejected': VendorPayoutRequest.objects.filter(status='rejected').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'paid': VendorPayoutRequest.objects.filter(status='paid').aggregate(total=Sum('requested_amount'))['total'] or 0,
    }
    return render(request, 'dashboard/pages/payout/pending_payouts.html', {'requests': requests_qs, 'totals': totals})

@admin_required
def admin_payout_requests_rejected(request):
    status_filter = request.GET.get('status', '').strip() or 'rejected'
    if status_filter not in ['pending', 'approved', 'rejected', 'paid']:
        status_filter = 'rejected'
    requests_qs = VendorPayoutRequest.objects.select_related('vendor').filter(status=status_filter).order_by('-created_at')
    totals = {
        'pending': VendorPayoutRequest.objects.filter(status='pending').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'approved': VendorPayoutRequest.objects.filter(status='approved').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'rejected': VendorPayoutRequest.objects.filter(status='rejected').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'paid': VendorPayoutRequest.objects.filter(status='paid').aggregate(total=Sum('requested_amount'))['total'] or 0,
    }
    return render(request, 'dashboard/pages/payout/rejected_payouts.html', {'requests': requests_qs, 'totals': totals})

@admin_required
def admin_payout_request_change_status(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    req = get_object_or_404(VendorPayoutRequest, pk=pk)
    new_status = request.POST.get('status')
    if new_status not in ['pending', 'approved', 'rejected', 'paid']:
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    req.status = new_status
    req.admin_response = request.POST.get('admin_response', '')
    req.save(update_fields=['status', 'admin_response'])

    if new_status == 'paid':
        VendorPayout.objects.create(
            vendor=req.vendor,
            amount=req.requested_amount,
            method=request.POST.get('method', ''),
            transaction_id=request.POST.get('transaction_id', ''),
            admin_remarks='Auto-paid from request'
        )

    return JsonResponse({'success': True})

@admin_required
def admin_orders_pending(request):
    orders = Order.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'dashboard/pages/order/pending_orders.html', {
        'orders': orders,
        'order_model': Order,
    })

@admin_required
def admin_orders_delivered(request):
    orders = Order.objects.filter(status='delivered').order_by('-created_at')
    return render(request, 'dashboard/pages/order/delivered_orders.html', {
        'orders': orders,
        'order_model': Order,
    })

@admin_required
def admin_order_delete(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    order.delete()
    return redirect('admin_orders_list')

@admin_required
def admin_order_change_status(request, order_number):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    order = get_object_or_404(Order, order_number=order_number)
    status = request.POST.get('status')
    payment_status = request.POST.get('payment_status')
    if status and status in dict(Order.STATUS_CHOICES):
        order.status = status
        if status == 'delivered':
            order.delivered_at = timezone.now()
    if payment_status and payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
        order.payment_status = payment_status
    order.save()
    return JsonResponse({'success': True})

@admin_required
def admin_order_items_json(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    items = []
    for item in order.items.select_related('product', 'variant').all():
        items.append({
            'product_name': item.product_name or (item.product.name if item.product else ''),
            'variant_name': item.variant_name or (item.variant.name if item.variant else ''),
            'quantity': item.quantity,
            'price': str(item.price),
            'total': str(item.get_total()),
            'image_url': item.product_image.url if item.product_image else (item.product.main_image.url if item.product and item.product.main_image else ''),
        })
    return JsonResponse({'success': True, 'items': items})

# Review Management
@admin_required
def admin_reviews_list(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'dashboard/pages/review/reviews_list.html', {'reviews': reviews})

@admin_required
def admin_review_add(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        user_id = request.POST.get('user')
        product = get_object_or_404(Product, pk=product_id)
        user = get_object_or_404(User, pk=user_id)
        Review.objects.create(
            product=product,
            user=user,
            rating=int(request.POST.get('rating')),
            comment=request.POST.get('comment', '')
        )
        messages.success(request, 'Review added successfully.')
        return redirect('admin_reviews_list')
    products = Product.objects.all()
    users = User.objects.all()
    return render(request, 'dashboard/pages/review/add_review.html', {'products': products, 'users': users})

@admin_required
def admin_review_update(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        product_id = request.POST.get('product')
        user_id = request.POST.get('user')
        review.product = get_object_or_404(Product, pk=product_id)
        review.user = get_object_or_404(User, pk=user_id)
        review.rating = int(request.POST.get('rating'))
        review.comment = request.POST.get('comment', '')
        review.save()
        messages.success(request, 'Review updated successfully.')
        return redirect('admin_reviews_list')
    products = Product.objects.all()
    users = User.objects.all()
    return render(request, 'dashboard/pages/review/edit_review.html', {'review': review, 'products': products, 'users': users})

@admin_required
def admin_review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, 'Review deleted successfully.')
    return redirect('admin_reviews_list')

# Contact Management
@admin_required
def admin_contacts_list(request):
    search = request.GET.get('search', '')
    contacts = Contact.objects.all().order_by('-created_at')

    if search:
        contacts = contacts.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(subject__icontains=search) |
            Q(message__icontains=search)
        )

    return render(request, 'admin/contacts_list.html', {'contacts': contacts})

@admin_required
def admin_contact_add(request):
    if request.method == 'POST':
        Contact.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            subject=request.POST.get('subject', ''),
            message=request.POST.get('message')
        )
        return redirect('admin_contacts_list')
    return render(request, 'admin/contact_add.html')

@admin_required
def admin_contact_update(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        contact.name = request.POST.get('name')
        contact.email = request.POST.get('email')
        contact.phone = request.POST.get('phone', '')
        contact.subject = request.POST.get('subject', '')
        contact.message = request.POST.get('message')
        contact.is_read = request.POST.get('is_read') == 'on'
        contact.replied = request.POST.get('replied') == 'on'
        contact.save()
        return redirect('admin_contacts_list')
    return render(request, 'admin/contact_update.html', {'contact': contact})

@admin_required
def admin_contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.delete()
    return redirect('admin_contacts_list')

# Newsletter Management
@admin_required
def admin_newsletter_list(request):
    subscribers = Newsletter.objects.all().order_by('-subscribed_at')
    return render(request, 'dashboard/pages/newsletter/newsletter_list.html', {'subscribers': subscribers})

@admin_required
def admin_newsletter_add(request):
    if request.method == 'POST':
        Newsletter.objects.create(
            email=request.POST.get('email')
        )
        messages.success(request, 'Subscriber added successfully.')
        return redirect('admin_newsletter_list')
    return render(request, 'dashboard/pages/newsletter/add_newsletter.html')

@admin_required
def admin_newsletter_update(request, pk):
    subscriber = get_object_or_404(Newsletter, pk=pk)
    if request.method == 'POST':
        subscriber.email = request.POST.get('email')
        subscriber.save()
        messages.success(request, 'Subscriber updated successfully.')
        return redirect('admin_newsletter_list')
    return render(request, 'dashboard/pages/newsletter/edit_newsletter.html', {'subscriber': subscriber})

@admin_required
def admin_newsletter_delete(request, pk):
    subscriber = get_object_or_404(Newsletter, pk=pk)
    subscriber.delete()
    messages.success(request, 'Subscriber deleted successfully.')
    return redirect('admin_newsletter_list')

# Slider Management
@admin_required
def admin_sliders_list(request):
    sliders = Slider.objects.all().order_by('-created_at')
    return render(request, 'dashboard/pages/content/sliders_list.html', {'sliders': sliders})


@admin_required
def admin_slider_add(request):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        subtitle = request.POST.get('subtitle', '')
        link = request.POST.get('link', '')
        image = request.FILES.get('image')  

        # Create the slider
        slider = Slider.objects.create(
            title=title,
            subtitle=subtitle,
            link=link,
            image=image
        )

        messages.success(request, 'Slider created successfully.')
        return redirect('admin_sliders_list')

    return render(request, 'dashboard/pages/content/slider_add.html')


@admin_required
def admin_slider_update(request, pk):
    slider = get_object_or_404(Slider, pk=pk)

    if request.method == 'POST':
        title = request.POST.get('title', '')
        subtitle = request.POST.get('subtitle', '')
        link = request.POST.get('link', '')
        slider.title = title
        slider.subtitle = subtitle
        slider.link = link
        if request.FILES.get('image'):
            slider.image = request.FILES['image']
        slider.save()
        messages.success(request, 'Slider updated successfully.')
        return redirect('admin_sliders_list')

    return render(request, 'dashboard/pages/content/slider_update.html', {'slider': slider})



@admin_required
def admin_slider_delete(request, pk):
    slider = get_object_or_404(Slider, pk=pk)
    slider.delete()
    return redirect('admin_sliders_list')

# Banner Management
@admin_required
def admin_banners_list(request):
    banners = Banner.objects.all().order_by('-created_at')
    return render(request, 'dashboard/pages/content/banners_list.html', {'banners': banners})

@admin_required
def admin_banner_add(request):
    if request.method == 'POST':
        banner = Banner.objects.create(
            title=request.POST.get('title', ''),
            link=request.POST.get('link', ''),
            page=request.POST.get('page','')

        )
        if request.FILES.get('image'):
            banner.image = request.FILES['image']
        banner.save()
        messages.success(request, 'Banner created successfully.')
        return redirect('admin_banners_list')
    return render(request, 'dashboard/pages/content/banner_add.html',{'page_choices':Banner.PAGE_CHOICES})

@admin_required
def admin_banner_update(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        banner.title = request.POST.get('title', '')
        banner.link = request.POST.get('link', '')
        banner.page=request.POST.get('page','')
        if request.FILES.get('image'):
            banner.image = request.FILES['image']
        banner.save()
        messages.success(request, 'Banner updated successfully.')
        return redirect('admin_banners_list')
    return render(request, 'dashboard/pages/content/banner_update.html', {'banner': banner,'page_choices':Banner.PAGE_CHOICES})

@admin_required
def admin_banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    banner.delete()
    return redirect('admin_banners_list')

# HomeCategory Management
@admin_required
def admin_home_categories_list(request):
    home_categories = HomeCategory.objects.all().order_by('position', '-created_at')
    return render(request, 'dashboard/pages/content/home_categories_list.html', {'home_categories': home_categories})

@admin_required
def admin_home_category_add(request):
    if request.method == 'POST':
        home_category = HomeCategory.objects.create(
            title=request.POST.get('title'),
            link=request.POST.get('link', ''),
            position=int(request.POST.get('position', 0))
        )
        if request.FILES.get('image'):
            home_category.image = request.FILES['image']
        home_category.save()
        messages.success(request, 'Home category created successfully.')
        return redirect('admin_home_categories_list')
    return render(request, 'dashboard/pages/content/home_category_add.html')

@admin_required
def admin_home_category_update(request, pk):
    home_category = get_object_or_404(HomeCategory, pk=pk)
    if request.method == 'POST':
        home_category.title = request.POST.get('title')
        home_category.link = request.POST.get('link', '')
        home_category.position = int(request.POST.get('position', 0))
        if request.FILES.get('image'):
            home_category.image = request.FILES['image']
        home_category.save()
        messages.success(request, 'Home category updated successfully.')
        return redirect('admin_home_categories_list')
    return render(request, 'dashboard/pages/content/home_category_update.html', {'home_category': home_category})

@admin_required
def admin_home_category_delete(request, pk):
    home_category = get_object_or_404(HomeCategory, pk=pk)
    home_category.delete()
    return redirect('admin_home_categories_list')

# Coupon Management
@admin_required
def admin_coupons_list(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'dashboard/pages/coupon/coupons_list.html', {'coupons': coupons})

@admin_required
def admin_coupon_add(request):
    if request.method == 'POST':
        coupon = Coupon.objects.create(
            code=request.POST.get('code'),
            description=request.POST.get('description', ''),
            discount_type=request.POST.get('discount_type'),
            discount_value=Decimal(request.POST.get('discount_value')),
            min_purchase=Decimal(request.POST.get('min_purchase', 0)),
            max_discount=Decimal(request.POST.get('max_discount')) if request.POST.get('max_discount') else None,
            usage_limit=int(request.POST.get('usage_limit')) if request.POST.get('usage_limit') else None,
            usage_limit_per_user=int(request.POST.get('usage_limit_per_user')) if request.POST.get('usage_limit_per_user') else None,
            valid_from=request.POST.get('valid_from'),
            valid_to=request.POST.get('valid_to')
        )
        return redirect('admin_coupons_list')
    return render(request, 'dashboard/pages/coupon/add_coupon.html')

@admin_required
def admin_coupon_update(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    if request.method == 'POST':
        coupon.code = request.POST.get('code')
        coupon.description = request.POST.get('description', '')
        coupon.discount_type = request.POST.get('discount_type')
        coupon.discount_value = Decimal(request.POST.get('discount_value'))
        coupon.min_purchase = Decimal(request.POST.get('min_purchase', 0))
        coupon.max_discount = Decimal(request.POST.get('max_discount')) if request.POST.get('max_discount') else None
        coupon.usage_limit = int(request.POST.get('usage_limit')) if request.POST.get('usage_limit') else None
        coupon.usage_limit_per_user = int(request.POST.get('usage_limit_per_user')) if request.POST.get('usage_limit_per_user') else None
        coupon.valid_from = request.POST.get('valid_from')
        coupon.valid_to = request.POST.get('valid_to')
        coupon.save()
        return redirect('admin_coupons_list')
    return render(request, 'dashboard/pages/coupon/edit_coupon.html', {'coupon': coupon})

@admin_required
def admin_coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.delete()
    return redirect('admin_coupons_list')

# Shipping Zone Management
@admin_required
def admin_shipping_zones_list(request):
    search = request.GET.get('search', '')
    shipping_zones = ShippingZone.objects.all().order_by('cost')

    if search:
        shipping_zones = shipping_zones.filter(
            Q(name__icontains=search) |
            Q(provinces__icontains=search)
        )

    return render(request, 'admin/shipping_zones_list.html', {'shipping_zones': shipping_zones})

@admin_required
def admin_shipping_zone_add(request):
    if request.method == 'POST':
        ShippingZone.objects.create(
            name=request.POST.get('name'),
            provinces=request.POST.get('provinces'),
            cost=Decimal(request.POST.get('cost')),
            free_shipping_threshold=Decimal(request.POST.get('free_shipping_threshold')) if request.POST.get('free_shipping_threshold') else None,
            estimated_days=request.POST.get('estimated_days', '')
        )
        return redirect('admin_shipping_zones_list')
    return render(request, 'admin/shipping_zone_add.html')

@admin_required
def admin_shipping_zone_update(request, pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=pk)
    if request.method == 'POST':
        shipping_zone.name = request.POST.get('name')
        shipping_zone.provinces = request.POST.get('provinces')
        shipping_zone.cost = Decimal(request.POST.get('cost'))
        shipping_zone.free_shipping_threshold = Decimal(request.POST.get('free_shipping_threshold')) if request.POST.get('free_shipping_threshold') else None
        shipping_zone.estimated_days = request.POST.get('estimated_days', '')
        shipping_zone.save()
        return redirect('admin_shipping_zones_list')
    return render(request, 'admin/shipping_zone_update.html', {'shipping_zone': shipping_zone})

@admin_required
def admin_shipping_zone_delete(request, pk):
    shipping_zone = get_object_or_404(ShippingZone, pk=pk)
    shipping_zone.delete()
    return redirect('admin_shipping_zones_list')

# Organization Management

# View: Display Organization Info
@admin_required
def admin_organization_view(request):
    organization = Organization.objects.first()
    return render(request, 'dashboard/pages/organization/organization.html', {
        'organization': organization
    })

@admin_required
def admin_organization_update(request):
    organization = Organization.objects.first()
    if request.method == 'POST':
        organization.name = request.POST.get('name')
        organization.tagline = request.POST.get('tagline', '')
        organization.email = request.POST.get('email')
        organization.phone = request.POPST.get('phone')
        organization.phone_secondary = request.POST.get('phone_secondary', '')
        organization.address = request.POST.get('address')
        organization.facebook = request.POST.get('facebook', '')
        organization.instagram = request.POST.get('instagram', '')
        organization.twitter = request.POST.get('twitter', '')
        organization.youtube = request.POST.get('youtube', '')
        organization.tiktok = request.POST.get('tiktok', '')
        if request.FILES.get('logo'):
            organization.logo = request.FILES['logo']
        if request.FILES.get('favicon'):
            organization.favicon = request.FILES['favicon']
        organization.save()
        return redirect('admin_organization_view')
    return render(request, 'dashboard/pages/organization/edit_organization.html', {'organization': organization})

# Notification Management
@admin_required
def admin_notifications_list(request):
    search = request.GET.get('search', '')
    notifications = Notification.objects.all().order_by('-created_at')

    if search:
        notifications = notifications.filter(
            Q(title__icontains=search) |
            Q(message__icontains=search)
        )

    return render(request, 'admin/notifications_list.html', {'notifications': notifications})

@admin_required
def admin_notification_add(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        user = get_object_or_404(User, pk=user_id)
        Notification.objects.create(
            user=user,
            notification_type=request.POST.get('notification_type'),
            title=request.POST.get('title'),
            message=request.POST.get('message'),
            link=request.POST.get('link', '')
        )
        return redirect('admin_notifications_list')
    users = User.objects.all()
    return render(request, 'admin/notification_add.html', {'users': users})

@admin_required
def admin_notification_update(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if request.method == 'POST':
        user_id = request.POST.get('user')
        notification.user = get_object_or_404(User, pk=user_id)
        notification.notification_type = request.POST.get('notification_type')
        notification.title = request.POST.get('title')
        notification.message = request.POST.get('message')
        notification.link = request.POST.get('link', '')
        notification.save()
        return redirect('admin_notifications_list')
    users = User.objects.all()
    return render(request, 'admin/notification_update.html', {'notification': notification, 'users': users})

@admin_required
def admin_notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.delete()
    return redirect('admin_notifications_list')