import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from users.models import *

# -------------------------
# USER CRUD
# -------------------------
def user_list(request):
    users = User.objects.all()
    return render(request, 'admin_dashboard/user_list.html', {'users': users})


def user_create(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        dob = request.POST.get('dob')
        password = request.POST.get('password')
        is_vendor = request.POST.get('is_vendor') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        user = User(
            email=email,
            full_name=full_name,
            gender=gender,
            phone_number=phone_number,
            dob=dob if dob else None,
            is_vendor=is_vendor,
            is_staff=is_staff
        )
        if password:
            user.set_password(password)
        user.save()
        messages.success(request, "User created successfully")
        return redirect('admin_user_list')
    return render(request, 'admin_dashboard/user_create.html')


def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.full_name = request.POST.get('full_name')
        user.gender = request.POST.get('gender')
        user.phone_number = request.POST.get('phone_number')
        dob = request.POST.get('dob')
        user.dob = dob if dob else None
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        user.is_vendor = request.POST.get('is_vendor') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.save()
        messages.success(request, "User updated successfully")
        return redirect('admin_user_list')
    return render(request, 'admin_dashboard/user_update.html', {'user': user})


def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "User deleted successfully")
        return redirect('admin_user_list')
    return render(request, 'admin_dashboard/user_delete.html', {'user': user})


# -------------------------
# VENDOR USER CRUD
# -------------------------
def vendor_list(request):
    vendors = VendorUser.objects.all()
    return render(request, 'admin_dashboard/vendor_list.html', {'vendors': vendors})


def vendor_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        shop_name = request.POST.get('shop_name')
        kyc_id = request.POST.get('kyc')
        image = request.FILES.get('image')
        user = User.objects.get(id=user_id)
        kyc = KYC.objects.get(id=kyc_id)
        vendor = VendorUser.objects.create(
            user=user,
            shop_name=shop_name,
            kyc=kyc,
            image=image,
            is_active=request.POST.get('is_active') == 'on'
        )
        messages.success(request, "Vendor created successfully")
        return redirect('admin_vendor_list')

    users = User.objects.filter(is_vendor=True)
    kycs = KYC.objects.all()
    return render(request, 'admin_dashboard/vendor_create.html', {'users': users, 'kycs': kycs})


def vendor_update(request, pk):
    vendor = get_object_or_404(VendorUser, pk=pk)
    if request.method == 'POST':
        vendor.shop_name = request.POST.get('shop_name')
        kyc_id = request.POST.get('kyc')
        vendor.kyc = KYC.objects.get(id=kyc_id)
        image = request.FILES.get('image')
        if image:
            if vendor.image and os.path.isfile(vendor.image.path):
                os.remove(vendor.image.path)
            vendor.image = image
        vendor.is_active = request.POST.get('is_active') == 'on'
        vendor.save()
        messages.success(request, "Vendor updated successfully")
        return redirect('admin_vendor_list')

    users = User.objects.filter(is_vendor=True)
    kycs = KYC.objects.all()
    return render(request, 'admin_dashboard/vendor_update.html', {
        'vendor': vendor,
        'users': users,
        'kycs': kycs
    })


def vendor_delete(request, pk):
    vendor = get_object_or_404(VendorUser, pk=pk)
    if request.method == 'POST':
        if vendor.image and os.path.isfile(vendor.image.path):
            os.remove(vendor.image.path)
        vendor.delete()
        messages.success(request, "Vendor deleted successfully")
        return redirect('admin_vendor_list')
    return render(request, 'admin_dashboard/vendor_delete.html', {'vendor': vendor})


# -------------------------
# KYC CRUD
# -------------------------
def kyc_list(request):
    kycs = KYC.objects.all()
    return render(request, 'admin_dashboard/kyc_list.html', {'kycs': kycs})


def kyc_create(request):
    if request.method == 'POST':
        pan_number = request.POST.get('pan_number')
        document_type = request.POST.get('document_type')
        document_file = request.FILES.get('document_file')
        kyc = KYC.objects.create(
            pan_number=pan_number,
            document_type=document_type,
            document_file=document_file,
            verified=request.POST.get('verified') == 'on'
        )
        messages.success(request, "KYC document added successfully")
        return redirect('admin_kyc_list')
    return render(request, 'admin_dashboard/kyc_create.html')


