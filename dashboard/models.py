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
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role',null=True,blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_customer(self):
        return self.role == 'customer'
    
    
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
    gender=models.CharField(max_length=10, choices=GENDER_CHOICES,null=True,blank=True)
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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    
    # Basic Info
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = RichTextField() 
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='For  tracking')
    
    # Stock Management
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text='Stock Keeping Unit')
    stock = models.PositiveIntegerField(default=0)
    low_stock_alert = models.PositiveIntegerField(default=5, help_text='Alert when stock reaches this level')
    
    # Product Details
    brand = models.CharField(max_length=100, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='Weight in kg')
    # Per-product shipping and delivery estimate
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Shipping cost per unit for this product')
    estimated_days = models.CharField(max_length=50, blank=True, null=True, help_text='Estimated delivery time (days or string like "2-4 days")')
    
    # Images
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    
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
    
 
    def in_stock(self):
        return self.stock > 0
    
 
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_alert
    

    def discount_percentage(self):
        if self.cost_price and self.cost_price > self.price:
            return int(((self.cost_price - self.price) / self.cost_price) * 100)
        return 0

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
    
    province = models.CharField(max_length=20,null=True,blank=True)
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
    # Human readable estimated delivery summary preserved at order creation
    estimated_days = models.CharField(max_length=100, blank=True, null=True, help_text='Estimated delivery summary (e.g. 2-4 days)')
    
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

    def calculate_totals(self):
        """Re-calculate subtotal, shipping_cost, tax and total for this order
        based on current items snapshot and global TaxCost setting.
        This stores the calculated values on the order record (does not create items).
        """
        items = self.items.all()
        subtotal = sum((item.price * item.quantity) for item in items) if items else Decimal('0.00')
        shipping_total = sum((item.shipping_cost * item.quantity) for item in items) if items else Decimal('0.00')

        # Global tax percentage (TaxCost) – apply to (subtotal + shipping)
        try:
            tax_setting = TaxCost.objects.first()
            tax_pct = Decimal(tax_setting.tax) if tax_setting else Decimal('0.00')
        except Exception:
            tax_pct = Decimal('0.00')

        tax_amount = ((subtotal + shipping_total) * (tax_pct / Decimal('100.0'))).quantize(Decimal('0.01'))

        total_val = subtotal + shipping_total + tax_amount - (self.discount or Decimal('0.00'))

        # Update using update() to avoid recursion and signals being re-fired
        Order.objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            shipping_cost=shipping_total,
            tax=tax_amount,
            total=total_val
        )
        # Keep the instance in sync
        self.subtotal = subtotal
        self.shipping_cost = shipping_total
        self.tax = tax_amount
        self.total = total_val
        # store a readable estimated_days summary for the order
        try:
            estimates = list({(it.estimated_days or '').strip() for it in items if (it.estimated_days or '').strip()})
            est_text = ', '.join(sorted(estimates)) if estimates else None
            Order.objects.filter(pk=self.pk).update(estimated_days=est_text)
            self.estimated_days = est_text
        except Exception:
            pass


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
 
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Snapshot the per-item shipping cost and estimated delivery at time of order placement
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_days = models.CharField(max_length=50, blank=True, null=True)
    

    def get_total(self):
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        """
        Ensure we store a snapshot of per-product shipping_cost and estimated_days
        when an OrderItem is saved (created) so later changes to the Product
        don't affect historical orders.
        """
        if self.product:
            # If shipping_cost is zero or not set, copy from product
            try:
                if (self.shipping_cost is None or self.shipping_cost == 0) and hasattr(self.product, 'shipping_cost'):
                    self.shipping_cost = self.product.shipping_cost or 0
                if (not self.estimated_days) and hasattr(self.product, 'estimated_days'):
                    self.estimated_days = self.product.estimated_days
            except Exception:
                # Keep existing values on lookup issues
                pass
        super().save(*args, **kwargs)
    
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
class TaxCost(models.Model):
    """Global tax configuration used for checkout/order tax calculations.

    We removed the concept of a single global shipping cost (shipping is per-product)
    and keep a single global TaxCost (percentage) to apply to order totals.
    """
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Tax percentage (e.g. 13 for 13%)")

    class Meta:
        verbose_name = 'Tax Setting'
        verbose_name_plural = 'Tax Settings'

    def __str__(self):
        return f"Tax: {self.tax}%"


