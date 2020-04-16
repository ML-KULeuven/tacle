from typing import Union, List, Optional

import numpy as np

from .core.virtual_template import VirtualLookup, VirtualConditionalAggregate
from .core.solutions import Solutions

from .indexing import Table, Block, Orientation, Range


def learn_constraints(data, tables, virtual=False, solve_timeout=None, semantic=False):
    # type: (np.ndarray, List[Table], bool, Optional[int], bool) -> Solutions

    if semantic:
        from .semantic_learning import get_default_templates
        from .semantic_learning import learn
    else:
        from .workflow import get_default_templates
        from .workflow import main as learn

    # if virtual:
    #     groups += [make_virtual_block(tables[1], Orientation.vertical, Typing.float)]
    templates = get_default_templates()
    if virtual:
        templates.append(VirtualLookup())
        templates += VirtualConditionalAggregate.instances()
    return learn(tables, templates, solve_timeout)