def kyc_update(request, pk):
    kyc = get_object_or_404(KYC, pk=pk)
    if request.method == 'POST':
        kyc.pan_number = request.POST.get('pan_number')
        kyc.document_type = request.POST.get('document_type')
        document_file = request.FILES.get('document_file')
        if document_file:
            if kyc.document_file and os.path.isfile(kyc.document_file.path):
                os.remove(kyc.document_file.path)
            kyc.document_file = document_file
        kyc.verified = request.POST.get('verified') == 'on'
        kyc.save()
        messages.success(request, "KYC updated successfully")
        return redirect('admin_kyc_list')
    return render(request, 'admin_dashboard/kyc_update.html', {'kyc': kyc})


def kyc_delete(request, pk):
    kyc = get_object_or_404(KYC, pk=pk)
    if request.method == 'POST':
        if kyc.document_file and os.path.isfile(kyc.document_file.path):
            os.remove(kyc.document_file.path)
        kyc.delete()
        messages.success(request, "KYC deleted successfully")
        return redirect('admin_kyc_list')
    return render(request, 'admin_dashboard/kyc_delete.html', {'kyc': kyc})


# -------------------------
# PRODUCT CRUD
# -------------------------
def product_list(request):
    products = Product.objects.all()
    return render(request, 'admin_dashboard/product_list.html', {'products': products})


def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        vendor_id = request.POST.get('vendor')
        price = int(request.POST.get('price', 0))
        sales_price = int(request.POST.get('sales_price', 0))
        quantity = int(request.POST.get('quantity', 0))
        low_stock_threshold = int(request.POST.get('low_stock_threshold', 10))
        is_featured = request.POST.get('is_featured') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        description = request.POST.get('description', '')
        flash_sale_id = request.POST.get('flash_sale')
        flash_sale_approved = request.POST.get('flash_sale_approved') == 'on'

        category = Category.objects.get(id=category_id) if category_id else None
        subcategory = SubCategory.objects.get(id=subcategory_id) if subcategory_id else None
        vendor = VendorUser.objects.get(id=vendor_id) if vendor_id else None
        flash_sale = FlashSale.objects.get(id=flash_sale_id) if flash_sale_id else None

        product = Product.objects.create(
            name=name,
            slug=slugify(name),
            category=category,
            subcategory=subcategory,
            vendor=vendor,
            price=price,
            sales_price=sales_price,
            quantity=quantity,
            low_stock_threshold=low_stock_threshold,
            is_featured=is_featured,
            is_active=is_active,
            description=description,
            flash_sale=flash_sale,
            flash_sale_approved=flash_sale_approved
        )
        messages.success(request, "Product created successfully")
        return redirect('admin_product_list')

    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    vendors = VendorUser.objects.all()
    flash_sales = FlashSale.objects.all()
    return render(request, 'admin_dashboard/product_create.html', {
        'categories': categories,
        'subcategories': subcategories,
        'vendors': vendors,
        'flash_sales': flash_sales
    })


def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.slug = slugify(product.name)
        product.price = int(request.POST.get('price', 0))
        product.sales_price = int(request.POST.get('sales_price', 0))
        product.quantity = int(request.POST.get('quantity', 0))
        product.low_stock_threshold = int(request.POST.get('low_stock_threshold', 10))
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.is_active = request.POST.get('is_active') == 'on'
        product.description = request.POST.get('description', '')
        flash_sale_id = request.POST.get('flash_sale')
        product.flash_sale = FlashSale.objects.get(id=flash_sale_id) if flash_sale_id else None
        product.flash_sale_approved = request.POST.get('flash_sale_approved') == 'on'

        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        vendor_id = request.POST.get('vendor')
        product.category = Category.objects.get(id=category_id) if category_id else None
        product.subcategory = SubCategory.objects.get(id=subcategory_id) if subcategory_id else None
        product.vendor = VendorUser.objects.get(id=vendor_id) if vendor_id else None

        product.save()
        messages.success(request, "Product updated successfully")
        return redirect('admin_product_list')

    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    vendors = VendorUser.objects.all()
    flash_sales = FlashSale.objects.all()
    return render(request, 'admin_dashboard/product_update.html', {
        'product': product,
        'categories': categories,
        'subcategories': subcategories,
        'vendors': vendors,
        'flash_sales': flash_sales
    })


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully")
        return redirect('admin_product_list')
    return render(request, 'admin_dashboard/product_delete.html', {'product': product})

