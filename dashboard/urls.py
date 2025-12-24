from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),

    # User Management
    path('users/', views.admin_users_list, name='admin_users_list'),
    # path('users/add/', views.admin_user_add, name='admin_user_add'),
    path('users/<int:pk>/update/', views.admin_user_update, name='admin_user_update'),
    path('users/<int:pk>/delete/', views.admin_user_delete, name='admin_user_delete'),


    
    # Payment Management
    path('payments/', views.admin_payments_overview, name='admin_payments_overview'),
 


    # Product Management
    path('products/', views.admin_products_list, name='admin_products_list'),
    path('products/featured/', views.admin_products_featured, name='admin_products_featured'),
    path('products/low-stock/', views.admin_products_low_stock, name='admin_products_low_stock'),
    path('products/add/', views.admin_product_add, name='admin_product_add'),
    path('products/<int:pk>/update/', views.admin_product_update, name='admin_product_update'),
    path('products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),

    # Category Management
    path('categories/', views.admin_categories_list, name='admin_categories_list'),
    path('categories/add/', views.admin_category_add, name='admin_category_add'),
    path('categories/<int:pk>/update/', views.admin_category_update, name='admin_category_update'),
    path('categories/<int:pk>/delete/', views.admin_category_delete, name='admin_category_delete'),

    # Order Management
    path('orders/', views.admin_orders_list, name='admin_orders_list'),
    path('odrer-details/<str:order_number>/',views.admin_order_details,name='admin_order_details'),
    path('orders/pending/', views.admin_orders_pending, name='admin_orders_pending'),
    path('orders/delivered/', views.admin_orders_delivered, name='admin_orders_delivered'),
    path('orders/<str:order_number>/status/', views.admin_order_change_status, name='admin_order_change_status'),
    path('orders/<str:order_number>/items/', views.admin_order_items_json, name='admin_order_items_json'),
    path('api/orders/<str:order_number>/payment-status/', views.api_update_order_payment_status, name='api_update_order_payment_status'),
    path('orders/<str:order_number>/delete/', views.admin_order_delete, name='admin_order_delete'),
    
    path('orders/<str:order_number>/invoice/',views.admin_order_invoice_view,name="admin_orders_invoice_list"),
    path('invoice/<str:invoice_number>/', views.admin_invoice_detail, name='admin_invoice_detail'),

    

    # Review Management
    path('reviews/', views.admin_reviews_list, name='admin_reviews_list'),
    path('reviews/add/', views.admin_review_add, name='admin_review_add'),
    path('reviews/<int:pk>/update/', views.admin_review_update, name='admin_review_update'),
    path('reviews/<int:pk>/delete/', views.admin_review_delete, name='admin_review_delete'),

 
    # Tax Settings (replaced previous Shipping Cost global setting)
    path('tax-settings/', views.tax_settings_view, name="admin_tax_settings"),
    path('tax-settings/edit/<int:pk>/', views.tax_settings_edit, name="admin_tax_settings_update"),
    
    

    # Slider Management
    path('sliders/', views.admin_sliders_list, name='admin_sliders_list'),
    path('sliders/add/', views.admin_slider_add, name='admin_slider_add'),
    path('sliders/<int:pk>/update/', views.admin_slider_update, name='admin_slider_update'),
    path('sliders/<int:pk>/delete/', views.admin_slider_delete, name='admin_slider_delete'),

    # Banner Management
    path('banners/', views.admin_banners_list, name='admin_banners_list'),
    path('banners/add/', views.admin_banner_add, name='admin_banner_add'),
    path('banners/<int:pk>/update/', views.admin_banner_update, name='admin_banner_update'),
    path('banners/<int:pk>/delete/', views.admin_banner_delete, name='admin_banner_delete'),

   
    # Coupon Management
    path('coupons/', views.admin_coupons_list, name='admin_coupons_list'),
    path('coupons/add/', views.admin_coupon_add, name='admin_coupon_add'),
    path('coupons/<int:pk>/update/', views.admin_coupon_update, name='admin_coupon_update'),
    path('coupons/<int:pk>/delete/', views.admin_coupon_delete, name='admin_coupon_delete'),

 
    # Organization Management
    path('organization/', views.admin_organization_view, name='admin_organization_view'),
    path('organization/update/', views.admin_organization_update, name='admin_organization_update'),

    # Notification Management
    path('notifications/', views.admin_notifications_list, name='admin_notifications_list'),
    path('notifications/add/', views.admin_notification_add, name='admin_notification_add'),
    path('notifications/<int:pk>/update/', views.admin_notification_update, name='admin_notification_update'),
    path('notifications/<int:pk>/delete/', views.admin_notification_delete, name='admin_notification_delete'),
    
    
    # Profile Management
    path('profile/',views.admin_profile_view,name="admin_profile"),
    path('profile/update/',views.admin_profile_edit,name="admin_profile_edit"),
    
    # Change Password
    path('change-password/',views.change_password_view,name="change_password"),
    
    # Supplier Management
    path('suppliers/', views.admin_suppliers_list, name='admin_suppliers_list'),
    path('suppliers/add/', views.admin_supplier_add, name='admin_supplier_add'),
    path('suppliers/<int:pk>/update/', views.admin_supplier_update, name='admin_supplier_update'),
    path('suppliers/<int:pk>/', views.admin_supplier_detail, name='admin_supplier_detail'),
    path('suppliers/<int:pk>/delete/', views.admin_supplier_delete, name='admin_supplier_delete'),
    path('supplier/update-payment/',views.admin_supplier_payments_update,name="admin_supplier_payment_update"),
    
    # Purchase Management
    path('purchases/', views.admin_purchases_list, name='admin_purchases_list'),
    path('purchases/add/', views.admin_purchase_add, name='admin_purchase_add'),
    path('purchases/<int:pk>/update/', views.admin_purchase_update, name='admin_purchase_update'),
    path('purchases/<int:pk>/delete/', views.admin_purchase_delete, name='admin_purchase_delete'),
    
    # Purchase Invoice Management
    path('purchase-invoices/', views.admin_purchase_invoices_list, name='admin_purchase_invoices_list'),
    path('purchase-invoices/<str:invoice_number>/', views.admin_purchase_invoice_detail, name='admin_purchase_invoice_detail'),
    path('purchase-invoices/<str:invoice_number>/update-payment/', views.admin_purchase_invoice_update_payment, name='admin_purchase_invoice_update_payment'),
    path('api/purchase-invoices/<str:invoice_number>/payment-status/', views.api_update_purchase_invoice_payment_status, name='api_update_purchase_invoice_payment_status'),
    
    
    # Sales Management (Physical/Offline)
    path('sales/', views.admin_sales_list, name='admin_sales_list'),
    path('sales/add/', views.admin_sales_add, name='admin_sales_add'),
    path('sales/<int:pk>/edit/', views.admin_sales_edit, name='admin_sales_edit'),
    path('sales/<int:pk>/', views.admin_sales_detail, name='admin_sales_detail'),
    path('sales/<int:pk>/delete/', views.admin_sales_delete, name='admin_sales_delete'),
    path('sales/customers/', views.admin_sales_customers, name='admin_sales_customers'),
    path('sales/customer/<int:pk>/', views.admin_sales_customer_detail, name='admin_sales_customer_detail'),
    path('sales/customer/<int:pk>/payment/', views.admin_sales_customer_payment, name='admin_sales_customer_payment'),
    path('sales/<int:pk>/payment/', views.admin_sales_detail_payment, name='admin_sales_detail_payment'),
    
    # Services Module
    path('services/', views.admin_services_list, name='admin_services_list'),
    path('services/add/', views.admin_service_add, name='admin_service_add'),
    path('services/<int:pk>/update/', views.admin_service_update, name='admin_service_update'),
    path('services/<int:pk>/delete/', views.admin_service_delete, name='admin_service_delete'),

    # Service Bookings (admin)
    path('service-bookings/', views.admin_service_bookings_list, name='admin_service_bookings_list'),
    path('service-bookings/add/', views.admin_service_booking_add, name='admin_service_booking_add'),
    path('service-bookings/<int:pk>/update/', views.admin_service_booking_update, name='admin_service_booking_update'),
    path('service-bookings/<int:pk>/delete/', views.admin_service_booking_delete, name='admin_service_booking_delete'),

    # Customer booking (public/simple)
    path('services/book/', views.customer_book_service, name='customer_book_service'),
]
    
    
