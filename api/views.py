# ========================================
#     Mobile App API Views
# ========================================
from django.shortcuts import get_object_or_404
from dashboard.models import UserProfile,UserRole,Vendor,OTPVerification,Slider, Product,ProductVariant,ProductImage,Category,Cart, Order,UserProfile, OrderItem
from django.contrib.auth.models import User


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
import random
from django.core.mail import send_mail
from django.db.models import F



# ========= Utility Function to Clean HTML Text ==========
import re
from django.utils.html import strip_tags


def clean_ckeditor_text(html_text):
    """
    Clean CKEditor content and return readable plain text.
    Splits common product info fields onto separate lines.
    """
    if not html_text:
        return ""

    # Remove HTML tags
    text = strip_tags(html_text)

    # Replace <br> and tabs with newline
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = text.replace('\t', ' ')

    # Normalize spaces
    text = re.sub(r' +', ' ', text)

    # Split on common product info keywords and add newline
    # This works well if CKEditor saves everything in one paragraph
    keywords = ['Brand:', 'Manufacturer:', 'Country of Origin:', 'Sold by:', 'Volume:']
    for kw in keywords:
        text = text.replace(kw, f'\n{kw}')

    # Remove extra newlines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join([line for line in lines if line])

    return text


# ========= Login =============
class LoginApiView(APIView):
    def post(self,request):
        try:
            email=request.data.get('email')
            password=request.data.get('password')
            try:
                user=User.objects.get(email=email,is_active=True)
                print(user)
            except User.DoesNotExist:
                return Response({'success':False,'error':'User not found'},status=400)
            if not user.check_password(password):
                return Response({'success':False,'error':'Incorrect password'},status=400)
            refresh=RefreshToken.for_user(user)
            return Response({
                'success':True,
                'refresh':str(refresh),
                'access':str(refresh.access_token),
                'user':{
                    'first_name':user.first_name,
                    'last_name':user.last_name,
                    'email':user.email,
                    'phone':user.profile.phone,
                    'gender':user.profile.gender,
                    'avatar':user.profile.avatar.url if user.profile.avatar else None,
                    'address':user.profile.address,
                    'city':user.profile.city  
                }})
            
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)


import logging
from django.utils import timezone
logger = logging.getLogger(__name__)

# ============= Logout =============
class LogoutView(APIView):
    def post(self,request):
        try:
            refresh_token=request.data.get('refresh')
            if not refresh_token:
                return Response({'success':False,'error':str(e)})
            token=RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User {request.user} logged out successfully.")
            return Response({'success':True,'message':'Logout successful'},status=200)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({'success':False,'error':str(e)},status=400)


# ============ Register =============
class RegisterApiView(APIView):
    def post(self,request):
        try:
            first_name=request.data.get('first_name')
            last_name=request.data.get('last_name')
            email=request.data.get('email')
            password=request.data.get('password')
            if User.objects.filter(email=email,is_active=True).exists():
                return Response({'success':False,'error':"User already found"},status=400)
            
            user=User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=False
            )
            otp=str(random.randint(100000,999999))
            otp_obj,_=OTPVerification.objects.get_or_create(user=user)
            otp_obj.otp_code=otp
            otp_obj.save()
            send_mail(
                subject="Your Hello Bajar OTP Verification Code",
                message=f"Hello {first_name},\n\nYour OTP code is: {otp}.",
                from_email="hellobajar@gmail.com",
                recipient_list=[email],
                fail_silently=False
            )
            return Response({'success':True,'message':'User registered successfully. Please verify OTP sent to your email.'},status=201)    
        except Exception as e:
            return Response({'success':False,'error':str(e)})


# =========== Resend Otp ===========
class  ResendOtpApiView(APIView):
    def post(self,request):
        try:
            email=request.data.get('email')
            try:
                user=User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'success':False,'error':'User not found'},status=400)

            otp=str(random.randint(100000,999999))
            otp_obj,_=OTPVerification.objects.get_or_create(user=user)
            otp_obj.otp_code=otp
            otp_obj.save()
            
            send_mail(
                subject="Your Hello Bajar OTP Verification Code",
                message=f"Hello {user.first_name},\n\nYour OTP code is: {otp}.",
                from_email="hellobajar@gmail.com",
                recipient_list=[email],
                fail_silently=False
            )
            return Response({'success':True,'message':'Otp resend successfully'},status=200)
            
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        

