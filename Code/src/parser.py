import json

import itertools
import numpy as np
import pandas as pd

from core.group import Bounds, Table, Group, GType


def parse(filename):
    with open(filename, "r") as file:
        data = np.array(pd.read_csv(file, header=None))
        return data


def get_groups_tables(csv_file, groups_file=None):
    data = parse(csv_file)
    if groups_file is None:
        type_data = np.vectorize(lambda x: int(np.floor(Group._infer_type_scalar(x) / 2) * 2))(data)
        t = list(detect_tables(data, type_data))
        print("Detected table areas: {}".format(t))
        t = [(b, Table("T{}".format(i + 1), Bounds(b).subset(data))) for i, b in enumerate(t)]
        return detect_groups(data, type_data, t)
    else:
        tables = {}
        groups = []
        with open(groups_file, "r") as group_file:
            json_data = json.load(group_file)
            for table_description in json_data["Tables"]:
                bounds = Bounds(table_description["Bounds"])
                data_subset = bounds.subset(data)
                name = table_description["Name"]
                tables[name] = Table(name, data_subset)
            for group_description in json_data["Groups"]:
                table = tables[group_description["Table"]]
                groups.append(create_group(group_description["Bounds"], table))
        return groups


def create_group(bounds_list, table):
    if bounds_list[0] == ":":
        return Group(table, Bounds([1, table.rows] + bounds_list[1:3]), False)
    elif bounds_list[2] == ":":
        return Group(table, Bounds(bounds_list[0:2] + [1, table.columns]), True)
    else:
        raise Exception("Could not create group")


def detect_tables(data, type_data):
    rectangles = []
    for row in range(np.size(data, 0)):
        line = []
        rect = None
        cols = np.size(data, 1)
        for col in range(cols):
            if isinstance(data[row, col], str):
                if rect is None:
                    rect = col
            elif rect is not None:
                line.append([row, row + 1, rect, col])
                rect = None
        if rect is not None:
            line.append([row, row + 1, rect, cols])
        rectangles.append(line)

    rectangles.append([])
    saved = []
    current = {(rec[2], rec[3]): rec for rec in rectangles[0]}
    for i in range(1, len(rectangles)):
        new_current = {}
        for rec in rectangles[i]:
            key = (rec[2], rec[3])
            if key in current:
                old = current.pop(key)
                old[1] = rec[1]
                new_current[key] = old
            else:
                new_current[key] = rec
        saved += current.values()
        current = new_current
    tables = [[r1 + 1, r2, c1 + 1, c2] for r1, r2, c1, c2 in [remove_header(rec, type_data) for rec in saved]]
    tables = [rec for rec in tables if rec[0] <= rec[1] and rec[2] <= rec[3]]
    return sorted(tables, key=lambda t: (t[0], t[2], t[1], t[3]))


def detect_groups(data, type_data, tables):
    groups = []

    def detect_horizontal():
        t_data = Bounds(b).subset(type_data)
        rows, cols = (table.rows, table.columns)
        for row in range(rows):
            row_same_type = all(t_data[row, col] == t_data[row, col - 1] for col in range(1, cols))
            if not row_same_type:
                return []
        same = [t_data[row, 0] == t_data[row - 1, 0] for row in range(1, rows)] + [False]

        start = 0
        for row in range(rows):
            if not same[row]:
                groups.append(create_group([start + 1, row + 1, ":"], table))
                start = row + 1

    def detect_verticals():
        t_data = Bounds(b).subset(type_data)
        rows, cols = (table.rows, table.columns)
        for col in range(cols):
            col_same_type = all(t_data[row, col] == t_data[row - 1, col] for row in range(1, rows))
            if not col_same_type:
                return []
        same = [t_data[0, col] == t_data[0, col - 1] for col in range(1, cols)] + [False]

        start = 0
        for col in range(cols):
            if not same[col]:
                groups.append(create_group([":", start + 1, col + 1, ":"], table))
                start = col + 1

    for t in tables:
        (b, table) = t
        detect_horizontal()
        detect_verticals()

    return groups


def remove_header(rec, type_data):
    r1, r2, c1, c2 = rec
    if all(type_data[r1, i] == GType.string.value for i in range(c1, c2)):
        return [r1 + 1, r2, c1, c2]
    if all(type_data[i, c1] == GType.string.value for i in range(r1, r2)):
        return [r1, r2, c1 + 1, c2]
    return rec
