from typing import List

import numpy as np

from .indexing import Table, Orientation, Typing, Block


def get_tables(data, type_data, ranges, names=None):
    data = np.array(data, dtype=np.object)
    if names is None:
        names = ["T{}".format(i + 1) for i in range(len(ranges))]
    tables = []
    for name, (t_range, t_headers) in zip(names, ranges):
        t_data = t_range.get_data(data)
        supported_orientation = [
            o
            for o in Orientation.all()
            if orientation_compatible(type_data, t_range, o)
        ]
        if len(supported_orientation) > 0:
            tables.append(
                Table(
                    t_data,
                    t_range.get_data(type_data),
                    t_range,
                    name,
                    supported_orientation,
                    header_ranges=t_headers,
                    header_data={o: hr.get_data(data) for o, hr in t_headers.items()}
                    if t_headers
                    else None,
                )
            )

    return tables


def get_blocks(table):
    # type: (Table) -> List[Block]
    blocks = []
    for orientation in table.orientations:
        rel_range = table.relative_range
        max_types = []
        vector_count = rel_range.vector_count(orientation)
        for i in range(vector_count):
            vector_type_data = rel_range.vector_range(i, orientation).get_data(
                table.type_data
            )
            max_type = Typing.max(vector_type_data)
            max_types.append(Typing.soft_root(max_type))
        block_indices = [0]
        for i in range(1, vector_count):
            if (
                max_types[i] == Typing.unknown
                or Typing.max([max_types[i], max_types[block_indices[-1]]]) is None
            ):
                block_indices.append(i)
        block_indices.append(vector_count)
        lengths = [
            block_indices[i + 1] - block_indices[i]
            for i in range(len(block_indices) - 1)
        ]
        for start, count in zip(block_indices, lengths):
            block_range = rel_range.sub_range(start, count, orientation)
            blocks.append(Block(table, block_range, orientation))
    return blocks


def orientation_compatible(type_data, t_range, orientation):
    for vi in range(t_range.vector_count(orientation)):
        vector_range = t_range.vector_range(vi, orientation)
        cell_types = vector_range.get_data(type_data)
        if Typing.max(cell_types) is None:
            return False
    return True


# def get_groups(data, indexing_data):
#     type_data = np.vectorize(detect_type)(data)
#     table_dict = {}
#     tables = []
#     groups = []
#
#     for table_description in indexing_data["Tables"]:
#         bounds = Bounds(table_description["Bounds"])
#         data_subset = bounds.subset(data)
#         name = table_description["Name"]
#         orientation = None
#         if "Orientation" in table_description:
#             o_string = table_description["Orientation"].lower()
#             if o_string == "row" or o_string == "horizontal":
#                 orientation = Orientation.HORIZONTAL
#             elif o_string == "column" or o_string == "col" or o_string == "vertical":
#                 orientation = Orientation.VERTICAL
#         table_dict[name] = Table(name, data_subset, orientation)
#         tables.append((bounds.bounds, table_dict[name]))
#
#     if "Groups" in indexing_data:
#         for group_description in indexing_data["Groups"]:
#             table = table_dict[group_description["Table"]]
#             groups.append(create_group(group_description["Bounds"], table))
#     else:
#         groups = detect_groups(type_data, tables)
#     return groups
#
#
# def create_group(bounds_list, table: Table):
#     if bounds_list[0] == ":":
#         bounds = Bounds([1, table.rows] + bounds_list[1:3])
#         row = False
#     elif bounds_list[2] == ":":
#         bounds = Bounds(bounds_list[0:2] + [1, table.columns])
#         row = True
#     else:
#         raise Exception("Could not create group")
#
#     data = bounds.subset(table.data)
#     types = np.vectorize(detect_type)(data)
#     if row:
#         gtype_set = [infer_type(row) for row in types]
#     else:
#         gtype_set = [infer_type(col) for col in types.T]
#     g_type = GType.max(gtype_set)
#     cast_f = np.vectorize(lambda t, v: cast(g_type, t, v), otypes=[np.object if g_type is GType.string else np.float])
#     return Group(table, bounds, row, cast_f(types, data), gtype_set)
