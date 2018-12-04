from enum import Enum

import numpy


class GType(Enum):
    int = 0
    float = 1
    string = 2

    @staticmethod
    def super(gtype):
        if gtype == GType.int:
            return GType.float
        else:
            return gtype

    @staticmethod
    def max(gtype_set):
        if any([gt == GType.string for gt in gtype_set]) and not all([gt == GType.string for gt in gtype_set]):
            raise Exception("Inconsistent types {}".format(gtype_set))
        return GType(max([gt.value for gt in gtype_set]))


# --- Orientation ---

class Orientation(Enum):
    HORIZONTAL = True
    VERTICAL = False

    @staticmethod
    def row(orientation):
        return orientation is None or orientation == Orientation.HORIZONTAL

    @staticmethod
    def column(orientation):
        return orientation is None or orientation == Orientation.VERTICAL


def null(var, val):
    return val if var is None else var


# --- Bounds ---

class Bounds:
    def __init__(self, bounds_list):
        self.bounds = tuple(bounds_list)

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

    def __hash__(self):
        return hash(self.bounds)

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return self.bounds == other.bounds


# --- Table ---

class Table:
    def __init__(self, name, data, orientation=None):
        self.name = name
        self.data = data
        self.rows = numpy.size(data, 0)
        self.columns = numpy.size(data, 1)
        self._orientation = orientation

    @property
    def orientation(self):
        return self._orientation

    def __repr__(self):
        repr_str = "Data:\n" + str(self.data) + "\nRows: " + str(self.rows) + "\nColumn: " + str(self.columns)
        return repr_str

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name


# --- Group ---

class Group:
    def __init__(self, table, bounds, row, data, gtype_set):
        self._table = table
        self._bounds = bounds
        self._row = row
        self._vector_types = gtype_set
        self._dtype = GType.max(gtype_set)
        self._data = data
        from tacle.core.template import blank_filter
        self._is_partial = not numpy.all(numpy.vectorize(blank_filter(self._data)[1])(self._data))
        self._subgroups = dict()
        self._hash = None

    @property
    def is_partial(self):
        return self._is_partial

    @property
    def row(self):
        return self._row

    @property
    def table(self):
        return self._table

    @property
    def bounds(self):
        return self._bounds

    @property
    def dtype(self):
        return self._dtype

    @property
    def vector_types(self):
        return self._vector_types

    @property
    def data(self):
        return self._data

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
        if bounds not in self._subgroups:
            sub_bounds = Bounds([1, self.rows(), 1, self.columns()]).combine(bounds)
            r1, r2, c1, c2 = sub_bounds.bounds
            sub_data = sub_bounds.subset(self.data)
            indices = [r1, r2] if self.row else [c1, c2]
            vector_types = [self._vector_types[i - 1] for i in range(indices[0], indices[1] + 1)]
            group = Group(self.table, self.bounds.combine(bounds), self.row, sub_data, vector_types)
            self._subgroups[bounds] = group
            return group
        return self._subgroups[bounds]

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

    def __hash__(self):
        if self._hash is None:
            self._hash = hash((self.table, self.row, self.bounds))
        return self._hash

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return isinstance(other, Group) \
            and (self.table, self.row, self.bounds) == (other.table, other.row, other.bounds)

    def __lt__(self, other):
        if not isinstance(other, Group):
            return NotImplemented
        if self.table < other.table:
            return True
        index = 0 if self.row else 2
        if self.row == other.row and self.bounds.bounds[index] < other.bounds.bounds[index]:
            return True
        return False