# -------------------------
#  Invoice
# -------------------------
class Invoice(models.Model):
    invoice_number = models.CharField(max_length=20,null=True, unique=True, editable=False)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='invoices')
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


# -------------------------
# Supplier Management
# -------------------------
class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True, help_text='Additional notes about the supplier')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


# -------------------------
# Purchase History (from Suppliers)
# -------------------------


class Purchase(models.Model):
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchases'
    )

    purchase_date = models.DateField(default=timezone.now)
    supplier_invoice_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Supplier invoice number'
    )
    purchase_order_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date', '-created_at']

    def save(self, *args, **kwargs):
        # 🔹 If supplier invoice number is not provided
        if not self.supplier_invoice_number:
            today = timezone.now().strftime('%Y%m%d')
            last_purchase = Purchase.objects.order_by('-id').first()
            next_id = (last_purchase.id + 1) if last_purchase else 1

            self.supplier_invoice_number = f"SUP-INV-{today}-{next_id:04d}"
            
        super().save(*args, **kwargs)
        
    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class PurchaseItem(models.Model):
    """Individual product items in a purchase order"""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    
    # Product reference (optional - product might be deleted)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_items')
    
    # Snapshot of product details at purchase time (to preserve history even if product changes)
    product_name = models.CharField(max_length=255, help_text='Product name at time of purchase')
    product_sku = models.CharField(max_length=100, blank=True, null=True, help_text='Product SKU at time of purchase')
    product_image = models.ImageField(upload_to='purchases/products/', blank=True, null=True, help_text='Product image at time of purchase')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price per unit paid to supplier')
    quantity = models.PositiveIntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def get_total(self):
        """Calculate total for this item"""
        return self.purchase_price * self.quantity
    
    def save(self, *args, **kwargs):
        # If product is linked, capture current product details as snapshot
        if self.product:
            if not self.product_name:
                self.product_name = self.product.name
            if not self.product_sku:
                self.product_sku = self.product.sku or ''
            # Note: product_image should be uploaded separately, not copied from product
            # This preserves the image that was uploaded at purchase time
        # Save the item first
        super().save(*args, **kwargs)
        # Recalculate purchase totals (only if purchase exists and is saved)
        # Use update_fields to avoid recursion
        if self.purchase and self.purchase.pk:
            try:
                # Refresh purchase from DB to ensure we have latest data
                self.purchase.refresh_from_db()
                self.purchase.calculate_totals()
            except Exception as e:
                # Log error but don't fail the save
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error calculating purchase totals: {e}")
    
    def delete(self, *args, **kwargs):
        purchase = self.purchase
        super().delete(*args, **kwargs)
        # Recalculate purchase totals after deletion
        if purchase:
            purchase.calculate_totals()
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity} - Rs. {self.get_total()}"


# -------------------------
# Purchase Invoice (for Supplier Purchases)
# -------------------------
class PurchaseInvoice(models.Model):
    """Invoice for purchases from suppliers - stores historical product and supplier data"""
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE, related_name='invoice')
    
    # Supplier snapshot (preserved even if supplier details change)
    supplier_name = models.CharField(max_length=200, help_text='Supplier name at time of purchase')
    supplier_email = models.EmailField(blank=True)
    supplier_phone = models.CharField(max_length=15, blank=True)
    supplier_address = models.TextField(blank=True)
    supplier_city = models.CharField(max_length=100, blank=True)
    
    # Purchase details snapshot
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Invoice details
    purchase_date = models.DateField()
    supplier_invoice_number = models.CharField(max_length=100, blank=True, help_text='Supplier invoice number')
    purchase_order_number = models.CharField(max_length=100, blank=True, help_text='Purchase order number')
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-purchase_date', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Format: PINV20250113123456
            self.invoice_number = f"PINV{timezone.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Purchase Invoice {self.invoice_number} - {self.supplier_name}"


