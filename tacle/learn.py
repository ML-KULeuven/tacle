from typing import Union, List

import numpy as np

from .core.solutions import Solutions
from .workflow import main as learn
from .parse.parser import get_groups
from .indexing import Table


def learn_constraints(data, tables):
    # type: (np.ndarray, List[Table]) -> Solutions
    indexing_data = {
        "Tables": [
            {"Name": table.name, "Bounds": table.range.as_legacy_bounds().bounds}
            for table in tables
        ],
        "Groups": [
            {
                "Table": table.name,
                "Bounds": block.relative_range.as_legacy_list(block.orientation),
                "Types": block.vector_types
            }
            for table in tables
            for block in table.blocks
        ]
    }
    groups = get_groups(np.array(data), indexing_data)
    return learn(None, None, False, True, groups=groups)
