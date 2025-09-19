from users.models import User
from django.shortcuts import render


def home_page(request):
    return render(request,'website/pages/home.html')