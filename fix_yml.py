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

    os.makedirs("docs", exist_ok=True)
    tree.write("docs/feed.yml", xml_declaration=True, encoding='UTF-8')
    print("Saved to docs/feed.yml")


if __name__ == "__main__":
    main()
