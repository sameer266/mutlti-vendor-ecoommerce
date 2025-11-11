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

    # Vendor Management
    path('vendors/', views.admin_vendors_list, name='admin_vendors_list'),
    path('vendors/pending-kyc/', views.admin_vendors_pending_kyc, name='admin_vendors_pending_kyc'),
    path('vendors/verified-kyc/', views.admin_vendors_verified_kyc, name='admin_vendors_verified_kyc'),
    path('vendors/add/', views.admin_vendor_add, name='admin_vendor_add'),
    path('vendors/<int:pk>/update/', views.admin_vendor_update, name='admin_vendor_update'),
    path('vendors/<int:pk>/delete/', views.admin_vendor_delete, name='admin_vendor_delete'),
    path('vendors/<int:pk>/status/', views.admin_vendor_change_status, name='admin_vendor_change_status'),

    
    # Payment Management
    path('payments/', views.admin_payments_overview, name='admin_payments_overview'),
    path('payments/vendor/<int:vendor_id>/', views.admin_vendor_payments_detail, name='admin_vendor_payments_detail'),
    
    # Commission
    path('admin/api/commission/update/', views.admin_update_commission, name='admin-update-commission'),

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
    
    path('orders/<str:order_number>/invoice/',views.admin_order_invoice_view,name="admin_orders_invoice_list"),
    path('invoice/<str:invoice_number>/', views.admin_invoice_detail, name='admin_invoice_detail'),

    

    # Review Management
    path('reviews/', views.admin_reviews_list, name='admin_reviews_list'),
    path('reviews/add/', views.admin_review_add, name='admin_review_add'),
    path('reviews/<int:pk>/update/', views.admin_review_update, name='admin_review_update'),
    path('reviews/<int:pk>/delete/', views.admin_review_delete, name='admin_review_delete'),

    # Contact Management
    path('contacts/', views.admin_contacts_list, name='admin_contacts_list'),
    path('contacts/<int:pk>/delete/', views.admin_contact_delete, name='admin_contact_delete'),
    path('contacts/unread/',views.admin_contacts_unread,name="admin_contact_unread"),
    path('contacts/read/', views.admin_read_contact, name='admin_read_contacts'),

    # Shipping Cost Management
    path('shipping-cost/', views.shipping_cost_view,name="admin_shipping_cost"),
    path('shipping-cost/edit/<int:pk>/',views.shipping_cost_edit,name="admin_shipping_update"),
    
    
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
    
    
    # =================================
    #   Vendor
    # =================================
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/products/', views.vendor_products_list, name='vendor_products_list'),
    path('vendor/products/add/', views.vendor_product_add, name='vendor_product_add'),
    path('vendor/products/<int:pk>/update/', views.vendor_product_update, name='vendor_product_update'),
    path('vendor/products/<int:pk>/delete/', views.vendor_product_delete, name='vendor_product_delete'),
    path('vendor/products/low-stock/', views.vendor_products_low_stock, name='vendor_products_low_stock'),
    
    path('vendor/orders/', views.vendor_orders_list, name='vendor_orders_list'),
    path('vendor/orders/pending/', views.vendor_orders_pending, name='vendor_orders_pending'),
    path('vendor/orders/delivered/', views.vendor_orders_delivered, name='vendor_orders_delivered'),
    path('vendor/api/orders/<str:order_number>/update-estimated-date/', views.vendor_update_estimated_date, name='vendor_update_estimated_date'),
    path('vendor/orders/<str:order_number>/invoice/',views.vendor_order_invoice_view,name="vendor_orders_invoice_list"),
    
    
    
    
    path('vendor/payout-lists/', views.vendor_payouts_list, name='vendor_payout_list'),
    path('vendor/payout-requests/add/', views.vendor_payout_request_add, name='vendor_payout_requests_add'),
    path('vendor/payouts/pending/', views.pending_payout_requests, name='vendor_pending_payout'),
    path('vendor/payouts/rejected/', views.rejected_payout_requests, name='vendor_rejected_payout'),
    
    

    path('vendor/wallet/', views.vendor_wallet_view, name='vendor_wallet_view'),
    
    
    # Review
    path('vendor/reviews/', views.vendor_reviews_list, name='vendor_reviews_list'),

    # Invoice
    path('vendor/invoice/',views.vendor_invoices,name="vendor_invoices_list"),
    path('vendor/invoice-details/<str:invoice_number>/',views.vendor_invoice_detail,name='vendor_invoice_detail'),
    
    #Vendor Profile 
    path('vendor/profile/',views.vendor_profile_view,name='vendor_profile'),
    path('vendor/profile/edit/', views.vendor_profile_edit_view, name='vendor_edit_profile'),
]
    
    
