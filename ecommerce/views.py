
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from dashboard.models import ( 
                              UserRole,UserProfile
                              )
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from  django.contrib import messages

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
                pass
            elif user.role.role == 'customer':
                pass
        except User.DoesNotExist:
            messages.error(request,'Invalid Username and Password')
            return redirect('login_page')
    
    return render(request,'website/pages/login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def home_page(request):
    return render(request,'website/pages/home.html')

def all_collections(request):
    return render(request,'website/pages/all_collections.html')

def new_arrivals(request):
    return render(request,'website/pages/new_arrivals.html')

def vendors(request):
    return render(request,'website/pages/vendors.html')

def vendor_details(request):
    return render(request,'website/pages/vendor_details.html')

def carts(request):
    return render(request,"website/pages/cart.html")



def signup_page(request):
    return render(request,'website/pages/signup.html')