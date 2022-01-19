import numpy as np

from tacle.core.template import (
    AllDifferent,
    ForeignKey,
    Equal,
    Aggregate,
    Permutation,
    Rank,
    Series,
    Lookup,
    ConditionalAggregate,
    RunningTotal,
    Diff,
    Ordered,
    MutualExclusiveVector,
    Product,
    MutualExclusivity,
    SumProduct,
    GroupedAggregate,
    Operation,
    ConditionalAggregate2,
)
from tacle.indexing import Table, Range, Typing, Orientation
from tacle import learn_constraints, filter_constraints


def test_nothing():
    pass


def test_all_different_present_int():
    constraints = learn([[[2], [1], [4]]]).constraints
    assert_constraints(constraints, [(AllDifferent, 1)])


def test_foreign_key():
    constraints = learn(
        [
            [["a", 1], ["b", 1], ["c", 4]],
            [["a", "yes"], ["a", "no"], ["c", "no"], ["c", "yes"]],
        ]
    ).constraints

    assert_constraints(constraints, [(AllDifferent, 1), (ForeignKey, 1)])


def test_equal():
    constraints = learn([[["a", 1, "a"], ["b", 1, "b"], ["b", 4, "b"]]]).constraints
    assert_constraints(constraints, [(Equal, 1)])


def test_min():
    constraints = learn(
        [
            [
                ["a", 1.1, 4.4, 3.3, 1.1],
                ["b", 5.5, 3.3, 6.6, 3.3],
                ["b", 2.2, 2.2, 4.4, 2.2],
            ]
        ]
    ).constraints

    assert_constraints(constraints, [(Aggregate, 1)])
    assert "min" in str(constraints[0]).lower()


def test_permutation():
    constraints = learn([[[3], [1], [2]]]).constraints
    assert_constraints(constraints, [(Permutation, 1), (AllDifferent, 1)])


def test_rank():
    constraints = learn([[[3, 340], [1, 500], [2, 420]]]).constraints
    assert_constraints(constraints, [(Permutation, 1), (Rank, 1), (AllDifferent, 2)])


def test_series():
    constraints = learn([[[3, 1], [1, 2], [2, 3]]]).constraints
    assert_constraints(
        constraints, [(Permutation, 2), (Series, 1), (AllDifferent, 2), (Ordered, 1)]
    )


def test_lookup():
    constraints = learn(
        [[["a", 10], ["b", 20], ["c", 20]], [["b", 5, 20], ["a", 5, 10], ["a", 7, 10]]]
    ).constraints
    assert_constraints(constraints, [(AllDifferent, 1), (ForeignKey, 1), (Lookup, 1)])


def test_conditional_max():
    constraints = learn(
        [
            [["a", 15], ["b", 20], ["c", 15]],
            [["b", 5, 20], ["a", 5, 10], ["a", 7, 15], ["c", 7, 15]],
        ]
    ).constraints
    assert_constraints(
        constraints, [(AllDifferent, 1), (ConditionalAggregate, 1), (ForeignKey, 1)]
    )
    assert (
        "max" in str(filter_constraints(constraints, ConditionalAggregate)[0]).lower()
    )


def test_running_total():
    constraints = learn(
        [[["a", 20, 10, 10], ["b", 20, 40, -10], ["c", 15, 15, -10], ["d", 17, 0, 7]]]
    ).constraints
    assert_constraints(constraints, [(AllDifferent, 2), (RunningTotal, 1)])


def test_diff():
    constraints = learn(
        [[["a", 20, 10, 10], ["b", 20, 40, -20], ["c", 15, 15, 0], ["d", 17, 0, 17]]]
    ).constraints
    assert_constraints(constraints, [(AllDifferent, 3), (Diff, 1)])


def test_ordered():
    constraints = learn([[[20, 40], [21, 50], [22, 40]]]).constraints
    assert_constraints(constraints, [(Ordered, 1), (AllDifferent, 1)])


def test_mutex_vector():
    constraints = learn([[[0, 0, 1], [1, 0, 1], [0, 1, 0], [0, 0, 0]]]).constraints
    assert_constraints(constraints, [(MutualExclusiveVector, 2)])


def test_mutex_block():
    constraints = learn(
        [[["a", 0, 0, 1], ["a", 1, 0, 0], ["a", 0, 1, 0], ["a", 0, 1, 0]]]
    ).constraints
    assert_constraints(
        constraints, [(MutualExclusivity, 1), (MutualExclusiveVector, 2)]
    )


def test_product():
    constraints = learn([[[3, 4, 12], [5, 5, 25], [4, 3, 12], [10, 0, 0]]]).constraints
    assert_constraints(constraints, [(Product, 1), (AllDifferent, 2)])


def test_sum_product():
    constraints = learn([[[3, 4], [5, 5], [4, 3], [10, 0]], [[49]]]).constraints
    assert_constraints(constraints, [(SumProduct, 1), (AllDifferent, 2)])


def test_grouped_average():
    constraints = learn(
        [
            [
                ["a", 1, "1.2"],
                ["a", 2, "2.2"],
                ["a", 2, "2.3"],
                ["a", 1, "2.2"],
                ["a", 1, "3.4"],
                ["a", 2, "4.5"],
                ["b", 2, "4.5"],
                ["b", 2, "7.2"],
                ["b", 1, "2.2"],
                ["b", 1, "2.2"],
                ["b", 2, "11.7"],
            ],
        ],
        templates=[AllDifferent(), GroupedAggregate(Operation.SUM)]
    ).constraints

    assert_constraints(constraints, [(GroupedAggregate, 1)])


def test_conditional_aggregate2():
    constraints = learn(
        [
            [
                ["a", 1, "1.2"],
                ["a", 2, "2.2"],
                ["a", 2, "2.3"],
                ["a", 1, "2.2"],
                ["b", 2, "4.5"],
                ["b", 2, "7.2"],
                ["b", 1, "2.2"],
            ],
            [
                ["a", 1, "3.4"],
                ["a", 2, "4.5"],
                ["b", 1, "2.2"],
                ["b", 2, "11.7"],
            ]
        ],
        templates=[AllDifferent(), ConditionalAggregate2(Operation.SUM)]
    ).constraints

    assert_constraints(constraints, [(ConditionalAggregate2, 1)])


def assert_constraints(constraints, template_count_pairs):
    print(*[str(c) for c in constraints], sep="\n")

    total = 0
    for template, count in template_count_pairs:
        total += count
        assert len(filter_constraints(constraints, template)) == count, \
            "Expected {} {} constraints, found {}".format(
                count,
                template.__name__,
                len(filter_constraints(constraints, template))
            )
    assert len(constraints) == total


def learn(data_arrays, templates=None):
    data_arrays = [np.array(arr) for arr in data_arrays]
    total_columns = sum(arr.shape[1] + 1 for arr in data_arrays) - 1
    max_rows = max(arr.shape[0] for arr in data_arrays)
    data = np.array(
        [["" for _c in range(total_columns)] for _r in range(max_rows)], dtype=np.object
    )
    offset = 0
    ranges = []
    for arr in data_arrays:
        shape = arr.shape
        data[0 : shape[0], offset : offset + shape[1]] = arr
        ranges.append(Range(offset, 0, shape[1], shape[0]))
        offset += shape[1] + 1

    type_data = np.vectorize(Typing.detect_type)(data)

    tables = []
    for i, r in enumerate(ranges):
        tables.append(
            Table(
                r.get_data(data),
                r.get_data(type_data),
                r,
                "T{}".format(i+1),
                [Orientation.vertical],
            )
        )
    return learn_constraints(data, tables, templates=templates)
