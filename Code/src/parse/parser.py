import json

import numpy as np
import pandas as pd
import re

from core.group import Bounds, Table, Group, Orientation, GType


# TODO Deal with currency's
# TODO Single vector => try both orientations

def parse(filename):
    with open(filename, "r") as file:
        data = np.array(pd.read_csv(file, header=None))
        return data


# --- Type detection ---

percent_pattern = re.compile(r"\d+(\.\d+)?%")


def cast(gtype: GType, value):
    if detect_type(value) == GType.nan.value:
        return None
    if gtype == GType.int:
        return float(str(value).replace(",", ""))
    elif gtype == GType.float:
        match = percent_pattern.match(str(value))
        return float(str(value).replace(",", "")) if not match else float(str(value).replace("%", "")) / 100.0
    elif gtype == GType.string:
        return str(value)
    raise ValueError("Unexpected GType: " + str(gtype))


def detect_type(val):
    if percent_pattern.match(str(val)):
        return GType.float.value
    try:
        val = float(str(val).replace(",", ""))
        if np.isnan(val):
            return GType.nan.value
        return GType.int.value if float(val) == int(val) else GType.float.value
    except ValueError:
        return GType.string.value


def numeric_type(data_type):
    return data_type == GType.int.value or data_type == GType.float.value or data_type == GType.nan.value


def infer_type(data):
    types = list(detect_type(val) for val in (data.flatten()))
    detected = GType(max(list(types)))
    if detected == GType.nan:
        raise Exception("NaN type not allowed for groups")
    return detected


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
        bounds = Bounds([1, table.rows] + bounds_list[1:3])
        row = False
    elif bounds_list[2] == ":":
        bounds = Bounds(bounds_list[0:2] + [1, table.columns])
        row = True
    else:
        raise Exception("Could not create group")

    data = bounds.subset(table.data)
    dtype = infer_type(data)
    return Group(table, bounds, row, np.vectorize(lambda x: cast(dtype, x))(data), dtype)


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