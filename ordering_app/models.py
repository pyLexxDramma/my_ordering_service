from django.db import models
from django.conf import settings
from django.utils import timezone


class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название поставщика")
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="Контактное лицо")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Поставщики"


class ProductAttribute(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название характеристики")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Характеристика товара"
        verbose_name_plural = "Характеристики товара"


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название товара")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name="products", verbose_name="Поставщик")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=255, verbose_name="Значение")

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"

    class Meta:
        verbose_name = "Значение характеристики товара"
        verbose_name_plural = "Значения характеристик товара"
        unique_together = ('product', 'attribute')


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('confirmed', 'Подтвержден'),
        ('processing', 'Обрабатывается'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders", verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Общая сумма")

    def __str__(self):
        return f"Заказ №{self.pk} от {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} (Заказ №{self.order.pk})"

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"

    def get_item_total(self):
        return self.quantity * self.price