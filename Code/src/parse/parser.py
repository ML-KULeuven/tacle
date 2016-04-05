import json

import numpy as np
import pandas as pd

from core.group import Bounds, Table, Group, GType, detect_type, numeric_type, Orientation


def parse(filename):
    with open(filename, "r") as file:
        data = np.array(pd.read_csv(file, header=None))
        return data


def get_groups_tables(csv_file, groups_file=None):
    data = parse(csv_file)
    type_data = np.vectorize(detect_type)(data)
    if groups_file is None:
        t = list(detect_tables(type_data))
        t = [(b, Table("T{}".format(i + 1), Bounds(b).subset(data), o)) for i, (b, o) in enumerate(t)]
        print("PARSE: Detected tables: {}".format(", ".join(["{} = [{}:{}, {}:{}]".format(table.name, *bounds)
                                                             for bounds, table in t])))
        groups = detect_groups(data, type_data, t)
        print("PARSE: Detected groups: {}".format(", ".join(str(g) for g in groups)))
        print()
        return groups
    else:
        table_dict = {}
        t = []
        groups = []
        with open(groups_file, "r") as group_file:
            json_data = json.load(group_file)
            for table_description in json_data["Tables"]:
                bounds = Bounds(table_description["Bounds"])
                data_subset = bounds.subset(data)
                name = table_description["Name"]
                orientation = None
                if "Orientation" in table_description:
                    o_string = table_description["Orientation"].lower()
                    if o_string == "row" or o_string == "horizontal":
                        orientation = Orientation.HORIZONTAL
                    elif o_string == "column" or o_string == "col" or o_string == "vertical":
                        orientation = Orientation.VERTICAL
                table_dict[name] = Table(name, data_subset, orientation)
                t.append((bounds.bounds, table_dict[name]))
            if "Groups" in json_data:
                for group_description in json_data["Groups"]:
                    table = table_dict[group_description["Table"]]
                    groups.append(create_group(group_description["Bounds"], table))
            else:
                groups = detect_groups(data, type_data, t)
                print("PARSE: Detected groups: {}".format(", ".join(str(g) for g in groups)))
                print()
        return groups


def create_group(bounds_list, table):
    if bounds_list[0] == ":":
        return Group(table, Bounds([1, table.rows] + bounds_list[1:3]), False)
    elif bounds_list[2] == ":":
        return Group(table, Bounds(bounds_list[0:2] + [1, table.columns]), True)
    else:
        raise Exception("Could not create group")


def detect_tables(type_data):
    rectangles = []
    for row in range(np.size(type_data, 0)):
        line = []
        rect = None
        cols = np.size(type_data, 1)
        for col in range(cols):
            if type_data[row, col] != GType.nan.value:
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
    tables = [((r1 + 1, r2, c1 + 1, c2), o) for (r1, r2, c1, c2), o in [remove_header(rec, type_data) for rec in saved]]
    tables = [(rec, o) for rec, o in tables if rec[0] <= rec[1] and rec[2] <= rec[3]]
    # TODO Error BMI (no T1)
    return sorted(tables, key=lambda t: (t[0][0], t[0][2], t[0][1], t[0][3]))


def detect_groups(data, type_data, tables):
    groups = []

    def detect_horizontal():
        t_data = Bounds(b).subset(type_data)
        rows, cols = (table.rows, table.columns)
        for row in range(rows):
            row_same_type = all(numeric_type(t_data[row, col]) == numeric_type(t_data[row, col - 1])
                                for col in range(1, cols))
            if not row_same_type:
                return []
        same = [numeric_type(t_data[row, 0]) == numeric_type(t_data[row - 1, 0]) for row in range(1, rows)] + [False]

        start = 0
        for row in range(rows):
            if not same[row]:
                groups.append(create_group([start + 1, row + 1, ":"], table))
                start = row + 1

    def detect_verticals():
        t_data = Bounds(b).subset(type_data)
        rows, cols = (table.rows, table.columns)
        for col in range(cols):
            col_same_type = all(numeric_type(t_data[row, col]) == numeric_type(t_data[row - 1, col])
                                for row in range(1, rows))
            if not col_same_type:
                return []
        same = [numeric_type(t_data[0, col]) == numeric_type(t_data[0, col - 1]) for col in range(1, cols)] + [False]

        start = 0
        for col in range(cols):
            if not same[col]:
                groups.append(create_group([":", start + 1, col + 1, ":"], table))
                start = col + 1

    for t in tables:
        (b, table) = t
        if Orientation.row(table.orientation):
            detect_horizontal()
        if Orientation.column(table.orientation):
            detect_verticals()

    return groups


def remove_header(rec, type_data):
    r1, r2, c1, c2 = rec
    o = None
    if all(type_data[r1, i] == GType.string.value for i in range(c1, c2)):
        rec = r1 + 1, r2, c1, c2
        o = Orientation.VERTICAL
    elif all(type_data[i, c1] == GType.string.value for i in range(r1, r2)):
        rec = r1, r2, c1 + 1, c2
        o = Orientation.HORIZONTAL

    r1, r2, c1, c2 = rec
    if c1 == c2 - 1:
        o = Orientation.VERTICAL
    elif r1 == r2 - 1:
        o = Orientation.HORIZONTAL
    return tuple(rec), o
