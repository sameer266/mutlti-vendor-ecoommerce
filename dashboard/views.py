from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from .models import (
    UserRole,  Vendor, Category, Product, ProductImage, ProductVariant, Order, OrderItem, Invoice,
    Review, Coupon,  Organization, Newsletter, Contact, 
    Notification, Slider, Banner, VendorCommission, VendorPayoutRequest,VendorWallet,VendorCommission,ShippingCost
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
    active_home_categories = Category.objects.filter(is_featured=True).count()
    total_reviews = Review.objects.count()
    unread_contacts = Contact.objects.filter(is_read=False).count()
    newsletter_subscribers = Newsletter.objects.filter(is_active=True).count()
    unread_notifications = Notification.objects.filter(is_read=False).count()

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
      
    }
    return render(request, 'dashboard/pages/admin_dashboard.html', context)

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

# @admin_required
# def admin_user_add(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         role = request.POST.get('role')
#         user = User.objects.create_user(username=username, email=email, password=password)
#         UserRole.objects.create(user=user, role=role)
#         return redirect('admin_users_list')
#     return render(request, 'dashboard/pages/users/user_add.html')

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

import random
import string
from django.core.mail import send_mail
from django.conf import settings


@admin_required
def admin_vendor_add(request):
    if request.method == 'POST':
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        email=request.POST.get('email'),
        user=User.objects.create(first_name=first_name,last_name=last_name,email=email)
        # Generate random password (8–10 chars, mix of letters/numbers/symbols)
        random_password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=10))
        user.set_password(random_password)
        user.save()

        vendor = Vendor.objects.create(
            user=user,
            shop_name=request.POST.get('shop_name'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            province=request.POST.get('province'),
            pan_number=request.POST.get('pan_number'),
            citizenship_number=request.POST.get('citizenship_number', ''),
            verification_status=request.POST.get('verification_status', 'pending')
        )
        if request.FILES.get('qr_image'):
            vendor.qr_image = request.FILES['qr_image']

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

        try:
            send_mail(
                subject='Your Vendor Account Has Been Created',
                message=f'Hello {user.first_name},\n\nYour vendor account has been created successfully.\n'
                        f'Password: {random_password}\n\n'
                        f'Please change your password after logging in.',
                from_email='hellobaja.com.np',
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            print("Email sending failed:", e)

        return redirect('admin_vendors_list')

    users = User.objects.all()
    provinces = Vendor.PROVINCE_CHOICES
    return render(request, 'dashboard/pages/vendor/add_vendor.html', {
        'users': users,
        'provinces': provinces
    })



@admin_required
def admin_vendor_update(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.user.first_name=request.POST.get('full_name')
        vendor.user.last_name=request.POST.get('last_name')
        vendor.user.email=request.POST.get('email')
        vendor.shop_name = request.POST.get('shop_name')
        vendor.phone = request.POST.get('phone')
        vendor.address = request.POST.get('address')
        vendor.city = request.POST.get('city')
        vendor.province = request.POST.get('province')
        vendor.pan_number = request.POST.get('pan_number')
        vendor.citizenship_number = request.POST.get('citizenship_number', '')
        
        vendor.verification_status = request.POST.get('verification_status')
        vendor.rejection_reason = request.POST.get('rejection_reason', '')
        if request.FILES.get('qr_image'):
            vendor.qr_image=request.FILES['qr_image']
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
    return render(request, 'vendor/product/add_product.html', {'categories': categories, 'vendors': vendors})

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

    # --- Vendor Filter ---
    vendors = Vendor.objects.all().order_by('shop_name')
    if search:
        vendors = vendors.filter(shop_name__icontains=search)

    # --- Get All Delivered & Paid Orders ---
    orders = OrderItem.objects.select_related('order', 'product__vendor').filter(
        order__status='delivered',
        order__payment_status='paid'
    )

    # --- Date Filters (on Order created_at) ---
    if date_from:
        orders = orders.filter(order__created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(order__created_at__date__lte=date_to)

    # --- Commission Rate (Latest VendorCommission) ---
    commission_obj = VendorCommission.objects.order_by('-created_at').first()
    commission_rate = commission_obj.rate if commission_obj else Decimal('0.10')

    # --- Initialize Totals ---
    total_platform_revenue = Decimal('0.00')
    total_vendor_earnings = Decimal('0.00')
    total_payouts = Decimal('0.00')
    pending_total=Decimal('0.00')

    vendor_rows = []

    # --- Compute Per-Vendor Aggregation ---
    for v in vendors:
        # All delivered + paid order items for this vendor
        vendor_orders = orders.filter(product__vendor=v)

        gross_sales = Decimal('0.00')
        admin_commission_sum = Decimal('0.00')
        vendor_earning_sum = Decimal('0.00')
        


        for oi in vendor_orders:
            amount = Decimal(oi.get_total())
            admin_commission = (amount * commission_rate).quantize(Decimal('0.01'))
            vendor_earning = (amount - admin_commission).quantize(Decimal('0.01'))

            gross_sales += amount
            admin_commission_sum += admin_commission
            vendor_earning_sum += vendor_earning

        # Get vendor wallet balance (total paid to vendor)
        wallet, _ = VendorWallet.objects.get_or_create(vendor=v)
        vendor_wallet = wallet.balance.quantize(Decimal('0.01'))
        
        pending = VendorPayoutRequest.objects.filter(vendor=v, status='pending').aggregate(total=Sum('requested_amount'))['total'] or Decimal('0.00')  
         
        # Update global totals
        pending_total += pending 
        total_platform_revenue += admin_commission_sum
        total_vendor_earnings += vendor_earning_sum
        total_payouts += VendorPayoutRequest.objects.filter(vendor=v, status='paid').aggregate(total=Sum('requested_amount'))['total'] or Decimal('0.00')   

        vendor_rows.append({
            'vendor': v,
            'total_revenue': gross_sales,
            'admin_commission': admin_commission_sum,
            'vendor_earning': vendor_earning_sum,
            'wallet': vendor_wallet,
            'pending': pending,
        })

    # --- Prepare Context ---
    context = {
        'vendor_rows': vendor_rows,
        'total_platform_revenue': total_platform_revenue.quantize(Decimal('0.01')),
        'total_vendor_earnings': total_vendor_earnings.quantize(Decimal('0.01')),
        'total_payouts': total_payouts.quantize(Decimal('0.01')),
        'pending_total':pending_total,
        'commission_rate_percent': (commission_rate * 100).quantize(Decimal('0.01')),
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'dashboard/pages/payment/overview.html', context)



@admin_required
def admin_vendor_payments_detail(request, vendor_id):
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        
        commission_obj = VendorCommission.objects.order_by('-created_at').first()
        commission_rate = commission_obj.rate if commission_obj else Decimal('0.10')

        order_items = (
            OrderItem.objects.filter(product__vendor=vendor, order__status='delivered', order__payment_status='paid')
            .select_related('order')
            .order_by('-order__created_at')
        )
        payouts = VendorPayoutRequest.objects.filter(vendor=vendor).order_by('-created_at')

        total_earning = Decimal('0')
        total_commission = Decimal('0')
        net_earning = Decimal('0')
        
        orders_data = []

        for oi in order_items:
            amount = Decimal(oi.get_total())
            admin_commission = (amount * commission_rate).quantize(Decimal('0.01'))
            vendor_earning = (amount - admin_commission).quantize(Decimal('0.01'))

            total_earning += amount
            net_earning += vendor_earning
            total_commission += admin_commission

            orders_data.append({
                'order': oi.order,
                'order_item': oi,
                'amount': amount,
                'admin_commission': admin_commission,
                'vendor_earning': vendor_earning,
                'payment_status': oi.order.payment_status,\
                    
            })
        wallet, _ = VendorWallet.objects.get_or_create(vendor=vendor)
        wallet = wallet.balance
        

        context = {
            'vendor': vendor,
            'orders_data': orders_data,
            'payouts': payouts,
            'total_earning': total_earning,
            'total_commission': total_commission,
            'wallet_balance': wallet,
            'net_earning': net_earning,
            'commission_rate_percent': (commission_rate * 100).quantize(Decimal('0.01')),
        }

        return render(request, 'dashboard/pages/payment/payment_detail.html', context)


# Payout Requests
@admin_required
def admin_payout_requests_list(request):
    status_filter = request.GET.get('status')
    requests_qs = VendorPayoutRequest.objects.select_related('vendor').all().order_by('-created_at')
    if status_filter in ['pending','rejected', 'paid']:
        requests_qs = requests_qs.filter(status=status_filter)
    totals = {
        'pending': VendorPayoutRequest.objects.filter(status='pending').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'rejected': VendorPayoutRequest.objects.filter(status='rejected').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'paid': VendorPayoutRequest.objects.filter(status='paid').aggregate(total=Sum('requested_amount'))['total'] or 0,
    }
    return render(request, 'dashboard/pages/payout/requests_list.html', {'requests': requests_qs, 'totals': totals})

@admin_required
def admin_payout_requests_pending(request):
    status_filter = request.GET.get('status', '').strip() or 'pending'
    if status_filter not in ['pending', 'rejected', 'paid']:
        status_filter = 'pending'
    requests_qs = VendorPayoutRequest.objects.select_related('vendor').filter(status=status_filter).order_by('-created_at')
    totals = {
        'pending': VendorPayoutRequest.objects.filter(status='pending').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'rejected': VendorPayoutRequest.objects.filter(status='rejected').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'paid': VendorPayoutRequest.objects.filter(status='paid').aggregate(total=Sum('requested_amount'))['total'] or 0,
    }
    return render(request, 'dashboard/pages/payout/pending_payouts.html', {'requests': requests_qs, 'totals': totals})

@admin_required
def admin_payout_requests_rejected(request):
    status_filter = request.GET.get('status', '').strip() or 'rejected'
    if status_filter not in ['pending','rejected', 'paid']:
        status_filter = 'rejected'
    requests_qs = VendorPayoutRequest.objects.select_related('vendor').filter(status=status_filter).order_by('-created_at')
    totals = {
        'pending': VendorPayoutRequest.objects.filter(status='pending').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'rejected': VendorPayoutRequest.objects.filter(status='rejected').aggregate(total=Sum('requested_amount'))['total'] or 0,
        'paid': VendorPayoutRequest.objects.filter(status='paid').aggregate(total=Sum('requested_amount'))['total'] or 0,
    }
    return render(request, 'dashboard/pages/payout/rejected_payouts.html', {'requests': requests_qs, 'totals': totals})

# Payout Request Status Change (JSON)
@admin_required
def admin_payout_request_change_status(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    req = get_object_or_404(VendorPayoutRequest, pk=pk)
    new_status = request.POST.get('status')

    if new_status not in ['pending', 'rejected', 'paid']:
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

    req.status = new_status
    req.admin_response = request.POST.get('admin_response', '')
    req.save(update_fields=['status', 'admin_response'])
    messages.success(request, f'Payout request status updated to {new_status}.')
    return JsonResponse({
        'success': True,
        'status': new_status,
        'admin_response': req.admin_response
    })


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

@login_required
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
    messages.success(request, 'Order updated successfully.')
    return JsonResponse({'success': True})


@login_required
def admin_order_items_json(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    items = []

    for item in order.items.select_related('product', 'variant').all():
        # Get all variants for the product
        all_variants = []
        for variant in item.product.variants.all():
            all_variants.append({
                'variant_type': variant.get_variant_type_display(),
                'name': variant.name,
                'price_adjustment': str(variant.price_adjustment),
            })

        items.append({
            'product_name': item.product.name,
            'selected_variant': item.variant.name if item.variant else '',
            'quantity': item.quantity,
            'price': str(item.price),
            'total': str(item.get_total()),
            'image_url': item.product.main_image.url if item.product.main_image else '',
            'all_variants': all_variants,
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



#============================
#   Contact Management
# ============================
@admin_required
def admin_contacts_list(request):
    search = request.GET.get('search', '')
    contacts = Contact.objects.all().order_by('-created_at')

    return render(request, 'dashboard/pages/contact/contact_list.html', {'contacts': contacts})

@admin_required
def admin_contacts_unread(request):
    contacts = Contact.objects.filter(is_read=False).order_by('-created_at')
    return render(request, 'dashboard/pages/contact/contact_unread.html', {'contacts': contacts})


@admin_required
def admin_read_contact(request):
    contact_id=request.GET.get('id')
    is_read=request.GET.get('is_read','true').lower() == 'true'
    contact = get_object_or_404(Contact, id=contact_id)
    contact.is_read = is_read
    contact.save(update_fields=['is_read'])
    status = "read" if is_read else "unread"
    messages.success(request, f"Message from {contact.name} marked as {status}.")
    return redirect('admin_contacts_list') 

@admin_required
def admin_contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.delete()
    return redirect('admin_contacts_list')



# Shipping Cost Management
@admin_required
def shipping_cost_view(request):
    shipping_cost = ShippingCost.objects.first()  # get the only record
    return render(request, 'dashboard/pages/shipping/shipping_list.html', {
        'shipping_cost': shipping_cost
    })


@admin_required
def shipping_cost_edit(request, pk):
    shipping_cost = get_object_or_404(ShippingCost, pk=pk)

    if request.method == "POST":
        cost = request.POST.get("cost")
        tax = request.POST.get("tax")

        shipping_cost.cost = cost
        shipping_cost.tax = tax
        shipping_cost.save()

        messages.success(request, "Shipping cost updated successfully.")
        return redirect("admin_shipping_cost_view")

    return render(request, "dashboard/pages/shipping/shipping_edit.html", {
        "shipping_cost": shipping_cost
    })


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
    if organization is None:
        organization = Organization.objects.create(
            name='',
            phone='',
            address='',
            email=''
        )
    if request.method == 'POST':
        print(request.POST)
        organization.name = request.POST.get('name')
        organization.phone = request.POST.get('phone')
        organization.email = request.POST.get('email')
        
        organization.phone_secondary = request.POST.get('phone_secondary', '')
        organization.address = request.POST.get('address')
        organization.facebook = request.POST.get('facebook', '')
        organization.instagram = request.POST.get('instagram', '')
        organization.twitter = request.POST.get('twitter', '')
        organization.youtube = request.POST.get('youtube', '')
        organization.tiktok = request.POST.get('tiktok', '')
        if request.FILES.get('logo'):
            organization.logo = request.FILES['logo']
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



# Admin Profile
@admin_required
def admin_profile_view(request):
    return  render(request,'dashboard/pages/profile/admin_profile.html')

@admin_required
def admin_profile_edit(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        user=request.user
        user.first_name=first_name
        user.last_name=last_name
        user.email=email
        user.save()
        messages.success(request,'Profile Updated Successfully')
        return redirect('admin_profile')
    return render(request,'dashboard/pages/profile/admin_profile_edit.html')

# =====================================
#   Vendor  Dashboard
# =================================

@login_required
def vendor_dashboard(request):
    user = request.user
    vendor_user=Vendor.objects.get(user=user)
    products = Product.objects.filter(vendor=vendor_user)
    orders = Order.objects.filter(
    items__product__vendor=vendor_user).distinct()

    context = {
        'total_products': products.count(),
        'active_products': products.filter(is_active=True).count(),
        'low_stock_products': products.filter(stock__lte=5).count(),
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status='pending').count(),
        'delivered_orders': orders.filter(status='delivered').count(),
        'total_revenue': orders.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0,
    }

    return render(request, 'vendor/vendor_dashboard.html', context)





# Product Management
@login_required
def vendor_products_list(request):
    print(request)
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    vendor=Vendor.objects.get(user=request.user)
    products = Product.objects.filter(vendor=vendor).order_by('-created_at')
    
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(brand__icontains=search) |
            Q(sku__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    categories = Category.objects.filter(is_active=True)


    return render(request, 'vendor/product/products_list.html', {
        'products': products,
        'categories': categories,
    })




@login_required
def vendor_product_add(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        vendor=Vendor.objects.get(user=request.user)
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
    return render(request, 'vendor/product/add_product.html', {'categories': categories, 'vendors': vendors})





@login_required
def vendor_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        
        category_id = request.POST.get('category')
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
        return redirect('vendor_products_list')
    categories = Category.objects.filter(is_active=True)
 
    return render(request, 'vendor/product/edit_product.html', {
        'product': product,
        'categories': categories,
    })



@login_required
def vendor_products_low_stock(request):
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    vendor=Vendor.objects.get(user=request.user)
    products = Product.objects.filter(vendor=vendor,stock__gt=0, stock__lte=F('low_stock_alert')).order_by('stock')

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(brand__icontains=search) |
            Q(sku__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

 
    categories = Category.objects.filter(is_active=True)
 
    return render(request, 'vendor/product/low_stock_products.html', {
        'products': products,
        'categories': categories,
       
    })



@login_required
def vendor_product_delete(request, pk):
    
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('vendor_products_list')



# Order Management
@login_required
def vendor_orders_list(request):
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    payment_status = request.GET.get('payment_status', '')
    vendor=Vendor.objects.get(user=request.user)
    orders = Order.objects.filter(
    items__product__vendor=vendor).distinct().order_by('-created_at')    

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__first_name=search) |
            Q(user__email__icontains=search) |
            Q(user__profile__phone__icontains=search)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    if payment_status:
        orders = orders.filter(payment_status=payment_status)

    return render(request, 'vendor/order/orders_list.html', {
        'orders': orders,
        'order_model': Order,
    })
    
@login_required
def vendor_orders_pending(request):
    vendor=Vendor.objects.get(user=request.user)
    orders = Order.objects.filter(
    items__product__vendor=vendor, status='pending').distinct().order_by('-created_at')
    return render(request, 'vendor/order/pending_orders.html', {
        'orders': orders,
        'order_model': Order,
    })

@login_required
def vendor_orders_delivered(request):
    vendor=Vendor.objects.get(user=request.user)
    orders = Order.objects.filter(
    items__product__vendor=vendor, status='delivered').distinct().order_by('-created_at')
    return render(request, 'vendor/order/delivered_orders.html', {
        'orders': orders,
        'order_model': Order,
    })
    

from django.utils.dateparse import parse_date

@login_required
def vendor_update_estimated_date(request, order_number):
    """
    JSON API to update estimated_delivery_date of an order
    """
    if request.method == "POST":
        new_date_str = request.POST.get("estimated_date")
        if not new_date_str:
            return JsonResponse({"success": False, "message": "No date provided."})

        order = Order.objects.filter(order_number=order_number).first()
        if not order:
            return JsonResponse({"success": False, "message": "Order not found."})

        # Parse date from string
        try:
            new_date = parse_date(new_date_str)
            if not new_date:
                raise ValueError
            order.estimated_delivery_date = new_date
            order.save()
            return JsonResponse({"success": True, "message": "Estimated delivery date updated."})
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid date format."})

    return JsonResponse({"success": False, "message": "Invalid request method."})


# Vendor Payouts
@login_required
def vendor_payouts_list(request):
    user = request.user
    vendor = Vendor.objects.get(user=user)

    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    payout_requests = VendorPayoutRequest.objects.filter(vendor=vendor)

    if search:
        payout_requests = payout_requests.filter(
            Q(admin_response__icontains=search)
        )

    if status_filter:
        payout_requests = payout_requests.filter(status=status_filter)

    totals = {
        'total_requested': payout_requests.aggregate(total=Sum('requested_amount'))['total'] or 0,
        'total_paid': payout_requests.filter(status='paid').aggregate(total=Sum('requested_amount'))['total'] or 0,
    }

    payout_requests = payout_requests.order_by('-created_at')

    return render(request, 'vendor/payout/payout_request_list.html', {
        'payout_requests': payout_requests,
        'totals': totals,
        'status_filter': status_filter,
        'search': search
    })



@login_required
def pending_payout_requests(request):
    """
    Display pending payout requests for the vendor.
    """
    vendor = Vendor.objects.get(user=request.user)
    payout_requests = VendorPayoutRequest.objects.filter(vendor=vendor, status='pending').order_by('-created_at')

    return render(request, 'vendor/payout/pending_payout.html', {
        'payout_requests': payout_requests
    })


@login_required
def rejected_payout_requests(request):
    """
    Display rejected payout requests for the vendor.
    """
    vendor = Vendor.objects.get(user=request.user)
    payout_requests = VendorPayoutRequest.objects.filter(vendor=vendor, status='rejected').order_by('-created_at')

    return render(request, 'vendor/payout/rejected_payout.html', {
        'payout_requests': payout_requests
    })
    
    

@login_required
def vendor_payout_request_add(request):
    vendor = get_object_or_404(Vendor, user=request.user)
    wallet, _ = VendorWallet.objects.get_or_create(vendor=vendor)

    if request.method == 'POST':
        if VendorPayoutRequest.objects.filter(vendor=vendor, status="pending"):
            messages.error(
        request,
        "You already have a payout request that is pending. "
        "You can send a new request only after the previous one is paid or rejected."
    )
            return redirect('vendor_payout_list')
        try:
            requested_amount = Decimal(request.POST.get('requested_amount', '0'))
        except:
            messages.error(request, "Invalid amount entered.")
            return redirect('vendor_payout_requests_add')

        #  Validation checks
        if requested_amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
            return redirect('vendor_payout_requests_add')

        if requested_amount > wallet.balance:
            messages.error(request, "Insufficient balance for this payout request.")
            return redirect('vendor_payout_requests_add')

        #  Create payout request (do NOT deduct balance yet)
        VendorPayoutRequest.objects.create(
            vendor=vendor,
            requested_amount=requested_amount,
            status='pending',  # initial status
            admin_response='',
        )

        messages.success(
            request, 
            " Payout request submitted successfully and is awaiting admin approval."
        )
        return redirect('vendor_payout_list')

    context = {
        "vendor": vendor,
        "available_balance": wallet.balance,  # show wallet balance
    }
    return render(request, 'vendor/payout/add_payout_request.html', context)


@login_required
def vendor_wallet_view(request):
   
    vendor = get_object_or_404(Vendor, user=request.user)
    
    wallet, _ = VendorWallet.objects.get_or_create(vendor=vendor)
    orders = OrderItem.objects.filter(
        product__vendor=vendor,
        order__status='delivered',
        order__payment_status='paid'
    ).select_related('order').order_by('-order__created_at')
    
    context = {
        'vendor': vendor,
        'wallet': wallet,
        'orders': orders,
    }
    
    return render(request, 'vendor/wallet/wallet.html', context)




#  Vendor Product Review
@login_required
def vendor_reviews_list(request):
    vendor=Vendor.objects.get(user=request.user)
    reviews = Review.objects.filter(product__vendor=vendor).order_by('-created_at')
    return render(request, 'vendor/review/reviews_list.html', {'reviews': reviews})





# Invoice
@login_required
def vendor_invoices(request):
    vendor=Vendor.objects.get(user=request.user)
    invoices = Invoice.objects.filter(vendor=vendor).order_by('-created_at')
    return render(request, 'vendor/invoice/invoices.html', {'invoices': invoices})


@login_required
def vendor_invoice_detail(request, invoice_number):
    vendor=Vendor.objects.get(user=request.user)
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number, vendor=vendor)
    shipping=ShippingCost.objects.first()
    tax_rate=shipping.tax
    shipping_cost=shipping.cost
    return render(request, 'vendor/invoice/invoice_detail.html', {
        'invoice': invoice,
        'tax_rate':tax_rate,
        'shipping_cost':shipping_cost
    })


# Vendor Profile
@login_required
def vendor_profile_view(request):
    vendor=Vendor.objects.get(user=request.user)
    return render(request,'vendor/profile/vendor_profile.html',{'vendor':vendor})






@login_required
def vendor_profile_edit_view(request):
    vendor = Vendor.objects.get(user=request.user)
    
    if request.method == 'POST':
        vendor.shop_name = request.POST.get('shop_name', vendor.shop_name)
        vendor.description = request.POST.get('description', vendor.description)
        vendor.phone = request.POST.get('phone', vendor.phone)
        vendor.email = request.POST.get('email', vendor.email)
        vendor.address = request.POST.get('address', vendor.address)
        vendor.city = request.POST.get('city', vendor.city)
        vendor.province = request.POST.get('province', vendor.province)
        vendor.pan_number = request.POST.get('pan_number', vendor.pan_number)
        vendor.citizenship_number = request.POST.get('citizenship_number', vendor.citizenship_number)

        files = request.FILES
        if 'shop_logo' in files:
            vendor.shop_logo = files['shop_logo']
        if 'shop_banner' in files:
            vendor.shop_banner = files['shop_banner']
        
        vendor.save()
        return redirect('vendor_profile')
    
    context = {'vendor': vendor}
    return render(request, 'vendor/profile/vendor_profile_edit.html', context)


from django.contrib.auth import update_session_auth_hash

@login_required
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
        elif len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
        else:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user) 
            messages.success(request, "Password updated successfully.")
            if user.role.role=='admin':
                return redirect('admin_dashboard')
            elif user.role.role == 'vendor':
                return redirect('vendor_profile')
            elif user.role.role == 'customer':
                return redirect('customer_profile')

    return render(request, 'dashboard/pages/change_password.html')