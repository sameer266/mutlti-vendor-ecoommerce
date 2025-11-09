from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView




# ==========================
#  Mobile App API URLs
# ==========================

urlpatterns = [
    
    # Authentication APIs
    path('login/', views.LoginApiView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('register/', views.RegisterApiView.as_view()),
    path('verify-otp/', views.VerifyOtpApiView.as_view()),
    path('forget-password/', views.ForgetPasswordApiView.as_view()),
    path('forget-password/verify-otp/', views.ForgetPasswordVerifyOtpApiView.as_view()),
    path('reset-password/', views.ResetPasswordApiView.as_view()),
    path('resend-otp/',views.ResendOtpApiView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    
    
    # Pages APIs
    path('home/', views.HomeApiView.as_view()),
    path('all-collections/', views.AllCollectionsApiView.as_view()),
    path('new-arrivals/', views.NewArrivalsApiView.as_view()),
    path('vendors/', views.VendorsApiView.as_view()),
    path('search-products/', views.FilterProductsApiView.as_view()),
    
    
    # Details APIs
    path('product/<int:id>/', views.ProductDetailsApiView.as_view()),
    path('category/<int:category_id>/products/', views.CategoryProductsApiView.as_view()),
 
    
    
    # Cart APIs
    path('cart/', views.ViewCartApiView.as_view()),
    path('cart-add/', views.AddToCartApiView.as_view()),
    path('cart-update/', views.UpdateCartItemApiView.as_view()),
    path('cart-remove/', views.RemoveFromCartApiView.as_view()),
    
    # profile APIs
    path('customer-profile/', views.CustomerProfileApiView.as_view()),
    path('edit-profile/', views.EditCustomerProfileApiView.as_view()),
    path('customer-orders/', views.CustomerOrderHistoryApiView.as_view()),
    path('customer-order/<str:order_id>/', views.CustomerOrderDetailsApiView.as_view()),
    path('change-password/', views.ChangePasswordApiView.as_view()),
    
    
   
]
