from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet)

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),

    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),

    path('cart/', views.CartDetailView.as_view(), name='cart-detail'),
    path('cart/items/', views.CartItemCreateUpdateView.as_view(), name='cart-item-create-update'),
    path('cart/items/<int:pk>/', views.CartItemDeleteView.as_view(), name='cart-item-delete'),

    path('', include(router.urls)),
]