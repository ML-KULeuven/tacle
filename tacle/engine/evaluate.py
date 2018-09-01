from typing import List, Dict, Tuple, Any

import numpy as np

from tacle.core.group import Orientation
from tacle.core.template import ConditionalAggregate, ConstraintTemplate, Aggregate, Operation, Lookup


def op_neutral(operation):
    # type: (Operation) -> Any
    if operation == Operation.SUM:
        return 0
    elif operation == Operation.PRODUCT:
        return 1
    elif operation == Operation.MAX:
        return None
    elif operation == Operation.MIN:
        return None
    elif operation == Operation.AVERAGE:
        return 0
    elif operation == Operation.COUNT:
        return 0
    else:
        raise ValueError("Unknown operation {}".format(operation))


def evaluate_template(template, assignment):
    # type: (ConstraintTemplate, Dict[str, np.ndarray]) -> np.ndarray
    if isinstance(template, ConditionalAggregate):
        ok, fk, v = (assignment[v] for v in [template.o_key, template.f_key, template.values])
        result = {k: [] for k in ok}
        for i in range(len(fk)):
            result[fk[i]].append(v[i])
        return np.array([template.operation.aggregate_f(np.array(result[k]))
                         if len(result[k]) > 0
                         else op_neutral(template.operation)
                         for k in ok])

    elif isinstance(template, Aggregate):
        x = assignment[template.x]
        axis = 0 if template.orientation == Orientation.HORIZONTAL else 1
        return template.operation.aggregate(x, axis=axis)

    elif isinstance(template, Lookup):
        ok, ov, fk = (assignment[v] for v in [template.o_key, template.o_value, template.f_key])
        d = {k: v for k, v in zip(ok, ov)}
        return np.array([d[k] for k in fk])

    elif template.target:
        raise RuntimeError("Cannot evaluate {}".format(template))

    else:
        raise ValueError("Cannot evaluate constraint")
