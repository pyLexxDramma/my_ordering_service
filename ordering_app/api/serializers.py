from rest_framework import serializers
from ordering_app.models import Product, Supplier, Category, ProductAttribute, ProductAttributeValue


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
    characteristics = ProductAttributeValueSerializer(many=True, source='attribute_values',
                                                      read_only=True)

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
        read_only_fields = ['supplier', 'category',
                            'characteristics']
