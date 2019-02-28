class CarFuelDataCarObject(object):
    def __init__(self, manufacturer=None, model=None, description=None, transmission=None, engine_capacity=None,
                 fuel_type=None, e_consumption_miles_per_kWh=None, e_consumption_wh_per_km=None, maximum_range_km=None,
                 maximum_range_miles=None, metric_urban_cold=None, metric_extra_urban=None, metric_combined=None,
                 imperial_urban_cold=None, imperial_extra_urban=None, imperial_combined=None, co2_g_per_km=None,
                 fuel_cost_6000_miles=None, fuel_cost_12000_miles=None, electricity_cost=None,
                 total_cost_per_12000_miles=None, euro_standard=None, noise_level_dB_a_=None,
                 emissions_co_mg_per_km=None, thc_emissions_mg_per_km=None, emissions_nox_mg_per_km=None,
                 thc_plus_nox_emissions_mg_per_km=None, particulates_no_mg_per_km=None, rde_nox_urban=None,
                 rde_nox_combined=None, year=None, date_of_change=None, wiki_hashes: [] = None):
        self.manufacturer = manufacturer
        self.model = model
        self.description = description
        self.transmission = transmission
        self.engine_capacity = engine_capacity
        self.fuel_type = fuel_type
        self.e_consumption_miles_per_kWh = e_consumption_miles_per_kWh
        self.e_consumption_wh_per_km = e_consumption_wh_per_km
        self.maximum_range_km = maximum_range_km
        self.maximum_range_miles = maximum_range_miles
        self.metric_urban_cold = metric_urban_cold
        self.metric_extra_urban = metric_extra_urban
        self.metric_combined = metric_combined
        self.imperial_urban_cold = imperial_urban_cold
        self.imperial_extra_urban = imperial_extra_urban
        self.imperial_combined = imperial_combined
        self.co2_g_per_km = co2_g_per_km
        self.fuel_cost_6000_miles = fuel_cost_6000_miles
        self.fuel_cost_12000_miles = fuel_cost_12000_miles
        self.electricity_cost = electricity_cost
        self.total_cost_per_12000_miles = total_cost_per_12000_miles
        self.euro_standard = euro_standard
        self.noise_level_dB_a_ = noise_level_dB_a_
        self.emissions_co_mg_per_km = emissions_co_mg_per_km
        self.thc_emissions_mg_per_km = thc_emissions_mg_per_km
        self.emissions_nox_mg_per_km = emissions_nox_mg_per_km
        self.thc_plus_nox_emissions_mg_per_km = thc_plus_nox_emissions_mg_per_km
        self.particulates_no_mg_per_km = particulates_no_mg_per_km
        self.rde_nox_urban = rde_nox_urban
        self.rde_nox_combined = rde_nox_combined
        self.date_of_change = date_of_change
        self.year = year
        self.wiki_hashes = wiki_hashes
