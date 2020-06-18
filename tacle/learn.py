from typing import Union, List, Optional

import numpy as np

from .core.virtual_template import VirtualLookup, VirtualConditionalAggregate
from .core.solutions import Solutions
from .workflow import main as learn
from .workflow import get_default_templates
from .indexing import Table, Block, Orientation, Range


def learn_constraints(data, tables, virtual=False, solve_timeout=None):
    # type: (np.ndarray, List[Table], bool, Optional[int]) -> Solutions

    # if virtual:
    #     groups += [make_virtual_block(tables[1], Orientation.vertical, Typing.float)]
    templates = get_default_templates()
    if virtual:
        templates.append(VirtualLookup())
        templates += VirtualConditionalAggregate.instances()
    return learn(tables, templates, solve_timeout)
