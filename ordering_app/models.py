from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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

class Category(models.Model):
    external_id = models.IntegerField(unique=True, verbose_name="Внешний ID категории")
    name = models.CharField(max_length=255, verbose_name="Название категории")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название товара")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name="products", verbose_name="Поставщик")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products", verbose_name="Категория")
    sku = models.CharField(max_length=255, verbose_name="Артикул (SKU)", blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

class ProductAttribute(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название характеристики")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Характеристика товара"
        verbose_name_plural = "Характеристики товара"

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

class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer', verbose_name=_("User"))
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Phone Number"))
    address = models.TextField(blank=True, null=True, verbose_name=_("Delivery Address"))

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', _('New')),
        ('confirmed', _('Confirmed')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('returned', _('Returned')),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name=_("User"))
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name=_("Customer"))
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("Total Amount"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name=_("Status"))
    shipping_address = models.TextField(blank=True, null=True, verbose_name=_("Shipping Address"))
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Phone Number"))

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()} ({self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_("Order"))
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items', verbose_name=_("Product"))
    product_name = models.CharField(max_length=255, verbose_name=_("Product Name"), default='Unknown Product')
    supplier_name = models.CharField(max_length=255, verbose_name=_("Supplier Name"), default='Unknown Supplier')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"), default=0.00)
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Order #{self.order.id})"

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def get_item_total(self):
        return self.price * self.quantity

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart', verbose_name=_("User"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date Created"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Last Updated"))

    def __str__(self):
        return f"Cart of {self.user.email}"

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")

    def get_total_price(self):
        total = sum(item.get_item_total() for item in self.items.all())
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Cart ID: {self.cart.pk})"

    class Meta:
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")
        unique_together = ('cart', 'product')

    def get_item_total(self):
        return self.quantity * self.product.price