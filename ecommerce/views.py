
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from dashboard.models import (
    UserRole,
    UserProfile,
    Slider,
    Banner,
    Category,SubCategory,
    Product,Cart,Vendor,ProductVariant,OTPVerification,Order,OrderItem,Coupon,CouponUsage,Contact,Invoice,Review,TaxRate
)
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from  django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import models
import json
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
import random
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db.models import F
from datetime import date, timedelta





from .recommender import get_recommendations


def home_page(request):
    sliders = Slider.objects.filter(is_active=True).order_by('-created_at')[:5]
    banners = Banner.objects.filter(is_active=True, page="home")
    categories = Category.objects.filter(is_active=True, is_featured=True).order_by('order')[:12]
    
    # Featured Products Pagination
    featured_products = Product.objects.filter(is_active=True, is_featured=True).order_by('-created_at')
    featured_paginator = Paginator(featured_products, 18)  # 12 items per page
    featured_page_number = request.GET.get('featured_page', 1)
    featured_products_page = featured_paginator.get_page(featured_page_number)
    
    # Best Offers Pagination
    best_offers = Product.objects.filter(
                is_active=True,
                price__lt=F('cost_price') * 0.75  # Price less than 75% of cost price = >25% discount
            ).order_by('-created_at')[:20]
    best_offers_paginator = Paginator(best_offers, 18)  # 12 items per page
    best_offers_page_number = request.GET.get('best_offers_page', 1)
    best_offers_page = best_offers_paginator.get_page(best_offers_page_number)

    context = {
        'sliders': sliders,
        'banners': banners,
        'categories': categories,
        'featured_products': featured_products_page,
        'best_offers': best_offers_page,
    }
    return render(request, 'website/pages/home.html', context)



def search_page(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
  

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(category__subcategories__name__icontains=query)
        ).distinct().order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 24) 
    page_number = request.GET.get('page', 1)
    products_page = paginator.get_page(page_number)

    context = {
        'query': query,
        'products': products_page,

       
    }
    return render(request, 'website/pages/search.html', context)



def all_collections(request):
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
     
    }
    return render(request, 'website/pages/all_collections.html', context)


def new_arrivals_page(request):
    # Calculate the date 29 days ago
    one_month_ago = timezone.now() - timedelta(days=29)
    new_arrivals = Product.objects.filter(
        is_active=True,
        created_at__gte=one_month_ago
    ).order_by('-created_at')
    
    paginator = Paginator(new_arrivals, 12)  
    page_number = request.GET.get('page', 1)
    new_arrivals_page = paginator.get_page(page_number)

    context = {
        'new_arrivals': new_arrivals_page,
    }
    return render(request, 'website/pages/new_arrivals.html', context)




import string

def become_vendor(request):
    if request.method == 'POST':
        try:
            print(request.POST)
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email', '').strip().lower()
            if User.objects.filter(email=email,is_active=True).exists():
                messages.error(request,'User already exists')
                return redirect('become_vendor_page')
            
            

            # Vendor info
            shop_name = request.POST.get('shop_name')
            description = request.POST.get('description')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            city = request.POST.get('city')
            province = request.POST.get('province')
            pan_number = request.POST.get('pan_number')
            citizenship_number=request.POST.get('citizenship_number')
            # Files
            shop_logo = request.FILES.get('shop_logo')
            shop_banner = request.FILES.get('shop_banner')
            pan_document = request.FILES.get('pan_document')
            citizenship_front = request.FILES.get('citizenship_front')
            citizenship_back = request.FILES.get('citizenship_back')
            company_registration = request.FILES.get('company_registration')
            qr_image=request.FILES.get('qr_image')

     
            # Update user info
            user,_=User.objects.get_or_create(email=email)
            user.username=email,
            user.first_name=first_name
            user.last_name=last_name
            user.email=email
            user.is_active=False
            user.save()
        
            # Create vendor
            vendor = Vendor.objects.create(
                user=user,
                shop_name=shop_name,
                shop_banner=shop_banner,
                description=description or "",
                phone=phone,
                address=address,
                city=city or "",
                province=province or "",
                pan_number=pan_number,
                shop_logo=shop_logo,
                pan_document=pan_document,
                citizenship_number=citizenship_number,
                citizenship_front=citizenship_front,
                citizenship_back=citizenship_back,
                company_registration=company_registration,
                qr_image=qr_image
            )
            random_password = ''.join(random.choices(string.ascii_letters + string.digits + "@#$%&", k=10))
            user.set_password(random_password)
            user.save()

            # Generate OTP
            otp_code = str(random.randint(100000, 999999))
            otp_obj,_=OTPVerification.objects.get_or_create(user=user)
            otp_obj.otp_code=otp_code
            otp_obj.save()
            
            # Send email
            try:
                send_mail(
                    subject="Your OTP Code - HelloBajar Vendor Verification",
                    message=f"Hello {first_name},\n\nYour OTP for vendor registration is: {otp_code}\n\nThank you for joining HelloBajar!",
                    from_email="hellobajar@gmail.com",
                    recipient_list=[email],
                    fail_silently=False
                )
                
            except Exception:
                messages.error(request, "Failed to send OTP. Please check your email address.")
                return redirect('become_vendor_page')
            
            request.session['user_email']=email
            messages.success(request, "Vendor registration submitted! Please verify OTP sent to your email.")
            return redirect('verify_otp_page')

        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('become_vendor_page')

    return render(request, 'website/pages/become_vendor.html')




