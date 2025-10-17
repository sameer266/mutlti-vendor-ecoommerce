from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from ckeditor.fields import RichTextField    



class OTPVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email}"
    
# -------------------------
# User Role Management
# -------------------------
class UserRole(models.Model):
    """Define user roles in the system"""
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role',null=True,blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_customer(self):
        return self.role == 'customer'
    
    def is_vendor(self):
        return self.role == 'vendor'
    
    def is_admin(self):
        return self.role == 'admin'


# -------------------------
# User Management
# -------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name="profile")
    phone = models.CharField(max_length=15)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    PROVINCE_CHOICES = [
        ('province1', 'Koshi Province'),
        ('madhesh', 'Madhesh Province'),
        ('bagmati', 'Bagmati Province'),
        ('gandaki', 'Gandaki Province'),
        ('lumbini', 'Lumbini Province'),
        ('karnali', 'Karnali Province'),
        ('sudurpashchim', 'Sudurpashchim Province'),
    ]
    province = models.CharField(max_length=20, choices=PROVINCE_CHOICES, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_role(self):
        """Get user role"""
        try:
            return self.user.role.get_role_display()
        except:
            return 'No Role Assigned'


# -------------------------
# Vendor Management with KYC
# -------------------------
class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Shop Info
    shop_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    shop_logo = models.ImageField(upload_to='vendor_logos/', blank=True, null=True)
    shop_banner = models.ImageField(upload_to='vendor_banners/', blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Contact Info
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    
    PROVINCE_CHOICES = [
        ('province1', 'Koshi Province'),
        ('madhesh', 'Madhesh Province'),
        ('bagmati', 'Bagmati Province'),
        ('gandaki', 'Gandaki Province'),
        ('lumbini', 'Lumbini Province'),
        ('karnali', 'Karnali Province'),
        ('sudurpashchim', 'Sudurpashchim Province'),
    ]
    province = models.CharField(max_length=20, choices=PROVINCE_CHOICES)
    
    # PAN (Permanent Account Number) - Required
    pan_number = models.CharField(max_length=15, unique=True)
    pan_document = models.FileField(
        upload_to='kyc/pan/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Upload PAN certificate (PDF/Image)'
    )
    
    # Citizenship or Company Registration
    citizenship_number = models.CharField(max_length=20, blank=True, help_text='For individuals')
    citizenship_front = models.FileField(
        upload_to='kyc/citizenship/',
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        help_text='Front side of citizenship'
    )
    citizenship_back = models.FileField(
        upload_to='kyc/citizenship/',
        blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        help_text='Back side of citizenship'
    )
    
    # For Company Registration
    company_registration = models.FileField(
        upload_to='kyc/company/',
        blank=True,
        validators=[FileExtensionValidator(['pdf'])],
        help_text='For companies: Company registration certificate'
    )
    
    # Bank Details for Payment
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=30, blank=True)
    bank_account_holder = models.CharField(max_length=200, blank=True)
    
    # Status & Verification
    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    rejection_reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.shop_name)
            slug = base_slug
            counter = 1
            while Vendor.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Automatically set user role to vendor
        if self.user:
            user_role, created = UserRole.objects.get_or_create(user=self.user)
            user_role.role = 'vendor'
            user_role.save()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.shop_name


class VendorCommission(models.Model):
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='commissions')
    rate = models.DecimalField(max_digits=5, decimal_places=4, help_text='Commission rate as a decimal e.g. 0.1000 for 10%')
    effective_from = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-active', '-effective_from', '-created_at']

    def __str__(self):
        percent = int((self.rate or 0) * 100)
        return f"{self.vendor.shop_name} - {percent}%"



class VendorPayout(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total payout amount to the vendor.")
    method = models.CharField(max_length=100, blank=True, help_text="Payment method used (e.g. Bank, eSewa, Khalti, etc.)")
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Transaction or reference ID from the payment gateway.")
    admin_remarks = models.CharField(max_length=255, blank=True, help_text="Remarks or notes from the admin regarding this payout.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current status of the payout.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vendor.shop_name} - {self.amount} ({self.get_status_display()})"

    def mark_completed(self, transaction_id=None):
        self.status = 'completed'
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()


class VendorPayoutRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]

    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='payout_requests')
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.TextField(blank=True, help_text="Optional message from vendor to admin")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, help_text="Admin notes or reason for approval/rejection")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vendor.shop_name} - {self.requested_amount} ({self.get_status_display()})"

    def approve(self):
        """
        Approve payout request and automatically create a VendorPayout record.
        """
        from .models import VendorPayout
        payout = VendorPayout.objects.create(
            vendor=self.vendor,
            amount=self.requested_amount,
            method="Manual",
            admin_remarks="Auto-created after approval",
            status="processing",
        )
        self.status = "approved"
        self.save(update_fields=['status'])
        return payout

