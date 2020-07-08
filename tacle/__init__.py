import fnmatch
from typing import List, Union

import numpy as np
import re

from .parse import parse_file
from .core.virtual_template import is_virtual
from .convert import get_tables
from .detect import detect_table_ranges, get_type_data
from .learn import learn_constraints
from .core.solutions import Constraint
from .indexing import Orientation


def save_heaeder(templates, text_dict):
    with open('dictionary.txt', 'r+') as reader:
        for line in reader.readlines():
            text = line.split("\t")
            key = text[0].strip(": ")
            words = text[1].split(",")
            for t in words:
                # t= re.sub('[-]', '_', t)
                t = re.sub('[\W]+', '', t)
                text_dict[key].append(t)

        for template in templates:
            #TODO Handle while there is no target
            target = template.template.target.name
            assigned_block = template.assignment[target]
            if (assigned_block.orientation == Orientation.vertical):
                header = assigned_block.table.header_data[Orientation.horizontal]
                i = assigned_block.relative_range.column
                header = "\n".join(
                    [str(header[j, i]) for j in range(header.shape[0])]
                )
            else:
                header = assigned_block.table.header_data[Orientation.vertical]
                i = assigned_block.relative_range.row
                header = "\n".join(
                    [str(header[i, j]) for j in range(header.shape[1])]
                )
            text_dict[template.template.name].append(re.sub('[- ]', '_', header))

    f = open("dictionary.txt", "w+")
    for k in text_dict.keys():
        f.write("{}:\t {}\t\n".format(k, list(set(text_dict[k]))))
    f.close()


def save_json_file(templates, text_dict, csv_file, orientation=None, min_cells=None, min_rows=None, min_columns=None):
    import json
    lst = []
    settings = [{
        "orientation": orientation,
        "min_cells": min_cells,
        "min_rows": min_rows,
        "min_columns": min_columns
    }]

    for template in templates:
        target = template.template.target.name \
            if template.template.target is not None \
            else template.template.get_variables()[0].name

        assigned_block = template.assignment[target]
        if assigned_block.orientation == Orientation.vertical:
            header = assigned_block.table.header_data[Orientation.horizontal]
            i = assigned_block.relative_range.column
            header = "\n".join(
                [str(header[j, i]) for j in range(header.shape[0])]
            )
        if assigned_block.orientation == Orientation.horizontal:
            header = assigned_block.table.header_data[Orientation.vertical]
            i = assigned_block.relative_range.row
            header = "\n".join(
                [str(header[i, j]) for j in range(header.shape[1])]
            )
        text_dict[template.template.name].append(re.sub('[- ]', '_', header))

        dictionary = {
                "word": "{}".format(str(header)),
                "template": "{}".format(template.template.name),
                "FalsePositive": "{}".format("Yes" if template.template.word in ['equal'] else "No"),
                "location": "{}".format(template.assignment)
        }
        if template.template.name != 'equal':
            lst.append(dictionary)

    dictionary = {"settings": settings,
                  "header": lst}

    import os
    base = os.path.splitext(csv_file)[0]
    file_name = "header/{}.json".format(base.split("/")[-1])
    directory= "/".join(base.split("/")[0:-2])+"header"
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file_name, "w+") as f:
        json.dump(dictionary, f, indent=2)

    # data= json.dumps(dic, indent= 2, sort_keys= True)
    # print(data)


def learn_from_file(
    csv_file,
    filters=None,
    virtual=None,
    solve_timeout=None,
    tables=None,
    sheet=None,
    semantic=False,
):
    return learn_from_cells(
        parse_file(csv_file, sheet),
        filters,
        virtual=virtual,
        solve_timeout=solve_timeout,
        tables=tables,
        semantic=semantic,
    )


def learn_from_cells(
    data,
    filters=None,
    virtual=None,
    orientation=None,
    solve_timeout=None,
    tables=None,
    semantic=False,
):
    data = np.array(data, dtype=object)
    type_data = get_type_data(data)
    tables = tables or get_tables(
        data, type_data, detect_table_ranges(type_data, orientation=orientation)
    )
    constraints = learn_constraints(
        data, tables, virtual, solve_timeout, semantic=semantic
    ).constraints
    if virtual:
        # constraints = [c for c in constraints if c.template.target and
        #                (Range.from_legacy_bounds(c.assignment[c.template.target.name].bounds).row == -1
        #                 if c.assignment[c.template.target.name].row
        #                 else Range.from_legacy_bounds(c.assignment[c.template.target.name].bounds).column == -1)]
        constraints = [c for c in constraints if is_virtual(c.template)]
    if filters is not None:
        constraints = filter_constraints(filters)
    return constraints


def ranges_from_csv(csv_file, orientation=None, sheet=None):
    return ranges_from_cells(parse_file(csv_file, sheet), orientation)


def ranges_from_cells(data, orientation=None):
    data = np.array(data, dtype=object)
    type_data = get_type_data(data)
    t_ranges = detect_table_ranges(type_data, orientation=orientation)
    return t_ranges


def tables_from_csv(
    csv_file, orientation=None, min_cells=None, min_rows=None, min_columns=None
):
    return tables_from_cells(
        parse_file(csv_file, sheet=None),
        orientation,
        min_cells=min_cells,
        min_rows=min_rows,
        min_columns=min_columns,
    )


def tables_from_cells(
    data, orientation=None, min_cells=None, min_rows=None, min_columns=None
):
    data = np.array(data, dtype=object)
    type_data = get_type_data(data)
    ranges = detect_table_ranges(
        type_data,
        orientation=orientation,
        min_cells=min_cells,
        min_rows=min_rows,
        min_columns=min_columns,
    )
    return get_tables(data, type_data, ranges)


def filter_constraints(constraints, *args):
    # type: (List[Constraint], List[Union[str, type]]) -> List[Constraint]

    all_formulas = "<formula>" in args or "<f>" in args
    all_constraints = "<constraint>" in args or "<c>" in args

    def check(_c):
        # type: (Constraint) -> bool
        if all_formulas and _c.is_formula():
            return True
        elif all_constraints and not _c.is_formula():
            return True
        return any(
            fnmatch.fnmatch(_c.template.name, pattern)
            if isinstance(pattern, str)
            else isinstance(_c.template, pattern)
            for pattern in args
        )

    return [c for c in constraints if check(c)]
