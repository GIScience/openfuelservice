from typing import Dict, AnyStr


class DataMappings(object):
    def __init__(self):
        """
        This class will hold all possible mappings for the entire project.
        Subclasses are allowed if necessary but it is better to include everything in one class.
        The getter functions will return the valid mapping or false! if none is found.
        """
        self.fuel_type_mappings: Dict[AnyStr, AnyStr] = {'diesel': ['diesel'],
                                                         'diesel_electric': ['diesel electric',
                                                                             'electricity / diesel',
                                                                             'Electricity / Diesel'],
                                                         'gasoline': ['gasoline', 'Petrol', 'gas'],
                                                         'gasoline_electric': ['gasoline_electric',
                                                                               'electricity / petrol',
                                                                               'Electricity / Petrol',
                                                                               'petrol electric', 'petrol hybrid'],
                                                         'electric': ['Electricity']}

    def get_fuel_type(self, fuel_type_to_check: str) -> object:
        """
        Get the correct fuel type mapping.
        :param fuel_type_to_check: String holding the fuel type to check against the mapping
        :return: String holding the correct mapped fuel type or False
        """
        check_to_lower = fuel_type_to_check.casefold().strip()
        mapping: str
        for mapping in self.fuel_type_mappings:
            if check_to_lower == mapping.casefold().strip():
                return mapping
            sub_mapping: str
            for sub_mapping in self.fuel_type_mappings[mapping]:
                if check_to_lower == sub_mapping.casefold().strip():
                    return mapping
        print("Couldn't find fuel_type_mapping for:", str(fuel_type_to_check))
        return False