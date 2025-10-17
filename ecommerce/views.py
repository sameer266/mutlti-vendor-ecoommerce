
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from dashboard.models import (
    UserRole,
    UserProfile,
    Slider,
    Banner,
    Category,
    Product,Cart,Vendor,ProductVariant,OTPVerification,Order,Wishlist,OrderItem,Coupon,CouponUsage
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

def home_page(request):
    sliders = Slider.objects.filter(is_active=True).order_by('-created_at')[:5]
    banners = Banner.objects.filter(is_active=True, page="home")
    categories = Category.objects.filter(is_active=True, is_featured=True).order_by('order')[:12]
    
    # Featured Products Pagination
    featured_products = Product.objects.filter(is_active=True, is_featured=True).order_by('-created_at')
    featured_paginator = Paginator(featured_products, 12)  # 12 items per page
    featured_page_number = request.GET.get('featured_page', 1)
    featured_products_page = featured_paginator.get_page(featured_page_number)
    
    # Best Offers Pagination
    best_offers = Product.objects.filter(is_active=True).order_by('-views_count', '-created_at')
    best_offers_paginator = Paginator(best_offers, 12)  # 12 items per page
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
        # Search products by name, description, or category name
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct().order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 24)  # 12 products per page
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
    # Calculate the date 7 days ago
    one_week_ago = timezone.now() - timedelta(days=7)
    new_arrivals = Product.objects.filter(
        is_active=True,
        created_at__gte=one_week_ago
    ).order_by('-created_at')
    
    paginator = Paginator(new_arrivals, 12)  # 12 products per page
    page_number = request.GET.get('page', 1)
    new_arrivals_page = paginator.get_page(page_number)

    context = {
        'new_arrivals': new_arrivals_page,
    }
    return render(request, 'website/pages/new_arrivals.html', context)

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
    
# ==============================
#   Cart
# ==============================



def get_session_key(request):
    """Get or create a session key for guest users"""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key




def carts(request):
    """Display cart page with user's cart items"""
    if request.user.is_authenticated:
        # Show cart items for logged-in user
        cart_items = Cart.objects.filter(user=request.user).select_related('product', 'variant')
    else:
        # Use session key for guest users
        session_key = request.session.session_key
        if not session_key:
            # Create a session if it doesn't exist
            request.session.create()
            session_key = request.session.session_key
        cart_items = Cart.objects.filter(user__isnull=True, session_key=session_key).select_related('product', 'variant')

    total_items = sum(item.quantity for item in cart_items)
    total_price = sum(item.get_total_price() for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_items': total_items,
        'total_price': total_price,
    }
    
    return render(request, "website/pages/cart.html", context)



