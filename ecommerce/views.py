from users.models import User
from django.shortcuts import render


def home_page(request):
    return render(request,'website/pages/home.html')

def all_collections(request):
    return render(request,'website/pages/all_collections.html')

def carts(request):
    return render(request,"website/pages/cart.html")

def login_page(request):
    return render(request,'website/pages/login.html')

def signup_page(request):
    return render(request,'website/pages/signup.html')