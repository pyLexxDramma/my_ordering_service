import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import Product, Category, Cart, CartItem, Order, Customer


@pytest.mark.django_db
class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(name='Test Product', category=self.category, price=100)
        self.customer = Customer.objects.create(user=self.user)
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.order = Order.objects.create(user=self.user, customer=self.customer, total_amount=200)

    def test_models_creation(self):
        assert str(self.category) == 'Test Category'
        assert str(self.product) == 'Test Product'
        assert isinstance(self.cart, Cart)
        assert isinstance(self.cart_item, CartItem)
        assert isinstance(self.order, Order)

    def test_cart_total_price(self):
        expected_total = self.cart_item.quantity * self.product.price
        assert expected_total == self.cart.get_total()

    def test_order_total_price(self):
        assert self.order.total_amount == 200


@pytest.mark.django_db
class APITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.client.force_authenticate(user=self.user)

    def test_get_products_list(self):
        response = self.client.get(reverse('product-list'))
        assert response.status_code == status.HTTP_200_OK

    def test_register_new_user(self):
        new_user_data = {'username': 'newuser', 'email': 'new@example.com', 'password': 'password'}
        response = self.client.post(reverse('register'), new_user_data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_login_user(self):
        auth_data = {'username': 'testuser', 'password': 'password'}
        response = self.client.post(reverse('login'), auth_data)
        assert response.status_code == status.HTTP_200_OK

    def test_add_to_cart(self):
        product = Product.objects.create(name='Test Product', price=100)
        add_to_cart_url = reverse('cart-item-create-update')
        payload = {'product_id': product.pk, 'quantity': 2}
        response = self.client.post(add_to_cart_url, payload)
        assert response.status_code == status.HTTP_201_CREATED