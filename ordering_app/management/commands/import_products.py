import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.utils import IntegrityError
from django.conf import settings

from ordering_app.models import Product, Supplier, Category, ProductAttribute, ProductAttributeValue

class Command(BaseCommand):
    help = 'Imports products, categories, and related data from a specific YAML file structure.'

    def add_arguments(self, parser):
        parser.add_argument('yaml_file', type=str, help='The path to the YAML file to import.')
        parser.add_argument('--create-suppliers', action='store_true', help='Create suppliers if they do not exist based on the "shop" field.')
        parser.add_argument('--update', action='store_true', help='Update existing products if they are found by SKU.')

    def handle(self, *args, **options):
        yaml_file_path = options['yaml_file']
        create_suppliers = options['create_suppliers']
        update_existing = options['update']

        try:
            with open(yaml_file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
        except FileNotFoundError:
            raise CommandError(f'File "{yaml_file_path}" not found.')
        except yaml.YAMLError as e:
            raise CommandError(f'Error parsing YAML file: {e}')

        if not data:
            self.stdout.write(self.style.WARNING('YAML file is empty. No data to import.'))
            return

        supplier_name_from_yaml = data.get('shop')
        categories_data = data.get('categories', [])
        goods_data = data.get('goods', [])

        if not supplier_name_from_yaml:
            raise CommandError('YAML file must contain a "shop" field for the supplier.')
        if not goods_data:
            self.stdout.write(self.style.WARNING('No "goods" found in the YAML file. Nothing to import.'))
            return

        with transaction.atomic():
            supplier_instance = None
            try:
                supplier_instance = Supplier.objects.get(name=supplier_name_from_yaml)
                self.stdout.write(f"Found existing supplier: '{supplier_name_from_yaml}'")
            except Supplier.DoesNotExist:
                if create_suppliers:
                    supplier_instance = Supplier.objects.create(name=supplier_name_from_yaml)
                    self.stdout.write(self.style.SUCCESS(f"Created new supplier: '{supplier_name_from_yaml}'"))
                else:
                    raise CommandError(
                        f"Supplier '{supplier_name_from_yaml}' not found. Use --create-suppliers flag to create it automatically."
                    )

            category_map = {}
            for cat_data in categories_data:
                external_id = cat_data.get('id')
                name = cat_data.get('name')
                if not external_id or not name:
                    self.stdout.write(self.style.WARNING(f"Skipping category with missing 'id' or 'name': {cat_data}"))
                    continue

                try:
                    category_instance, created = Category.objects.get_or_create(external_id=external_id, defaults={'name': name})
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created new category: '{name}' (ID: {external_id})"))
                    else:
                        if category_instance.name != name:
                            category_instance.name = name
                            category_instance.save()
                            self.stdout.write(f"Updated category name for ID {external_id} to '{name}'")
                    category_map[external_id] = category_instance
                except IntegrityError:
                    self.stdout.write(self.style.ERROR(f"Integrity error creating category with external_id {external_id}. Skipping."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"An unexpected error occurred processing category {external_id}: {e}"))

            for item_data in goods_data:
                product_name = item_data.get('name')
                product_sku = item_data.get('model')
                category_external_id = item_data.get('category')

                if not product_name or not product_sku or not category_external_id:
                    self.stdout.write(self.style.WARNING(f"Skipping item due to missing 'name', 'model' (SKU), or 'category': {item_data}"))
                    continue

                category_instance = category_map.get(category_external_id)
                if not category_instance:
                    self.stdout.write(self.style.WARNING(f"Category with external ID {category_external_id} not found for product '{product_name}'. Skipping product."))
                    continue

                product_instance = None
                if update_existing:
                    try:
                        product_instance = Product.objects.get(sku=product_sku, supplier=supplier_instance)
                        self.stdout.write(f"Found existing product: '{product_name}' (SKU: {product_sku})")
                    except Product.DoesNotExist:
                        pass
                    except Product.MultipleObjectsReturned:
                        self.stdout.write(self.style.ERROR(f"Multiple products found with SKU '{product_sku}' and supplier '{supplier_instance.name}'. Cannot determine which to update. Skipping."))
                        continue

                price = item_data.get('price')
                stock_quantity = item_data.get('quantity', 0)
                description = item_data.get('name')

                try:
                    price_decimal = float(price) if price is not None else 0.0
                except (ValueError, TypeError):
                    self.stdout.write(self.style.WARNING(f"Invalid price '{price}' for product '{product_name}' (SKU: {product_sku}). Setting price to 0.00"))
                    price_decimal = 0.0

                if product_instance:
                    product_instance.name = product_name
                    product_instance.description = description
                    product_instance.price = price_decimal
                    product_instance.stock_quantity = stock_quantity
                    product_instance.category = category_instance
                    product_instance.supplier = supplier_instance
                    product_instance.save()
                    self.stdout.write(self.style.SUCCESS(f"Successfully updated product: '{product_name}' (SKU: {product_sku})"))
                else:
                    try:
                        product_instance = Product.objects.create(
                            name=product_name,
                            description=description,
                            price=price_decimal,
                            supplier=supplier_instance,
                            category=category_instance,
                            sku=product_sku,
                            stock_quantity=stock_quantity,
                        )
                        self.stdout.write(self.style.SUCCESS(f"Successfully created product: '{product_name}' (SKU: {product_sku})"))
                    except IntegrityError:
                        self.stdout.write(self.style.ERROR(f"Product with SKU '{product_sku}' already exists but was not found by update logic. Skipping creation."))
                        continue

                attributes_data = item_data.get('parameters', {})
                ProductAttributeValue.objects.filter(product=product_instance).delete()

                for attr_name, attr_value in attributes_data.items():
                    if attr_value is None:
                        continue

                    attr_value_str = str(attr_value)

                    try:
                        attribute_instance, created = ProductAttribute.objects.get_or_create(name=attr_name)
                        if created:
                            self.stdout.write(f"Created new product attribute: '{attr_name}'")

                        ProductAttributeValue.objects.create(
                            product=product_instance,
                            attribute=attribute_instance,
                            value=attr_value_str
                        )
                    except IntegrityError:
                        self.stdout.write(self.style.ERROR(f"Integrity error processing attribute '{attr_name}' for product '{product_name}' (SKU: {product_sku})."))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"An unexpected error occurred processing attribute '{attr_name}' for product '{product_name}' (SKU: {product_sku}): {e}"))

        self.stdout.write(self.style.SUCCESS('Product import process finished.'))