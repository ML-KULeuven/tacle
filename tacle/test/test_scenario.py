import os

from tacle.indexing import Range
from tacle.core.template import MutualExclusiveVector
from tacle import learn_from_file, filter_constraints


def get_constraints(name):
    return learn_from_file(os.path.join(os.path.dirname(__file__), "res", name))


def test_mutual_exclusive_vector_positive_1():
    constraints = filter_constraints(
        get_constraints("mutual_exclusive_vector_positive_1.csv"), MutualExclusiveVector
    )
    assert len(constraints) == 1
    assert constraints[0][0].relative_range.column == 1


def test_ice_cream():
    constraints = get_constraints("magic_ice_cream.csv")
    assert len(constraints) == 6

    sum_constraint = filter_constraints(constraints, "sum*")[0]
    print(sum_constraint["X"])


if __name__ == "__main__":
    test_ice_cream()