# ============ Register =============
class RegisterApiView(APIView):
    def post(self, request):
        try:
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            email = request.data.get('email')
            password = request.data.get('password')

            # Check if active user already exists
            if User.objects.filter(email=email, is_active=True).exists():
                return Response({'success': False, 'error': "User already exists"}, status=400)

            if User.objects.filter(email=email,is_active=False).exists():
                user=User.objects.get(email=email)
                user.first_name=first_name
                user.last_name=last_name
                user.save()
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=False
                )

            # Generate OTP and save
            otp = str(random.randint(100000, 999999))
            otp_obj, _ = OTPVerification.objects.get_or_create(user=user)
            otp_obj.otp_code = otp
            otp_obj.save()

            # Send OTP via email
            send_mail(
                subject="Your Hello Bajar OTP Verification Code",
                message=f"Hello {first_name},\n\nYour OTP code is: {otp}.",
                from_email="hellobajar@gmail.com",
                recipient_list=[email],
                fail_silently=False
            )

            return Response({'success': True, 'message': 'User registered successfully. Please verify OTP sent to your email.'}, status=201)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)


# =========== Verify OTP =============
class VerifyOtpApiView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            otp_code = request.data.get('otp_code')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'success': False, 'error': 'User not found'}, status=400)

            if user.is_active:
                return Response({'success': False, 'error': 'User is already exists'}, status=400)

            try:
                otp_obj = OTPVerification.objects.get(user=user)
            except OTPVerification.DoesNotExist:
                return Response({'success': False, 'error': 'OTP not found. Please request a new one.'}, status=400)
            if otp_obj.otp_code != otp_code:
                return Response({'success': False, 'error': 'Invalid OTP code'}, status=400)

            user.is_active = True
            user.save()
            UserProfile.objects.create(user=user)
            UserRole.objects.create(user=user, role='customer')
            otp_obj.delete()

            return Response({'success': True, 'message': 'OTP verified successfully. Your account is now active.'}, status=200)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)


# ========== Forget Password Verify OTP =============
class ForgetPasswordVerifyOtpApiView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            otp_code = request.data.get('otp_code')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'success': False, 'error': 'User not found'}, status=400)

            try:
                otp_obj = OTPVerification.objects.get(user=user)
            except OTPVerification.DoesNotExist:
                return Response({'success': False, 'error': 'OTP not found. Please request a new one.'}, status=400)
            if otp_obj.otp_code != otp_code:
                return Response({'success': False, 'error': 'Invalid OTP code'}, status=400)
            
            access_token = str(RefreshToken.for_user(user).access_token)
            return Response({'success': True,'access':access_token, 'message': 'OTP verified successfully. You can now reset your password.'}, status=200)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)
        



# ========== Reset Password ==============
class ResetPasswordApiView(APIView):
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        try:
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            try:
                user = User.objects.get(email=request.user.email)
            except User.DoesNotExist:
                return Response({'success': False, 'error': 'User not found'}, status=400)

            if new_password != confirm_password:
                return Response({'success': False, 'error': 'Passwords do not match'}, status=400)

            user.set_password(new_password)
            user.save()

            return Response({'success': True, 'message': 'Password reset successfully'}, status=200)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)
    
        
# ========== Forget Password =============
class ForgetPasswordApiView(APIView):
    def post(self,request):
        try:
            email=request.data.get('email')
            try:
                user=User.objects.get(email=email,is_active=True)
            except User.DoesNotExist:
                return Response({'success':False,'error':'No account found with that email'},status=400)
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
            return Response({'success':True,'message':'OTP sent to your email for password reset.'},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)





