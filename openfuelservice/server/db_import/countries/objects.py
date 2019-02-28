class CountryObject(object):
    def __init__(self, country_name, country_alpha_2, country_alpha_3, country_numeric, country_currency_code,
                 country_currency_name, geom):
        self.country_name = country_name
        self.country_alpha_2 = country_alpha_2
        self.country_alpha_3 = country_alpha_3
        self.country_numeric = country_numeric
        self.country_currency_code = country_currency_code
        self.country_currency_name = country_currency_name
        self.geom = 'SRID=4326;' + geom.__str__()