# -------------------------
# Category Management (Hierarchical)
# -------------------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text='Display order')
    is_active = models.BooleanField(default=True)
    is_featured=models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
      
    
    


# -------------------------
# Product Management
# -------------------------

class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    
    # Basic Info
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = RichTextField() 
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='For vendor tracking')
    
    # Stock Management
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text='Stock Keeping Unit')
    stock = models.PositiveIntegerField(default=0)
    low_stock_alert = models.PositiveIntegerField(default=5, help_text='Alert when stock reaches this level')
    
    # Product Details
    brand = models.CharField(max_length=100, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='Weight in kg')
    
    # Images
    main_image = models.ImageField(upload_to='products/')
    
    # Status & Stats
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if blank
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        import uuid
        if not self.sku:
            self.sku = uuid.uuid4().hex[:8].upper()
            
        super().save(*args, **kwargs)
    
    @property
    def in_stock(self):
        return self.stock > 0
    
    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_alert
    
    @property
    def discount_percentage(self):
        if self.cost_price and self.cost_price > self.price:
            return int(((self.cost_price - self.price) / self.cost_price) * 100)
        return 0
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(r.rating for r in reviews) / len(reviews)
        return 0
    
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    """For size, color, weight variations"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    VARIANT_TYPES = [
        ('size', 'Size'),
        ('color', 'Color'),
        ('weight', 'Weight'),
        ('storage', 'Storage Capacity'),
        ('ram', 'RAM'),
        ('material', 'Material'),
        ('style', 'Style'),
        ('pattern', 'Pattern'),
        ('flavor', 'Flavor'),
        ('other', 'Other'),
        
    ]
    variant_type = models.CharField(max_length=20, choices=VARIANT_TYPES)
    name = models.CharField(max_length=100)
    
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    
    class Meta:
        unique_together = ('product', 'variant_type', 'name')
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"


# -------------------------
# Cart & Wishlist
# -------------------------


class Cart(models.Model):
    # Authenticated user (optional for guest)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="For non-authenticated users")
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        price = self.product.price
        if self.variant:
            price += self.variant.price_adjustment
        return price * self.quantity

    def get_item_price(self):
        price = self.product.price
        if self.variant:
            price += self.variant.price_adjustment
        return price
    
    def __str__(self):
        if self.user:
            return f"{self.user.username}'s cart - {self.product.name}"
        return f"Guest cart ({self.session_key}) - {self.product.name}"


class Wishlist(models.Model):
    # Authenticated user (optional for guest)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="For non-authenticated users")
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        if self.user:
            return f"{self.user.username}'s wishlist - {self.product.name}"
        return f"Guest wishlist ({self.session_key}) - {self.product.name}"

# -------------------------
# Order Management
# -------------------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
        ('imepay', 'IME Pay'),
        ('connectips', 'ConnectIPS'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Order Info
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Shipping Info
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    
    PROVINCE_CHOICES = [
        ('province1', 'Koshi Province'),
        ('madhesh', 'Madhesh Province'),
        ('bagmati', 'Bagmati Province'),
        ('gandaki', 'Gandaki Province'),
        ('lumbini', 'Lumbini Province'),
        ('karnali', 'Karnali Province'),
        ('sudurpashchim', 'Sudurpashchim Province'),
    ]
    province = models.CharField(max_length=20, choices=PROVINCE_CHOICES)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Order Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Coupon
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Order Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text='Customer notes')
    admin_notes = models.TextField(blank=True, help_text='Internal admin notes')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Format: ORD20250113123456
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Snapshot data (in case product is deleted/changed)
    product_name = models.CharField(max_length=255)
    product_image = models.ImageField(upload_to='order_items/', blank=True, null=True)
    variant_name = models.CharField(max_length=100, blank=True)
    
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Vendor fulfillment tracking
    FULFILLMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready to Ship'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]
    fulfillment_status = models.CharField(max_length=20, choices=FULFILLMENT_STATUS, default='pending')
    
    def get_total(self):
        return self.quantity * self.price
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"


# -------------------------
# Reviews & Ratings
# -------------------------
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


# -------------------------
# Coupons & Discounts
# -------------------------
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)
    
    DISCOUNT_TYPES = [
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Conditions
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Minimum order value')
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Max discount amount (for percentage)')
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Total usage limit')
    usage_limit_per_user = models.PositiveIntegerField(null=True, blank=True, help_text='Per user limit')
    used_count = models.PositiveIntegerField(default=0)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Restrictions
    categories = models.ManyToManyField(Category, blank=True, help_text='Applicable categories')
    vendors = models.ManyToManyField(Vendor, blank=True, help_text='Applicable vendors')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        now = timezone.now()
        return (self.is_active and 
                self.valid_from <= now <= self.valid_to and
                (self.usage_limit is None or self.used_count < self.usage_limit))
    
    def get_discount_amount(self, subtotal):
        if self.discount_type == 'percent':
            discount = (self.discount_value / 100) * subtotal
            if self.max_discount is not None:
                discount = min(discount, self.max_discount)
        else:
            discount = self.discount_value
        return discount
    
    def __str__(self):
        return self.code


class CouponUsage(models.Model):
    """Track coupon usage per user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} used {self.coupon.code}"


