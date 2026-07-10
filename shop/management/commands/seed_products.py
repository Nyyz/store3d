import os
import shutil
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from api.models import Product


PRODUCTS_DATA = [
    {
        'name': 'Дракон Вогняний Страж',
        'description': (
            'Величезний дракон у бойовій позі з розкритими крилами та язиками полумʼя. '
            'Висота 18 см. Деталізація лусок та крил вражає реалістичністю. '
            'Виготовлений з PLA-пластику з ручним фарбуванням у відтінках червоного та золотого.'
        ),
        'price': 1450.00,
        'stock': 12,
        'image_filename': 'dragon.webp',
    },
    {
        'name': 'Кіберсамурай 2077',
        'description': (
            'Футуристичний самурай у кібернетичному обладунку з неоновими елементами. '
            'Висота 15 см. Комбінація традиційної японської естетики з sci-fi деталями. '
            'LED-елементи на обладунку світяться в темряві (батарейки входять у комплект).'
        ),
        'price': 1850.00,
        'stock': 8,
        'image_filename': 'cybersamurai.webp',
    },
    {
        'name': 'Ельфійська Лучниця',
        'description': (
            'Витончена ельфійка з довгим луком у динамічній позі. '
            'Висота 16 см. Деталі включають плащ з тонкою текстурою, '
            'колчан зі стрілами та вінок з листя у волоссі. Фарбування пастельними тонами.'
        ),
        'price': 1250.00,
        'stock': 15,
        'image_filename': 'elf_archer.webp',
    },
    {
        'name': 'Космічний Десантник',
        'description': (
            'Важкоозброєний космічний десантник в потужному силовому обладунку. '
            'Висота 14 см. Масивна фігурка з високим рівнем деталізації обладунку, '
            'зброї та знаків відмінності підрозділу. Ідеальна для настільних ігор.'
        ),
        'price': 980.00,
        'stock': 25,
        'image_filename': 'space_marine.webp',
    },
    {
        'name': 'Некромант Тіней',
        'description': (
            'Темний маг у довгій мантії, що підносить руку з магічною сферою. '
            'Висота 17 см. Навколо фігурки закручені вихори темної магії та духи. '
            'Вишукана деталізація елементів одягу та магічних ефектів.'
        ),
        'price': 1680.00,
        'stock': 6,
        'image_filename': 'necromancer.webp',
    },
    {
        'name': 'Меха-Робот «Титан»',
        'description': (
            'Гігантський бойовий робот у стилі японських аніме. '
            'Висота 22 см — найбільша фігурка колекції! '
            'Рухомі зʼєднання рук та ніг. Деталізація панелей корпусу, '
            'ракетних установок та кокпіту пілота. Розбірна модель із 5 частин.'
        ),
        'price': 2450.00,
        'stock': 4,
        'image_filename': 'mecha_titan.webp',
    },
    {
        'name': 'Відьмак з Рівії',
        'description': (
            'Легендарний мисливець на монстрів із двома мечами за спиною. '
            'Висота 16 см. Детальне опрацювання обладунку, шрамів на обличчі, '
            'медальйона вовка та ефектів магічного знаку Ігні. Ексклюзивний тираж.'
        ),
        'price': 1990.00,
        'stock': 3,
        'image_filename': 'witcher.webp',
    },
    {
        'name': 'Стімпанк Інженерка',
        'description': (
            'Дівчина-інженер у стімпанк стилі з механічною рукою та гогглами. '
            'Висота 14 см. Безліч дрібних деталей: шестерні, труби, інструменти. '
            'Підставка у вигляді робочого столу з кресленнями та пристроями.'
        ),
        'price': 1350.00,
        'stock': 10,
        'image_filename': 'steampunk.webp',
    },
    {
        'name': 'Крижаний Фенікс',
        'description': (
            'Міфічний птах із крижаними крилами розмахом 20 см. '
            'Виготовлений з напівпрозорого синього PLA з ефектом льоду. '
            'Крила мають внутрішню LED-підсвітку (USB-кабель у комплекті). '
            'Ексклюзивна лімітована серія — всього 50 одиниць.'
        ),
        'price': 2890.00,
        'stock': 2,
        'image_filename': 'ice_phoenix.webp',
    },
]


class Command(BaseCommand):
    help = 'Заповнює базу демо-товарами для Store3D'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистити всі існуючі товари перед заповненням',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Product.objects.count()
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Видалено {count} товарів.'))

        # Створення директорії для зображень
        products_media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        os.makedirs(products_media_dir, exist_ok=True)

        # Копіювання зображень з seed_images, якщо вони є
        seed_images_dir = os.path.join(settings.BASE_DIR, 'shop', 'seed_images')

        created_count = 0
        for data in PRODUCTS_DATA:
            # Перевірка чи товар вже існує
            if Product.objects.filter(name=data['name']).exists():
                self.stdout.write(f'  ⏭️  "{data["name"]}" вже існує, пропускаю.')
                continue

            product = Product(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                stock=data['stock'],
            )

            # Спроба додати зображення
            image_filename = data.get('image_filename', '')
            seed_image_path = os.path.join(seed_images_dir, image_filename) if image_filename else ''

            if seed_image_path and os.path.exists(seed_image_path):
                with open(seed_image_path, 'rb') as img_file:
                    product.image.save(image_filename, File(img_file), save=False)
                self.stdout.write(f'  🖼️  Зображення додано для "{data["name"]}"')

            product.save()
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'  ✅ Створено: "{data["name"]}" — {data["price"]} ₴'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'🎉 Готово! Створено {created_count} нових товарів.'))
        self.stdout.write(f'   Всього в базі: {Product.objects.count()} товарів.')
