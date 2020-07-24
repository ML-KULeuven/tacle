from typing import List, Tuple, Union, Optional, Dict

import numpy
import numpy as np

from .indexing import Typing, Range, Orientation, OrientationType


def get_headers_count(table_range: Range, table_type_data, orientation):
    def get(_vi, _ei):
        return (
            table_type_data[_vi, _ei]
            if orientation == Orientation.horizontal
            else table_type_data[_ei, _vi]
        )

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


def get_type_data(data):
    data = numpy.array(data, dtype=object, ndmin=2)
    return numpy.vectorize(Typing.detect_type)(data)


def detect_table_ranges(
    type_data: Union[List[List], np.ndarray],
    typed: bool = True,
    orientation: Optional[OrientationType] = None,
    min_cells: Optional[int] = None,
    min_rows: Optional[int] = None,
    min_columns: Optional[int] = None,
) -> List[Tuple[Range, Dict[OrientationType, Range]]]:
    """
    Detects and returns table ranges in a set of cells
    :param type_data:
        A matrix (list-of-list or numpy array) of data or of types (see tacle.indexing.Typing)
    :param typed:
        If true, then type-data consists of types, otherwise it consists of data and will be converted
    :param orientation:
        If not None, then only table ranges will be returned that are type-consistent in the given orientation.
    :param min_cells:
        If not None, then only table ranges will be returned that contain at least min_cells cells
    :param min_rows:
        If not None, then only table ranges will be returned that contain at least min_rows rows
    :param min_columns:
        If not None, then only table ranges will be returned that contain at least min_columns colums
    :return:
        A list of tuples containing: 1) table range containing type consistent data; and 2) a dictionary mapping
        orientations to header ranges (vertical for a top header and horizontal for a left header)
    """
    if not typed:
        type_data = get_type_data(type_data)

    ranges = []

    def find_range(_c, _r):
        for _i, _range in enumerate(ranges):
            if _range is not None and _range.contains_cell((_c, _r)):
                return _i, _range
        return None

    for r in range(numpy.size(type_data, 0)):
        for c in range(numpy.size(type_data, 1)):
            if type_data[r, c] != Typing.any:
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

        orientations = [Orientation.vertical, Orientation.horizontal] if orientation is None else [orientation]

        # Choose headers that maximize the number of non-header cells
        for o in orientations:
            for header in range(t_range.vector_count(o)):
                if o == Orientation.vertical:
                    candidate_headers = (header, max(column_headers[header:]))
                else:
                    candidate_headers = (max(row_headers[header:]), header)

                cell_score = (t_range.columns - candidate_headers[0]) * (t_range.rows - candidate_headers[1])
                if cell_score > cells:
                    cells = cell_score
                    headers = candidate_headers

        # Pasted in
        selected = Range(
            t_range.x0 + headers[0],
            t_range.y0 + headers[1],
            t_range.columns - headers[0],
            t_range.rows - headers[1],
        )
        t_r = t_range.intersect(selected)
        t_h = {
            Orientation.horizontal: Range(
                t_range.x0 + headers[0],
                t_range.y0,
                t_range.columns - headers[0],
                headers[1],
            ),
            Orientation.vertical: Range(
                t_range.x0,
                t_range.y0 + headers[1],
                headers[0],
                t_range.rows - headers[1],
            ),
        }

        if (
            (min_cells is None or t_r.columns * t_r.rows >= min_cells)
            and (min_rows is None or t_r.rows >= min_rows)
            and (min_columns is None or t_r.columns >= min_columns)
        ):
            table_ranges.append((t_r, t_h))

    return table_ranges
