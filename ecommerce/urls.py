"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-dashboard/',include('dashboard.urls')),
    
    
    path('',views.home_page,name="home"),
    path('all-collections/',views.all_collections,name="all_collections"),
    path("new-arrivals/",views.new_arrivals,name="new_arrivals"),
    path("vendors/",views.vendors,name="vendors"),
    path("vendors/vendor-details/",views.vendor_details,name="vendor_details"),
    path('carts/',views.carts,name="carts"),
    
    
    path("login/",views.login_page,name="login_page"),
    path("signup/",views.signup_page,name='signup_page'),
    
    
]
