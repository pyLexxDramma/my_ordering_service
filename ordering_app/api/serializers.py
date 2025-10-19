from rest_framework import serializers
from django.contrib.auth import get_user_model
from ordering_app.models import Product, Supplier, Category, ProductAttribute, ProductAttributeValue, Cart, CartItem

User = get_user_model()

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)

    class Meta:
        model = ProductAttributeValue
        fields = ('attribute_name', 'value')

class ProductSerializer(serializers.ModelSerializer):
    supplier = serializers.CharField(source='supplier.name', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    characteristics = ProductAttributeValueSerializer(many=True, source='attribute_values', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'supplier',
            'category',
            'characteristics',
            'price',
            'stock_quantity',
        ]
        read_only_fields = ['supplier', 'category', 'characteristics']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'password_confirm')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают."})

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Пользователь с таким email уже существует."})

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    supplier_name = serializers.CharField(source='product.supplier.name', read_only=True)
    price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    item_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product_name',
            'supplier_name',
            'price',
            'quantity',
            'item_total'
        ]
        read_only_fields = ['item_total']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'updated_at', 'items', 'total_price']
        read_only_fields = ['user', 'created_at', 'updated_at', 'items', 'total_price']