# ====== Home API View ======
class HomeApiView(APIView):

    def get(self,request):
        try:
            categorys=Category.objects.filter(is_active=True,is_featured=True)[:10]
            featured_products=Product.objects.filter(is_active=True,is_featured=True).order_by('-created_at')[:20]
            best_offers = Product.objects.filter(
                is_active=True,
                price__lt=F('cost_price') * 0.75  # Price less than 75% of cost price = >25% discount
            ).order_by('-created_at')[:20]
            sliders=Slider.objects.filter(is_active=True).order_by('-created_at')
            category_data=[]
            featured_product_data=[]
            best_offers_product_data=[]
            slider_data=[]
            for slider in sliders:
                slider_data.append({
                    'id':slider.id,
                    'image':slider.image.url,
                })
            for category in categorys:
                category_data.append({
                    'id':category.id,
                    'name':category.name,
                    'image':category.image.url,
                })
            for product in featured_products:
                featured_product_data.append({
                    'id':product.id,
                    'name':product.name,
                    'price':product.price,
                    'cost_price':product.cost_price,
                    'in_stock':product.in_stock,
                    'category':product.category.name,
                    'main_image':product.main_image.url,
                })
            
            for product in best_offers:
                best_offers_product_data.append({
                    'id':product.id,
                    'name':product.name,
                    'price':product.price,
                    'cost_price':product.cost_price,
                    'in_stock':product.in_stock,
                    'category':product.category.name,
                    'main_image':product.main_image.url,
                })
            return Response({'success':True,'sliders':slider_data,'categories':category_data,'featured_products':featured_product_data,'best_offers_products':best_offers_product_data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)



# =============== All Collections ==============
class AllCollectionsApiView(APIView):
    def get(self,request):
        products=Product.objects.filter(is_active=True).order_by('-created_at')
        product_data=[]
        for product in products:
            product_data.append({
                'id':product.id,
                'name':product.name,
                'price':product.price,
                'cost_price':product.cost_price,
                'in_stock':product.in_stock,
                'category':product.category.name,
                'main_image':product.main_image.url,
            })
        return Response({'success':True,'products':product_data},status=200)
    



# ============= New Arrivals =============
class NewArrivalsApiView(APIView):
    def get(self,request):
        one_month_ago=timezone.now()-timezone.timedelta(days=29)
        new_arrivals=Product.objects.filter(is_active=True,created_at__gte=one_month_ago).order_by('-created_at')
        product_data=[]
        for product in new_arrivals:
            product_data.append({
                'id':product.id,
                'name':product.name,
                'price':product.price,
                'cost_price':product.cost_price,
                'in_stock':product.in_stock,
                'category':product.category.name,
                'main_image':product.main_image.url,
            })
        return Response({'success':True,'new_arrivals':product_data},status=200)
    



# ==========Vendor Page =============
class VendorsApiView(APIView):
    def get(self,request):
        vendors=Vendor.objects.filter(is_active=True).order_by('-created_at')
        vendor_data=[]
        for vendor in vendors:
            vendor_data.append({
                'id':vendor.id,
                'name':vendor.shop_name,
                'banner':vendor.shop_banner.url if vendor.shop_banner else None,
                'logo':vendor.shop_logo.url if vendor.shop_logo else None,
                'description':vendor.description,
            })
        return Response({'success':True,'vendors':vendor_data},status=200)
    
    

        
        
# ========== Filter Product Category  Brand  ,Price =============
class FilterProductsApiView(APIView):
    def get(self, request):
        try:
            # Get query params
            category_name = request.GET.get('category_name', '')  
            brand_name = request.GET.get('brand_name', '')        
            min_price = request.GET.get('min_price', None)
            max_price = request.GET.get('max_price', None)

    
            products = Product.objects.all()
            if category_name:
                products = products.filter(category__name__icontains=category_name)

            if brand_name:
                products = products.filter(brand__icontains=brand_name)

            if min_price is not None:
                products = products.filter(price__gte=float(min_price))

            if max_price is not None:
                products = products.filter(price__lte=float(max_price))

            product_data = []
            for product in products:
                product_data.append({
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'cost_price': product.cost_price,
                    'in_stock': product.in_stock,
                    'category': product.category.name,
                    'main_image': product.main_image.url,
                })

            return Response({'success': True, 'products': product_data}, status=200)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)




# ============ Product Details =============
class ProductDetailsApiView(APIView):
    def get(self, request, id):
        try:

            product = get_object_or_404(Product, pk=id)
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': clean_ckeditor_text(product.description),
                'price': product.price,
                'cost_price': product.cost_price,
                'in_stock': product.in_stock,
                'category': product.category.name,
                'main_image': product.main_image.url if product.main_image else None,
            }

            # Get product gallery images
            images = ProductImage.objects.filter(product=product)
            product_data['gallery'] = [img.image.url for img in images if img.image]

            # Get product variants
            variants = ProductVariant.objects.filter(product=product)
            variant_list = []
            for v in variants:
                variant_list.append({
                    'id': v.id,
                    'variant_type': v.get_variant_type_display(),  # shows "Size", "Color", etc.
                    'name': v.name,
                    'price_adjustment': v.price_adjustment,
                })
            product_data['variants'] = variant_list
            return Response({'success': True, 'product': product_data}, status=200)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)


