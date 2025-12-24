from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.db.models import Q, Sum, F, Count, Max, Exists, OuterRef, DecimalField
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
import json

from datetime import timedelta
from django.db.models.functions import TruncDate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from .models import (
    UserRole, Category, Product, ProductImage, ProductVariant, Order, OrderItem, Invoice,
    Review, Coupon,  Organization, Newsletter, Contact, 
    Notification, Slider, Banner, TaxCost, Supplier, Purchase, PurchaseItem, PurchaseInvoice, PurchaseInvoiceItem,
    Sale, SaleCustomer, SaleItem, SalePayment,
    Service, ServiceBooking
)

# Helper decorator to check admin access
def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'role') or not request.user.role.is_admin():
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper




def _create_product_from_purchase_item(name, sku, purchase_price, selling_price, estimated_days, quantity, supplier, image_file=None, category_id=None):
    """Helper to create product from purchase item data"""
    product_data = {
        'name': name,
        'sku': sku or None,
        'cost_price': purchase_price,
        'price': selling_price,
        'estimated_days': estimated_days if estimated_days else None,
        'stock': quantity,
        'is_active': True,
    }
    
    if category_id:
        try:
            product_data['category_id'] = int(category_id)
        except (ValueError, TypeError):
            pass
    
    product = Product.objects.create(**product_data)
    
    if image_file:
        product.main_image = image_file
        product.save(update_fields=['main_image'])
    
    return product, True

def _ensure_purchase_invoice(purchase):
    """Create a PurchaseInvoice for the given purchase if one doesn't exist.

    This mirrors the logic in the post_save signal but is called explicitly
    in the admin view to make invoice creation deterministic for bulk flows.
    """
    try:
        # If an invoice already exists, nothing to do
        if hasattr(purchase, 'invoice'):
            return purchase.invoice

        # only create invoice when purchase has items
        if not purchase.items.exists():
            return None

        supplier = purchase.supplier
        supplier_name = supplier.name if supplier else 'Unknown Supplier'
        supplier_email = supplier.email if supplier else ''
        supplier_phone = supplier.phone if supplier else ''
        supplier_address = supplier.address if supplier else ''
        supplier_city = supplier.city if supplier else ''

        invoice = PurchaseInvoice.objects.create(
            purchase=purchase,
            supplier_name=supplier_name,
            supplier_email=supplier_email,
            supplier_phone=supplier_phone,
            supplier_address=supplier_address,
            supplier_city=supplier_city,
            subtotal=purchase.subtotal,
            tax_amount=purchase.tax_amount if hasattr(purchase, 'tax_amount') else purchase.tax_amount,
            discount=purchase.discount if hasattr(purchase, 'discount') else purchase.discount,
            total_amount=purchase.total_amount,
            purchase_date=purchase.purchase_date,
            supplier_invoice_number=purchase.supplier_invoice_number,
            purchase_order_number=purchase.purchase_order_number,
            notes=purchase.notes,
            payment_status='pending',
        )

        # Create invoice items – snapshot current purchase items
        for item in purchase.items.all():
            PurchaseInvoiceItem.objects.create(
                invoice=invoice,
                product_name=item.product_name,
                product_sku=item.product_sku or '',
                product_image=item.product_image,
                quantity=item.quantity,
                unit_price=item.purchase_price,
                total=item.get_total(),
            )

        return invoice
    except Exception:
        # best-effort mask errors; the signal already attempts the same operation
        return None


# Admin Dashboard (Last 30 Days)
# Admin Dashboard (Last 30 Days)
@admin_required
def admin_dashboard(request):
    # Date range
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    # Users
    total_users = User.objects.count()
    customers_count = UserRole.objects.filter(role='customer').count()
    admins_count = UserRole.objects.filter(role='admin').count()

    # Products
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(stock__lte=5, stock__gt=0).count()

    # Orders
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(Sum('total'))['total__sum'] or 0

    # Last 30 days analytics
    recent_orders = Order.objects.filter(payment_status='paid', created_at__date__gte=last_30_days)
    recent_products = Product.objects.filter(created_at__date__gte=last_30_days)

    # Daily revenue & orders
    daily_orders = (recent_orders
                    .annotate(date=TruncDate('created_at'))
                    .values('date')
                    .annotate(total_orders=Count('id'), revenue=Sum('total'))
                    .order_by('date'))
    
    revenue_labels = [item['date'].strftime('%Y-%m-%d') for item in daily_orders]
    revenue_data = [float(item['revenue'] or 0) for item in daily_orders]
    orders_data = [item['total_orders'] for item in daily_orders]

    # Daily new products
    daily_products = (recent_products
                      .annotate(date=TruncDate('created_at'))
                      .values('date')
                      .annotate(new_products=Count('id'))
                      .order_by('date'))
    product_labels = [item['date'].strftime('%Y-%m-%d') for item in daily_products]
    new_products_data = [item['new_products'] for item in daily_products]

    # Content / Others
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
        'admins_count': admins_count,
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
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'orders_data': orders_data,
        'product_labels': product_labels,
        'new_products_data': new_products_data,
    }

    return render(request, 'dashboard/pages/admin_dashboard.html', context)


# -------------------------
# Services - Admin
# -------------------------
@admin_required
def admin_services_list(request):
    services = Service.objects.all().order_by('-created_at')
    return render(request, 'dashboard/pages/services/services_list.html', {'services': services})


@admin_required
def admin_service_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price = request.POST.get('price') or None
        is_active = True if request.POST.get('is_active') == 'on' else False
        try:
            price_val = Decimal(price) if price else None
        except Exception:
            price_val = None
        Service.objects.create(name=name, description=description, price=price_val, is_active=is_active)
        messages.success(request, 'Service added')
        return redirect('admin_services_list')
    return render(request, 'dashboard/pages/services/add_service.html')


@admin_required
def admin_service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.name = request.POST.get('name')
        service.description = request.POST.get('description', '')
        price = request.POST.get('price') or None
        try:
            service.price = Decimal(price) if price else None
        except Exception:
            service.price = None
        service.is_active = True if request.POST.get('is_active') == 'on' else False
        service.save()
        messages.success(request, 'Service updated')
        return redirect('admin_services_list')
    return render(request, 'dashboard/pages/services/edit_service.html', {'service': service})