# -------------------------
# Shipping Zones
# -------------------------
class ShippingZone(models.Model):
    name = models.CharField(max_length=100)
    
    PROVINCE_CHOICES = [
        ('province1', 'Koshi Province'),
        ('madhesh', 'Madhesh Province'),
        ('bagmati', 'Bagmati Province'),
        ('gandaki', 'Gandaki Province'),
        ('lumbini', 'Lumbini Province'),
        ('karnali', 'Karnali Province'),
        ('sudurpashchim', 'Sudurpashchim Province'),
    ]
    provinces = models.CharField(max_length=255, help_text='Comma-separated province codes')
    
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Free shipping above this amount')
    estimated_days = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['cost']
    
    def __str__(self):
        return f"{self.name} - Rs. {self.cost}"


# -------------------------
# Organization Info
# -------------------------
class Organization(models.Model):
    # Basic Info
    name = models.CharField(max_length=200, default="My Store")
    tagline = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='org/', blank=True, null=True)
    favicon = models.ImageField(upload_to='org/', blank=True, null=True)
    
    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    phone_secondary = models.CharField(max_length=15, blank=True)
    address = models.TextField()
    
    # Social Media
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    
    class Meta:
        verbose_name = 'Organization Info'
        verbose_name_plural = 'Organization Info'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.pk and Organization.objects.exists():
            raise ValueError('Only one Organization instance allowed')
        super().save(*args, **kwargs)


# -------------------------
# Newsletter
# -------------------------
class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.email


# -------------------------
# Contact Messages
# -------------------------
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    replied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.name}"


# -------------------------
# Notifications
# -------------------------
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    NOTIFICATION_TYPES = [
        ('order', 'Order Update'),
        ('product', 'Product Update'),
        ('message', 'Message'),
        ('promotion', 'Promotion'),
        ('other', 'Other'),
    ]
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    
   

# Slider model
class Slider(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to='sliders/')
    link = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title or f"Slider {self.id}"


# Banner model
# Banner model
from django.db import models

class Banner(models.Model):
    PAGE_CHOICES = [
        ('home', 'Home Page'),
        ('products', 'Products Page'),
      
    ]

    title = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='banners/')
    link = models.URLField(max_length=500, blank=True, null=True)
    page = models.CharField(
        max_length=50, 
        choices=PAGE_CHOICES, 
        default='home', 
        unique=True,  # Only one banner per page
        help_text="Select where to display the banner"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title or f"Banner {self.id}"


# Home page category Section
class HomeCategory(models.Model):
    title = models.CharField(max_length=150, help_text="Title displayed below the image")
    image = models.ImageField(upload_to='home_categories/')
    link = models.URLField(max_length=500, blank=True, null=True, help_text="Optional URL for this tile")
    position = models.PositiveIntegerField(default=0, help_text="Order in which it appears on homepage")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return self.title