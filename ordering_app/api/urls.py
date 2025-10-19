from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),

    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),

    path('cart/', views.CartDetailView.as_view(), name='cart-detail'),
    path('cart/items/', views.CartItemCreateUpdateView.as_view(), name='cart-item-create-update'),
    path('cart/items/update/<int:pk>/', views.CartItemUpdateView.as_view(), name='cart-item-update'),
    path('cart/items/<int:pk>/', views.CartItemDeleteView.as_view(), name='cart-item-delete'),
]