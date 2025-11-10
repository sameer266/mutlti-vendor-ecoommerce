from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from ckeditor.fields import RichTextField    
from django.db.models.signals import post_save
from django.dispatch import receiver


class OTPVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True,blank=True)
    otp_code = models.CharField(max_length=6,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    GENDER_CHOICES=( ('male','Male'),
                    ('female','Female'))
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name="profile")
    phone = models.CharField(max_length=15,null=True,blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    gender=models.CharField(choices=GENDER_CHOICES,null=True,blank=True)
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
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='vendor')
    
    # Shop Info
    shop_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    shop_logo = models.ImageField(upload_to='vendor_logos/', blank=True, null=True)
    shop_banner = models.ImageField(upload_to='vendor_banners/', blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Contact Info
    phone = models.CharField(max_length=15)
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
    qr_image = models.ImageField(upload_to='vendor_qr/', blank=True, null=True)
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
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.10'),  # Default 10% commission
        help_text='Commission rate as a decimal (e.g. 0.10 for 10%)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        percent = float(self.rate) * 100
        return f"{percent:.0f}%"
    
    
class VendorPayoutRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]

    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='payout_requests')
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, help_text="Admin notes or reason for approval/rejection")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vendor.shop_name} - {self.requested_amount} ({self.get_status_display()})"

 
            
            
# -------------------------
#  Wallet Management
# -------------------------
class VendorWallet(models.Model):
    vendor = models.OneToOneField('Vendor', on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vendor.shop_name} - Wallet Balance: {self.balance}"

    def credit(self, amount):
        """Add amount to wallet"""
        self.balance += Decimal(amount)
        self.save()

    def debit(self, amount):
        """Subtract amount from wallet if sufficient balance"""
        if self.balance >= Decimal(amount):
            self.balance -= Decimal(amount)
            self.save()
            return True
        return False

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


# -------------------------
# Order Management
# -------------------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
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
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES,default="cod")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Coupon
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Order Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    estimated_delivery_date = models.DateField(
        null=True, blank=True,
        help_text="Calculated expected delivery date"
    )
    
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
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
 
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    

    def get_total(self):
        return self.quantity * self.price
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


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
    categories = models.ManyToManyField('Category', blank=True, help_text='Applicable categories')
    vendors = models.ManyToManyField('Vendor', blank=True, help_text='Applicable vendors')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self, user=None, cart_items=None):
        """Check if coupon is valid for the user and cart"""
        now = timezone.now()
        # Basic checks: active and date
        if not (self.is_active and self.valid_from <= now <= self.valid_to):
            return False, "This coupon is not active or has expired."

        # Check total usage limit
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "This coupon has reached its usage limit."

        # Check per-user usage
        if user and self.usage_limit_per_user is not None:
            user_used_count = CouponUsage.objects.filter(user=user, coupon=self).count()
            if user_used_count >= self.usage_limit_per_user:
                return False, "You have already used this coupon the maximum number of times."

        # Check minimum purchase
        if cart_items is not None:
            subtotal = sum(item.get_item_price() * item.quantity for item in cart_items)
            if subtotal < self.min_purchase:
                return False, f"Minimum order amount of Rs {self.min_purchase} required."

        return True, "Coupon is valid."

    def get_discount_amount(self, subtotal):
        """Calculate discount based on subtotal"""
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
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.first_name} used {self.coupon.code}"


# -------------------------
# Shipping Zones
# -------------------------
class ShippingCost(models.Model):

    cost = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Tax percentage (e.g. 13 for 13%)")

    class Meta:
        ordering = ['cost']
    
    def __str__(self):
        return f" Rs. {self.cost}"


# -------------------------
#  Invoice
# -------------------------
class Invoice(models.Model):
    invoice_number = models.CharField(max_length=20,null=True, unique=True, editable=False)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='invoices')
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, related_name='invoices')
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    payment_status = models.CharField(max_length=20, choices=[
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('failed', 'Failed')
    ], default='pending')
    
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.order.order_number}"


# -------------------------
# Organization Info
# -------------------------
class Organization(models.Model):
    # Basic Info
    name = models.CharField(max_length=200, default="My Store")
    logo = models.ImageField(upload_to='org/', blank=True, null=True)
    
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
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title or f"Slider {self.id}"



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


# ===========================
#   Signals 
# ===========================


@receiver(post_save, sender=Order)
def credit_vendor_wallet_on_order_complete(sender, instance, **kwargs):
    """
    Credit vendor wallet when an order is delivered.
    Deducts admin commission using VendorCommission.
    """
    if instance.status == 'delivered':
        for item in instance.items.all():
            vendor = item.product.vendor
            if vendor:
                # Get vendor-specific commission rate, or default if not set
                vc = VendorCommission.objects.first()
                rate = vc.rate
                total_amount = Decimal(item.get_total())
                admin_commission = (total_amount * rate).quantize(Decimal('0.01'))
                vendor_earning = (total_amount - admin_commission).quantize(Decimal('0.01'))

                # Credit vendor wallet
                wallet, _ = VendorWallet.objects.get_or_create(vendor=vendor)
                wallet.credit(vendor_earning)



@receiver(post_save, sender=VendorPayoutRequest)
def process_vendor_payout_request(sender, instance, **kwargs):
    """
    Process vendor payout request by debiting vendor wallet if approved.
    """
    if instance.status == 'paid':
        wallet, _ = VendorWallet.objects.get_or_create(vendor=instance.vendor)
        wallet.debit(instance.requested_amount)



@receiver(post_save,sender=Order)
def change_invoice_payment_status_with_order(sender,instance,**kwargs):
    """
    Sync payment status of invoices with the order's payment status.
    Creates an invoice per vendor if not already created.

    """
    for item in instance.items.all():
        vendor=item.product.vendor
        customer=instance.user
        
        invoice=Invoice.objects.get(order=instance,vendor=vendor,customer=customer)
        if instance.payment_status=="unpaid":
            invoice.payment_status="pending"
        elif instance.payment_status=="paid":
            invoice.payment_status="paid"
        elif instance.payment_status=="failed":
            invoice.payment_status="failed"
        instance.save()
        
            
            
        
        