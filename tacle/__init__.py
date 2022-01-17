import fnmatch
from typing import List, Union

import numpy as np

from .parse import parse_file
from .core.virtual_template import is_virtual
from .convert import get_tables
from .detect import detect_table_ranges, get_type_data
from .learn import learn_constraints
from .core.solutions import Constraint


def learn_from_file(
    csv_file, filters=None, virtual=None, solve_timeout=None, tables=None, sheet=None
):
    return learn_from_cells(
        parse_file(csv_file, sheet),
        filters,
        virtual=virtual,
        solve_timeout=solve_timeout,
        tables=tables,
    )


def learn_from_cells(
    data, filters=None, virtual=None, orientation=None, solve_timeout=None, tables=None, templates=None
):
    data = np.array(data, dtype=object)
    type_data = get_type_data(data)
    tables = tables or get_tables(
        data, type_data, detect_table_ranges(type_data, orientation=orientation)
    )
    constraints = learn_constraints(data, tables, virtual, solve_timeout, templates=templates).constraints
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
