from enum import Enum

import numpy
import re


def null(var, val):
    return val if var is None else var

percent_pattern = re.compile(r"\d+(\.\d+)?%")


class Bounds:
    def __init__(self, bounds_list):
        self.bounds = bounds_list

    def subset(self, data):
        top_row = self.bounds[0] - 1
        bottom_row = self.bounds[1]
        left_column = self.bounds[2] - 1
        right_column = self.bounds[3]
        return data[top_row:bottom_row, left_column:right_column]

    def rows(self):
        return self.bounds[1] - self.bounds[0] + 1

    def columns(self):
        return self.bounds[3] - self.bounds[2] + 1

    def combine(self, bounds):
        r1, r2, c1, c2 = bounds.bounds
        r1, c1 = [null(r1, 1), null(c1, 1)]
        b = lambda x, offset: min(max(x, self.bounds[offset]), self.bounds[offset + 1])
        return Bounds([
            b(self.bounds[0] + r1 - 1, 0),
            b(self.bounds[1] if r2 is None else self.bounds[0] + r2 - 1, 0),
            b(self.bounds[2] + c1 - 1, 2),
            b(self.bounds[3] if c2 is None else self.bounds[2] + c2 - 1, 2)
        ])

    def contains(self, bounds):
        r1, r2, c1, c2 = bounds.bounds
        sr1, sr2, sc1, sc2 = self.bounds
        return sr1 <= r1 and sr2 >= r2 and sc1 <= c1 and sc2 >= c2

    def overlaps_with(self, bounds):
        r1, r2, c1, c2 = bounds.bounds
        sr1, sr2, sc1, sc2 = self.bounds
        return not (r2 < sr1 or r1 > sr2 or c2 < sc1 or c1 > sc2)

    def __repr__(self):
        return str(self.bounds)


class Table:
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.rows = numpy.size(data, 0)
        self.columns = numpy.size(data, 1)

    def __repr__(self):
        repr_str = "Data:\n" + str(self.data) + "\nRows: " + str(self.rows) + "\nColumn: " + str(self.columns)
        return repr_str

    def __str__(self):
        return self.name


class GType(Enum):
    int = 0
    float = 1
    string = 2


def cast(gtype: GType, value):
    if gtype == GType.int:
        return int(value)
    elif gtype == GType.float:
        match = percent_pattern.match(str(value))
        return float(value) if not match else float(str(value).replace("%", ""))
    elif gtype == GType.string:
        return str(value)
    raise ValueError("Unexpected GType: " + str(gtype))


class Group:
    def __init__(self, table, bounds, row):
        self.table = table
        self.bounds = bounds
        self.row = row
        self.data = self._get_group_data()
        self.dtype = self.infer_type()
        f = numpy.vectorize(lambda x: cast(self.dtype, x))
        self.data = f(self.data)

    def __repr__(self):
        r1, r2, c1, c2 = self.bounds.bounds
        if self.row:
            rows = str(r1) if r1 == r2 else "{}:{}".format(r1, r2)
            columns = ":"
        else:
            rows = ":"
            columns = str(c1) if c1 == c2 else "{}:{}".format(c1, c2)
        return "{}[{}, {}]".format(self.table.name, rows, columns)

    def _get_group_data(self):
        data = self.table.data
        bounds = self.bounds
        return bounds.subset(data)

    def get_group_data(self):
        return self.data

    @staticmethod
    def _infer_type_scalar(val):
        if percent_pattern.match(str(val)):
            return 1
        try:
            val = int(val)
            return 0
        except:
            try:
                val = float(val)
                return 1
            except:
                return 2

    def infer_type(self):
        flat = self.data.flatten()
        dtype = max(list(map(self._infer_type_scalar, flat)))
        if dtype == 0:
            return GType.int
        if dtype == 1:
            return GType.float
        else:
            return GType.string

    def length(self):
        return self.bounds.columns() if self.row else self.bounds.rows()

    def columns(self):
        return self.bounds.columns()

    def rows(self):
        return self.bounds.rows()

    def vectors(self):
        return self.rows() if self.row else self.columns()

    def is_numeric(self):
        return self.dtype is GType.float or self.dtype is GType.int

    def is_integer(self):
        return self.dtype is GType.int

    def is_float(self):
        return self.dtype is GType.int

    def is_textual(self):
        return self.dtype is GType.string

    def row_oriented(self):
        return self.row

    def subgroup(self, bounds):
        return Group(self.table, self.bounds.combine(bounds), self.row)

    def get_vector(self, i):
        return self.data[i - 1, :] if self.row else self.data[:, i - 1]

    def __iter__(self):
        for i in range(1, self.vectors() + 1):
            yield self.vector_subset(i, i)

    def is_subgroup(self, group):
        return self.table == group.table and self.bounds.contains(group.bounds)

    def overlaps_with(self, group):
        if self.table != group.table:
            return False
        return self.bounds.overlaps_with(group.bounds)

    def vector_subset(self, start, end):
        l = [start, end] + [None, None] if self.row else [None, None] + [start, end]
        return self.subgroup(Bounds(l))
