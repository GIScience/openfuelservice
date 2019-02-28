import csv

import yaml


def write_csvlist_to_yaml(input_csv: str, output: str):
    with open(input_csv, encoding='utf-8') as f:
        with open(output, mode='w') as outfile:
            reader = csv.reader(f, delimiter=";")
            brand_dict = dict()
            for row in reader:
                brand = row[0]
                if brand not in brand_dict:
                    brand_dict[brand] = ""
            yaml.dump(brand_dict, outfile, default_flow_style=False)
