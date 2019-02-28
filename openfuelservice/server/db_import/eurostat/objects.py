from shapely.geometry import Polygon


class CountryPrice(object):
    def __init__(self, date, country_alpha_2, taux, euro_price, euro_ht, euro_ttc, diesel_ht, diesel_ttc,
                 euro_unit, euro_quantity, diesel_unit, diesel_quantity):
        self.date = date
        self.country_alpha_2 = country_alpha_2
        self.taux = taux
        self.euro_price = euro_price
        self.euro_ht = euro_ht
        self.euro_ttc = euro_ttc
        self.euro_unit = euro_unit
        self.euro_quantity = euro_quantity
        self.diesel_ht = diesel_ht
        self.diesel_ttc = diesel_ttc
        self.diesel_unit = diesel_unit
        self.diesel_quantity = diesel_quantity


class CountryPriceExtended(CountryPrice):
    def __init__(self, date, country_alpha_2, taux, euro_price, euro_ht, euro_ttc, diesel_ht, diesel_ttc,
                 euro_unit, euro_quantity, diesel_unit, diesel_quantity, geom: Polygon):
        super().__init__(date=date,
                         country_alpha_2=country_alpha_2,
                         taux=taux,
                         euro_price=euro_price,
                         euro_ht=euro_ht,
                         euro_ttc=euro_ttc,
                         euro_unit=euro_unit,
                         euro_quantity=euro_quantity,
                         diesel_ht=diesel_ht,
                         diesel_ttc=diesel_ttc,
                         diesel_unit=diesel_unit,
                         diesel_quantity=diesel_quantity)
        self.geom: Polygon = geom

    def get_country_price_object(self) -> CountryPrice:
        return CountryPrice(
            date=self.date,
            country_alpha_2=self.country_alpha_2,
            taux=self.taux,
            euro_price=self.euro_price,
            euro_ht=self.euro_ht,
            euro_ttc=self.euro_ttc,
            euro_unit=self.euro_unit,
            euro_quantity=self.euro_quantity,
            diesel_ht=self.diesel_ht,
            diesel_ttc=self.diesel_ttc,
            diesel_unit=self.diesel_unit,
            diesel_quantity=self.diesel_quantity
        )


class GeneralPrice(object):
    def __init__(self, date, euro_price, euro_ht, euro_ttc, diesel_ht, diesel_ttc, euro_unit, diesel_unit,
                 euro_quantity, diesel_quantity):
        self.date = date
        self.euro_price = euro_price
        self.euro_ht = euro_ht
        self.euro_ttc = euro_ttc
        self.euro_unit = euro_unit
        self.euro_quantity = euro_quantity
        self.diesel_ht = diesel_ht
        self.diesel_ttc = diesel_ttc
        self.diesel_unit = diesel_unit
        self.diesel_quantity = diesel_quantity
