import numpy as np
import csv

from .detect import detect_table_ranges, get_type_data
from .learn import learn_constraints


def parse(csv_file):
    data = []
    with open(csv_file) as f:
        csv_reader = csv.reader(f, delimiter=',')
        max_length = 0
        for row in csv_reader:
            max_length = max(max_length, len(row))
            data.append(row)

    # Fill rows to max length
    for i in range(len(data)):
        data[i] += ["" for _ in range(max_length - len(data[i]))]

    return data


def learn_from_csv(csv_file):
    return learn_from_cells(parse(csv_file))


def learn_from_cells(data):
    data = np.array(data, dtype=object)
    type_data = get_type_data(data)
    t_ranges = detect_table_ranges(type_data)
    # tables = get_tables(data, type_data, t_ranges)
    return learn_constraints(data, t_ranges).constraints
