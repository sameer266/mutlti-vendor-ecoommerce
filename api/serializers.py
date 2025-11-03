from dashboard.models import Product, Cart, Order,UserProfile, OrderItem
from django.contrib.auth.models import User
from rest_framework import serializers


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'in_stock', 'category', 'created_at', 'updated_at'] 
        
        
        
class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'quantity', 'added_at']  
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'order_number', 'total_amount', 'status', 'created_at', 'updated_at']
        
        