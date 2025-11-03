# # ========================================
# #     Mobile App API Views
# # ========================================
# from django.shortcuts import get_object_or_404
# from dashboard.models import Product, Cart, Order,UserProfile, OrderItem
# from django.contrib.auth.models import User


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.simplejwt.authentication import JWTAuthentication
# from rest_framework.simplejwt.tokens import RefreshToken


# class LoginApiView(APIView):
#     def post(self,request):
#         try:
#             email=request.data.get('email')
#             password=request.data.get('password')
#             try:
#                 user=User.objects.get(email=email)
#             except User.DoesNotExist:
#                 return Response({'success':False,'error':'User not found'},status=400)
#         except Exception as e:
#             return Response({'success':False,'error':str(e)},status=400)