def vendors(request):
    # Fetch all active and verified vendors
    vendors = Vendor.objects.filter(is_active=True, verification_status='verified').order_by('shop_name')
    search_term = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '')

    if search_term:
        vendors = vendors.filter(shop_name__icontains=search_term)
    if category_id:
        vendors = vendors.filter(products__category__id=category_id).distinct()
    paginator = Paginator(vendors, 12)  # Show 12 vendors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'vendors': page_obj,
    }
    return render(request, 'website/pages/vendors.html', context)


def vendor_details(request, slug=None):
    """Display vendor details with their products"""
    if slug:
        try:
            vendor = Vendor.objects.select_related('user').prefetch_related('products').get(slug=slug, is_active=True)
            products = vendor.products.filter(is_active=True).order_by('-created_at')[:12]
            
            context = {
                'vendor': vendor,
                'products': products,
            }
            return render(request, 'website/pages/vendor_details.html', context)
        except Vendor.DoesNotExist:
            messages.error(request, 'Vendor not found')
            return redirect('vendors')
    else:
        
        return render(request, 'website/pages/vendor_details.html')
    
    
    
from django.shortcuts import render, get_object_or_404
# ====================
#  Category details
# ======================
def category_details(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'category': category,
    
        'products': products,
        'categories': categories,
    }
    return render(request, 'website/pages/category_details.html', context)


# ================================
# Subcategoru Details
# =================================
def category_subcategory_details(request, slug):
    subcategory = get_object_or_404(SubCategory, slug=slug)
    products = Product.objects.filter(subcategory=subcategory, is_active=True)

    return render(request, 'website/pages/subcategory_details.html', {
        'subcategory': subcategory,
        'products': products
    })

    
# ==============================
#   Cart
# ==============================



def get_session_key(request):
    """Get or create a session key for guest users"""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key




def carts(request):
    # --- Get user's cart items with optimized queries ---
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(
            user=request.user
        ).select_related(
            'product',
            'product__vendor'
        ).prefetch_related(
            'variant'  # Prefetch all variants (ManyToMany)
        )
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_items = Cart.objects.filter(
            user__isnull=True, 
            session_key=session_key
        ).select_related(
            'product',
            'product__vendor'
        ).prefetch_related(
            'variant'
        )

    # --- Calculate totals ---
    total_items = sum(item.quantity for item in cart_items)
    
    # Use the model's get_total_price() which now handles multiple variants
    sub_total_price = sum(item.get_total_price() for item in cart_items)

    # --- Calculate shipping dynamically per product ---
    total_shipping = sum(
        item.product.shipping_cost * item.quantity 
        for item in cart_items
    )

    # --- Get tax rate ---
    tax_obj = TaxRate.objects.first()
    tax_rate = tax_obj.tax if tax_obj else Decimal('0.00')

    # --- Calculate tax on subtotal + shipping ---
    tax_amount = (sub_total_price + total_shipping) * (tax_rate / Decimal('100'))
    tax_amount = tax_amount.quantize(Decimal('0.01'))

    # --- Total price ---
    total_price = (sub_total_price + total_shipping + tax_amount).quantize(Decimal('0.01'))

    # --- Additional context for better UI ---
    # Add variant details to each cart item for template display
    for item in cart_items:
        # Get all variants for this cart item
        item.variant_list = list(item.variant.all())
        # Calculate item price with variants
        item.unit_price = item.get_item_price()
        item.line_total = item.get_total_price()

    context = {
        'cart_items': cart_items,
        'total_items': total_items,
        'sub_total_price': sub_total_price,
        'shipping_cost': total_shipping,
        'tax_amount': tax_amount,
        'tax_rate': tax_rate,
        'total_price': total_price,
    }

    return render(request, "website/pages/cart.html", context)




