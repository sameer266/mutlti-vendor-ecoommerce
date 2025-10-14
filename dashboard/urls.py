from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),

    # User Management
    path('users/', views.admin_users_list, name='admin_users_list'),
    path('users/add/', views.admin_user_add, name='admin_user_add'),
    path('users/<int:pk>/update/', views.admin_user_update, name='admin_user_update'),
    path('users/<int:pk>/delete/', views.admin_user_delete, name='admin_user_delete'),

    # Vendor Management
    path('vendors/', views.admin_vendors_list, name='admin_vendors_list'),
    path('vendors/pending-kyc/', views.admin_vendors_pending_kyc, name='admin_vendors_pending_kyc'),
    path('vendors/verified-kyc/', views.admin_vendors_verified_kyc, name='admin_vendors_verified_kyc'),
    path('vendors/add/', views.admin_vendor_add, name='admin_vendor_add'),
    path('vendors/<int:pk>/update/', views.admin_vendor_update, name='admin_vendor_update'),
    path('vendors/<int:pk>/delete/', views.admin_vendor_delete, name='admin_vendor_delete'),
    path('vendors/<int:pk>/status/', views.admin_vendor_change_status, name='admin_vendor_change_status'),

    path('payments/', views.admin_payments_overview, name='admin_payments_overview'),
    path('payments/vendor/<int:vendor_id>/', views.admin_vendor_payments_detail, name='admin_vendor_payments_detail'),

    # Payout Requests
    path('payout-requests/', views.admin_payout_requests_list, name='admin_payout_requests_list'),
    path('payout-requests/pending/', views.admin_payout_requests_pending, name='admin_payout_requests_pending'),
    path('payout-requests/rejected/', views.admin_payout_requests_rejected, name='admin_payout_requests_rejected'),
    path('payout-requests/<int:pk>/status/', views.admin_payout_request_change_status, name='admin_payout_request_change_status'),

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
    path('orders/pending/', views.admin_orders_pending, name='admin_orders_pending'),
    path('orders/delivered/', views.admin_orders_delivered, name='admin_orders_delivered'),
    path('orders/<str:order_number>/status/', views.admin_order_change_status, name='admin_order_change_status'),
    path('orders/<str:order_number>/items/', views.admin_order_items_json, name='admin_order_items_json'),
    path('orders/<str:order_number>/delete/', views.admin_order_delete, name='admin_order_delete'),

    # Review Management
    path('reviews/', views.admin_reviews_list, name='admin_reviews_list'),
    path('reviews/add/', views.admin_review_add, name='admin_review_add'),
    path('reviews/<int:pk>/update/', views.admin_review_update, name='admin_review_update'),
    path('reviews/<int:pk>/delete/', views.admin_review_delete, name='admin_review_delete'),

    # Contact Management
    path('contacts/', views.admin_contacts_list, name='admin_contacts_list'),
    path('contacts/add/', views.admin_contact_add, name='admin_contact_add'),
    path('contacts/<int:pk>/update/', views.admin_contact_update, name='admin_contact_update'),
    path('contacts/<int:pk>/delete/', views.admin_contact_delete, name='admin_contact_delete'),

    # Newsletter Management
    path('newsletter/', views.admin_newsletter_list, name='admin_newsletter_list'),
    path('newsletter/add/', views.admin_newsletter_add, name='admin_newsletter_add'),
    path('newsletter/<int:pk>/update/', views.admin_newsletter_update, name='admin_newsletter_update'),
    path('newsletter/<int:pk>/delete/', views.admin_newsletter_delete, name='admin_newsletter_delete'),

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

    # Home Category Management
    path('home-categories/', views.admin_home_categories_list, name='admin_home_categories_list'),
    path('home-categories/add/', views.admin_home_category_add, name='admin_home_category_add'),
    path('home-categories/<int:pk>/update/', views.admin_home_category_update, name='admin_home_category_update'),
    path('home-categories/<int:pk>/delete/', views.admin_home_category_delete, name='admin_home_category_delete'),

    # Coupon Management
    path('coupons/', views.admin_coupons_list, name='admin_coupons_list'),
    path('coupons/add/', views.admin_coupon_add, name='admin_coupon_add'),
    path('coupons/<int:pk>/update/', views.admin_coupon_update, name='admin_coupon_update'),
    path('coupons/<int:pk>/delete/', views.admin_coupon_delete, name='admin_coupon_delete'),

    # Shipping Zone Management
    path('shipping-zones/', views.admin_shipping_zones_list, name='admin_shipping_zones_list'),
    path('shipping-zones/add/', views.admin_shipping_zone_add, name='admin_shipping_zone_add'),
    path('shipping-zones/<int:pk>/update/', views.admin_shipping_zone_update, name='admin_shipping_zone_update'),
    path('shipping-zones/<int:pk>/delete/', views.admin_shipping_zone_delete, name='admin_shipping_zone_delete'),

    # Organization Management
    path('organization/', views.admin_organization_view, name='admin_organization_view'),
    path('organization/update/', views.admin_organization_update, name='admin_organization_update'),

    # Notification Management
    path('notifications/', views.admin_notifications_list, name='admin_notifications_list'),
    path('notifications/add/', views.admin_notification_add, name='admin_notification_add'),
    path('notifications/<int:pk>/update/', views.admin_notification_update, name='admin_notification_update'),
    path('notifications/<int:pk>/delete/', views.admin_notification_delete, name='admin_notification_delete'),
]