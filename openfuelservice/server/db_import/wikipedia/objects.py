class CarObject(object):
    def __init__(self, hash_id, category_short_eu: str, brand_name: str, car_name: str, page_id=None, wiki_name=None,
                 page_language=None):
        self.hash_id = hash_id
        self.wiki_name = wiki_name
        self.category_short_eu = category_short_eu
        self.brand_name = brand_name
        self.car_name = car_name
        self.page_id = page_id
        self.page_language = page_language


class CarCategoryObject(object):
    def __init__(self, category_name_de, category_name_en, category_short_eu):
        self.category_name_de = category_name_de
        self.category_name_en = category_name_en
        self.category_short_eu = category_short_eu


class WikiCarPageTextObject(object):
    def __init__(self, brand_name: str, car_name: str, wiki_name=None, page_text: str = None, page_language: str = None,
                 category_short_eu: str = None):
        self.wiki_name = wiki_name
        self.brand_name = brand_name
        self.car_name = car_name
        self.page_text = page_text
        self.page_language = page_language
        self.category_short_eu = category_short_eu