class PurchaseInvoiceItem(models.Model):
    """Individual items in purchase invoice - stores historical product data"""
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='items')
    
    # Product snapshot (preserved even if product details change)
    product_name = models.CharField(max_length=255, help_text='Product name at time of purchase')
    product_sku = models.CharField(max_length=100, blank=True, null=True, help_text='Product SKU at time of purchase')
    product_image = models.ImageField(upload_to='purchase_invoice_items/', blank=True, null=True, help_text='Product image at time of purchase')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price per unit at time of purchase')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


# ===========================
#   Signals 
# ===========================


@receiver(post_save, sender=Order)
def handle_order_payment_status_change(sender, instance, created, **kwargs):
    """
    Handle order payment status changes:
    1. Auto-update order status to 'delivered' when payment is marked as 'paid'
    2. Sync invoice payment status with order payment status
    
    Uses update() to prevent signal recursion.
    """
    # Skip if this is a new order to avoid unnecessary processing
    if created:
        return
    
    # Auto-update order status to 'delivered' when payment is marked as 'paid'
    if instance.payment_status == 'paid':
        # Only update to delivered if order is not already cancelled or refunded or delivered
        if instance.status not in ['cancelled', 'refunded', 'delivered']:
            # Use update() to avoid triggering signals again (prevents recursion)
            Order.objects.filter(pk=instance.pk).update(
                status='delivered',
                delivered_at=timezone.now() if not instance.delivered_at else instance.delivered_at
            )
    
    # Sync invoice payment status with order payment status
    try:
        if instance.user:
            invoice = Invoice.objects.filter(order=instance, customer=instance.user).first()
            if invoice:
                invoice_status_map = {
                    "unpaid": "pending",
                    "paid": "paid",
                    "failed": "failed",
                    "refunded": "failed"
                }
                new_invoice_status = invoice_status_map.get(instance.payment_status, invoice.payment_status)
                if invoice.payment_status != new_invoice_status:
                    invoice.payment_status = new_invoice_status
                    invoice.save(update_fields=['payment_status'])
    except Exception:
        # Silently fail if invoice doesn't exist or other error
        pass


@receiver(post_save, sender=OrderItem)
def update_order_totals_on_item_change(sender, instance, created, **kwargs):
    """Recalculate Order totals whenever an OrderItem is created/updated."""
    try:
        if instance.order_id:
            instance.order.calculate_totals()
    except Exception:
        pass


from django.db.models.signals import post_delete


@receiver(post_delete, sender=OrderItem)
def update_order_totals_on_item_delete(sender, instance, **kwargs):
    try:
        if instance.order_id:
            order = Order.objects.filter(pk=instance.order_id).first()
            if order:
                order.calculate_totals()
    except Exception:
        pass


@receiver(post_save, sender=Order)
def ensure_order_items_snapshots(sender, instance, created, **kwargs):
    """Make sure any newly added order items have shipping snapshot filled.

    This is a best-effort to keep historical consistency for systems that
    create items directly after the order is saved.
    """
    try:
        for it in instance.items.all():
            if (not it.shipping_cost or it.shipping_cost == 0) or not it.estimated_days:
                it.save()
    except Exception:
        pass