@csrf_exempt
@require_http_methods(["POST"])
def add_to_cart(request):
    """Add product to cart with multiple variants (auth + guest)"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        variant_ids = data.get('variant_ids', [])  # Now accepts array
        
        # Determine user or session
        user = request.user if request.user.is_authenticated else None
        session_key = None if user else get_session_key(request)
        
        # Validate product
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Product not found'
            }, status=404)

        # Check stock
        if product.stock < quantity:
            return JsonResponse({
                'success': False, 
                'message': f'Only {product.stock} items available'
            }, status=400)
        
        # Validate variants
        selected_variants = []
        variants_with_price = []
        
        if variant_ids:
            for variant_id in variant_ids:
                try:
                    variant = ProductVariant.objects.get(
                        id=variant_id, 
                        product=product
                    )
                    selected_variants.append(variant)
                    
                    # Track variants with price adjustments
                    if variant.price_adjustment != 0:
                        variants_with_price.append(variant)
                        
                except ProductVariant.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': f'Invalid variant selected'
                    }, status=400)
            
            # Enforce rule: Only ONE variant with price adjustment
            if len(variants_with_price) > 1:
                return JsonResponse({
                    'success': False,
                    'message': 'You can only select one variant with price adjustment'
                }, status=400)
        
        # Find existing cart items with same product
        if user:
            existing_cart_items = Cart.objects.filter(user=user, product=product)
        else:
            existing_cart_items = Cart.objects.filter(
                session_key=session_key, 
                product=product
            )
        
        # Check for exact variant match
        cart_item = None
        for item in existing_cart_items:
            item_variants = set(item.variant.all())
            if item_variants == set(selected_variants):
                cart_item = item
                break
        
        if cart_item:
            # Update existing cart item
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot add more. Only {product.stock} available'
                }, status=400)
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            # Create new cart item
            cart_item = Cart.objects.create(
                user=user,
                session_key=session_key,
                product=product,
                quantity=quantity
            )
            # Add selected variants (ManyToMany)
            if selected_variants:
                cart_item.variant.set(selected_variants)
        
        # Calculate cart count
        if user:
            cart_count = Cart.objects.filter(user=user)
        else:
            cart_count = Cart.objects.filter(session_key=session_key)
        
        total_items = sum(item.quantity for item in cart_count)
        
        # Build variant display string
        variant_names = ', '.join([v.name for v in selected_variants]) if selected_variants else ''
        product_display = f"{product.name} ({variant_names})" if variant_names else product.name

        return JsonResponse({
            'success': True,
            'message': f'{quantity} × {product_display} added to cart',
            'cart_count': total_items,
            'item_total': float(cart_item.get_total_price())
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON data'
        }, status=400)
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid quantity'
        }, status=400)
    except Exception as e:
        # Log the error for debugging
        print(f"Cart Error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Error adding to cart'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_cart_item(request):
    """Update cart item quantity (auth + guest)"""
    try:
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        quantity = int(data.get('quantity', 1))

        user = request.user if request.user.is_authenticated else None
        session_key = None if user else get_session_key(request)

        try:
            cart_item = Cart.objects.get(id=cart_item_id, user=user, session_key=session_key)
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart item not found'}, status=404)

        if quantity <= 0:
            cart_item.delete()
            action = 'removed'
        else:
            if quantity > cart_item.product.stock:
                return JsonResponse({'success': False, 'message': f'Only {cart_item.product.stock} items available'}, status=400)
            cart_item.quantity = quantity
            cart_item.save()
            action = 'updated'

        # Get updated cart totals
        cart_items = Cart.objects.filter(user=user) if user else Cart.objects.filter(session_key=session_key)
        total_items = sum(item.quantity for item in cart_items)
        total_price = sum(item.get_total_price() for item in cart_items)

        return JsonResponse({
            'success': True,
            'message': f'Cart item {action} successfully',
            'cart_count': total_items,
            'total_price': float(total_price),
            'item_total': float(cart_item.get_total_price()) if quantity > 0 else 0
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error updating cart'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def remove_from_cart(request):
    """Remove item from cart (auth + guest)"""
    try:
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')

        user = request.user if request.user.is_authenticated else None
        session_key = None if user else get_session_key(request)

        try:
            cart_item = Cart.objects.get(id=cart_item_id, user=user, session_key=session_key)
            product_name = cart_item.product.name
            cart_item.delete()
        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart item not found'}, status=404)

        # Get updated cart totals
        cart_items = Cart.objects.filter(user=user) if user else Cart.objects.filter(session_key=session_key)
        total_items = sum(item.quantity for item in cart_items)
        total_price = sum(item.get_total_price() for item in cart_items)

        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart',
            'cart_count': total_items,
            'total_price': float(total_price)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error removing from cart'}, status=500)




@login_required
def checkout(request):
    """Handle checkout process and create separate orders per vendor"""
    cart_items = Cart.objects.filter(user=request.user).select_related(
        'product', 'product__vendor'
    ).prefetch_related('variant')

    if not cart_items.exists():
        messages.error(request, "Your cart is empty. Please add items to proceed.")
        return redirect('all_collections')

    tax_obj = TaxRate.objects.first()
    tax_rate = tax_obj.tax if tax_obj else Decimal('0.00')

    coupon_code = request.session.get('coupon_code')
    coupon = None
    discount = Decimal('0.00')

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            is_valid, message = coupon.is_valid(user=request.user, cart_items=list(cart_items))
            if not is_valid:
                request.session.pop('coupon_code', None)
                coupon = None
                messages.warning(request, message)
        except Coupon.DoesNotExist:
            request.session.pop('coupon_code', None)

    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone')
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        province = request.POST.get('province')
        postal_code = request.POST.get('postal_code', '')
        payment_method = request.POST.get('payment_method')

        if not all([email, phone, full_name, address, city, province, payment_method]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'website/pages/checkout.html', {
                'cart_items': cart_items,
                'coupon': coupon,
            })

        valid_provinces = [choice[0] for choice in Order.PROVINCE_CHOICES]
        if province not in valid_provinces:
            messages.error(request, "Please select a valid province.")
            return render(request, 'website/pages/checkout.html', {'cart_items': cart_items, 'coupon': coupon})

        valid_payment_methods = [choice[0] for choice in Order.PAYMENT_CHOICES]
        if payment_method not in valid_payment_methods:
            messages.error(request, "Please select a valid payment method.")
            return render(request, 'website/pages/checkout.html', {'cart_items': cart_items, 'coupon': coupon})

        # Group cart items by vendor
        vendor_items = {}
        for item in cart_items:
            vendor = item.product.vendor
            vendor_items.setdefault(vendor, []).append(item)

        created_orders = []

        for vendor, items in vendor_items.items():
            subtotal = sum(item.get_total_price() for item in items)
            total_shipping = sum(item.product.shipping_cost * item.quantity for item in items)
            tax_amount = (subtotal + total_shipping) * (tax_rate / Decimal('100'))
            tax_amount = tax_amount.quantize(Decimal('0.01'))

            vendor_discount = Decimal('0.00')
            if coupon:
                is_valid, message = coupon.is_valid(user=request.user, cart_items=items)
                if is_valid:
                    vendor_discount = coupon.get_discount_amount(subtotal)
                else:
                    messages.warning(request, f"Coupon not valid for vendor {vendor.shop_name}.")

            total = max(subtotal + total_shipping + tax_amount - vendor_discount, Decimal('0.00'))
            total = total.quantize(Decimal('0.01'))

            # --- Calculate estimated delivery date from estimated_delivery_days ---
            product_delivery_days = [
                item.product.estimated_delivery_days for item in items if item.product.estimated_delivery_days
            ]
            if product_delivery_days:
                max_days = max(product_delivery_days)
                estimated_delivery_date = date.today() + timedelta(days=max_days)
            else:
                estimated_delivery_date = None

            # Create Order
            order = Order.objects.create(
                user=request.user,
                email=email,
                phone=phone,
                full_name=full_name,
                address=address,
                city=city,
                province=province,
                postal_code=postal_code,
                payment_method=payment_method,
                payment_status='unpaid',
                subtotal=subtotal,
                shipping_cost=total_shipping,
                tax_percentage=tax_rate,
                tax_amount=tax_amount,
                discount=vendor_discount,
                total=total,
                coupon=coupon,
                status='pending',
                estimated_delivery_date=estimated_delivery_date,  # updated
                created_at=timezone.now(),
            )
            created_orders.append(order)

            # Create Order Items with variants
            for item in items:
                order_item = OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.get_item_price(),
                )
                order_item.variant.set(item.variant.all())

            # Create Invoice
            Invoice.objects.create(
                customer=request.user,
                vendor=vendor,
                order=order,
                subtotal=subtotal,
                total=total,
                tax_percentage=tax_rate,
                tax_amount=tax_amount,
                discount=vendor_discount,
                shipping_cost=total_shipping,
            )

            # Record coupon usage
            if coupon and vendor_discount > 0:
                CouponUsage.objects.create(
                    user=request.user,
                    coupon=coupon,
                    order=order,
                    used_at=timezone.now(),
                )

        if coupon and discount > 0:
            coupon.used_count += 1
            coupon.save()

        cart_items.delete()
        request.session.pop('coupon_code', None)

        messages.success(request, f"{len(created_orders)} order(s) placed successfully!")
        return redirect('order_confirmation', order_id=created_orders[-1].id)

    # --- GET Request ---
    subtotal = sum(item.get_total_price() for item in cart_items)
    total_shipping = sum(item.product.shipping_cost * item.quantity for item in cart_items)
    tax_amount = (subtotal + total_shipping) * (tax_rate / Decimal('100'))
    tax_amount = tax_amount.quantize(Decimal('0.01'))

    if coupon:
        discount = coupon.get_discount_amount(subtotal)
    
    total = subtotal + total_shipping + tax_amount - discount
    total = total.quantize(Decimal('0.01'))

    for item in cart_items:
        item.variant_list = list(item.variant.all())
        item.unit_price = item.get_item_price()
        item.line_total = item.get_total_price()

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': total_shipping,
        'tax_rate': tax_rate,
        'tax': tax_amount,
        'discount': discount,
        'total': total,
        'coupon': coupon,
    }

    return render(request, 'website/pages/checkout.html', context)


@login_required
def apply_coupon(request):
    """Apply or remove a coupon code via AJAX"""
    coupon_code = request.POST.get('coupon_code', '').strip()
    action = request.POST.get('action', 'apply')

    if action == 'remove':
        request.session.pop('coupon_code', None)
        return JsonResponse({'success': True, 'message': 'Coupon removed successfully!'})

    try:
        coupon = Coupon.objects.get(code=coupon_code)
        cart_items = Cart.objects.filter(user=request.user).select_related('product').prefetch_related('variant')

        is_valid, message = coupon.is_valid(user=request.user, cart_items=cart_items)
        if not is_valid:
            return JsonResponse({'success': False, 'message': message}, status=400)

        request.session['coupon_code'] = coupon_code
        return JsonResponse({'success': True, 'message': f'Coupon "{coupon_code}" applied successfully!'})

    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=400)


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'website/pages/order_confirmation.html', {
        'order': order,
     
    })



def product_details(request, slug):
    try:
        product = Product.objects.select_related('vendor', 'category')\
                    .prefetch_related('images', 'variants', 'reviews')\
                    .get(slug=slug, is_active=True)

        # Increment view count
        product.views_count += 1
        product.save(update_fields=['views_count'])

        # --- Convert estimated_delivery_days to estimated delivery date ---
        estimated_delivery_str = None
        if product.estimated_delivery_days:
            estimated_delivery_date = date.today() + timedelta(days=product.estimated_delivery_days)
            estimated_delivery_str = estimated_delivery_date.strftime("%b %d")  # e.g., Nov 18

        # Get recommended products
        recommended_df = get_recommendations(product.id, top_n=30)
        recommended_products = []
        if recommended_df:  
            for row in recommended_df: 
                recommended_products.append({
                    'id': row['id'],
                    'name': row['name'],
                    'slug': row['slug'],
                    'price': row['price'],
                    'cost_price': row['cost_price'],
                    'main_image': row['main_image'] if row['main_image'] and row['main_image'].startswith('http') 
                                   else settings.MEDIA_URL + str(row['main_image']),
                })

        # Get latest 10 reviews
        reviews = product.reviews.select_related('user').order_by('-created_at')[:10]

        context = {
            'product': product,
            'related_products': recommended_products,
            'reviews': reviews,
            'banners': Banner.objects.filter(is_active=True, page="products"),
            'estimated_delivery_str': estimated_delivery_str,
        }

        return render(request, 'website/pages/product_details.html', context)

    except Product.DoesNotExist:
        messages.error(request, 'Product not found')
        return redirect('home')




def login_page(request):
    if request.method == 'POST':
        print(request.POST)
        email= request.POST.get('email')
        password = request.POST.get('password')
        try:
            user=User.objects.get(email=email,is_active=True)
            if user.check_password(password):
                auth_login(request, user)
                messages.success(request,'Login Successfull')
                
                if user.role.role =='admin':
                    return redirect('admin_dashboard')
        
                elif user.role.role == 'customer' or user.role.role == 'vendor':
                    return redirect('customer_profile')
                
            else:
                messages.error(request,'Invalid Username and Password')
                return redirect('login_page')
        except User.DoesNotExist:
            messages.error(request,'Invalid Username and Password')
            return redirect('login_page')
    
    
    return render(request,'website/pages/login.html')


def signup_page(request):
    if request.method == "POST":
        try:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email', '').strip()
         

            if User.objects.filter(email=email, is_active=True).exists():
                messages.error(request, 'User already exists')
                return redirect('signup_page')

            if User.objects.filter(email=email, is_active=False).exists():
                user = User.objects.get(email=email)
                user.first_name = first_name
                user.last_name = last_name
                user.save()
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=False
                )

            otp = str(random.randint(100000, 999999))
            otp_obj, _ = OTPVerification.objects.get_or_create(user=user)
            otp_obj.otp_code = otp
            otp_obj.save()

            try:
                send_mail(
                    subject="Your Hello Bajar OTP Verification Code",
                    message=f"Hello {first_name},\n\nYour OTP code is: {otp}",
                    from_email="hellobajar@gmail.com",
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as mail_error:
                messages.error(request, f"Error sending OTP email: {mail_error}")
                return redirect('signup_page')

            request.session['user_email'] = email
            messages.info(request, "OTP has been sent to your email.")
            return redirect('verify_otp_page')

        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")
            return redirect('signup_page')

    return render(request, 'website/pages/signup.html')




def forget_password(request):
    if request.method == "POST":
        email=request.POST.get('email', '').strip().lower()
        try:
            user=User.objects.get(email=email,is_active=True)
        except User.DoesNotExist:
            messages.error(request,'No account found with that email')
            return render(request,'website/pages/forget.html')
        otp=str(random.randint(100000,999999))
     
        otp_obj,_=OTPVerification.objects.get_or_create(
            user=user    
        )
        otp_obj.otp_code=otp
        otp_obj.save()
        send_mail(
            subject="Your Password Reset OTP",
            message=f"Your OTP for password reset is {otp} .",
            from_email="hellobajar@gmail.com",
            recipient_list=[email],
            fail_silently=False
            
        )
        request.session['user_email']=email
        messages.success(request,'OTP sent to your email')
        return redirect('verify_otp_page')
    return render(request,'website/pages/forget.html')


def set_password_view(request):

    if request.method  == "POST":
        new_password=request.POST.get('new_password')
        try:
            user=User.objects.get(email=request.user.email,is_active=True)
            user.set_password(new_password)
            user.save()
            messages.success(request,'Password changed successfully. Please Login')
            return redirect('login_page')
        except User.DoesNotExist:
            messages.error(request,'User not found')
            return redirect('forget_password')
    return render(request,'website/pages/set_password.html')



def verify_otp_page(request):
    email = request.session.get('user_email')
    try:
        user = User.objects.get(email=email)
        otp_obj = OTPVerification.objects.get(user=user)
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        messages.error(request, "Invalid request.")
        return redirect('login_page')

    if request.method == "POST":
        entered_otp = request.POST.get('otp', '').strip()

        if entered_otp == otp_obj.otp_code:
            if not user.is_active:
                user.is_active = True
                user.save()
                if Vendor.objects.filter(user=user).exists():
                    UserRole.objects.get_or_create(role="vendor",user=user)
                else:
                    UserRole.objects.get_or_create(role="customer",user=user)
                    
               
                UserProfile.objects.get_or_create(user=user)
                otp_obj.delete()
                del request.session['user_email']
                auth_login(request, user)
                messages.success(request, "Your account has been verified successfully!")
                return redirect('set_password')
            elif user.is_active:
                otp_obj.delete()
                del request.session['user_email']
                auth_login(request, user)
                messages.success(request, "Otp verified successfully! Please Reset New Password")
                return redirect('set_password')
                
            
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'website/pages/otp.html', {'email': email})


def logout_view(request):
    auth_logout(request)
    messages.success(request,'Logout Successfull')
    return redirect('login_page')



def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        Contact.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message_text
            )
        messages.success(request, "Your message has been sent successfully!")
        return redirect('contact')
       

    return render(request, 'website/pages/contact.html')

    


# =============================
#  Customer Dashboard
# =============================

@login_required
def customer_profile(request):
    if request.user.is_authenticated:
        if request.user.role.role == 'admin':
            return redirect('admin_dashboard')
    return render(request,'website/pages/profile.html')


@login_required
def edit_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()

        profile.phone = request.POST.get('phone', '').strip()
        profile.address = request.POST.get('address', '').strip()
        profile.city = request.POST.get('city', '').strip()
        profile.province = request.POST.get('province', '').strip()

        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']

        user.save()
        profile.save()

        return redirect('customer_profile') 

    return render(request, 'website/pages/edit_profile.html', {
        'profile': profile,
    })
    
    

@login_required
def customer_orders(request):
        user=request.user
        orders_list = Order.objects.filter(user=user).order_by('-created_at')
        total_orders=orders_list.count()
        
       
        paginator = Paginator(orders_list, 10) 
        
        page_number = request.GET.get('page')
        orders = paginator.get_page(page_number)
        
        return render(request, 'website/pages/orders.html', {
            'orders': orders,
            'total_orders':total_orders,
            
        })


@login_required
def customer_order_detail(request, order_number):

    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    coupon_used = order.coupon if order.coupon else None

    return render(request, 'website/pages/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'coupon_used': coupon_used,
       
    })


# =====================
#  Invoice
# ====================

@login_required
def customer_invoices(request):
    invoice_list=Invoice.objects.filter(customer=request.user).order_by('-created_at')
    paginator=Paginator(invoice_list,10)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    return render(request,'website/pages/invoices.html',{'page_obj':page_obj})


@login_required
def customer_invoice_detail(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number, customer=request.user)
    return render(request, 'website/pages/invoice_detail.html', {'invoice': invoice})


@login_required
def write_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order_id = request.GET.get('order')
    order = Order.objects.filter(id=order_id).first()  # Safe get

    existing_review = Review.objects.filter(product=product, user=request.user).first()

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Please select a valid rating between 1 and 5 stars.")
            return render(request, 'website/pages/write_review.html', {
                'product': product, 'comment': comment, 'rating': rating
            })

        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            messages.success(request, "Your review has been updated!")
        else:
            Review.objects.create(product=product, user=request.user, rating=rating, comment=comment)
            messages.success(request, "Thank you for your review!")

        # Redirect to order or product page
        return redirect('customer_order_detail', order_number=order.order_number) if order else redirect('product_detail', product_id=product.id)

    # GET request - show form
    existing_reviews = Review.objects.filter(product=product).exclude(user=request.user).order_by('-created_at')[:5]

    return render(request, 'website/pages/write_review.html', {
        'product': product,
        'order_number': order.order_number if order else None,
        'existing_review': existing_review,
        'existing_reviews': existing_reviews,
        'comment': existing_review.comment if existing_review else '',
        'rating': existing_review.rating if existing_review else None,
    })
