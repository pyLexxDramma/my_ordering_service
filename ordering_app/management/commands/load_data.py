import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from ordering_app.models import Supplier, Category, Product

class Command(BaseCommand):
    help = 'Загружает данные из YML файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument('yaml_file', type=str, help='Путь к YML файлу с данными')

    def handle(self, *args, **options):
        yaml_file_path = options['yaml_file']

        try:
            with open(yaml_file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
        except FileNotFoundError:
            raise CommandError(f'Файл "{yaml_file_path}" не найден.')
        except yaml.YAMLError:
            raise CommandError(f'Ошибка при парсинге YML файла "{yaml_file_path}".')

        if not data:
            self.stdout.write(self.style.WARNING('YML файл пуст или не содержит данных.'))
            return

        shop_name = data.get('shop')
        supplier = None
        if shop_name:
            try:
                supplier, created = Supplier.objects.get_or_create(name=shop_name)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Создан или найден поставщик (магазин): {supplier.name}"))
                else:
                    self.stdout.write(f"Поставщик '{supplier.name}' уже существует.")
            except IntegrityError:
                self.stderr.write(self.style.ERROR(f"Ошибка целостности данных для поставщика '{shop_name}'. Возможно, дубликат."))
        else:
            self.stderr.write(self.style.ERROR("В YML файле не указано поле 'shop' для определения поставщика."))

        categories_data = data.get('categories', [])
        self.stdout.write(f"Найдено {len(categories_data)} категорий для загрузки.")
        for cat_data in categories_data:
            try:
                category, created = Category.objects.get_or_create(
                    external_id=cat_data['id'],
                    defaults={'name': cat_data['name']}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Создана категория: {category.name} (ID: {category.external_id})"))
                else:
                    self.stdout.write(f"Категория '{category.name}' уже существует.")
            except KeyError as e:
                self.stderr.write(self.style.ERROR(f"Ошибка в данных категории: отсутствует поле {e} в {cat_data}"))
            except IntegrityError:
                self.stderr.write(self.style.ERROR(f"Ошибка целостности данных для категории с ID {cat_data.get('id')}. Возможно, дубликат."))

        products_data = data.get('goods', [])
        self.stdout.write(f"Найдено {len(products_data)} товаров для загрузки.")
        for prod_data in products_data:
            try:
                current_supplier = supplier

                category_id = prod_data.get('category')
                category = None
                if category_id:
                    category = Category.objects.filter(external_id=category_id).first()
                    if not category:
                        self.stderr.write(self.style.WARNING(f"Категория с ID {category_id} для товара '{prod_data.get('name')}' не найдена. Товар будет создан без категории."))

                product_sku = prod_data.get('sku')
                product = None

                if product_sku:
                    product, product_created = Product.objects.get_or_create(
                        sku=product_sku,
                        defaults={
                            'name': prod_data['name'],
                            'description': prod_data.get('description'),
                            'price': prod_data['price'],
                            'supplier': current_supplier,
                            'category': category,
                            'stock_quantity': prod_data.get('quantity', 0)
                        }
                    )
                    if product_created:
                        self.stdout.write(self.style.SUCCESS(f"Создан товар по SKU: {product.name} ({product.sku})"))
                    else:
                        product.name = prod_data['name']
                        product.description = prod_data.get('description')
                        product.price = prod_data['price']
                        product.supplier = current_supplier
                        product.category = category
                        product.stock_quantity = prod_data.get('quantity', 0)
                        product.save()
                        self.stdout.write(f"Обновлен товар по SKU: {product.name} ({product.sku})")
                else:
                    existing_product = Product.objects.filter(
                        name=prod_data['name'],
                        supplier=current_supplier,
                        category=category
                    ).first()

                    if existing_product:
                        product = existing_product
                        product.description = prod_data.get('description')
                        product.price = prod_data['price']
                        product.stock_quantity = prod_data.get('quantity', 0)
                        if product.supplier != current_supplier:
                             product.supplier = current_supplier
                        if product.category != category:
                            product.category = category
                        product.save()
                        self.stdout.write(f"Обновлен товар (найден по имени): {product.name}")
                    else:
                        product = Product.objects.create(
                            name=prod_data['name'],
                            description=prod_data.get('description'),
                            price=prod_data['price'],
                            supplier=current_supplier,
                            category=category,
                            sku=None,
                            stock_quantity=prod_data.get('quantity', 0)
                        )
                        self.stdout.write(self.style.SUCCESS(f"Создан новый товар: {product.name}"))

            except KeyError as e:
                self.stderr.write(self.style.ERROR(f"Ошибка в данных товара: отсутствует поле {e} в {prod_data}"))
            except IntegrityError:
                self.stderr.write(self.style.ERROR(f"Ошибка целостности данных для товара '{prod_data.get('name')}'. Возможно, дубликат SKU или другая проблема."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Непредвиденная ошибка при обработке товара {prod_data.get('name')}: {e}"))

        self.stdout.write(self.style.SUCCESS('Загрузка данных завершена.'))
