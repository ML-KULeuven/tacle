import numpy

from .indexing import Typing, Range, Orientation


def get_headers_count(table_range: Range, table_type_data, orientation):
    def get(_vi, _ei):
        return table_type_data[_vi, _ei] if orientation == Orientation.horizontal else table_type_data[_ei, _vi]

    headers = []
    for vector_index in range(table_range.vector_count(orientation)):
        running_type = get(vector_index, 0)
        running_header = 0
        for element_index in range(1, table_range.vector_length(orientation)):
            current_type = get(vector_index, element_index)
            if Typing.lowest_common_ancestor(current_type, running_type) is None:
                running_header = max(running_header, element_index)
                running_type = current_type

        headers.append(running_header)

    return headers


def detect_table_ranges(data, typed=False):
    if not typed:
        data = numpy.array(data, dtype=object)
        type_data = numpy.vectorize(Typing.detect_type)(data)
    else:
        type_data = data

    ranges = []

    def find_range(_c, _r):
        for _i, _range in enumerate(ranges):
            if _range is not None and _range.contains_cell((_c, _r)):
                return _i, _range
        return None

    for r in range(numpy.size(type_data, 0)):
        for c in range(numpy.size(type_data, 1)):
            if type_data[r, c] != "None":
                selected_range = find_range(c, r)
                if selected_range is None:
                    top_range = find_range(c, r - 1) if r - 1 >= 0 else None
                    left_range = find_range(c - 1, r) if c - 1 >= 0 else None
                    cell_range = Range(c, r, 1, 1)
                    if top_range is None and left_range is None:
                        ranges.append(cell_range)
                    elif top_range is None:
                        ranges[left_range[0]] = cell_range.bounding_box(left_range[1])
                    elif left_range is None:
                        ranges[top_range[0]] = cell_range.bounding_box(top_range[1])
                    else:
                        ranges[top_range[0]] = top_range[1].bounding_box(left_range[1])
                        ranges[left_range[0]] = None

    ranges = [r for r in ranges if r is not None]
    table_ranges = []

    for t_range in ranges:
        t_type_data = t_range.get_data(type_data)
        row_headers = get_headers_count(t_range, t_type_data, Orientation.horizontal)
        column_headers = get_headers_count(t_range, t_type_data, Orientation.vertical)
        headers = None
        cells = 0

        for column_header in range(t_range.columns):
            row_header = max(column_headers[column_header:])
            cell_score = (t_range.rows - row_header) * (t_range.columns - column_header)
            if cell_score > cells:
                cells = cell_score
                headers = (column_header, row_header)

        for row_header in range(t_range.rows):
            column_header = max(row_headers[row_header:])
            cell_score = (t_range.rows - row_header) * (t_range.columns - column_header)
            if cell_score > cells:
                cells = cell_score
                headers = (column_header, row_header)

        t_r = t_range.intersect(Range(t_range.x0 + headers[0], t_range.y0 + headers[1], t_range.columns, t_range.rows))
        table_ranges.append(t_r)

    return table_ranges
