import re
from typing import Any, Optional, List, Dict

import numpy as np
from dateutil.parser import parse
from openpyxl.utils import datetime


class Typing(object):
    numeric = "numeric"
    int = "int"
    float = "float"
    string = "string"
    date = "date"
    currency = "currency"
    percentage = "percentage"
    nested_index = "nested_index"
    any = "any"
    unknown = "unknown"

    percent_pattern = re.compile(r"\s*-?\s*\d+(\.\d+)?\s*%")
    currency_pattern = re.compile(
        r"(\s*[$€£]\s*\d+[\d,]*\s*)|(\s*\d+[\d,]*\s*[$€£]\s*)"
    )
    currency_symbols = re.compile(r"[$€£]")
    place_holder = re.compile(r"[\s,]")
    nested_index_pattern = re.compile(r"\d+\.\d+(\.\d+)")

    @staticmethod
    def hierarchy():
        return {
            Typing.int: Typing.numeric,
            Typing.float: Typing.numeric,
            Typing.currency: Typing.float,
            Typing.percentage: Typing.float,
            Typing.nested_index: Typing.string,
            # Typing.date: Typing.string,  # Should date be subtype of string?
        }

    @staticmethod
    def root(cell_type):
        hierarchy = Typing.hierarchy()
        return (
            Typing.root(hierarchy[cell_type]) if cell_type in hierarchy else cell_type
        )

    @staticmethod
    def soft_root(cell_type):
        hierarchy = Typing.hierarchy()
        return (
            Typing.soft_root(hierarchy[cell_type])
            if cell_type not in [Typing.int, Typing.string, Typing.float, Typing.date]
            and cell_type in hierarchy
            else cell_type
        )

    @staticmethod
    def lowest_common_ancestor(cell_type1, cell_type2):
        if cell_type1 == cell_type2:
            return cell_type1
        if cell_type1 is None or cell_type2 is None:
            return None
        if cell_type1 == Typing.any or cell_type1 == Typing.unknown:
            return cell_type2 if cell_type2 != Typing.int else Typing.float
        if cell_type2 == Typing.any or cell_type2 == Typing.unknown:
            return cell_type1 if cell_type1 != Typing.int else Typing.float
        if (
            Typing.root(cell_type1) == Typing.numeric
            and cell_type2 == Typing.nested_index
            or cell_type1 == Typing.nested_index
            and Typing.root(cell_type2) == Typing.numeric
        ):
            return Typing.nested_index

        hierarchy = Typing.hierarchy()
        path1 = [cell_type1]
        while cell_type1 in hierarchy:
            cell_type1 = hierarchy[cell_type1]
            path1.append(cell_type1)

        path2 = [cell_type2]
        while cell_type2 in hierarchy:
            cell_type2 = hierarchy[cell_type2]
            path2.append(cell_type2)

        if path1[-1] != path2[-1]:
            return None

        last = -1
        while (
            min(len(path1), len(path2)) > -last + 1
            and path1[last - 1] == path2[last - 1]
        ):
            last -= 1

        return path1[last]

    @staticmethod
    def max(cell_types):
        if isinstance(cell_types, np.ndarray):
            cell_types = cell_types.flatten()
        super_type = cell_types[0]
        for cell_type in cell_types[1:]:
            super_type = Typing.lowest_common_ancestor(super_type, cell_type)
        return super_type

    @staticmethod
    def compatible(*args):
        return Typing.max(args) is not None

    @staticmethod
    def is_sub_type(sub_type, super_type):
        return Typing.lowest_common_ancestor(sub_type, super_type) == super_type

    @staticmethod
    def blank_detector(cell_type):
        if Typing.root(cell_type) == Typing.numeric is not None:
            return lambda e: not np.isnan(e)
        else:
            return lambda e: e is not None

    @staticmethod
    def get_blank(cell_type):
        if Typing.max([cell_type, Typing.numeric]) is not None:
            return np.nan
        else:
            return None

    @staticmethod
    def detect_type(value):
        if isinstance(value, int):
            return Typing.int
        elif isinstance(value, float):
            return Typing.float

        value = str(value).strip()
        if value == "":
            return Typing.any
        if value == "#?":
            return Typing.unknown
        elif re.match(Typing.percent_pattern, value):
            return Typing.percentage
        elif re.match(Typing.currency_pattern, value):
            return Typing.currency
        elif re.match(Typing.nested_index_pattern, value):
            return Typing.nested_index

        try:
            value = float(value.replace(",", ""))
            if np.isnan(value):
                return Typing.any
            return Typing.int if float(value) == int(value) else Typing.float
        except ValueError:
            pass

        try:
            parse(value)
            return Typing.date
        except ValueError:
            pass

        return Typing.string

    @staticmethod
    def cast(cell_type, value):
        original_cell_type = Typing.detect_type(value)
        if original_cell_type != cell_type and original_cell_type != Typing.any:
            value = Typing.cast(original_cell_type, value)

        if cell_type in (Typing.string, Typing.nested_index):
            return str(value) if value is not None else None
        elif cell_type == Typing.percentage:
            try:
                return Typing.cast(Typing.float, str(value).replace("%", "")) / 100.0
            except ValueError:
                print("Could not convert percentage {}".format(value))
                raise
        elif cell_type == Typing.currency:
            return Typing.cast(
                Typing.float, re.sub(Typing.currency_symbols, "", str(value))
            )
        elif cell_type in [Typing.int, Typing.float, Typing.numeric]:
            if str(value) not in [None, "#?", ""]:
                cleaned = re.sub(Typing.place_holder, "", str(value))
                try:
                    converted = float(cleaned)
                except ValueError:
                    print("Cleaned from", value, "to", cleaned)
                    raise
            else:
                converted = np.nan
            if cell_type == Typing.int and not np.isnan(converted):
                converted = int(converted)
            return converted
        elif cell_type == Typing.date:
            return parse(value)
        elif cell_type == Typing.unknown:
            return "#?"
        elif cell_type == Typing.any:
            return value
        raise ValueError("Unexpected cell type: " + cell_type)

    # @staticmethod
    # def as_legacy_type(cell_type):
    #     from legacy.group import GType
    #
    #     if isinstance(cell_type, GType):
    #         return cell_type
    #     cell_type = Typing.soft_root(cell_type)
    #     if cell_type == Typing.int:
    #         return GType.int
    #     if cell_type == Typing.string:
    #         return GType.string
    #     if cell_type == Typing.float:
    #         return GType.float
    #     raise ValueError("Cannot convert {}".format(cell_type))


