import numpy as np
import csv

from .detect import detect_table_ranges


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
    learn_from_cells(parse(csv_file))


def learn_from_cells(data):
    data = np.array(data, dtype=object)
    print(*[t_range.get_data(data) for t_range in detect_table_ranges(data)], sep="\n")
