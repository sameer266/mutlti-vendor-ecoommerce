
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from dashboard.models import (
    UserRole,
    UserProfile,
    Slider,
    Banner,
    Category,
    Product,Cart,Vendor,ProductVariant,OTPVerification,Order,OrderItem,Coupon,CouponUsage,Contact,ShippingCost,Invoice
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
    # Calculate the date 29 days ago
    one_month_ago = timezone.now() - timedelta(days=29)
    new_arrivals = Product.objects.filter(
        is_active=True,
        created_at__gte=one_month_ago
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
        cart_items = Cart.objects.filter(user=request.user).select_related('product', 'variant')
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_items = Cart.objects.filter(user__isnull=True, session_key=session_key).select_related('product', 'variant')

    total_items = sum(item.quantity for item in cart_items)
    sub_total_price = sum(item.get_total_price() for item in cart_items)

    shipping = ShippingCost.objects.first()
    shipping_cost = shipping.cost if shipping else Decimal('0.00')
    tax_rate = shipping.tax if shipping else Decimal('0.00')

    tax_amount = (sub_total_price * tax_rate / Decimal('100')).quantize(Decimal('0.01'))
    total_price = (sub_total_price + tax_amount + shipping_cost).quantize(Decimal('0.01'))

    context = {
        'cart_items': cart_items,
        'total_items': total_items,
        'sub_total_price': sub_total_price,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'tax_rate': tax_rate,
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



@login_required
def checkout(request):
    """Handle checkout process for authenticated users"""
    cart_items = Cart.objects.filter(user=request.user).select_related('product', 'variant')

    if not cart_items:
        messages.error(request, "Your cart is empty. Please add items to proceed.")
        return redirect('all_collections')

    # --- Shipping and Base Totals ---
    shipping = ShippingCost.objects.first()
    subtotal = sum(item.get_total_price() for item in cart_items)
    discount = Decimal('0.00')
    shipping_cost = shipping.cost if shipping else Decimal('0.00')
    tax_rate = shipping.tax if shipping else Decimal('0.00')

    # 🔹 Convert tax percentage to actual amount
    tax_amount = (subtotal * tax_rate) / Decimal('100')

    coupon = None
    coupon_code = request.session.get('coupon_code')

    # --- Handle Coupon ---
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

    # --- Calculate Final Total ---
    total = max(subtotal + shipping_cost + tax_amount - discount, Decimal('0.00'))

    # --- Handle Form Submission ---
    if request.method == "POST":
        try:
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            full_name = request.POST.get('full_name')
            address = request.POST.get('address')
            city = request.POST.get('city')
            province = request.POST.get('province')
            postal_code = request.POST.get('postal_code', '')
            payment_method = request.POST.get('payment_method')

            # Validate required fields
            if not all([email, phone, full_name, address, city, province, payment_method]):
                messages.error(request, "Please fill in all required fields.")
                return render(request, 'website/pages/checkout.html', {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'shipping_cost': shipping_cost,
                    'tax': tax_amount,
                    'tax_rate': tax_rate,
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
                    'tax': tax_amount,
                    'tax_rate': tax_rate,
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
                    'tax': tax_amount,
                    'tax_rate': tax_rate,
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
                    total = subtotal + shipping_cost + tax_amount

            # --- Create Order ---
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
        
                payment_method=payment_method,
                payment_status='unpaid' ,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax=tax_amount, 
                discount=discount,
                total=total,
                coupon=coupon,
                status='pending',
                created_at=timezone.now(),
            )

            # --- Create Order Items and Invoice ---
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=item.get_item_price(),
                )
                
                Invoice.objects.create(customer=request.user,
                                       vendor=item.product.vendor,
                                       order=order,
                                       subtotal=subtotal,
                                       total=total,
                                       tax_amount=tax_amount,
                                       discount=discount
                                       )

                
                

            # --- Record Coupon Usage ---
            if coupon:
                CouponUsage.objects.create(
                    user=request.user,
                    coupon=coupon,
                    order=order,
                    used_at=timezone.now(),
                )
                coupon.used_count += 1
                coupon.save()
            
        

            # --- Handle Payment Method ---
            if payment_method == 'cod':
                cart_items.delete()
                request.session.pop('coupon_code', None)
                messages.success(request, f"Order {order.order_number} placed successfully! You will pay on delivery.")
                return redirect('order_confirmation', order_id=order.id)
            else:
                messages.info(request, f"Payment via {payment_method} is not yet implemented. Please use COD.")
                return render(request, 'website/pages/checkout.html', {
                    'cart_items': cart_items,
                    'subtotal': subtotal,
                    'shipping_cost': shipping_cost,
                    'tax': tax_amount,
                    'tax_rate': tax_rate,
                    'discount': discount,
                    'total': total,
                    'coupon': coupon,
                })

           

        except Exception as e:
            messages.error(request, f"Error processing order: {str(e)}")

    # --- Render Checkout Page ---
    return render(request, 'website/pages/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax_amount,
        'tax_rate': tax_rate,
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
        return JsonResponse({'success': True, 'message': f'Coupon "{coupon_code}" applied successfully!'})

    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=400)


@login_required
def order_confirmation(request, order_id):
    order = Order.objects.get(id=order_id,user=request.user)
    shipping_cost=ShippingCost.objects.first()
    cost=shipping_cost.cost
    tax=shipping_cost.tax
    tax_amount = order.subtotal * Decimal(tax) / Decimal('100')
    total_price = order.subtotal + cost + tax_amount
    return render(request, 'website/pages/order_confirmation.html', {'order': order, 'tax_amount': tax_amount, 'total_price': total_price,'tax_rate':tax,'shipping_cost':cost})



def product_details(request, slug):
    """Display detailed product information"""
    try:
        product = Product.objects.select_related('vendor', 'category')\
                    .prefetch_related('images', 'variants', 'reviews')\
                    .get(slug=slug, is_active=True)

        # Increment view count
        product.views_count += 1
        product.save(update_fields=['views_count'])

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
        
                    # Build full image URL
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
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('signup_page')
        
        if User.objects.filter(email=email,is_active=True).exists():
            messages.error(request,'User already exists')
            return redirect('signup_page')

        if User.objects.filter(email=email,is_active=False).exists():
            user=User.objects.get(email=email)
            user.first_name=first_name
            user.last_name=last_name
            user.save()
        else:            
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                is_active=False  
            )

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            otp_obj,_=OTPVerification.objects.get_or_create(
                user=user,
    
            )
            otp_obj.otp_code=otp
            otp_obj.save()
            send_mail(
                subject="Your Hello Bajar OTP Verification Code",
                message=f"Hello {first_name},\n\nYour OTP code is: {otp}",
                from_email="hellobajar@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )

            # Redirect to OTP page
            request.session['user_email'] = email
            messages.info(request, "OTP has been sent to your email.")
            return redirect('verify_otp_page')

    return render(request, 'website/pages/signup.html')



def forget_password(request):
    if request.method == "POST":
        email=request.POST.get('email')
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
                UserRole.objects.create(role="customer",user=user)
                UserProfile.objects.create(user=user)
                otp_obj.delete()
                del request.session['user_email']
                auth_login(request, user)
                messages.success(request, "Your account has been verified successfully!")
                return redirect('login_page')
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
        email = request.POST.get('email')
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
    shipping_cost_obj = ShippingCost.objects.first()
    shipping_cost = shipping_cost_obj.cost if shipping_cost_obj else Decimal('0.00')
    tax_rate = shipping_cost_obj.tax if shipping_cost_obj else Decimal('0.00')

    tax_amount = order.subtotal * Decimal(tax_rate) / Decimal('100')
    total_price = order.subtotal + shipping_cost + tax_amount - (order.discount or Decimal('0.00'))

    coupon_used=order.coupon if order.coupon else None

    order_items = OrderItem.objects.filter(order=order)

    return render(request, 'website/pages/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'tax_amount': tax_amount,
        'total_price': total_price,
        'tax_rate': tax_rate,
        'coupon_used': coupon_used,
        'discount_amount': order.discount,
        'shipping_cost': shipping_cost,
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
    shipping=ShippingCost.objects.first()
    shipping_cost=shipping.cost
    tax_rate=shipping.tax
    return render(request, 'website/pages/invoice_detail.html', {'invoice': invoice,'tax_rate':tax_rate,'shipping_cost':shipping_cost})