@admin_required
def admin_service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    messages.success(request, 'Service deleted')
    return redirect('admin_services_list')


# Service Bookings (admin)
@admin_required
def admin_service_bookings_list(request):
    bookings = ServiceBooking.objects.select_related('service', 'customer').order_by('-created_at')
    return render(request, 'dashboard/pages/services/bookings_list.html', {'bookings': bookings})


@admin_required
def admin_service_booking_add(request):
    users = User.objects.all()
    services = Service.objects.filter(is_active=True)
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        service_id = request.POST.get('service')
        booking_date = request.POST.get('booking_date')
        status = request.POST.get('status', 'pending')
        notes = request.POST.get('notes', '')
        customer = get_object_or_404(User, pk=customer_id)
        service = get_object_or_404(Service, pk=service_id)
        ServiceBooking.objects.create(customer=customer, service=service, booking_date=booking_date, status=status, notes=notes)
        messages.success(request, 'Booking created')
        return redirect('admin_service_bookings_list')
    return render(request, 'dashboard/pages/services/booking_add.html', {'users': users, 'services': services})


@admin_required
def admin_service_booking_update(request, pk):
    booking = get_object_or_404(ServiceBooking, pk=pk)
    users = User.objects.all()
    services = Service.objects.filter(is_active=True)
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        service_id = request.POST.get('service')
        booking_date = request.POST.get('booking_date')
        status = request.POST.get('status', 'pending')
        notes = request.POST.get('notes', '')
        booking.customer = get_object_or_404(User, pk=customer_id)
        booking.service = get_object_or_404(Service, pk=service_id)
        booking.booking_date = booking_date
        booking.status = status
        booking.notes = notes
        booking.save()
        messages.success(request, 'Booking updated')
        return redirect('admin_service_bookings_list')
    return render(request, 'dashboard/pages/services/booking_edit.html', {'booking': booking, 'users': users, 'services': services})


@admin_required
def admin_service_booking_delete(request, pk):
    booking = get_object_or_404(ServiceBooking, pk=pk)
    booking.delete()
    messages.success(request, 'Booking deleted')
    return redirect('admin_service_bookings_list')


# Simple customer booking view
@login_required
def customer_book_service(request):
    services = Service.objects.filter(is_active=True)
    if request.method == 'POST':
        service_id = request.POST.get('service')
        booking_date = request.POST.get('booking_date')
        service = get_object_or_404(Service, pk=service_id)
        ServiceBooking.objects.create(customer=request.user, service=service, booking_date=booking_date)
        messages.success(request, 'Service booked successfully')
        return redirect('admin_services_list')
    return render(request, 'dashboard/pages/services/customer_book.html', {'services': services})


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

    if role in ['customer', 'admin']:
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



# Product Management
@admin_required
def admin_products_list(request):
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    products = Product.objects.all().order_by('-created_at').select_related('category')

    pending_invoice_subquery = PurchaseInvoice.objects.filter(
        purchase__items__product=OuterRef('pk'),
        payment_status__in=['pending', 'partial', 'overdue']
    )

    products = products.annotate(
        has_pending_supplier_payment=Exists(pending_invoice_subquery),
        pending_supplier_total=Sum(
            'purchase_items__purchase__invoice__total_amount',
            filter=Q(purchase_items__purchase__invoice__payment_status__in=['pending', 'partial', 'overdue']),
            distinct=True
        )
    )

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
    return render(request, 'dashboard/pages/product/products_list.html', {
        'products': products,
        'categories': categories,
    })

@admin_required
def admin_products_featured(request):
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
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
    categories = Category.objects.filter(is_active=True)


    return render(request, 'dashboard/pages/product/featured_products.html', {
        'products': products,
        'categories': categories,
    })

@admin_required
def admin_products_low_stock(request):
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
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

    categories = Category.objects.filter(is_active=True)

    return render(request, 'dashboard/pages/product/low_stock_products.html', {
        'products': products,
        'categories': categories,
    })

