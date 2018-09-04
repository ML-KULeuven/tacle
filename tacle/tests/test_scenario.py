import os

from tacle.indexing import Range
from tacle.core.template import MutualExclusiveVector
from tacle import learn_from_csv, filter_constraints


def get_constraints(name):
    return learn_from_csv(os.path.join(os.path.dirname(__file__), "res", name))


def test_mutual_exclusive_vector_positive_1():
    constraints = filter_constraints(get_constraints("mutual_exclusive_vector_positive_1.csv"), MutualExclusiveVector)
    assert len(constraints) == 1
    assert Range.from_legacy_bounds(constraints[0][0].bounds).column == 1

