import json

import numpy
from flask import Flask, request, jsonify
from flask_cors import CORS

import workflow
from core.group import Bounds
from experiment import is_excel_constraint
from indexing import Typing, Orientation, Range
from parse.parser import get_groups

app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return "Hello"


@app.route("/foo")
def foo():
    return "foo()"


# def import_data(data_tables):
#     raw_data_list = [data_table["data"] for data_table in data_tables]
#     type_data_list = [numpy.vectorize(Typing.detect_type)(raw_data) for raw_data in raw_data_list]
#     data_list = [numpy.vectorize(Typing.cast)(t, r) for t, r in zip(type_data_list, raw_data_list)]
#
#     tables = [Table(numpy.array(numpy.array(data_table["data"])), data_table["range"], data_table["address"])
#               for data_table in data_tables]
#
#     blocks = []

def learn_constraints(data, data_tables):
    table_bounds_lookup = {data_table["address"]: data_table["bounds"] for data_table in data_tables}
    indexing_data = {"Tables": [{"Name": data_table["address"], "Bounds": data_table["bounds"]}
                                for data_table in data_tables]}
    groups = get_groups(numpy.array(data), indexing_data)
    solutions = workflow.main(None, None, False, True, groups=groups)
    constraints = []
    for constraint in solutions.solutions:
        if is_excel_constraint(constraint) and len(solutions.get_solutions(constraint)) > 0:
            for solution in solutions.get_solutions(constraint):
                constraint_solution = {"name": constraint.name, "vars": dict()}
                for var_name, block in solution.items():
                    absolute_bounds = Bounds(table_bounds_lookup[block.table.name]).combine(block.bounds)
                    block_dict = Range.from_legacy_bounds(absolute_bounds).as_dict()
                    block_dict["orientation"] = str(Orientation.horizontal if block.row else Orientation.vertical)
                    constraint_solution["vars"][var_name] = block_dict
                constraints.append(constraint_solution)
    return constraints


@app.route("/learn/", methods=["POST"])
def learn():
    tables = json.loads(request.form["data"])
    constraints = learn_constraints(tables["data"], tables["indexing"])
    return jsonify(constraints)


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

    return [[t_range.x0, t_range.y0, t_range.columns, t_range.rows] for t_range in table_ranges]


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


@app.route("/detect_tables/", methods=['POST'])
def detect_tables():
    data = json.loads(request.form["data"])
    tables = detect_table_ranges(data)
    return jsonify(tables)


if __name__ == "__main__":
    app.run()