@admin_required
def admin_product_add(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, pk=category_id)
        product = Product.objects.create(
            category=category,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            price=Decimal(request.POST.get('price')),
            cost_price=Decimal(request.POST.get('cost_price')) if request.POST.get('cost_price') else None,
            shipping_cost=Decimal(request.POST.get('shipping_cost')) if request.POST.get('shipping_cost') else Decimal('0.00'),
            estimated_days=request.POST.get('estimated_days', '') or None,
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
   
    return render(request, 'dashboard/pages/product/add_product.html', {'categories': categories, })

@admin_required
def admin_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        category_id = request.POST.get('category')
        product.category = get_object_or_404(Category, pk=category_id)
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = Decimal(request.POST.get('price'))
        product.cost_price = Decimal(request.POST.get('cost_price')) if request.POST.get('cost_price') else None
        product.stock = int(request.POST.get('stock', 0))
        # update per-product shipping and delivery estimates
        try:
            product.shipping_cost = Decimal(request.POST.get('shipping_cost')) if request.POST.get('shipping_cost') else Decimal('0.00')
        except Exception:
            product.shipping_cost = Decimal('0.00')
        product.estimated_days = request.POST.get('estimated_days', '') or None
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
  
    return render(request, 'dashboard/pages/product/edit_product.html', {
        'product': product,
        'categories': categories,
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
    


@admin_required
def admin_order_details(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    order_items = order.items.all()

    return render(request, 'dashboard/pages/order/order_details.html', {
        'order': order,
        'order_items': order_items,
    })
    
    
# Payments Overview

@admin_required
def admin_payments_overview(request):
    """
    Show a clean summary of all completed (delivered + paid) orders for the admin dashboard.
    """

    # --- Filters ---
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    # --- Get all delivered & paid orders ---
    orders = OrderItem.objects.select_related('order').filter(
        order__status='delivered',
        order__payment_status='paid'
    )

    # --- Apply date filters ---
    if date_from:
        orders = orders.filter(order__created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(order__created_at__date__lte=date_to)

    # --- Totals ---
    total_orders = orders.count()
    total_sales = Decimal('0.00')

    for oi in orders:
        total_sales += Decimal(oi.get_total())

    # --- Context ---
    context = {
        'total_orders': total_orders,
        'total_sales': total_sales.quantize(Decimal('0.01')),
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'dashboard/pages/payment/overview.html', context)




@admin_required
def admin_payments_detail(request):
    """
    Show a detailed list of all delivered & paid orders for the admin.
    """

    # --- Get orders ---
    order_items = (
        OrderItem.objects.filter(order__status='delivered', order__payment_status='paid')
        .select_related('order', 'product')
        .order_by('-order__created_at')
    )

    # --- Totals ---
    total_sales = Decimal('0.00')
    total_orders = order_items.count()

    orders_data = []

    for oi in order_items:
        amount = Decimal(oi.get_total())
        total_sales += amount

        orders_data.append({
            'order': oi.order,
            'order_item': oi,
            'product': oi.product,
            'amount': amount,
            'payment_status': oi.order.payment_status,
        })

    # --- Context ---
    context = {
        'orders_data': orders_data,
        'total_sales': total_sales.quantize(Decimal('0.01')),
        'total_orders': total_orders,
    }

    return render(request, 'dashboard/pages/payment/payment_detail.html', context)


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
    
    # Prevent deletion of orders that are pending, processing, or shipped
    # Only allow deletion of delivered, cancelled, or refunded orders
    non_deletable_statuses = ['pending', 'processing', 'shipped']
    
    if order.status in non_deletable_statuses:
        messages.error(
            request, 
            f'Cannot delete order with status "{order.get_status_display()}". '
            f'Only delivered, cancelled, or refunded orders can be deleted.'
        )
        return redirect('admin_orders_list')
    
    # Additional check: if payment is unpaid and order is not delivered, prevent deletion
    if order.payment_status == 'unpaid' and order.status != 'delivered':
        messages.error(
            request,
            'Cannot delete unpaid orders that are not delivered. '
            'Please mark the order as delivered or update payment status first.'
        )
        return redirect('admin_orders_list')
    
    # Safe to delete
    order_number_display = order.order_number
    order.delete()
    messages.success(request, f'Order {order_number_display} has been deleted successfully.')
    return redirect('admin_orders_list')

@admin_required
def admin_order_invoice_view(request,order_number):
    order=get_object_or_404(Order,order_number=order_number)
    invoices=Invoice.objects.filter(order=order)
    return render(request,'dashboard/pages/order/invoice_list.html',{'invoices':invoices,'order_number':order_number})
    

@admin_required
def admin_invoice_detail(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    tax_setting = TaxCost.objects.first()
    tax_rate = tax_setting.tax if tax_setting else 0

    # Use order snapshot shipping_cost when available (Order stores aggregated shipping)
    shipping_cost = 0
    try:
        if invoice.order:
            shipping_cost = invoice.order.shipping_cost or 0
    except Exception:
        shipping_cost = 0

    return render(request, 'dashboard/pages/order/invoice_detail.html', {
        'invoice': invoice,
        'tax_rate': tax_rate,
        'shipping_cost': shipping_cost,
    })
    
    

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


@admin_required
def api_update_order_payment_status(request, order_number):
    """
    AJAX API endpoint to update order payment status.
    Automatically sets order status to 'delivered' when payment is marked as 'paid'.
    
    Expected JSON payload:
    {
        "payment_status": "paid" | "unpaid" | "failed" | "refunded",
        "transaction_id": "optional transaction ID",
        "notes": "optional notes"
    }
    
    Returns JSON response:
    {
        "success": true/false,
        "message": "Status message",
        "data": {
            "order_number": "...",
            "payment_status": "...",
            "order_status": "...",
            "updated_at": "..."
        },
        "error": "Error message if success is false"
    }
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Method not allowed. Use POST.',
            'message': 'Invalid request method'
        }, status=405)
    
    # Check if request is AJAX
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest' and not request.content_type == 'application/json':
        # Allow form data as well for flexibility
        pass
    
    try:
        # Get order
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Order not found',
                'message': f'Order with number {order_number} does not exist'
            }, status=404)
        
        # Parse request data (support both JSON and form data)
        if request.content_type == 'application/json':
            try:
                import json
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON format',
                    'message': 'Request body must be valid JSON'
                }, status=400)
        else:
            data = request.POST
        
        # Validate payment_status
        payment_status = data.get('payment_status', '').strip().lower()
        
        if not payment_status:
            return JsonResponse({
                'success': False,
                'error': 'Missing required field',
                'message': 'payment_status is required'
            }, status=400)
        
        # Validate payment_status value
        valid_statuses = [choice[0] for choice in Order.PAYMENT_STATUS_CHOICES]
        if payment_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Invalid payment status',
                'message': f'payment_status must be one of: {", ".join(valid_statuses)}',
                'valid_statuses': valid_statuses
            }, status=400)
        
        # Store old values for response
        old_payment_status = order.payment_status
        old_order_status = order.status
        
        # Update payment status
        order.payment_status = payment_status
        
        # Update transaction_id if provided
        transaction_id = data.get('transaction_id', '').strip()
        if transaction_id:
            order.transaction_id = transaction_id
        
        # Auto-update order status to 'delivered' when payment is marked as 'paid'
        if payment_status == 'paid':
            # Only update to delivered if order is not already cancelled or refunded
            if order.status not in ['cancelled', 'refunded']:
                order.status = 'delivered'
                # Set delivered_at timestamp if not already set
                if not order.delivered_at:
                    order.delivered_at = timezone.now()
        
        # Handle refunded status
        elif payment_status == 'refunded':
            # Optionally set order status to refunded
            if order.status not in ['cancelled']:
                order.status = 'refunded'
        
        # Save order
        order.save()
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': f'Payment status updated successfully from "{old_payment_status}" to "{payment_status}"',
            'data': {
                'order_number': order.order_number,
                'payment_status': order.payment_status,
                'order_status': order.status,
                'previous_payment_status': old_payment_status,
                'previous_order_status': old_order_status,
                'updated_at': order.updated_at.isoformat(),
                'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
                'transaction_id': order.transaction_id,
            }
        }
        
        # Add additional message if order status was auto-updated
        if payment_status == 'paid' and old_order_status != 'delivered':
            response_data['message'] += f'. Order status automatically updated to "delivered".'
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        # Log error in production (you can use logging module)
        import traceback
        error_trace = traceback.format_exc()
        
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'message': 'An error occurred while updating payment status',
            'details': str(e) if settings.DEBUG else 'Please contact support'
        }, status=500)


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
            'shipping_cost': str(item.shipping_cost),
            'estimated_days': item.estimated_days or '',
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




# Tax Settings management (global TaxCost replacement for previous ShippingCost)
@admin_required
def tax_settings_view(request):
    tax_setting = TaxCost.objects.first()  # global tax setting (we removed global shipping cost)
    return render(request, 'dashboard/pages/tax/tax_list.html', {
        'tax_setting': tax_setting
    })


@admin_required
def tax_settings_edit(request, pk):
    tax_setting = get_object_or_404(TaxCost, pk=pk)

    if request.method == "POST":
        tax = request.POST.get("tax")
        try:
            tax_setting.tax = Decimal(tax)
        except Exception:
            tax_setting.tax = tax
        tax_setting.save()

        messages.success(request, "Tax updated successfully.")
        return redirect("admin_tax_settings")

    return render(request, "dashboard/pages/tax/tax_edit.html", {
        "tax_setting": tax_setting
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
            return redirect('admin_dashboard')
          

    return render(request, 'dashboard/pages/change_password.html')


# ===========================
#   Supplier Management
# ===========================

@admin_required
def admin_suppliers_list(request):
    search = request.GET.get('search', '')
    suppliers = Supplier.objects.all().order_by('name')
    
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) |
            Q(contact_person__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    suppliers = suppliers.annotate(
        outstanding_amount=Sum(
            'purchases__invoice__total_amount',
            filter=Q(purchases__invoice__payment_status__in=['pending', 'partial', 'overdue']),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        paid_amount=Sum(
            'purchases__invoice__total_amount',
            filter=Q(purchases__invoice__payment_status='paid'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        purchase_count=Count('purchases', distinct=True),
        last_purchase_date=Max('purchases__purchase_date')
    )
    
    return render(request, 'dashboard/pages/supplier/suppliers_list.html', {
        'suppliers': suppliers,
    })


@admin_required
def admin_supplier_add(request):
    if request.method == 'POST':
        supplier = Supplier.objects.create(
            name=request.POST.get('name'),
            contact_person=request.POST.get('contact_person', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            notes=request.POST.get('notes', ''),
            is_active=True if request.POST.get('is_active') == 'on' else False,
        )
        messages.success(request, 'Supplier added successfully.')
        return redirect('admin_suppliers_list')
    
    return render(request, 'dashboard/pages/supplier/add_supplier.html')


@admin_required
def admin_supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.contact_person = request.POST.get('contact_person', '')
        supplier.email = request.POST.get('email', '')
        supplier.phone = request.POST.get('phone', '')
        supplier.address = request.POST.get('address', '')
        supplier.city = request.POST.get('city', '')
        supplier.notes = request.POST.get('notes', '')
        supplier.is_active = True if request.POST.get('is_active') == 'on' else False
        supplier.save()
        messages.success(request, 'Supplier updated successfully.')
        return redirect('admin_suppliers_list')
    
    return render(request, 'dashboard/pages/supplier/edit_supplier.html', {'supplier': supplier})


@admin_required
def admin_supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.delete()
    messages.success(request, 'Supplier deleted successfully.')
    return redirect('admin_suppliers_list')


@admin_required
def admin_supplier_payments_update(request):
    if request.method == 'POST':
        try:
            supplier_id = request.POST.get('supplier_id')
            amount_str = request.POST.get('amount', '')
            notes = request.POST.get('notes', '')
            invoice_id = request.POST.get('invoice_id')  # Optional: specific invoice payment
            
            # Validate supplier exists
            try:
                supplier = Supplier.objects.get(id=supplier_id)
            except Supplier.DoesNotExist:
                messages.error(request, 'Supplier not found')
                return redirect(request.META.get('HTTP_REFERER', 'admin_suppliers_list'))
            
            # Validate and convert amount
            try:
                amount = Decimal(amount_str)
            except (ValueError, TypeError):
                messages.error(request, 'Invalid payment amount')
                return redirect(request.META.get('HTTP_REFERER'))
            
            if amount <= 0:
                messages.error(request, 'Payment amount must be greater than 0')
                return redirect(request.META.get('HTTP_REFERER'))
            
            # If paying specific invoice
            if invoice_id:
                try:
                    invoice = PurchaseInvoice.objects.get(id=invoice_id)
                    if invoice.purchase.supplier_id != int(supplier_id):
                        messages.error(request, 'Invoice does not belong to this supplier')
                        return redirect(request.META.get('HTTP_REFERER'))
                except PurchaseInvoice.DoesNotExist:
                    messages.error(request, 'Invoice not found')
                    return redirect(request.META.get('HTTP_REFERER'))
                
                # Check if payment exceeds outstanding
                outstanding = invoice.total_amount
                if amount > outstanding:
                    messages.warning(request, f'Payment amount exceeds outstanding balance of Rs. {outstanding}')
                
                # Update payment status
                paid_so_far = invoice.total_amount - outstanding
                new_paid_amount = paid_so_far + amount
                
                if new_paid_amount >= invoice.total_amount:
                    invoice.payment_status = 'paid'
                    invoice.payment_date = timezone.now().date()
                else:
                    invoice.payment_status = 'partial'
                
                invoice.save()
                messages.success(request, 'Payment recorded successfully')
            else:
                # Pay all outstanding invoices for the supplier
                invoices = PurchaseInvoice.objects.filter(
                    purchase__supplier_id=supplier_id,
                    payment_status__in=['pending', 'partial', 'overdue']
                ).order_by('purchase_date')
                
                if not invoices.exists():
                    messages.warning(request, 'No outstanding invoices for this supplier')
                    return redirect(request.META.get('HTTP_REFERER'))
                
                remaining_payment = amount
                
                for invoice in invoices:
                    if remaining_payment <= 0:
                        break
                    
                    outstanding = invoice.total_amount
                    payment_for_this_invoice = min(remaining_payment, outstanding)
                    
                    paid_so_far = invoice.total_amount - outstanding
                    new_paid_amount = paid_so_far + payment_for_this_invoice
                    
                    if new_paid_amount >= invoice.total_amount:
                        invoice.payment_status = 'paid'
                        invoice.payment_date = timezone.now().date()
                    else:
                        invoice.payment_status = 'partial'
                    
                    invoice.save()
                    remaining_payment -= payment_for_this_invoice
                
                messages.success(request, f'Payment of Rs. {amount} processed successfully')
            
            return redirect(request.META.get('HTTP_REFERER', 'admin_suppliers_list'))
        
        except Exception as e:
            messages.error(request, f'Error processing payment: {str(e)}')
            return redirect(request.META.get('HTTP_REFERER', 'admin_suppliers_list'))
    
    return redirect('admin_suppliers_list')
        
        
        
        

@admin_required
def admin_supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    purchases = (
        supplier.purchases
        .select_related('invoice')
        .prefetch_related('items__product')
        .order_by('-purchase_date', '-created_at')
    )

    invoices = (
        PurchaseInvoice.objects
        .filter(purchase__supplier=supplier)
        .prefetch_related('items')
        .order_by('-purchase_date', '-created_at')
    )

    from django.db.models import Max, Count, Q

    # Products supplied with last purchase date + pending payment count
    supplier_products = (
        Product.objects
        .filter(purchase_items__purchase__supplier=supplier)
        .annotate(
            last_purchase_date=Max('purchase_items__purchase__purchase_date'),
            pending_payments=Count(
                'purchase_items__purchase__invoice',
                filter=Q(
                    purchase_items__purchase__invoice__payment_status__in=[
                        'pending', 'partial', 'overdue'
                    ]
                )
            )
        )
        .distinct()
        .order_by('-created_at')
    )

    # Stats
    total_amount = sum((p.total_amount for p in purchases), Decimal('0'))
    outstanding_amount = Decimal('0')
    paid_amount = Decimal('0')

    for invoice in invoices:
        if invoice.payment_status in ['pending', 'partial', 'overdue']:
            outstanding_amount += invoice.total_amount
        elif invoice.payment_status == 'paid':
            paid_amount += invoice.total_amount

    context = {
        'supplier': supplier,
        'purchases': purchases,
        'invoices': invoices,
        'supplier_products': supplier_products,
        'stats': {
            'total_amount': total_amount,
            'outstanding_amount': outstanding_amount,
            'paid_amount': paid_amount,
            'purchase_count': purchases.count(),
            'product_count': supplier_products.count(),
        }
    }

    return render(request, 'dashboard/pages/supplier/supplier_detail.html', context)



# ===========================
#   Purchase Management
# ===========================

@admin_required
def admin_purchases_list(request):
    search = request.GET.get('search', '')
    supplier_id = request.GET.get('supplier', '')
    payment_status = request.GET.get('payment_status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    purchases = Purchase.objects.all().select_related('supplier').prefetch_related('items__product', 'invoice').order_by('-purchase_date', '-created_at')
    
    if search:
        purchases = purchases.filter(
            Q(supplier_invoice_number__icontains=search) |
            Q(purchase_order_number__icontains=search) |
            Q(supplier__name__icontains=search) |
            Q(items__product_name__icontains=search) |
            Q(items__product_sku__icontains=search) |
            Q(invoice__invoice_number__icontains=search)
        ).distinct()
    
    if supplier_id:
        purchases = purchases.filter(supplier_id=supplier_id)
    
    if payment_status:
        purchases = purchases.filter(invoice__payment_status=payment_status)
    
    if date_from:
        purchases = purchases.filter(purchase_date__gte=date_from)
    
    if date_to:
        purchases = purchases.filter(purchase_date__lte=date_to)
    
    # Calculate totals
    total_amount = sum(p.total_amount for p in purchases)
    total_quantity = sum(p.get_total_quantity() for p in purchases)
    
    # Calculate payment statistics
    paid_amount = Decimal('0')
    pending_amount = Decimal('0')
    for p in purchases:
        if hasattr(p, 'invoice') and p.invoice:
            if p.invoice.payment_status == 'paid':
                paid_amount += p.invoice.total_amount
            elif p.invoice.payment_status in ['pending', 'partial', 'overdue']:
                pending_amount += p.invoice.total_amount
    
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'dashboard/pages/purchase/purchases_list.html', {
        'purchases': purchases,
        'suppliers': suppliers,
        'total_amount': total_amount,
        'total_quantity': total_quantity,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
    })


@admin_required
def admin_purchase_add(request):
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    if request.method == 'POST':
        try:
            # Get supplier
            supplier_id = request.POST.get('supplier')
            if not supplier_id:
                messages.error(request, 'Please select a supplier.')
                raise ValueError('Supplier is required')
            
            supplier = get_object_or_404(Supplier, pk=supplier_id)
            
            # Get purchase details
            purchase_date = request.POST.get('purchase_date', timezone.now().date())
            notes = request.POST.get('notes', '')
            tax_amount = Decimal(request.POST.get('tax_amount', 0))
            discount = Decimal(request.POST.get('discount', 0))
            
            # Get product arrays
            product_ids = request.POST.getlist('product_id[]')
            product_names = request.POST.getlist('product_name[]')
            product_categories = request.POST.getlist('product_category[]')
            purchase_prices = request.POST.getlist('purchase_price[]')
            selling_prices = request.POST.getlist('selling_price[]')
            estimated_days_list = request.POST.getlist('estimated_days[]')
            quantities = request.POST.getlist('quantity[]')
            product_images = request.FILES.getlist('product_image[]')
            
            # Basic validation
            if not product_names:
                messages.error(request, 'Please add at least one product.')
                raise ValueError('No products added')
            
            # Create purchase with transaction
            with transaction.atomic():
                purchase = Purchase.objects.create(
                    supplier=supplier,
                    purchase_date=purchase_date,
                    notes=notes,
                    tax_amount=tax_amount,
                    discount=discount,
                    subtotal=0,
                    total_amount=0,
                )
                
                items_added = 0
                auto_created_products = 0
                updated_products = 0
                
                for i in range(len(product_names)):
                    product_name = product_names[i].strip()
                    if not product_name:
                        continue
                    
                    category_id = product_categories[i] if i < len(product_categories) else ''
                    product_id = product_ids[i] if i < len(product_ids) and product_ids[i] else ''
                    purchase_price = Decimal(purchase_prices[i]) if i < len(purchase_prices) else Decimal('0')
                    selling_price = Decimal(selling_prices[i]) if i < len(selling_prices) else Decimal('0')
                    estimated_days = estimated_days_list[i].strip() if i < len(estimated_days_list) else ''
                    quantity = int(quantities[i]) if i < len(quantities) else 1
                    product_image = product_images[i] if i < len(product_images) and product_images[i] else None
                    
                    # Skip invalid entries
                    if purchase_price <= 0 or selling_price <= 0 or quantity <= 0:
                        continue
                    
                    # Get or create product
                    product = None
                    product_created = False
                    
                    if product_id:
                        try:
                            product = Product.objects.get(pk=product_id)
                            # Update existing product with new data
                            product.cost_price = purchase_price
                            product.price = selling_price
                            if estimated_days:
                                product.estimated_days = estimated_days
                            product.save(update_fields=['cost_price', 'price', 'estimated_days'])
                            updated_products += 1
                        except Product.DoesNotExist:
                            pass
                    
                    # Auto-create product if not selected
                    if not product:
                        product, product_created = _create_product_from_purchase_item(
                            name=product_name,
                            sku='',
                            purchase_price=purchase_price,
                            selling_price=selling_price,
                            estimated_days=estimated_days,
                            quantity=quantity,
                            supplier=supplier,
                            image_file=product_image,
                            category_id=category_id
                        )
                        auto_created_products += 1
                        
                        # Reset file pointer for reuse
                        if product_image and hasattr(product_image, 'seek'):
                            product_image.seek(0)
                    
                    # Create purchase item
                    purchase_item = PurchaseItem(
                        purchase=purchase,
                        product=product,
                        product_name=product_name,
                        product_sku=product.sku or '',
                        purchase_price=purchase_price,
                        quantity=quantity,
                    )
                    
                    if product_image:
                        purchase_item.product_image = product_image
                    
                    purchase_item.save()
                    
                    # Update stock for existing products
                    if product and not product_created:
                        product.stock += quantity
                        product.save(update_fields=['stock'])
                    
                    items_added += 1
                
                if items_added == 0:
                    raise ValueError('No valid products were added.')
                
                # Calculate totals
                purchase.calculate_totals()
                purchase.refresh_from_db()
                
                # Ensure a single invoice exists for this purchase
                if not hasattr(purchase, 'invoice') and purchase.items.exists():
                    _ensure_purchase_invoice(purchase)
            
            # Success message
            message = f'Purchase order created successfully with {items_added} item(s).'
            if auto_created_products > 0:
                message += f' {auto_created_products} new product(s) created.'
            if updated_products > 0:
                message += f' {updated_products} existing product(s) updated with new cost price, selling price, and ETA.'
            messages.success(request, message)
            
            return redirect('admin_purchases_list')
            
        except ValueError:
            pass  # Error message already set
        except Exception as e:
            messages.error(request, f'Error creating purchase: {str(e)}')
    
    # Render form
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')
    selected_supplier_id = request.GET.get('supplier', '')
    
    return render(request, 'dashboard/pages/purchase/add_purchase.html', {
        'suppliers': suppliers,
        'products': products,
        'categories': categories,
        'selected_supplier_id': selected_supplier_id,
    })


@admin_required
def admin_purchase_update(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        supplier = get_object_or_404(Supplier, pk=supplier_id)
        
        # Update basic purchase info
        purchase.supplier = supplier
        purchase.purchase_date = request.POST.get('purchase_date', purchase.purchase_date)
        purchase.supplier_invoice_number = request.POST.get('supplier_invoice_number', '')
        purchase.purchase_order_number = request.POST.get('purchase_order_number', '')
        purchase.notes = request.POST.get('notes', '')
        purchase.tax_amount = Decimal(request.POST.get('tax_amount', 0))
        purchase.discount = Decimal(request.POST.get('discount', 0))
        purchase.save()
        
        # Recalculate totals
        purchase.calculate_totals()
        # Ensure invoice exists after update when items present
        if not hasattr(purchase, 'invoice') and purchase.items.exists():
            _ensure_purchase_invoice(purchase)
        
        messages.success(request, 'Purchase updated successfully.')
        return redirect('admin_purchases_list')
    
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'dashboard/pages/purchase/edit_purchase.html', {
        'purchase': purchase,
        'suppliers': suppliers,
    })


@admin_required
def admin_purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Update product stock for all items
    for item in purchase.items.all():
        if item.product:
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.save()
    
    purchase.delete()
    messages.success(request, 'Purchase deleted successfully.')
    return redirect('admin_purchases_list')


# ===========================
#   Purchase Invoice Management
# ===========================

@admin_required
def admin_purchase_invoices_list(request):
    """List all purchase invoices with summary statistics"""
    search = request.GET.get('search', '')
    supplier_filter = request.GET.get('supplier', '')
    payment_status = request.GET.get('payment_status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    invoices = PurchaseInvoice.objects.all().prefetch_related('items').order_by('-purchase_date', '-created_at')
    
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(supplier_name__icontains=search) |
            Q(items__product_name__icontains=search) |
            Q(items__product_sku__icontains=search) |
            Q(supplier_invoice_number__icontains=search)
        ).distinct()
    
    if supplier_filter:
        invoices = invoices.filter(supplier_name__icontains=supplier_filter)
    
    if payment_status:
        invoices = invoices.filter(payment_status=payment_status)
    
    if date_from:
        invoices = invoices.filter(purchase_date__gte=date_from)
    
    if date_to:
        invoices = invoices.filter(purchase_date__lte=date_to)
    
    # Calculate summary statistics
    total_invoices = invoices.count()
    total_amount = sum(inv.total_amount for inv in invoices)
    total_paid = sum(inv.total_amount for inv in invoices.filter(payment_status='paid'))
    total_pending = sum(inv.total_amount for inv in invoices.filter(payment_status='pending'))
    
    return render(request, 'dashboard/pages/purchase/invoices_list.html', {
        'invoices': invoices,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_pending': total_pending,
    })


@admin_required
def admin_purchase_invoice_detail(request, invoice_number):
    """View detailed purchase invoice"""
    invoice = get_object_or_404(PurchaseInvoice.objects.prefetch_related('items'), invoice_number=invoice_number)
    organization = Organization.objects.first()
    
    return render(request, 'dashboard/pages/purchase/invoice_detail.html', {
        'invoice': invoice,
        'organization': organization,
    })


@admin_required
def admin_purchase_invoice_update_payment(request, invoice_number):
    """Update payment status of a purchase invoice"""
    invoice = get_object_or_404(PurchaseInvoice, invoice_number=invoice_number)
    
    if request.method == 'POST':
        payment_status = request.POST.get('payment_status')
        payment_date = request.POST.get('payment_date', '')
        
        if payment_status in dict(PurchaseInvoice.PAYMENT_STATUS_CHOICES):
            invoice.payment_status = payment_status
            if payment_date:
                invoice.payment_date = payment_date
            invoice.save()
            messages.success(request, 'Payment status updated successfully.')
        else:
            messages.error(request, 'Invalid payment status.')
    
    return redirect('admin_purchase_invoice_detail', invoice_number=invoice_number)


@admin_required
def api_update_purchase_invoice_payment_status(request, invoice_number):
    """AJAX API endpoint to update purchase invoice payment status"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    try:
        invoice = PurchaseInvoice.objects.get(invoice_number=invoice_number)
    except PurchaseInvoice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invoice not found'}, status=404)
    
    try:
        data = json.loads(request.body)
        payment_status = data.get('payment_status')
        payment_date = data.get('payment_date', '')
        
        if payment_status not in dict(PurchaseInvoice.PAYMENT_STATUS_CHOICES):
            return JsonResponse({'success': False, 'error': 'Invalid payment status'}, status=400)
        
        invoice.payment_status = payment_status
        if payment_date:
            try:
                from datetime import datetime
                # Parse the date string
                if isinstance(payment_date, str) and payment_date.strip():
                    invoice.payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
            except (ValueError, TypeError) as e:
                # If date parsing fails, only set it if status is 'paid' and use today's date
                if payment_status == 'paid':
                    invoice.payment_date = timezone.now().date()
        elif payment_status == 'paid' and not invoice.payment_date:
            # Auto-set payment date to today if status is paid and no date provided
            invoice.payment_date = timezone.now().date()
        elif payment_status != 'paid':
            # Clear payment date if status is not paid
            invoice.payment_date = None
        
        invoice.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment status updated successfully',
            'payment_status': invoice.payment_status,
            'payment_status_display': invoice.get_payment_status_display(),
            'payment_date': invoice.payment_date.strftime('%Y-%m-%d') if invoice.payment_date else None,
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ===========================
#   Sales Management (Physical/Offline)
# ===========================

@admin_required
def admin_sales_list(request):
    """Display list of all sales"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    sales = Sale.objects.all().select_related('customer').order_by('-created_at')
    
    if search:
        sales = sales.filter(
            Q(invoice_number__icontains=search) | 
            Q(customer__name__icontains=search)
        )
    
    if status in ['paid', 'partially_paid', 'unpaid']:
        sales = sales.filter(payment_status=status)
    
    context = {
        'sales': sales,
    }
    return render(request, 'dashboard/pages/sales/sales_list.html', context)


@admin_required
def admin_sales_add(request):
    """Create a new sale"""
    if request.method == 'POST':
        with transaction.atomic():
            try:
                customer_type = request.POST.get('customer_type', 'existing')
                
                # Get or create customer
                if customer_type == 'existing':
                    customer_id = request.POST.get('customer')
                    customer = get_object_or_404(SaleCustomer, id=customer_id)
                else:
                    customer_name = request.POST.get('new_customer_name')
                    customer_email = request.POST.get('new_customer_email', '')
                    customer_phone = request.POST.get('new_customer_phone', '')
                    customer_address = request.POST.get('new_customer_address', '')
                    
                    customer = SaleCustomer.objects.create(
                        name=customer_name,
                        email=customer_email or None,
                        phone=customer_phone or None,
                        address=customer_address or None,
                    )
                
                # Get form data
                paid_amount = Decimal(request.POST.get('paid_amount', '0'))
                payment_method = request.POST.get('payment_method', '')
                payment_notes = request.POST.get('payment_notes', '')
                notes = request.POST.get('notes', '')
                
                # Create sale
                sale = Sale.objects.create(
                    customer=customer,
                    paid_amount=paid_amount,
                    payment_method=payment_method or None,
                    payment_notes=payment_notes or None,
                    notes=notes or None,
                )
                
                # Get product data from form
                # Assuming form sends multiple product_id, quantity, unit_price
                total_amount = Decimal('0.00')
                
                # Parse product items (they should be sent as arrays or repeated fields)
                product_ids = request.POST.getlist('product_id')
                quantities = request.POST.getlist('quantity')
                unit_prices = request.POST.getlist('unit_price')
                
                for prod_id, qty, price in zip(product_ids, quantities, unit_prices):
                    product = get_object_or_404(Product, id=prod_id)
                    quantity = int(qty)
                    unit_price = Decimal(price)
                    
                    item = SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                    )
                    total_amount += item.total_amount
                
                # Update sale with total amount and save
                sale.total_amount = total_amount
                sale.save()
                
                # Record initial payment if any
                if paid_amount > 0:
                    SalePayment.objects.create(
                        sale=sale,
                        amount=paid_amount,
                        payment_method=payment_method or 'cash',
                    )
                
                messages.success(request, f'Sale #{sale.invoice_number} created successfully')
                return redirect('admin_sales_list')
                
            except Exception as e:
                messages.error(request, f'Error creating sale: {str(e)}')
                return redirect('admin_sales_add')
    
    customers = SaleCustomer.objects.all().order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'customers': customers,
        'products': products,
    }
    return render(request, 'dashboard/pages/sales/add_sale.html', context)


@admin_required
def admin_sales_edit(request, pk):
    """Edit an existing sale"""
    sale = get_object_or_404(Sale, id=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            try:
                paid_amount = Decimal(request.POST.get('paid_amount', '0'))
                payment_status = request.POST.get('payment_status', sale.payment_status)
                payment_method = request.POST.get('payment_method', '')
                payment_notes = request.POST.get('payment_notes', '')
                
                # Update sale
                sale.paid_amount = paid_amount
                sale.payment_status = payment_status
                sale.payment_method = payment_method or None
                sale.payment_notes = payment_notes or None
                sale.save()
                
                messages.success(request, f'Sale #{sale.invoice_number} updated successfully')
                return redirect('admin_sales_detail', pk=sale.id)
                
            except Exception as e:
                messages.error(request, f'Error updating sale: {str(e)}')
    
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'sale': sale,
        'products': products,
    }
    return render(request, 'dashboard/pages/sales/edit_sale.html', context)


@admin_required
def admin_sales_detail(request, pk):
    """View sale details"""
    sale = get_object_or_404(Sale, id=pk)
    payments = sale.payments.all()
    
    context = {
        'sale': sale,
        'payments': payments,
    }
    return render(request, 'dashboard/pages/sales/sale_detail.html', context)


@admin_required
def admin_sales_delete(request, pk):
    """Delete a sale"""
    sale = get_object_or_404(Sale, id=pk)
    sale.delete()
    messages.success(request, 'Sale deleted successfully')
    return redirect('admin_sales_list')


@admin_required
def admin_sales_customers(request):
    """View all customers with their sales summary"""
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    customers = SaleCustomer.objects.all().order_by('-created_at')
    
    if search:
        customers = customers.filter(
            Q(name__icontains=search) | 
            Q(email__icontains=search)
        )
    
    # Filter by payment status
    if status == 'paid':
        customers = customers.filter(sales__payment_status='paid').distinct()
    elif status == 'partially_paid':
        # Get customers with at least one partially paid sale
        customers = customers.exclude(
            sales__payment_status='paid'
        ).exclude(
            sales__payment_status='unpaid'
        ).distinct()
    elif status == 'unpaid':
        customers = customers.filter(sales__payment_status='unpaid').distinct()
    
    # Annotate with aggregated data
    customers = customers.annotate(
        total_sales_amount=Sum('sales__total_amount'),
        total_paid_amount=Sum('sales__paid_amount'),
        total_outstanding_amount=Sum('sales__outstanding_amount'),
        sales_count=Count('sales'),
    )
    
    context = {
        'customers': customers,
    }
    return render(request, 'dashboard/pages/sales/sales_customers.html', context)


@admin_required
def admin_sales_customer_detail(request, pk):
    """View customer details and their sales history"""
    customer = get_object_or_404(SaleCustomer, id=pk)
    sales = customer.sales.all().order_by('-created_at')
    
    # Calculate stats
    stats = {
        'sales_count': sales.count(),
        'total_sales_amount': sales.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
        'total_paid_amount': sales.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00'),
        'total_outstanding_amount': sales.aggregate(Sum('outstanding_amount'))['outstanding_amount__sum'] or Decimal('0.00'),
        'paid_sales_count': sales.filter(payment_status='paid').count(),
        'partially_paid_sales_count': sales.filter(payment_status='partially_paid').count(),
        'unpaid_sales_count': sales.filter(payment_status='unpaid').count(),
    }
    
    context = {
        'customer': customer,
        'sales': sales,
        'stats': stats,
    }
    return render(request, 'dashboard/pages/sales/customer_detail.html', context)


@admin_required
def admin_sales_customer_payment(request, pk):
    """Record payment for a customer"""
    customer = get_object_or_404(SaleCustomer, id=pk)
    
    if request.method == 'POST':
        try:
            payment_amount = Decimal(request.POST.get('payment_amount', '0'))
            payment_method = request.POST.get('payment_method', 'cash')
            notes = request.POST.get('notes', '')
            
            # Apply payment to oldest unpaid/partially paid sales
            outstanding = payment_amount
            
            for sale in customer.sales.exclude(payment_status='paid').order_by('created_at'):
                if outstanding <= 0:
                    break
                
                if outstanding >= sale.outstanding_amount:
                    # Pay this sale completely
                    sale.paid_amount = sale.total_amount
                    outstanding -= sale.outstanding_amount
                else:
                    # Partial payment
                    sale.paid_amount += outstanding
                    outstanding = Decimal('0.00')
                
                sale.save()
                
                # Record payment
                SalePayment.objects.create(
                    sale=sale,
                    amount=min(payment_amount, sale.outstanding_amount + sale.paid_amount - sale.paid_amount) if outstanding == 0 else min(payment_amount, sale.outstanding_amount),
                    payment_method=payment_method,
                    notes=notes,
                )
            
            messages.success(request, f'Payment of Rs.{payment_amount} recorded successfully')
            return redirect('admin_sales_customer_detail', pk=customer.id)
            
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
            return redirect('admin_sales_customer_detail', pk=customer.id)
    
    return redirect('admin_sales_customer_detail', pk=customer.id)


@admin_required
def admin_sales_detail_payment(request, pk):
    """Record payment for a specific sale"""
    sale = get_object_or_404(Sale, id=pk)
    
    if request.method == 'POST':
        try:
            payment_amount = Decimal(request.POST.get('payment_amount', '0'))
            payment_method = request.POST.get('payment_method', 'cash')
            notes = request.POST.get('notes', '')
            
            sale.paid_amount += payment_amount
            sale.save()
            
            # Record payment
            SalePayment.objects.create(
                sale=sale,
                amount=payment_amount,
                payment_method=payment_method,
                notes=notes,
            )
            
            messages.success(request, f'Payment of Rs.{payment_amount} recorded successfully')
            return redirect('admin_sales_detail', pk=sale.id)
            
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
            return redirect('admin_sales_detail', pk=sale.id)
    
    return redirect('admin_sales_detail', pk=sale.id)