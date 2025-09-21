from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.text import slugify
from ckeditor.fields import RichTextField
from django.utils import timezone
from datetime import timedelta

import os

# ----------------------
# User & Vendor Models
# ----------------------
class UserManager(BaseUserManager):
    def create_user(self, email, full_name,gender, phone_number=None, dob=None, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            dob=dob,
            gender=gender,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name,gender, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, full_name, gender, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    )
    email = models.EmailField(unique=True, db_index=True,null=True,blank=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, db_index=True,null=True,blank=True)
    dob = models.DateField(null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    is_active = models.BooleanField(default=True)
    is_vendor = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'gender']

    def __str__(self):
        return self.full_name


class KYC(models.Model):
    DOCUMENT_TYPES = (
        ('citizenship', 'Citizenship'),
        ('passport', 'Passport'),
        ('pan', 'PAN Certificate'),
        ('vat_certificate', 'VAT Certificate'),
    )
    pan_number = models.CharField(max_length=20, db_index=True)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='kyc_docs/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.document_type} - {self.pan_number}"


class VendorUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100, db_index=True)
    image = models.ImageField(upload_to='vendor/')
    kyc = models.ForeignKey(KYC, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        if self.image:
            os.remove(self.image.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.shop_name

# ----------------------
# Category Models
# ----------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} - {self.name}"

# ----------------------
# Attribute System
# ----------------------
class AttributeCategory(models.Model):
    """E.g., Color, Size, Material"""
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name


class Attribute(models.Model):
    """E.g., Red, Blue, M, L, Cotton"""
    attribute_category = models.ForeignKey(AttributeCategory, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('attribute_category', 'name')

    def __str__(self):
        return f"{self.attribute_category.name} : {self.name}"


class ProductAttribute(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} - {self.attribute}"

# ----------------------
# Flash Sale Model
# ----------------------
class FlashSale(models.Model):
    name = models.CharField(max_length=150)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def is_running(self):
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time


# -----------------
#  Banner
# -------------------
class Banner(models.Model):
    title=models.CharField(max_length=255,blank=True,null=True)
    image=models.ImageField(upload_to='banners/')
    link=models.URLField(blank=True,null=True)
    is_active=models.DateTimeField(auto_now_add=True)
    
    def delete(self,*args,**kwargs):
        if self.image:
            os.remove(self.image.path)
        super().save(*args,**kwargs)
        
    
    def __str__(self):
        return self.title or f"Banner {self.id}"
    

    
        

# --------------------
# Shipping Option
# ---------------------

class ShippingOption(models.Model):
    """Delivery options for products"""
    name = models.CharField(max_length=100)  # e.g., Standard Delivery, Express Delivery
    estimated_days = models.PositiveIntegerField(default=3)  # delivery estimate in days
    price = models.PositiveIntegerField(default=0)  # shipping fee
    cash_on_delivery = models.BooleanField(default=False)  # COD available
    created_at = models.DateTimeField(auto_now_add=True)

    def estimated_date_range(self):
        """Return estimated delivery date range"""
        start_date = timezone.now().date() + timedelta(days=self.estimated_days)
        end_date = start_date + timedelta(days=1)  # e.g., 1-day window
        return f"{start_date.strftime('%d-%b')} – {end_date.strftime('%d-%b')}"

    def __str__(self):
        return f"{self.name} - Rs. {self.price}"


# ----------------------
# Product Model
# ----------------------
class Product(models.Model):
    vendor = models.ForeignKey('VendorUser', on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey('SubCategory', on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, blank=True)
    description = RichTextField(blank=True, null=True)
    
    price = models.PositiveIntegerField(default=0)
    sales_price = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Flash sale related fields
    flash_sale = models.ForeignKey(FlashSale, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    flash_sale_approved = models.BooleanField(default=False)  # admin approval
    
    # Shipping options (many-to-many because a product can have multiple shipping methods)
    shipping_options = models.ManyToManyField(ShippingOption,  blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def discount_percentage(self):
        """Calculate discount tag"""
        if self.sales_price and self.sales_price < self.price:
            return int(((self.price - self.sales_price) / self.price) * 100)
        return 0

    def is_flash_sale_active(self):
        """Check if the product is in an active flash sale"""
        return self.flash_sale and self.flash_sale.is_running() and self.flash_sale_approved

    def __str__(self):
        return self.name

# ------------------
#  Product Image
# -------------------
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} Image"


# ------------------
#  Cart
# -------------------
class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    is_ordered=models.BooleanField(default=False)
    
    def total_price(self):
        sum=0
        for item in self.cart_items.all():
            sum += item.sub_total()
        return sum
            
    
    def __str__(self):
        return f" Cart {self.user.full_name} "
    

#-------------------
#  Cart Items
# ------------------ 
class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='cart_items')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    added_at=models.DateTimeField(auto_now_add=True)
    
    def unit_price(self):
        if self.product.is_flash_sale_active():
            return self.product.sales_price
        if self.product.sales_price and  self.product.sales_price < self.product.price:
            return self.product.sales_price
        return self.product.price
    
    def sub_total(self):
        return self.unit_price() * self.quantity
    
    def __str__(self):
        return f" Cart Items {self.product.name}"



# --------------------------
#  Shipping Address
# -------------------------
class ShippingAddress(models.Model):
    STATE_CHOICES = (
        ('bagmati', 'Bagmati'),
        ('gandaki', 'Gandaki'),
        ('karnali', 'Karnali'),
        ('lumbini', 'Lumbini'),
        ('madhesh', 'Madhesh'),
        ('province1', 'Province 1'),
        ('sudurpaschim', 'Sudurpaschim')
    )
    country=models.CharField(max_length=50,default="Nepal")
    state = models.CharField(max_length=50, choices=STATE_CHOICES)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    address_line1=models.CharField(max_length=255)
    address_line2=models.CharField(max_length=255)
    city=models.CharField(max_length=100)
    state=models.CharField(max_length=50,choices=STATE_CHOICES)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.full_name} -{self.address_line1}"
    
    
    
    
# ------------------------
#  Order
# -----------------------
class Order(models.Model):
    STATUS_CHOICES=(
        ('pending','Pending'),
        ('processing','Processing'),
        ('shipped','Shipped'),
        ('delivered','Delivered'),
        ('cancelled','Cancelled')
    )

    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    total_price=models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    status=models.CharField(max_length=50,choices=STATUS_CHOICES,default='pending')
    payment_method=models.CharField(max_length=100 ,null=True,blank=True)
    shipping_address=models.ForeignKey(ShippingAddress,on_delete=models.CASCADE)
    order_at=models.DateTimeField(auto_now_add=True)
    
    def save(self,*args,**kwargs):
        if self.product.sales_price< self.product.price:
            self.total_price=self.product.sales_price * self.quantity
        else:
            self.total_price=self.product.price * self.quantity
        super().save(*args,**kwargs)
            
        if self.status in ['delivered']:
            if self.product.quantity>=self.quantity:
                self.product.quantity -= self.quantity
                self.product.save()
        
        
        
        
        
    

    
    
    # ===== Here whne status is delivedred or shipped remove the product from database or make inactive ========= )
    # ======== See webiste that  i medtioned in note file =================
    # ======= Crate  a tags like New Arrivalsand others
    #======== Create a banner from differnt section in home page =============
    # =====  In category after the banner in home page show top 6 most sales list of category ========
    # ======== In featured products add Load more ================
    # ======think needed to add top vendor of feature vendor in home page ===========
    