# This variable is used to indicate the type of variables that should be an orientation, one of the enum values
OrientationType = str


class Orientation(object):
    vertical = "vertical"
    horizontal = "horizontal"

    @staticmethod
    def all():
        return [Orientation.vertical, Orientation.horizontal]

    # @staticmethod
    # def from_legacy_orientation(o):
    #     if group.Orientation.column(o):
    #         return Orientation.vertical
    #     elif group.Orientation.row(o):
    #         return Orientation.horizontal
    #
    # def as_legacy_orientation(self, o):
    #     if o == Orientation.vertical:
    #         return group.Orientation.VERTICAL
    #     elif o == Orientation.horizontal:
    #         return group.Orientation.HORIZONTAL

    @staticmethod
    def is_vertical(orientation):
        if orientation not in Orientation.all():
            raise ValueError(
                "Orientation {} is not a valid orientation".format(orientation)
            )
        return orientation == Orientation.vertical

    @staticmethod
    def is_horizontal(orientation):
        if orientation not in Orientation.all():
            raise ValueError(
                "Orientation {} is not a valid orientation".format(orientation)
            )
        return orientation == Orientation.horizontal


class Range(object):
    def __init__(self, column, row, width, height):
        self.column = column
        self.row = row
        self.width = width
        self.height = height

    @staticmethod
    def from_coordinates(x0, y0, x1, y1):
        return Range(x0, y0, x1 - x0, y1 - y0)

    @staticmethod
    def from_legacy_bounds(bounds):
        return Range.from_coordinates(
            bounds.bounds[2] - 1,
            bounds.bounds[0] - 1,
            bounds.bounds[3],
            bounds.bounds[1],
        )

    @property
    def rows(self):
        return self.height

    @property
    def columns(self):
        return self.width

    @property
    def x0(self):
        return self.column

    @property
    def y0(self):
        return self.row

    @property
    def x1(self):
        return self.column + self.width

    @property
    def y1(self):
        return self.row + self.height

    @property
    def cells(self):
        if self.rows < 0 or self.columns < 0:
            return 0
        return self.rows * self.columns

    def get_data(self, data):
        return data[self.y0 : self.y1, self.x0 : self.x1]

    def intersect(self, other):
        return self.from_coordinates(
            max(self.x0, other.x0),
            max(self.y0, other.y0),
            min(self.x1, other.x1),
            min(self.y1, other.y1),
        )

    def bounding_box(self, other):
        return self.from_coordinates(
            min(self.x0, other.x0),
            min(self.y0, other.y0),
            max(self.x1, other.x1),
            max(self.y1, other.y1),
        )

    def contains(self, other):
        return (
            self.x0 <= other.x0
            and self.y0 <= other.y0
            and self.x1 >= other.x1
            and self.y1 >= other.y1
        )

    def contains_cell(self, cell):
        if isinstance(cell, (list, tuple)):
            x, y = cell
        else:
            x, y = cell.x, cell.y
        return self.x0 <= x < self.x1 and self.y0 <= y < self.y1

    def overlaps_with(self, other):
        return self.intersect(other).cells > 0

    def relative_to_absolute(self, sub_range):
        return Range(
            self.x0 + sub_range.x0,
            self.y0 + sub_range.y0,
            sub_range.width,
            sub_range.height,
        )

    def vector_count(self, orientation):
        return self.columns if orientation == Orientation.vertical else self.rows

    def vector_length(self, orientation):
        return self.rows if orientation == Orientation.vertical else self.columns

    def vector_index(self, orientation):
        return self.x0 if orientation == Orientation.vertical else self.y0

    def sub_range(self, vector_index, vector_count, orientation):
        if self.vector_index(
            orientation
        ) + vector_index + vector_count > self.vector_index(
            orientation
        ) + self.vector_count(
            orientation
        ):
            raise ValueError("Sub range exceeds range")

        if orientation == Orientation.vertical:
            return Range(self.x0 + vector_index, self.y0, vector_count, self.height)
        else:
            return Range(self.x0, self.y0 + vector_index, self.width, vector_count)

    def vector_range(self, vector_index, orientation):
        return self.sub_range(vector_index, 1, orientation)

    def as_dict(self):
        return {
            "columnIndex": self.column,
            "rowIndex": self.row,
            "columns": self.columns,
            "rows": self.rows,
        }

    # def as_legacy_bounds(self):
    #     # type: () -> group.Bounds
    #     return group.Bounds((self.y0 + 1, self.y1, self.x0 + 1, self.x1))
    #
    # def as_legacy_list(self, orientation=None):
    #     # type: (Optional[Orientation]) -> List[Union[str, int]]
    #     if orientation is None:
    #         return group.Bounds((self.y0 + 1, self.y1, self.x0 + 1, self.x1)).bounds
    #     elif orientation == Orientation.vertical:
    #         return [":", self.x0 + 1, self.x1]
    #     elif orientation == Orientation.horizontal:
    #         return [self.y0 + 1, self.y1, ":"]

    def __and__(self, other):
        return self.intersect(other)

    def __repr__(self):
        return "Range(x:{}, y:{}, w:{}, h:{})".format(
            self.column, self.row, self.width, self.height
        )

    def __str__(self):
        return "({}:{}, {}:{})".format(self.y0, self.y1, self.x0, self.x1)

    def __hash__(self):
        return hash((self.row, self.column, self.width, self.height))

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        return (
            self.x0 == other.x0
            and self.y0 == other.y0
            and self.x1 == other.x1
            and self.y1 == other.y1
        )


