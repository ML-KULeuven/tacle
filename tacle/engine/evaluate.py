from typing import Dict, Any

import numpy as np

from tacle.core.assignment import Variable
from tacle.indexing import Orientation
from tacle.core.template import (
    ConditionalAggregate,
    ConstraintTemplate,
    Aggregate,
    Operation,
    Lookup,
    Ordered,
    MutualExclusivity,
    Rank,
    MutualExclusiveVector,
    Product,
    Diff,
    DateDifference)


class UnsupportedFormula(BaseException):
    def __init__(self, template):
        super().__init__("Cannot evaluate {}".format(template))
        self.template = template


class InvalidArguments(BaseException):
    pass


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

    assignment = {
        (k.name if isinstance(k, Variable) else k): v for k, v in assignment.items()
    }
    if all(type(k) == str for k in assignment.keys()):
        assignment = {
            v: assignment[v.name]
            if isinstance(assignment[v.name], np.ndarray)
            else assignment[v.name].data
            for v in template.variables
            if v != template.target
        }

    if isinstance(template, ConditionalAggregate):
        ok, fk, v = (
            assignment[v] for v in [template.o_key, template.f_key, template.values]
        )
        if any(len(d.shape) != 1 for d in (ok, fk, v)):
            raise InvalidArguments()
        result = {k: [] for k in ok}
        for i in range(len(fk)):
            if fk[i] not in result:
                raise InvalidArguments()
            result[fk[i]].append(v[i])
        return np.array(
            [
                template.operation.aggregate_f(np.array(result[k]))
                if len(result[k]) > 0
                else op_neutral(template.operation)
                for k in ok
            ]
        )

    elif isinstance(template, Aggregate):
        x = assignment[template.x]
        axis = 1 if Orientation.is_horizontal(template.orientation) else 0
        return template.operation.aggregate(x, axis)

    elif isinstance(template, Product):
        return assignment[template.first] * assignment[template.second]

    elif isinstance(template, Diff):
        return assignment[template.first] - assignment[template.second]

    elif isinstance(template, Lookup):
        ok, ov, fk = (
            assignment[v] for v in [template.o_key, template.o_value, template.f_key]
        )
        if any(len(d.shape) > 1 for d in (ok, ov, fk)):
            ok, ov, fk = ok.squeeze(), ov.squeeze(), fk.squeeze()

        d = {k: v for k, v in zip(ok, ov)}
        return np.array([d[k] for k in fk])

    elif isinstance(template, Rank):
        from tacle.engine.native import rank_data

        x = assignment[Rank.x].squeeze()
        return np.array(rank_data(x))

    elif isinstance(template, DateDifference):
        pass

    elif template.target:
        raise UnsupportedFormula(template)

    else:
        raise ValueError("Cannot evaluate constraint")


def check_template(template, assignment):
    # type: (ConstraintTemplate, Dict[str, np.ndarray]) -> bool

    assignment = {
        (k.name if isinstance(k, Variable) else k): v for k, v in assignment.items()
    }

    if isinstance(template, Ordered):
        x = assignment[template.x.name]
        for i in range(len(x) - 1):
            if x[i + 1] < x[i]:
                return False
        return True

    elif isinstance(template, MutualExclusivity):
        x = assignment[template.x.name]
        return template.test_data(x)

    elif isinstance(template, MutualExclusiveVector):
        x = assignment[template.x.name]
        return template.test_data(x)

    elif not template.target:
        raise RuntimeError("Cannot evaluate {}".format(template))

    else:
        res = assignment[template.target.name].squeeze()
        computed = evaluate_template(template, assignment)
        return np.all(np.abs(res - computed) < 10 ** -10)