# ============ Category Products =============
class CategoryProductsApiView(APIView):
    def get(self,request,category_id):
        try:
            category=get_object_or_404(Category,id=category_id)
            products=Product.objects.filter(category=category)
            product_data=[]
            for product in products:
                product_data.append({
                    'id':product.id,
                    'name':product.name,
                    'price':product.price,
                    'cost_price':product.cost_price,
                    'in_stock':product.in_stock,
                    'category':product.category.name,
                    'main_image':product.main_image.url,
                })
            return Response({'success':True,'featured_category':category.name,'products':product_data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
        
    

# ========== Add to Cart =============
class AddToCartApiView(APIView):

    authentication_classes=[JWTAuthentication]
    
    def post(self,request):
        try:
            print(request.data)
            user=request.user
            print(user)
            product_id=request.data.get('product_id')
            quantity=request.data.get('quantity',1)
            product=get_object_or_404(Product,id=product_id)
            if not product.in_stock:
                return Response({'success':False,'error':'Product is out of stock'},status=400)
            cart_item,created=Cart.objects.get_or_create(user=user,product=product)
            if not created:
                cart_item.quantity+=quantity
            else:
                cart_item.quantity=quantity
            cart_item.save()
            return Response({'success':True,'message':'Product added to cart successfully.'},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
        
        

# ========== View Cart =============
class ViewCartApiView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def get(self,request):
        try:
            user=request.user
            cart_items=Cart.objects.filter(user=user)
            cart_data=[]
            for item in cart_items:
                cart_data.append({
                    'id':item.id,
                    'product_id':item.product.id,
                    'product_name':item.product.name,
                    'quantity':item.quantity,
                    'price':item.product.price,
                    'total_price':item.product.price * item.quantity,
                })
            return Response({'success':True,'cart_items':cart_data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
        
        
 
# ========== Update Cart Item =============
class UpdateCartItemApiView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def post(self,request):
        try:
            user=request.user
            cart_item_id=request.data.get('cart_item_id')
            cart_item=get_object_or_404(Cart,id=cart_item_id,user=user)
            quantity=request.data.get('quantity',1)
            
            if cart_item.product.in_stock < quantity:
                return Response({'success':False,'error':'Requested quantity exceeds available stock.'},status=400)
            
            cart_item.quantity=quantity
            cart_item.save()
            return Response({'success':True,'message':'Cart item updated successfully.'},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
        
# ========== Remove from Cart =============
class RemoveFromCartApiView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def post(self,request):
        try:
            user=request.user
            cart_item_id=request.data.get('cart_item_id')
            cart_item=get_object_or_404(Cart,id=cart_item_id,user=user)
            cart_item.delete()
            return Response({'success':True,'message':'Cart item removed successfully.'},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)       
    


# ============= Users Profile API View =============
class CustomerProfileApiView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def get(self,request):
        try:
            user=request.user
            profile=user.profile
            profile_data={
                'first_name':user.first_name,
                'last_name':user.last_name,
                'email':user.email,
                'phone':profile.phone,
                'gender':profile.gender,   
                'avatar':profile.avatar.url if profile.avatar else None,
                'address':profile.address,
                'city':profile.city,
            }
            return Response({'success':True,'profile':profile_data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)

class EditCustomerProfileApiView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def post(self,request):
        try:
            user=request.user
            profile=user.profile
            user.first_name=request.data.get('first_name',user.first_name)
            user.last_name=request.data.get('last_name',user.last_name)
            user.email=request.data.get('email',user.email)
            profile.phone=request.data.get('phone',profile.phone)
            if 'avatar' in request.FILES:  
                profile.avatar = request.FILES['avatar']
            
            profile .gender=request.data.get('gender',profile.gender)
            profile.address=request.data.get('address',profile.address) 
            profile.city=request.data.get('city',profile.city)
            user.save()
            profile.save()
            return Response({'success':True,'message':'Profile updated successfully.'},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        
  
# ============= Order History API View =============
class CustomerOrderHistoryApiView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def get(self,request):
        try:
            user=request.user
            orders=Order.objects.filter(user=user).order_by('status','-created_at')
            order_data=[]
            for order in orders:
                order_data.append({
                    'id':order.id,
                    'products':[{
                        'product_name':item.product.name,
                        'quantity':item.quantity,
                        'price':item.price,
                    } for item in OrderItem.objects.filter(order=order)],
                    'order_number':order.order_number,
                    'total_amount':order.total,
                    'status':order.status,
                    'created_at':order.created_at,
                })
            return Response({'success':True,'orders':order_data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)    



# ============= Order Details API View =============
class CustomerOrderDetailsApiView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def get(self,request,order_id):
        try:
            user=request.user
            order=get_object_or_404(Order,id=order_id,user=user)
            order_data={
                'id':order.id,
                'products':[{
                    'product_name':item.product.name,
                    'quantity':item.quantity,
                    'price':item.price,
                } for item in OrderItem.objects.filter(order=order)],
                'order_number':order.order_number,
                'total_amount':order.total,
                'status':order.status,
                'created_at':order.created_at,
            }
            return Response({'success':True,'order':order_data},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)
        

      

# ============= Change Password API View =============
class ChangePasswordApiView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def post(self,request):
        try:
            user=request.user
            current_password=request.data.get('current_password')
            new_password=request.data.get('new_password')
            confirm_password=request.data.get('confirm_password')
            if not user.check_password(current_password):
                return Response({'success':False,'error':'Current password is incorrect.'},status=400)
            if new_password != confirm_password:
                return Response({'success':False,'error':'New passwords do not match.'},status=400)
            user.set_password(new_password)
            user.save()
            return Response({'success':True,'message':'Password changed successfully.'},status=200)
        except Exception as e:
            return Response({'success':False,'error':str(e)},status=400)

