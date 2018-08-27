import numpy as np

from .indexing import Table, Orientation, Typing


def get_tables(data, type_data, ranges, names=None):
    data = np.array(data, dtype=np.object)
    if names is None:
        names = ["T{}".format(i + 1) for i in range(len(ranges))]
    tables = []
    for name, t_range in zip(names, ranges):
        t_data = t_range.get_data(data)
        supported_orientation = [o for o in Orientation.all() if orientation_compatible(type_data, t_range, o)]
        if len(supported_orientation) > 0:
            tables.append(Table(t_data, t_range, name, supported_orientation))

    return tables


def orientation_compatible(type_data, t_range, orientation):
    for vi in range(t_range.vector_count(orientation)):
        vector_range = t_range.vector_range(vi, orientation)
        cell_types = vector_range.get_data(type_data)
        if not Typing.compatible(cell_types):
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
