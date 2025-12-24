
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from dashboard.models import (
    UserRole,
    UserProfile,
    Slider,
    Banner,
    Category,
    Product,Cart,ProductVariant,OTPVerification,Order,OrderItem,Coupon,CouponUsage,Contact,TaxCost,Invoice
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
                return redirect('admin_dashboard')
        
            else:
                messages.error(request,'Invalid Username and Password')
                return redirect('login_page')
        except User.DoesNotExist:
            messages.error(request,'Invalid Username and Password')
            return redirect('login_page')
    
    
    return render(request,'website/pages/login.html')





def logout_view(request):
    auth_logout(request)
    messages.success(request,'Logout Successfull')
    return redirect('login_page')