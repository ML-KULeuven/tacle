import json
from enum import Enum

import numpy as np
import pandas as pd
import re

import time

from tacle.core.group import Bounds, Table, Group, Orientation, GType


# TODO Single vector => try both orientations
from tacle.util import printing


def parse(filename):
    with open(filename, "r") as file:
        data = np.array(pd.read_csv(file, header=None))
        return data


# --- Type detection ---

class DType(Enum):
    nan = -1
    int = 0
    float = 1
    percent = 1.1
    currency = 1.2
    string = 2

    def to_gtype(self):
        return GType(int(self.value))

    def __repr__(self):
        return "DT.{}".format(self.name[0:3])


percent_pattern = re.compile(r"\s*-?\s*\d+(\.\d+)?\s*%")
currency_pattern = re.compile(r"(\s*[\$€£]\s*\d+[\d,]*\s*)|(\s*\d+[\d,]*\s*[\$€£]\s*)")
currency_symbols = re.compile(r"[\$€£]")
place_holder = re.compile(r"[\s,]")


def cast(g_type: GType, v_type: DType, value):
    if v_type is DType.nan:
        return None
    if g_type == GType.string:
        return str(value)
    else:
        if v_type == DType.percent:
            value = float(str(value).replace("%", "")) / 100.0
        elif v_type == DType.currency:
            value = re.sub(currency_symbols, "", str(value))
        value = re.sub(place_holder, "", str(value))
        if g_type == GType.int or g_type == GType.float:
            if value == "":
                return np.nan
            return float(value)
        raise ValueError("Unexpected GType: " + str(g_type))


def detect_type(val) -> DType:
    if percent_pattern.match(str(val)):
        return DType.percent
    elif re.match(currency_pattern, str(val)):
        return DType.currency
    try:
        val = float(str(val).replace(",", ""))
        if np.isnan(val):
            return DType.nan
        return DType.int if float(val) == int(val) else DType.float
    except ValueError:
        return DType.string


def numeric_type(d_type: DType):
    return d_type == DType.percent or d_type == DType.currency or d_type == DType.int \
        or d_type == DType.float or d_type == DType.nan


def infer_type(types):
    if all(t == DType.nan for t in types):
        raise Exception("NaN type not allowed for groups")
    if any(t == DType.string for t in types):
        return GType.string
    if all(t == DType.int for t in types):
        return GType.int
    return GType.float


def get_groups_tables(csv_file, groups_file=None):
    parse_printer = printing.get(__name__, on=False)
    t_start = time.time()
    data = parse(csv_file)
    type_data = np.vectorize(detect_type)(data)
    if groups_file is None:
        t = list(detect_tables(type_data))
        t = [(b, Table("T{}".format(i + 1), Bounds(b).subset(data), o)) for i, (b, o) in enumerate(t)]

        if parse_printer.on():
            tables = ["{} = [{}:{}, {}:{}]".format(table.name, *bounds) for bounds, table in t]
            parse_printer.form("PARSE: Detected tables: {}", ", ".join(tables))

        groups = detect_groups(type_data, t)
        parse_printer.form("PARSE: Detected groups: {}", ", ".join(str(g) for g in groups))
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
                groups = detect_groups(type_data, t)
                parse_printer.form("PARSE: Detected groups: {}", ", ".join(str(g) for g in groups))
    parse_printer.form("PARSE: Parsing took {}s", time.time() - t_start)
    return groups


def get_groups(data, indexing_data):
    type_data = np.vectorize(detect_type)(data)
    table_dict = {}
    tables = []
    groups = []

    for table_description in indexing_data["Tables"]:
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
        tables.append((bounds.bounds, table_dict[name]))

    if "Groups" in indexing_data:
        for group_description in indexing_data["Groups"]:
            table = table_dict[group_description["Table"]]
            if "Types" in group_description:
                from tacle.indexing import Typing
                g_types = [GType.int if Typing.root(gt) == "numeric" else GType.string
                           for gt in group_description["Types"]]
            else:
                g_types = None
            groups.append(create_group(group_description["Bounds"], table, g_types))
    else:
        groups = detect_groups(type_data, tables)
    return groups


def create_group(bounds_list, table: Table, g_types=None):
    if bounds_list[0] == ":":
        bounds = Bounds([1, table.rows] + bounds_list[1:3])
        row = False
    elif bounds_list[2] == ":":
        bounds = Bounds(bounds_list[0:2] + [1, table.columns])
        row = True
    else:
        raise Exception("Could not create group")

    data = bounds.subset(table.data)
    types = np.vectorize(detect_type)(data)
    if g_types is not None:
        gtype_set = g_types
    elif row:
        gtype_set = [infer_type(row) for row in types]
    else:
        gtype_set = [infer_type(col) for col in types.T]
    g_type = GType.max(gtype_set)
    cast_f = np.vectorize(lambda t, v: cast(g_type, t, v), otypes=[np.object if g_type is GType.string else np.float])
    return Group(table, bounds, row, cast_f(types, data), gtype_set)


def detect_tables(type_data):
    rectangles = []
    for row in range(np.size(type_data, 0)):
        line = []
        rect = None
        cols = np.size(type_data, 1)
        for col in range(cols):
            if type_data[row, col] != DType.nan:
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


def detect_groups(type_data, tables):
    groups = []

    def detect_horizontal():
        t_data = Bounds(b).subset(type_data)
        rows, cols = (table.rows, table.columns)
        for row in range(rows):
            if not is_type_consistent(t_data[row, :]):
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
            if not is_type_consistent(t_data[:, col]):
                return []
        same = [numeric_type(t_data[0, col]) == numeric_type(t_data[0, col - 1]) for col in range(1, cols)] + [False]

        start = 0
        for col in range(cols):
            if not same[col]:
                groups.append(create_group([":", start + 1, col + 1], table))
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
    if all(type_data[r1, i] == DType.string for i in range(c1, c2)):
        rec = r1 + 1, r2, c1, c2
        o = Orientation.VERTICAL
    elif all(type_data[i, c1] == DType.string for i in range(r1, r2)):
        rec = r1, r2, c1 + 1, c2
        o = Orientation.HORIZONTAL
    return tuple(rec), o


def is_type_consistent(v):
    for i in range(1, len(v)):
        if v[i] != DType.nan and v[i - 1] != DType.nan and numeric_type(v[i]) != numeric_type(v[i - 1]):
            return False
    return True