@csrf_exempt
@require_http_methods(["POST"])
def add_to_cart(request):
    """Add product to cart (auth + guest)"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        variant_id = data.get('variant_id')
        user = request.user if request.user.is_authenticated else None
        session_key = None if user else get_session_key(request)
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)

        if product.stock < quantity:
            return JsonResponse({'success': False, 'message': f'Only {product.stock} items available'}, status=400)
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Product variant not found'}, status=404)
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            session_key=session_key,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )
        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return JsonResponse({'success': False, 'message': f'Cannot add more. Only {product.stock} available'}, status=400)
            cart_item.quantity = new_quantity
            cart_item.save()

        cart_count = Cart.objects.filter(user=user) if user else Cart.objects.filter(session_key=session_key)
        total_items = sum(item.quantity for item in cart_count)

        return JsonResponse({
            'success': True,
            'message': f'{quantity} × {product.name} added to cart',
            'cart_count': total_items,
            'item_total': cart_item.get_total_price()
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error adding to cart'}, status=500)


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


from decimal import Decimal


@login_required
def checkout(request):
    """Handle checkout process for authenticated users"""
    cart_items = Cart.objects.filter(user=request.user).select_related('product', 'variant')
    
    if not cart_items:
        messages.error(request, "Your cart is empty. Please add items to proceed.")
        return redirect('all_collections')

    # Calculate totals
    subtotal = sum(item.get_total_price() for item in cart_items)
    shipping_cost = Decimal('0.00')  # Hardcoded as free
    tax = Decimal('0.00')  # Hardcoded as per template
    discount = Decimal('0.00')
    coupon = None
    coupon_code = request.session.get('coupon_code')

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            is_valid, message = coupon.is_valid(user=request.user, cart_items=cart_items)
            if is_valid:
                discount = coupon.get_discount_amount(subtotal)
            else:
                messages.error(request, message)
                request.session.pop('coupon_code', None)
                coupon = None
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or expired coupon code.")
            request.session.pop('coupon_code', None)

    total = max(subtotal + shipping_cost + tax - discount, Decimal('0.00'))

    if request.method == "POST":
        try:
            # Extract form data
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            full_name = request.POST.get('full_name')
            address = request.POST.get('address')
            city = request.POST.get('city')
            province = request.POST.get('province')
            postal_code = request.POST.get('postal_code', '')
            notes = request.POST.get('notes', '')
            payment_method = request.POST.get('payment_method')

            # Validate required fields
            if not all([email, phone, full_name, address, city, province, payment_method]):
                messages.error(request, "Please fill in all required fields.")
                return render(request, 'website/pages/checkout.html', {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'shipping_cost': shipping_cost,
                    'tax': tax,
                    'discount': discount,
                    'total': total,
                    'coupon': coupon,
                })

            # Validate province
            valid_provinces = [choice[0] for choice in Order.PROVINCE_CHOICES]
            if province not in valid_provinces:
                messages.error(request, "Please select a valid province.")
                return render(request, 'website/pages/checkout.html', {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'shipping_cost': shipping_cost,
                    'tax': tax,
                    'discount': discount,
                    'total': total,
                    'coupon': coupon,
                })

            # Validate payment method
            valid_payment_methods = [choice[0] for choice in Order.PAYMENT_CHOICES]
            if payment_method not in valid_payment_methods:
                messages.error(request, "Please select a valid payment method.")
                return render(request, 'website/pages/checkout.html', {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'shipping_cost': shipping_cost,
                    'tax': tax,
                    'discount': discount,
                    'total': total,
                    'coupon': coupon,
                })

            # Re-validate coupon if present
            if coupon:
                is_valid, message = coupon.is_valid(user=request.user, cart_items=cart_items)
                if not is_valid:
                    messages.error(request, message)
                    request.session.pop('coupon_code', None)
                    coupon = None
                    discount = Decimal('0.00')
                    total = subtotal + shipping_cost + tax

            # Create or update UserProfile
            user_profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'phone': phone,
                    'address': address,
                    'city': city,
                    'province': province,
                    'postal_code': postal_code,
                }
            )
            if not created:
                user_profile.phone = phone
                user_profile.address = address
                user_profile.city = city
                user_profile.province = province
                user_profile.postal_code = postal_code
                user_profile.save()

            # Create Order
            order = Order.objects.create(
                user=request.user,
                order_number='',  # Auto-generated in save()
                email=email,
                phone=phone,
                full_name=full_name,
                address=address,
                city=city,
                province=province,
                postal_code=postal_code,
                notes=notes,
                payment_method=payment_method,
                payment_status='unpaid' if payment_method != 'cod' else 'paid',
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax=tax,
                discount=discount,
                total=total,
                coupon=coupon,
                status='pending',
                created_at=timezone.now(),
            )

            # Create OrderItems
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    vendor=item.product.vendor,
                    product=item.product,
                    variant=item.variant,
                    product_name=item.product.name,
                    product_image=item.product.main_image,
                    variant_name=item.variant.name if item.variant else '',
                    quantity=item.quantity,
                    price=item.get_item_price(),
                    fulfillment_status='pending',
                )

            # Record CouponUsage if coupon is applied
            if coupon:
                CouponUsage.objects.create(
                    user=request.user,
                    coupon=coupon,
                    order=order,
                    used_at=timezone.now(),
                )
                coupon.used_count += 1
                coupon.save()

            # Handle payment method
            if payment_method == 'cod':
                # Clear cart and session
                cart_items.delete()
                request.session.pop('coupon_code', None)
                messages.success(request, f"Order {order.order_number} placed successfully! You will pay on delivery.")
                return redirect('order_confirmation', order_id=order.id)
            else:
                # Placeholder for online payment gateway integration
                messages.info(request, f"Payment via {payment_method} is not yet implemented. Please use COD.")
                return render(request, 'website/pages/checkout.html', {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'shipping_cost': shipping_cost,
                    'tax': tax,
                    'discount': discount,
                    'total': total,
                    'coupon': coupon,
                })

        except Exception as e:
            messages.error(request, f"Error processing order: {str(e)}")
            return render(request, 'website/pages/checkout.html', {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'shipping_cost': shipping_cost,
                'tax': tax,
                'discount': discount,
                'total': total,
                'coupon': coupon,
            })

    # GET request: Render checkout page
    return render(request, 'website/pages/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax,
        'discount': discount,
        'total': total,
        'coupon': coupon,
    })
    




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
        cart_items = Cart.objects.filter(user=request.user).select_related('product', 'variant')
        
        is_valid, message = coupon.is_valid(user=request.user, cart_items=cart_items)
        if not is_valid:
            return JsonResponse({'success': False, 'message': message}, status=400)

        request.session['coupon_code'] = coupon_code
        return JsonResponse({'success': True, 'message': f'Coupon {coupon_code} applied successfully!'})
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=400)
    

@login_required
def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id,user=request.user)
    return render(request, 'website/pages/order_confirmation.html', {'order': order})


    
def product_details(request, slug):
    """Display detailed product information"""
    try:
        product = Product.objects.select_related('vendor', 'category').prefetch_related('images', 'variants', 'reviews').get(slug=slug, is_active=True)
        
        # Get related products from same vendor
        related_products = Product.objects.filter(
            vendor=product.vendor, 
            is_active=True
        ).exclude(id=product.id)[:8]
        
        # Get reviews for this product
        reviews = product.reviews.select_related('user').order_by('-created_at')[:10]
        
        # Increment view count
        product.views_count += 1
        product.save(update_fields=['views_count'])

        context = {
            'product': product,
            'related_products': related_products,
            'reviews': reviews,
            "banners":Banner.objects.filter(is_active=True,page="products")
        }
        return render(request, 'website/pages/product_details.html', context)
        
    except Product.DoesNotExist:
        messages.error(request, 'Product not found')
        return redirect('home')
    


# -------------------------
# User Authentication
# -------------------------
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Create user role (default: customer)
        UserRole.objects.create(user=user, role='customer')
        
        # Create user profile
        UserProfile.objects.create(user=user, phone=phone)
        
        # Auto login
        auth_login(request, user)
        return redirect('home')
    
    return render(request, 'register.html')


def login_page(request):
    if request.method == 'POST':
        print(request.POST)
        email= request.POST.get('email')
        password = request.POST.get('password')
        try:
            user=User.objects.get(email=email)
            user.check_password(password)
            if user.role.role =='admin':
                auth_login(request, user)
                return redirect('admin_dashboard')
            elif user.role.role == 'vendor':
                auth_login(request, user)
                
                pass
            elif user.role.role == 'customer':
                auth_login(request, user)
                
                return redirect('customer_profile')
        except User.DoesNotExist:
            messages.error(request,'Invalid Username and Password')
            return redirect('login_page')
    
    return render(request,'website/pages/login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login_page')
    
    
from django.core.mail import send_mail
import random

def signup_page(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if password1 != password2:
            messages.error(request, "Passwords do not match.")

        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password1,
                first_name=full_name,
                is_active=False  # temporarily deactivate until OTP verified
            )

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            expiry_time = timezone.now() + timezone.timedelta(minutes=5)

            OTPVerification.objects.create(
                user=user,
                otp_code=otp,
                expires_at=expiry_time
            )

            # Send OTP email
            send_mail(
                subject="Your Hello Bajar OTP Verification Code",
                message=f"Hello {full_name},\n\nYour OTP code is: {otp}\nIt expires in 5 minutes.",
                from_email="hellobajar.com.np",
                recipient_list=[email],
                fail_silently=False,
            )

            # Redirect to OTP page
            request.session['user_email'] = email
            messages.info(request, "OTP has been sent to your email.")
            return redirect('verify_otp_page')

    return render(request, 'website/pages/signup.html')


def verify_otp_page(request):
    email = request.session.get('user_email')

    try:
        user = User.objects.get(email=email)
        otp_obj = OTPVerification.objects.get(user=user)
    except (User.DoesNotExist, OTPVerification.DoesNotExist):
        messages.error(request, "Invalid request.")
        return redirect('signup_page')

    if request.method == "POST":
        entered_otp = request.POST.get('otp', '').strip()

        if otp_obj.is_expired():
            otp_obj.delete()
            messages.error(request, "OTP expired. Please sign up again.")
            return redirect('signup_page')

        if entered_otp == otp_obj.otp_code:
            user.is_active = True
            user.save()
            UserRole.objects.create(role="customer",user=user)
            otp_obj.delete()
            auth_login(request, user)
            messages.success(request, "Your account has been verified successfully!")
            return redirect('login_page')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'website/pages/otp.html', {'email': email})


# =============================
#  Customer Dashboard
# =============================
from django.contrib.auth.decorators import login_required


@login_required
def customer_profile(request):
    return render(request,'website/pages/profile.html')


@login_required
def edit_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Basic user info
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()

        # Profile info
        profile.phone = request.POST.get('phone', '').strip()
        profile.address = request.POST.get('address', '').strip()
        profile.city = request.POST.get('city', '').strip()
        profile.province = request.POST.get('province', '').strip()

        # Avatar upload
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']

        # Save changes
        user.save()
        profile.save()

        return redirect('customer_profile') 

    return render(request, 'website/pages/edit_profile.html', {
        'profile': profile,
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'website/pages/orders.html', {
        'orders': orders
    })



@login_required
def my_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product').order_by('-added_at')
    return render(request, 'website/pages/wishlist.html', {
        'wishlist_items': wishlist_items
    })


@login_required
def remove_wishlist_item(request, item_id):
    try:
        item = Wishlist.objects.get(id=item_id, user=request.user)
        item.delete()
    except Wishlist.DoesNotExist:
        pass
    return redirect('customer_wishlist')