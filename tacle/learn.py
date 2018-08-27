from typing import Union, List

import numpy as np

from .core.solutions import Solutions
from .workflow import main as learn
from .parse.parser import get_groups
from .indexing import Range


def learn_constraints(data, table_ranges, names=None):
    # type: (np.ndarray, List[Range], Union[None, List[str]]) -> Solutions
    if names is None:
        names = ["T{}".format(i + 1) for i in range(len(table_ranges))]
    bounds_list = [t_range.as_legacy_bounds() for t_range in table_ranges]
    indexing_data = {
        "Tables": [{"Name": name, "Bounds": bounds.bounds} for name, bounds in zip(names, bounds_list)]
    }
    groups = get_groups(np.array(data), indexing_data)
    return learn(None, None, False, True, groups=groups)