class DataSheet(object):
    def __init__(self, data):
        self.raw_data = data
        self.type_data = np.vectorize(Typing.detect_type)(self.raw_data)
        self.data = np.vectorize(Typing.cast)(self.type_data, self.raw_data)

    def columns(self):
        return np.size(self.data, 1)

    def rows(self):
        return np.size(self.data, 0)


class Table(object):
    def __init__(
            self,
            data: np.ndarray,
            type_data: np.ndarray,
            t_range: Range,
            name: Optional[str] = None,
            orientations: List[OrientationType] = None,
            header_ranges: Dict[OrientationType, Range] = None,
            header_data: Dict[OrientationType, np.ndarray] = None
    ):
        if any(
            orientation not in [None, Orientation.vertical, Orientation.horizontal]
            for orientation in orientations
        ):
            raise ValueError("Invalid orientations {}".format(orientations))

        if np.size(data, 1) != t_range.columns or np.size(data, 0) != t_range.rows:
            raise ValueError(
                "Mismatch between data and range dimensions: {} vs {}".format(
                    (np.size(data, 1), np.size(data, 0)),
                    (t_range.columns, t_range.rows),
                )
            )

        if (
            np.size(type_data, 1) != t_range.columns
            or np.size(type_data, 0) != t_range.rows
        ):
            raise ValueError(
                "Mismatch between data and range dimensions: {} vs {}".format(
                    (np.size(type_data, 1), np.size(type_data, 0)),
                    (t_range.columns, t_range.rows),
                )
            )

        self.name = name if name is not None else str(t_range)
        self.data = data
        self.type_data = type_data
        self.range = t_range  # type: Range
        self.orientations = orientations
        self.header_ranges = header_ranges
        self.header_data = header_data

        from tacle.convert import get_blocks

        self.blocks = get_blocks(self)

    @property
    def columns(self):
        return self.range.columns

    @property
    def rows(self):
        return self.range.rows

    @property
    def relative_range(self):
        return Range(0, 0, self.range.width, self.range.height)

    def get_vector_data(self, i, orientation=None):
        if orientation is None and len(self.orientations) > 1:
            raise ValueError("Ambiguous orientation, please specify")
        elif orientation is None and len(self.orientations) == 1:
            orientation = self.orientations[0]

        if i < 0 or i >= self.range.vector_count(orientation):
            raise ValueError(
                "Invalid index {} (should be 0 <= i <= {})".format(
                    i, self.range.vector_count(orientation)
                )
            )

        vector_range = self.relative_range.vector_range(i, orientation)

        for block in self.blocks:
            if block.orientation == orientation and vector_range.overlaps_with(
                block.relative_range
            ):
                return block.vector_data[
                    i - block.relative_range.vector_index(orientation)
                ]
        raise RuntimeError("Illegal state: {}, {}, {}".format(i, orientation, self))

    def get_vector_type(self, i, orientation=None):
        if orientation is None and len(self.orientations) > 1:
            raise ValueError("Ambiguous orientation, please specify")
        elif orientation is None and len(self.orientations) == 1:
            orientation = self.orientations[0]

        if i < 0 or i >= self.range.vector_count(orientation):
            raise ValueError(
                "Invalid index {} (should be 0 <= i <= {})".format(
                    i, self.range.vector_count(orientation)
                )
            )

        vector_range = self.relative_range.vector_range(i, orientation)

        for block in self.blocks:
            if block.orientation == orientation and vector_range.overlaps_with(
                block.relative_range
            ):
                return block.vector_types[
                    i - block.relative_range.vector_index(orientation)
                ]
        raise RuntimeError("Illegal state: {}, {}, {}".format(i, orientation, self))

    def copy(self):
        return Table(
            self.data.copy(),
            self.type_data.copy(),
            self.range,
            self.name,
            self.orientations,
        )

    def add_vector(self, vector_data, vector_types, orientation):
        data = self.data.copy()
        type_data = self.type_data.copy()
        if orientation not in self.orientations:
            raise ValueError("Unsupported orientation: {}".format(orientation))
        if orientation == Orientation.vertical:
            new_data = np.concatenate((data, vector_data[:, np.newaxis]), axis=1)
            new_type_data = np.concatenate(
                (type_data, vector_types[:, np.newaxis]), axis=1
            )
            new_range = Range(
                self.range.column,
                self.range.row,
                self.range.width + 1,
                self.range.height,
            )
            return Table(
                new_data, new_type_data, new_range, self.name, self.orientations
            )
        raise ValueError("Horizontal orientation is not yet supported")

    def reload_data(self, data: np.ndarray):
        raise NotImplementedError()  # TODO

    def __repr__(self):
        return "Table({}, {}, {}, {})".format(
            self.name, self.data, repr(self.range), self.orientations
        )

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