@receiver(post_save, sender=Purchase)
def create_purchase_invoice(sender, instance, created, **kwargs):
    """
    Automatically create a purchase invoice when a purchase is created or updated with items.
    Stores snapshot of supplier and product details.
    """
    # Check if invoice already exists
    if hasattr(instance, 'invoice'):
        return
    
    # Only create invoice if purchase has items
    if not instance.items.exists():
        return
    
    # Capture supplier details snapshot
    supplier_name = instance.supplier.name if instance.supplier else 'Unknown Supplier'
    supplier_email = instance.supplier.email if instance.supplier else ''
    supplier_phone = instance.supplier.phone if instance.supplier else ''
    supplier_address = instance.supplier.address if instance.supplier else ''
    supplier_city = instance.supplier.city if instance.supplier else ''
    
    # Create invoice with totals from purchase
    invoice = PurchaseInvoice.objects.create(
        purchase=instance,
        supplier_name=supplier_name,
        supplier_email=supplier_email,
        supplier_phone=supplier_phone,
        supplier_address=supplier_address,
        supplier_city=supplier_city,
        subtotal=instance.subtotal,
        tax_amount=instance.tax_amount,
        discount=instance.discount,
        total_amount=instance.total_amount,
        purchase_date=instance.purchase_date,
        supplier_invoice_number=instance.supplier_invoice_number,
        purchase_order_number=instance.purchase_order_number,
        notes=instance.notes,
        payment_status='pending',
    )
    
    # Create invoice items from purchase items
    for item in instance.items.all():
        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            product_name=item.product_name,
            product_sku=item.product_sku or '',
            product_image=item.product_image,  # Copy image if available
            quantity=item.quantity,
            unit_price=item.purchase_price,
            total=item.get_total(),
        )
        
            
            
        


@receiver(post_save, sender=User)
def create_user_role_and_profile(sender, instance, created, **kwargs):
    """
    Automatically creates a UserRole and UserProfile
    when a new user (including superuser) is created.
    """

    # Run only when a new user is created
    if created and instance.is_superuser:
        UserRole.objects.get_or_create(role="admin",user=instance)
        UserProfile.objects.get_or_create(user=instance)
        print("created")


# ===========================
#   Sales Management (Physical/Offline)
# ===========================


# -------------------------
# Services Module
# -------------------------
class Service(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ServiceBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_bookings')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='bookings')
    booking_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service} - {self.customer.username} on {self.booking_date}"


class SaleCustomer(models.Model):
    """Customer records for offline/physical sales"""
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    
    def total_sales_amount(self):
        """Total amount of all sales for this customer"""
        return self.sales.aggregate(total=models.Sum('total_amount'))['total'] or Decimal('0.00')
    
    def total_paid_amount(self):
        """Total amount paid for this customer"""
        return self.sales.aggregate(total=models.Sum('paid_amount'))['total'] or Decimal('0.00')

    def total_outstanding_amount(self):
        """Total outstanding amount for this customer"""
        return self.sales.aggregate(total=models.Sum('outstanding_amount'))['total'] or Decimal('0.00')

    def sales_count(self):
        """Number of sales for this customer"""
        return self.sales.count()
    
    def payment_status(self):
        """Overall payment status"""
        if self.total_outstanding_amount == 0 and self.total_sales_amount > 0:
            return 'paid'
        elif self.total_outstanding_amount > 0 and self.total_paid_amount > 0:
            return 'partially_paid'
        elif self.total_outstanding_amount > 0:
            return 'unpaid'
        return 'unpaid'


class Sale(models.Model):
    """Offline/Physical Sales Record"""
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('unpaid', 'Unpaid'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit', 'Credit'),
    ]
    
    customer = models.ForeignKey(SaleCustomer, on_delete=models.CASCADE, related_name='sales')
    invoice_number = models.CharField(max_length=50, unique=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    outstanding_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_notes = models.TextField(blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sale #{self.invoice_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate outstanding amount and update payment status"""
        if not self.invoice_number:
            # Generate invoice number
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.invoice_number = f"SALE-{timestamp}"
        
        # Calculate outstanding amount
        self.outstanding_amount = self.total_amount - self.paid_amount
        
        # Update payment status
        if self.outstanding_amount <= 0:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partially_paid'
        else:
            self.payment_status = 'unpaid'
        
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    """Individual items in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate total amount"""
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class SalePayment(models.Model):
    """Payment records for sales"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Sale.PAYMENT_METHOD_CHOICES)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment of Rs.{self.amount} for Sale #{self.sale.invoice_number}"