# -------------------------
# CATEGORY CRUD
# -------------------------
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'admin_dashboard/category_list.html', {'categories': categories})


def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        Category.objects.create(name=name, description=description)
        messages.success(request, "Category created successfully")
        return redirect('admin_category_list')
    return render(request, 'admin_dashboard/category_create.html')


def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.save()
        messages.success(request, "Category updated successfully")
        return redirect('admin_category_list')
    return render(request, 'admin_dashboard/category_update.html', {'category': category})


def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully")
        return redirect('admin_category_list')
    return render(request, 'admin_dashboard/category_delete.html', {'category': category})



# -------------------------
# ATTRIBUTE CATEGORY CRUD
# -------------------------
def attribute_category_list(request):
    categories = AttributeCategory.objects.all()
    return render(request, 'admin_dashboard/attribute_category_list.html', {'categories': categories})


def attribute_category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            AttributeCategory.objects.create(name=name)
            messages.success(request, "Attribute category created successfully")
        return redirect('admin_attribute_category_list')
    return render(request, 'admin_dashboard/attribute_category_create.html')


def attribute_category_update(request, pk):
    category = get_object_or_404(AttributeCategory, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.save()
        messages.success(request, "Attribute category updated successfully")
        return redirect('admin_attribute_category_list')
    return render(request, 'admin_dashboard/attribute_category_update.html', {'category': category})


def attribute_category_delete(request, pk):
    category = get_object_or_404(AttributeCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Attribute category deleted successfully")
        return redirect('admin_attribute_category_list')
    return render(request, 'admin_dashboard/attribute_category_delete.html', {'category': category})


# -------------------------
# ATTRIBUTE CRUD
# -------------------------
def attribute_list(request):
    attributes = Attribute.objects.all()
    return render(request, 'admin_dashboard/attribute_list.html', {'attributes': attributes})


def attribute_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('attribute_category')
        category = AttributeCategory.objects.get(id=category_id) if category_id else None
        if name and category:
            Attribute.objects.create(name=name, attribute_category=category)
            messages.success(request, "Attribute created successfully")
        return redirect('admin_attribute_list')

    categories = AttributeCategory.objects.all()
    return render(request, 'admin_dashboard/attribute_create.html', {'categories': categories})


def attribute_update(request, pk):
    attribute = get_object_or_404(Attribute, pk=pk)
    if request.method == 'POST':
        attribute.name = request.POST.get('name')
        category_id = request.POST.get('attribute_category')
        attribute.attribute_category = AttributeCategory.objects.get(id=category_id) if category_id else None
        attribute.save()
        messages.success(request, "Attribute updated successfully")
        return redirect('admin_attribute_list')

    categories = AttributeCategory.objects.all()
    return render(request, 'admin_dashboard/attribute_update.html', {'attribute': attribute, 'categories': categories})


def attribute_delete(request, pk):
    attribute = get_object_or_404(Attribute, pk=pk)
    if request.method == 'POST':
        attribute.delete()
        messages.success(request, "Attribute deleted successfully")
        return redirect('admin_attribute_list')
    return render(request, 'admin_dashboard/attribute_delete.html', {'attribute': attribute})


# -------------------------
# PRODUCT ATTRIBUTE CRUD
# -------------------------
def product_attribute_list(request):
    product_attributes = ProductAttribute.objects.all()
    return render(request, 'admin_dashboard/product_attribute_list.html', {'product_attributes': product_attributes})


def product_attribute_create(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        attribute_id = request.POST.get('attribute')
        product = Product.objects.get(id=product_id) if product_id else None
        attribute = Attribute.objects.get(id=attribute_id) if attribute_id else None
        if product and attribute:
            ProductAttribute.objects.create(product=product, attribute=attribute)
            messages.success(request, "Product Attribute added successfully")
        return redirect('admin_product_attribute_list')

    products = Product.objects.all()
    attributes = Attribute.objects.all()
    return render(request, 'admin_dashboard/product_attribute_create.html', {'products': products, 'attributes': attributes})


def product_attribute_delete(request, pk):
    pa = get_object_or_404(ProductAttribute, pk=pk)
    if request.method == 'POST':
        pa.delete()
        messages.success(request, "Product Attribute deleted successfully")
        return redirect('admin_product_attribute_list')
    return render(request, 'admin_dashboard/product_attribute_delete.html', {'product_attribute': pa})


# -------------------------
# BANNER CRUD
# -------------------------
def banner_list(request):
    banners = Banner.objects.all()
    return render(request, 'admin_dashboard/banner_list.html', {'banners': banners})


def banner_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        link = request.POST.get('link')
        image = request.FILES.get('image')
        if image:
            Banner.objects.create(title=title, link=link, image=image)
            messages.success(request, "Banner created successfully")
        return redirect('admin_banner_list')
    return render(request, 'admin_dashboard/banner_create.html')


def banner_update(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        banner.title = request.POST.get('title')
        banner.link = request.POST.get('link')
        image = request.FILES.get('image')
        if image:
            if banner.image and os.path.isfile(banner.image.path):
                os.remove(banner.image.path)
            banner.image = image
        banner.save()
        messages.success(request, "Banner updated successfully")
        return redirect('admin_banner_list')
    return render(request, 'admin_dashboard/banner_update.html', {'banner': banner})


def banner_delete(request, pk):
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        if banner.image and os.path.isfile(banner.image.path):
            os.remove(banner.image.path)
        banner.delete()
        messages.success(request, "Banner deleted successfully")
        return redirect('admin_banner_list')
    return render(request, 'admin_dashboard/banner_delete.html', {'banner': banner})




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cart, CartItem, Order, ShippingAddress, User, Product

# -------------------------
# CART CRUD
# -------------------------
def cart_list(request):
    carts = Cart.objects.all()
    return render(request, 'admin_dashboard/cart_list.html', {'carts': carts})


def cart_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        user = User.objects.get(id=user_id) if user_id else None
        if user:
            Cart.objects.create(user=user)
            messages.success(request, "Cart created successfully")
        return redirect('admin_cart_list')
    users = User.objects.all()
    return render(request, 'admin_dashboard/cart_create.html', {'users': users})


def cart_update(request, pk):
    cart = get_object_or_404(Cart, pk=pk)
    if request.method == 'POST':
        cart.is_ordered = request.POST.get('is_ordered') == 'on'
        cart.save()
        messages.success(request, "Cart updated successfully")
        return redirect('admin_cart_list')
    return render(request, 'admin_dashboard/cart_update.html', {'cart': cart})


def cart_delete(request, pk):
    cart = get_object_or_404(Cart, pk=pk)
    if request.method == 'POST':
        cart.delete()
        messages.success(request, "Cart deleted successfully")
        return redirect('admin_cart_list')
    return render(request, 'admin_dashboard/cart_delete.html', {'cart': cart})


# -------------------------
# CART ITEM CRUD
# -------------------------
def cart_item_list(request):
    items = CartItem.objects.all()
    return render(request, 'admin_dashboard/cart_item_list.html', {'items': items})


def cart_item_create(request):
    if request.method == 'POST':
        cart_id = request.POST.get('cart')
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))
        cart = Cart.objects.get(id=cart_id) if cart_id else None
        product = Product.objects.get(id=product_id) if product_id else None
        if cart and product:
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)
            messages.success(request, "Cart item added successfully")
        return redirect('admin_cart_item_list')

    carts = Cart.objects.all()
    products = Product.objects.all()
    return render(request, 'admin_dashboard/cart_item_create.html', {'carts': carts, 'products': products})


def cart_item_update(request, pk):
    item = get_object_or_404(CartItem, pk=pk)
    if request.method == 'POST':
        item.quantity = int(request.POST.get('quantity', 1))
        product_id = request.POST.get('product')
        cart_id = request.POST.get('cart')
        item.product = Product.objects.get(id=product_id) if product_id else item.product
        item.cart = Cart.objects.get(id=cart_id) if cart_id else item.cart
        item.save()
        messages.success(request, "Cart item updated successfully")
        return redirect('admin_cart_item_list')

    carts = Cart.objects.all()
    products = Product.objects.all()
    return render(request, 'admin_dashboard/cart_item_update.html', {'item': item, 'carts': carts, 'products': products})


def cart_item_delete(request, pk):
    item = get_object_or_404(CartItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Cart item deleted successfully")
        return redirect('admin_cart_item_list')
    return render(request, 'admin_dashboard/cart_item_delete.html', {'item': item})


# -------------------------
# SHIPPING ADDRESS CRUD
# -------------------------
def shipping_list(request):
    addresses = ShippingAddress.objects.all()
    return render(request, 'admin_dashboard/shipping_list.html', {'addresses': addresses})


def shipping_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        user = User.objects.get(id=user_id) if user_id else None
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country', 'Nepal')
        if user:
            ShippingAddress.objects.create(
                user=user,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                country=country
            )
            messages.success(request, "Shipping address created successfully")
        return redirect('admin_shipping_list')
    users = User.objects.all()
    return render(request, 'admin_dashboard/shipping_create.html', {'users': users})


def shipping_update(request, pk):
    address = get_object_or_404(ShippingAddress, pk=pk)
    if request.method == 'POST':
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country', 'Nepal')
        user_id = request.POST.get('user')
        address.user = User.objects.get(id=user_id) if user_id else address.user
        address.save()
        messages.success(request, "Shipping address updated successfully")
        return redirect('admin_shipping_list')
    users = User.objects.all()
    return render(request, 'admin_dashboard/shipping_update.html', {'address': address, 'users': users})


def shipping_delete(request, pk):
    address = get_object_or_404(ShippingAddress, pk=pk)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Shipping address deleted successfully")
        return redirect('admin_shipping_list')
    return render(request, 'admin_dashboard/shipping_delete.html', {'address': address})


# -------------------------
# ORDER CRUD
# -------------------------
def order_list(request):
    orders = Order.objects.all()
    return render(request, 'admin_dashboard/order_list.html', {'orders': orders})


def order_create(request):
    if request.method == 'POST':
        user_id = request.POST.get('user')
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))
        shipping_id = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status', 'pending')

        user = User.objects.get(id=user_id) if user_id else None
        product = Product.objects.get(id=product_id) if product_id else None
        shipping = ShippingAddress.objects.get(id=shipping_id) if shipping_id else None

        if user and product and shipping:
            order = Order.objects.create(
                user=user,
                product=product,
                quantity=quantity,
                shipping_address=shipping,
                payment_method=payment_method,
                status=status
            )
            messages.success(request, "Order created successfully")
        return redirect('admin_order_list')

    users = User.objects.all()
    products = Product.objects.all()
    shippings = ShippingAddress.objects.all()
    return render(request, 'admin_dashboard/order_create.html', {
        'users': users,
        'products': products,
        'shippings': shippings
    })


def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.quantity = int(request.POST.get('quantity', order.quantity))
        order.status = request.POST.get('status', order.status)
        order.payment_method = request.POST.get('payment_method', order.payment_method)

        user_id = request.POST.get('user')
        product_id = request.POST.get('product')
        shipping_id = request.POST.get('shipping_address')

        order.user = User.objects.get(id=user_id) if user_id else order.user
        order.product = Product.objects.get(id=product_id) if product_id else order.product
        order.shipping_address = ShippingAddress.objects.get(id=shipping_id) if shipping_id else order.shipping_address

        order.save()
        messages.success(request, "Order updated successfully")
        return redirect('admin_order_list')

    users = User.objects.all()
    products = Product.objects.all()
    shippings = ShippingAddress.objects.all()
    return render(request, 'admin_dashboard/order_update.html', {
        'order': order,
        'users': users,
        'products': products,
        'shippings': shippings
    })


def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, "Order deleted successfully")
        return redirect('admin_order_list')
    return render(request, 'admin_dashboard/order_delete.html', {'order': order})

