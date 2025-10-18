from django.contrib import admin
from .models import Supplier, Product, Category, ProductAttribute, ProductAttributeValue, Order, OrderItem

admin.site.register(Supplier)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductAttribute)
admin.site.register(ProductAttributeValue)
admin.site.register(Order)
admin.site.register(OrderItem)