class Block(object):
    def __init__(
        self, table, relative_range, orientation, vector_types=None, virtual=False
    ):
        """
        :type table: Table
        :type relative_range: Range
        """
        if orientation not in [Orientation.vertical, Orientation.horizontal]:
            raise ValueError("Invalid orientation {}".format(orientation))

        self.table = table
        self.relative_range = relative_range
        self.orientation = orientation
        self.virtual = virtual

        if virtual is False:
            self.vector_types = [] if not vector_types else vector_types
            self.vector_data = []
            for i in range(relative_range.vector_count(orientation)):
                if vector_types is None:
                    v_type = Typing.max(
                        relative_range.vector_range(i, orientation).get_data(
                            table.type_data
                        )
                    )
                    self.vector_types.append(v_type)
                else:
                    v_type = vector_types[i]

                v_data = relative_range.vector_range(i, orientation).get_data(
                    table.data
                )
                self.vector_data.append(
                    np.vectorize(lambda v: Typing.cast(v_type, v))(v_data.flatten())
                )

            self.type = Typing.max(self.vector_types)
            self.data = np.vectorize(lambda v: Typing.cast(self.type, v))(
                relative_range.get_data(table.data)
            )
            self.has_blanks = not np.all(
                np.vectorize(Typing.blank_detector(self.type))(self.data)
            )
        else:
            v_type, blanks = virtual
            self.vector_types = [v_type]
            self.type = v_type
            self.data = None
            self.has_blanks = blanks

        self.cache = dict()
        self.hash = hash((self.table, self.relative_range, self.orientation))

    def update(self, new_table):
        return Block(
            new_table,
            self.relative_range,
            self.orientation,
            self.vector_types,
            self.virtual,
        )

    @property
    def absolute_range(self):
        return self.table.range.relative_to_absolute(self.relative_range)

    def __repr__(self):
        return "Block({}, {}, {}, {})".format(
            self.table, self.relative_range, self.type, self.orientation
        )

    def vector_count(self):
        return self.relative_range.vector_count(self.orientation)

    def vector_length(self):
        return self.relative_range.vector_length(self.orientation)

    def vector_index(self):
        return self.relative_range.vector_index(self.orientation)

    def columns(self):
        return self.relative_range.columns

    def rows(self):
        return self.relative_range.rows

    #
    # @property
    # def bounds(self):
    #     return self.relative_range.as_legacy_bounds()

    def sub_block(self, vector_index, vector_count=1):
        key = (vector_index, vector_count)
        if key not in self.cache:
            new_range = self.relative_range.sub_range(
                vector_index, vector_count, self.orientation
            )
            vector_types = self.vector_types[vector_index : vector_index + vector_count]
            sub_block = Block(
                self.table,
                new_range,
                self.orientation,
                vector_types,
                virtual=self.virtual,
            )
            self.cache[key] = sub_block
            return sub_block
        else:
            return self.cache[key]

    def vector(self, vector_index):
        return self.sub_block(vector_index)

    def set_data(self, data):
        raise NotImplementedError()
        # if self.virtual:
        #     # block = Block(self.table, self.relative_range, self.orientation, virtual=self.virtual)
        #     # block.vector_data = [data]
        #     # block.data = data
        #     if self.orientation == Orientation.horizontal:
        #         data = data[np.newaxis, :]
        #     elif self.orientation == Orientation.vertical:
        #         data = data[:, np.newaxis]
        #     from tacle.core.group import Group
        #
        #     return Group(
        #         self.table,
        #         self.relative_range.as_legacy_bounds(),
        #         self.orientation == Orientation.horizontal,
        #         data,
        #         [Typing.as_legacy_type(self.type)],
        #     )

    def __iter__(self):
        for i in range(self.vector_count()):
            yield self.sub_block(i)

    def is_sub_block(self, block):
        return self.table == block.table and self.relative_range.contains(
            block.relative_range
        )

    def overlaps_with(self, block):
        return self.table == block.table and self.relative_range.overlaps_with(
            block.relative_range
        )

    def __hash__(self):
        return self.hash

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return (
            isinstance(other, Block)
            and self.table == other.table
            and self.orientation == other.orientation
            and self.relative_range == other.relative_range
        )

    def __lt__(self, other):
        return (
            self.table,
            self.orientation,
            self.vector_index(),
            self.vector_count(),
            self.vector_length(),
        ) < (
            other.table,
            other.orientation,
            other.vector_index(),
            other.vector_count(),
            other.vector_length(),
        )
