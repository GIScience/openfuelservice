import numpy as np
from tqdm import tqdm

from openfuelservice.server import ofs_settings
from openfuelservice.server.statistics.objects import AverageEnviroCarVehicleTypeStatisticObject, \
    AverageEnviroCarManufacturerStatisticObject

model_measurements_threshold = ofs_settings['statistics_provider']['envirocar_provider']['model_measurements_threshold']


class AverageStatistics:
    """This class holds all the functions to calculate the average statistics from the envirocar data


    Every function will serve a different average statistic.
    - av_vehicle_type_statistics: This function will calculate the per vehicle type average statistics. E.g. car,...
    - av_enginge_statistics: This function will calculate the per engine statistics.
    - av_model_statistics: This function will calculate the per model statistics.
    - av_manufacturer_statistics: This function will calculate the per manufacturer statistics.

    """

    @staticmethod
    def av_vehicle_type_statistics(sensors: dict, phenomenons: dict) -> []:
        """
        This function calculates the average statistics for all vehicle types delivered by envirocar. E.g. car, motor-cicle etc.
        At the moment there is only "car" in the database of envirocar. Let's hope it changes soon.

        :param sensors: Takes a list of the crawled sensors.
        :param phenomenons: Takes a list of the crawled phenomenons
        :return: The return will be a per vehicle type ordered list of the average phenomenons values
        """
        # Holding the final data
        av_vehicle_type_statistics = []
        # Holding the temporary data
        type_statistics = dict()
        # Diversity table to show the amounts of sensors per fuel type
        div_table = dict()
        # Iterate over each sensor in sensors
        for sensor in tqdm(sensors, total=len(sensors), unit=' Calculating Sensor Statistics'):
            # Get the vehicle type
            vehicle_type = sensors[sensor]['type']
            # Get the fuel type
            fuel_type = sensors[sensor]['fuel_type']
            # Add to diversity tables
            if fuel_type in div_table:
                if sensor not in div_table[fuel_type]:
                    div_table[fuel_type].append(sensor)
            else:
                div_table[fuel_type] = []
                div_table[fuel_type].append(sensor)

            if vehicle_type not in type_statistics:
                type_statistics[vehicle_type] = dict()

            if fuel_type not in type_statistics[vehicle_type]:
                type_statistics[vehicle_type][fuel_type] = dict()

            # Check for each phenomenon and its values in each sensor
            for phenomenon in phenomenons:
                if 'statistics' in sensors[sensor]:
                    if phenomenon in sensors[sensor]['statistics']:
                        phenomenon_value = sensors[sensor]['statistics'][phenomenon]
                        # Get the phenomenon value and add it to the list
                        if phenomenon not in type_statistics[vehicle_type][fuel_type]:
                            type_statistics[vehicle_type][fuel_type][phenomenon] = []
                            type_statistics[vehicle_type][fuel_type][phenomenon].append(phenomenon_value)
                        else:
                            type_statistics[vehicle_type][fuel_type][phenomenon].append(phenomenon_value)

        # Now generate the average statistics for each vehicle type
        # and for each phenomenon and add it to the type av_vehicle_type_statistics
        # The weighted arithmetic average is used, to reduce the impact of extreme values
        # The weights are the amounts of measurements for each phenomenon value
        # TODO add the distinction for vehicle type and fuel type per vehicle type (its not finished)
        # TODO add generalized data for vehicle types (besides the specific general data in the fueltypes)
        for vehicle_type in tqdm(type_statistics, total=len(type_statistics),
                                 unit=' Calculating Vehicle Type Statistics'):
            for fuel_type in type_statistics[vehicle_type]:
                for phenomenon in type_statistics[vehicle_type][fuel_type]:

                    max = []
                    average = []
                    min = []
                    phenomenon_weights = []
                    # Access the single values in the phenomenon
                    for value in type_statistics[vehicle_type][fuel_type][phenomenon]:
                        max.append(value['max'][0])
                        average.append(value['avg'][0])
                        min.append(value['min'][0]) if float(value['min'][0]) > 0 else min.append(0)
                        phenomenon_weights.append(value['measurements'][0])

                    # Create the averaged and weighted phenomenon statistics
                    av_vehicle_type_statistics.append(AverageEnviroCarVehicleTypeStatisticObject(
                        vehicle_type=vehicle_type,
                        fuel_type=fuel_type,
                        phenomenon=phenomenon,
                        max=np.average(max, weights=phenomenon_weights),
                        average=np.average(average, weights=phenomenon_weights),
                        min=np.average(min, weights=phenomenon_weights),
                        measurements=sum(phenomenon_weights),
                        numb_sensors=len(div_table[fuel_type])
                    ))
        return av_vehicle_type_statistics

    # TODO
    @staticmethod
    def av_manufacturer_statistics(sensors, phenomenons):
        # Holding the final data
        av_man_statistics = []
        # Holding the temporary data
        man_statistics = dict()
        # Diversity table to show the amounts of sensors per manufacturer
        div_table = dict()
        # Iterate over each sensor in sensors
        for sensor in tqdm(sensors, total=len(sensors), unit=' Calculating Sensor Statistics'):
            if 'statistics' in sensors[sensor]:
                # Get the manufacturer
                manufacturer = sensors[sensor]['manufacturer'].casefold().strip()
                # Get the vehicle type
                vehicle_type = sensors[sensor]['type'].casefold().strip()
                # Get the fuel type
                fuel_type = sensors[sensor]['fuel_type'].casefold().strip()
                # Add data to the diversity tables
                if manufacturer is not "":
                    if manufacturer not in div_table:
                        div_table[manufacturer] = dict()
                    if vehicle_type not in div_table[manufacturer]:
                        div_table[manufacturer][vehicle_type] = dict()
                    if fuel_type in div_table[manufacturer][vehicle_type]:
                        if sensor not in div_table[manufacturer][vehicle_type][fuel_type]:
                            div_table[manufacturer][vehicle_type][fuel_type].append(sensor)
                    else:
                        div_table[manufacturer][vehicle_type][fuel_type] = []
                        div_table[manufacturer][vehicle_type][fuel_type].append(sensor)

                    # Fill the temporary statistics dict
                    if manufacturer not in man_statistics:
                        man_statistics[manufacturer] = dict()
                    if vehicle_type not in man_statistics[manufacturer]:
                        man_statistics[manufacturer][vehicle_type] = dict()
                    if fuel_type not in man_statistics[manufacturer][vehicle_type]:
                        man_statistics[manufacturer][vehicle_type][fuel_type] = dict()

                    # Check for each phenomenon and its values in each sensor
                    for phenomenon in phenomenons:
                        if 'statistics' in sensors[sensor]:
                            if phenomenon in sensors[sensor]['statistics']:
                                phenomenon_value = sensors[sensor]['statistics'][phenomenon]
                                # Get the phenomenon value and add it to the list
                                if phenomenon not in man_statistics[manufacturer][vehicle_type][fuel_type]:
                                    man_statistics[manufacturer][vehicle_type][fuel_type][phenomenon] = []
                                    man_statistics[manufacturer][vehicle_type][fuel_type][phenomenon].append(
                                        phenomenon_value)
                                else:
                                    man_statistics[manufacturer][vehicle_type][fuel_type][phenomenon].append(
                                        phenomenon_value)

        for manufacturer in tqdm(man_statistics, total=len(man_statistics),
                                 unit=' Calculating Manufacturer Statistics'):
            for vehicle_type in man_statistics[manufacturer]:
                for fuel_type in man_statistics[manufacturer][vehicle_type]:
                    for phenomenon in man_statistics[manufacturer][vehicle_type][fuel_type]:

                        max = []
                        average = []
                        min = []
                        phenomenon_weights = []
                        # Access the single values in the phenomenon
                        for value in man_statistics[manufacturer][vehicle_type][fuel_type][phenomenon]:
                            max.append(value['max'][0])
                            average.append(value['avg'][0])
                            min.append(value['min'][0]) if float(value['min'][0]) > 0 else min.append(0)
                            phenomenon_weights.append(value['measurements'][0])
                        min = np.average(min, weights=phenomenon_weights)
                        if phenomenon.casefold().strip() == 'co2' and min < 0:
                            min = 0
                        if phenomenon.casefold().strip() == 'speed' and min < 0:
                            min = 0
                        if sum(phenomenon_weights) >= model_measurements_threshold:
                            # Create the averaged and weighted phenomenon statistics
                            av_man_statistics.append(AverageEnviroCarManufacturerStatisticObject(
                                manufacturer=manufacturer,
                                vehicle_type=vehicle_type,
                                fuel_type=fuel_type,
                                phenomenon=phenomenon,
                                max=np.average(max, weights=phenomenon_weights),
                                average=np.average(average, weights=phenomenon_weights),
                                min=min,
                                measurements=sum(phenomenon_weights),
                                numb_sensors=len(div_table[manufacturer][vehicle_type][fuel_type])
                            ))
        return av_man_statistics



