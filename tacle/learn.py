from typing import Union, List, Optional

import numpy as np

from .core.virtual_template import VirtualLookup, VirtualConditionalAggregate
from .core.solutions import Solutions
from .rank_workflow import main as learn
from .rank_workflow import get_constraint_list
from .parse.parser import get_groups
from .indexing import Table, Block, Orientation, Range, Typing


def learn_constraints(data, tables, virtual=False, solve_timeout=None):
    # type: (np.ndarray, List[Table], bool, Optional[int]) -> Solutions
    for table in tables:
        print("Here is my header: {}".format(table.header))
    indexing_data = {
        "Tables": [
            {
                "Name": table.name, 
                "Header": (table.header.as_legacy_bounds().bounds if table.header is not None else table.header), 
                "Bounds": table.range.as_legacy_bounds().bounds}
            for table in tables
        ],
        "Groups": [
            {
                "Table": table.name,
                "Bounds": block.relative_range.as_legacy_list(block.orientation), #Range.as_legacy_list(orientation)-->Bounds
                "Types": block.vector_types
            }
            for table in tables
            for block in table.blocks
        ]
    }
    groups = get_groups(np.array(data), indexing_data)# groups block based on numeric or string
    # if virtual:
    #     groups += [make_virtual_block(tables[1], Orientation.vertical, Typing.float)]
    templates = get_constraint_list()
    if virtual:
        templates.append(VirtualLookup())
        templates += VirtualConditionalAggregate.instances()
    return learn(data, None, None, tables, False, True, templates, groups=groups, solve_timeout=solve_timeout)


def make_virtual_block(table, orientation, block_type):
    # type: (Table, Orientation, str) -> Block
    if orientation == Orientation.vertical:
        b_range = Range(-1, 0, 1, table.range.height)
    else:
        b_range = Range(0, -1, table.range.width, 1)
    return Block(table, b_range, orientation, virtual=(block_type, False))
