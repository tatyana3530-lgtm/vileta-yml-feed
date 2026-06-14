import xml.etree.ElementTree as ET
import urllib.request
import os

# URL оригинального YML с Тильды
YML_SOURCE = "https://vileta.ru/tstore/yml/d0c79023fb412afffa0f9411671cd622.yml"

# Category IDs — Распашные
CAT_RASP    = "630962611542"
CAT_RASP_1  = "661777141122"  # Однодверные
CAT_RASP_2  = "951467927032"  # Двухдверные
CAT_RASP_3  = "642509673332"  # Трехдверные
CAT_RASP_4  = "835727302272"  # Четырехдверные

# Category IDs — Книжные
CAT_BOOK    = "948362801802"
CAT_BOOK_1  = "844966021672"  # Однодверные книжные
CAT_BOOK_2  = "275441089652"  # Двухдверные книжные

# Категории верхнего уровня (должны ссылаться на All)
CAT_ALL     = "593339166932"
TOP_LEVEL   = (CAT_RASP, CAT_BOOK, "195652040962", "267808129302", "764217904632")

# Страницы каталога для микроразметки Яндекс.Директ
CATALOG_PAGES = [
    ("https://vileta.ru/catalog/",                          CAT_ALL),
    ("https://vileta.ru/shkafy-raspashnye/",                CAT_RASP),
    ("https://vileta.ru/shkafy-odnodvernye/",               CAT_RASP_1),
    ("https://vileta.ru/shkafy-dvukhdvernye/",              CAT_RASP_2),
    ("https://vileta.ru/shkafy-trekhdvernye/",              CAT_RASP_3),
    ("https://vileta.ru/shkafy-chetyrekhdvernye/",          CAT_RASP_4),
    ("https://vileta.ru/shkafy-knizhnyye/",                 CAT_BOOK),
    ("https://vileta.ru/shkafy-knizhnyye-odnodvernye/",     CAT_BOOK_1),
    ("https://vileta.ru/shkafy-knizhnyye-dvukhdvernye/",    CAT_BOOK_2),
    ("https://vileta.ru/shkafy-s-yashikami/",               "764217904632"),
]


def get_rasp_category(width):
    if width <= 60:
        return CAT_RASP_1
    elif width <= 120:
        return CAT_RASP_2
    elif width <= 180:
        return CAT_RASP_3
    else:
        return CAT_RASP_4


def get_book_category(width):
    if width <= 60:
        return CAT_BOOK_1
    else:
        return CAT_BOOK_2


def main():
    print(f"Downloading YML from {YML_SOURCE}...")
    urllib.request.urlretrieve(YML_SOURCE, "source.yml")

    ET.register_namespace('', '')
    tree = ET.parse("source.yml")
    root = tree.getroot()
    shop = root.find('shop')
    offers = shop.find('offers')

    fixed = 0
    for offer in offers.findall('offer'):
        name_el = offer.find('name')
        cat_el  = offer.find('categoryId')
        if name_el is None or cat_el is None:
            continue

        name        = name_el.text or ''
        current_cat = cat_el.text or ''

        width = None
        for param in offer.findall('param'):
            if param.get('name') == 'Ширина':
                try:
                    width = int(param.text)
                except Exception:
                    pass
                break

        if width is None:
            continue

        is_book = current_cat == CAT_BOOK or 'книж' in name.lower() or 'витрин' in name.lower()
        is_rasp = current_cat == CAT_RASP or 'распашн' in name.lower()

        if is_book:
            new_cat = get_book_category(width)
        elif is_rasp:
            new_cat = get_rasp_category(width)
        else:
            continue

        if cat_el.text != new_cat:
            cat_el.text = new_cat
            fixed += 1

    print(f"Fixed {fixed} offers")

    categories = shop.find('categories')
    for cat in categories.findall('category'):
        if cat.get('id') in TOP_LEVEL and cat.get('parentId') is None:
            cat.set('parentId', CAT_ALL)
            print(f"Added parentId to: {cat.text}")

    # Блок <pages> для микроразметки каталогов
    pages_el = ET.SubElement(shop, 'pages')
    for i, (url, cat_id) in enumerate(CATALOG_PAGES, start=1):
        page_el = ET.SubElement(pages_el, 'page')
        page_el.set('id', str(i))
        url_el = ET.SubElement(page_el, 'url')
        url_el.text = url
        type_el = ET.SubElement(page_el, 'page-type')
        type_el.text = 'catalog'
        cat_el = ET.SubElement(page_el, 'category-id')
        cat_el.text = cat_id

    print(f"Added {len(CATALOG_PAGES)} catalog pages")

    os.makedirs("docs", exist_ok=True)
    tree.write("docs/feed.yml", xml_declaration=True, encoding='UTF-8')
    print("Saved to docs/feed.yml")


if __name__ == "__main__":
    main()
