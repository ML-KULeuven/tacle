from enum import Enum
from typing import List, Dict, Union

import numpy

from .assignment import (
    Source,
    Filter,
    Variable,
    SameLength,
    ConstraintSource,
    SameTable,
    SameOrientation,
    SameType,
    SizeFilter,
    Not,
    NotPartial,
    Partial,
    Neighbors,
)
from tacle.indexing import Orientation, Typing, Block


class ConstraintTemplate:
    def __init__(
        self, name, print_format, source, filters, depends_on=None, target=None
    ):
        # type: (str, str, Source, List[Filter], Union[set, None], Union[Variable, None]) -> None
        self.name = name
        self.print_format = print_format
        self.source = source
        self._filters = filters
        self._depends_on = source.depends_on()
        if depends_on is not None:
            self._depends_on |= depends_on
        self.target = target

    @property
    def filters(self):
        return self._filters

    @property
    def variables(self):
        return self.source.variables

    def is_formula(self):
        return self.target is not None

    def depends_on(self):
        return self._depends_on

    def get_variables(self):
        return self.variables

    def to_string(self, assignment):
        return self.print_format.format(**assignment)

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not (self == other)


integer = {Typing.int}
numeric = {Typing.int, Typing.float}
textual = {Typing.string}
discrete = {Typing.string, Typing.int}


def filter_nan(e):
    return not numpy.isnan(e)


def filter_none(e):
    return e is not None


def blank_filter(data, vectorized=False):
    if numpy.issubdtype(data.dtype, numpy.floating):
        blank, blank_f = [numpy.nan, filter_nan]
    else:
        blank, blank_f = [None, filter_none]
    return blank, (blank_f if not vectorized else numpy.vectorize(blank_f))


def count_agg(data, axis=None):
    if axis is None:
        res = [len(data.flatten())]
    elif axis == 0:
        res = [data.shape[0]] * data.shape[1]
    elif axis == 1:
        res = [data.shape[1]] * data.shape[0]
    else:
        raise Exception("Invalid axis: {}".format(axis))
    return numpy.array(res)


class Operation(Enum):
    SUM = (numpy.sum, lambda x, y: x + y)
    MAX = (numpy.max, lambda x, y: max(x, y))
    MIN = (numpy.min, lambda x, y: min(x, y))
    AVERAGE = (numpy.average, lambda x, y: (x + y) / 2)
    PRODUCT = (numpy.product, lambda x, y: x * y)
    COUNT = (count_agg, lambda x, y: x + y)

    # noinspection PyInitNewSignature
    def __init__(self, aggregate, func):
        self.aggregate_f = aggregate
        self._func = func

    @property
    def aggregate(self):
        def apply(data, axis=None, partial=True):
            data = numpy.array(data)
            if axis == 1:
                data = data.T

            if not data.shape:
                data = numpy.array([[data]])
            blank, blank_test = blank_filter(data, vectorized=True)
            if len(data.shape) > 1:
                rows, cols = data.shape
                if partial:
                    results = numpy.array([blank] * cols)
                    for i in range(cols):
                        vec = data[:, i][blank_test(data[:, i])]
                        if len(vec) != 0:
                            vec = numpy.array(vec, dtype=numpy.float64)
                            results[i] = self.aggregate_f(vec)
                    return results
                else:
                    return self.aggregate_f(data, 0)
            else:
                if partial:
                    array = numpy.array(data[blank_test(data)], dtype=numpy.float64)
                    return self.aggregate_f(array) if len(array) > 0 else blank
                else:
                    return self.aggregate_f(data)

        return apply

    @property
    def func(self):
        return self._func


class Aggregate(ConstraintTemplate):
    x = Variable("X", types=numeric)
    y = Variable("Y", vector=True, types=numeric)

    def __init__(self, orientation: Orientation, operation: Operation):
        self._orientation = orientation
        self._operation = operation
        self.min_size = 2
        self.min_vectors = (
            3 if operation == Operation.PRODUCT or operation == Operation.SUM else 2
        )
        size = Filter.cols if Orientation.is_vertical(orientation) else Filter.rows
        or_string = "col" if Orientation.is_vertical(orientation) else "row"
        op_string = operation.name
        variables = [self.x, self.y]

        def test(_, a: Dict[str, Block], _solutions):
            x_group, y_group = [a[v.name] for v in variables]
            o_match = Filter.orientation(x_group) == orientation
            # o_match = x_group.row == (orientation == Orientation.HORIZONTAL)
            if not o_match and Filter.vector_count(x_group) < self.min_vectors:
                return False
            return (
                Filter.vector_length(y_group) <= size(x_group)
                if o_match
                else Filter.vector_length(y_group) == size(x_group)
            )

        filter_class = type(
            "{}{}Length".format(op_string.lower().capitalize(), or_string.capitalize()),
            (Filter,),
            {"test": test},
        )
        x_size_filter = (
            SizeFilter([self.x], rows=self.min_size)
            if Orientation.is_vertical(orientation)
            else SizeFilter([self.x], cols=self.min_size)
        )
        filters = [x_size_filter, filter_class(variables)]
        format_s = "{Y} = " + op_string.upper() + "({X}, " + or_string + ")"
        name = "{} ({})".format(op_string.lower(), or_string)
        # TODO Dependency only min max average
        super().__init__(
            name, format_s, Source(variables), filters, {Equal(), Projection()}, self.y
        )

    @property
    def orientation(self):
        return self._orientation

    @property
    def operation(self):
        return self._operation

    @classmethod
    def instance(cls, orientation: Orientation, operation: Operation):
        return Aggregate(orientation, operation)

    @classmethod
    def instances(cls):
        return list(
            cls.instance(o, op) for o in Orientation.all() for op in Operation
        )  # if not op == Operation.PRODUCT)


class GroupedAggregate(ConstraintTemplate):
    k1 = Variable("K1", vector=True, types=discrete)
    k2 = Variable("K2", vector=True, types=discrete)
    v = Variable("V", vector=True, types=numeric)

    def __init__(self, operation: Operation):
        self._operation = operation
        name = operation.name
        variables = [self.k1, self.k2, self.v]
        filters = [
            SameLength([self.k1, self.k2, self.v]),
            SameTable([self.k1, self.k2, self.v]),
            NotPartial([self.k1, self.k2, self.v]),
            SameOrientation([self.k1, self.k2, self.v]),
            Neighbors([self.k1, self.k2]),
            # Not(SatisfiesConstraint([self.k1], AllDifferent(), {self.k1.name: AllDifferent.x.name})),
            # Not(SatisfiesConstraint([self.k2], AllDifferent(), {self.k2.name: AllDifferent.x.name})),
        ]
        p_format = name.upper() + "({V}, GROUP-BY: {K1}, {K2})"
        super().__init__(
            "{}-group-by2".format(name.lower()),
            p_format,
            Source(variables),
            filters,
            {AllDifferent()},
        )

    @property
    def operation(self) -> Operation:
        return self._operation

    @classmethod
    def instance(cls, operation: Operation):
        return GroupedAggregate(operation)

    @classmethod
    def instances(cls):
        return list(cls.instance(op) for op in Operation if not op == Operation.PRODUCT)


# TODO Same table, different orientation, overlapping bounds => prune assignment already

# TODO Subset -> Fuzzy lookup


class Permutation(ConstraintTemplate):
    x = Variable("X", types=numeric)

    def __init__(self):
        variables = [self.x]
        source = ConstraintSource(
            variables, AllDifferent(), {AllDifferent.x.name: self.x.name}
        )
        filters = [NotPartial(variables)]
        super().__init__("permutation", "PERMUTATION({X})", source, filters)


class Series(ConstraintTemplate):
    x = Variable("X", types=numeric)

    def __init__(self):
        variables = [self.x]
        source = ConstraintSource(
            variables, Permutation(), {Permutation.x.name: self.x.name}
        )
        filters = [NotPartial(variables)]
        super().__init__("series", "SERIES({X})", source, filters, None, self.x)


class AllDifferent(ConstraintTemplate):
    x = Variable("X", types=discrete)

    def __init__(self):
        variables = [self.x]
        filters = [NotPartial(variables), SizeFilter(variables, length=2)]
        super().__init__(
            "all-different", "ALLDIFFERENT({X})", Source(variables), filters
        )


class Ordered(ConstraintTemplate):
    x = Variable("X", types=numeric)

    def __init__(self):
        variables = [self.x]
        source = Source(variables)
        filters = [NotPartial(variables), SizeFilter(variables, length=2)]
        super().__init__("ordered", "ORDERED({X})", source, filters)


class Rank(ConstraintTemplate):
    x = Variable("X", vector=True, types=numeric)
    y = Variable("Y", vector=True, types=integer)

    def __init__(self):
        variables = [self.x, self.y]
        source = Source(variables)  # Not from Permutation because of possible ties
        filters = [SameLength(variables), NotPartial(variables)]
        super().__init__("rank", "{Y} = RANK({X})", source, filters, {Equal()}, self.y)


class ForeignKey(ConstraintTemplate):
    pk = Variable("PK", vector=True, types=discrete)
    fk = Variable("FK", vector=True, types=discrete)

    def __init__(self):
        variables = [self.pk, self.fk]
        source = ConstraintSource(variables, AllDifferent(), {"X": "PK"})
        filters = [
            Not(SameTable(variables)),
            SameType(variables),
            NotPartial([self.pk]),
        ]
        super().__init__("foreign-key", "{FK} -> {PK}", source, filters)


class Lookup(ConstraintTemplate):
    o_key = Variable("OK", vector=True, types=discrete)
    o_value = Variable("OV", vector=True)
    f_key = Variable("FK", vector=True, types=discrete)
    f_value = Variable("FV", vector=True)

    def __init__(self):
        variables = [self.o_key, self.o_value, self.f_key, self.f_value]
        source = ConstraintSource(variables, ForeignKey(), {"PK": "OK", "FK": "FK"})
        filters = [
            SameType([self.o_value, self.f_value]),
            NotPartial(variables),
            SameLength([self.f_key, self.f_value]),
            SameLength([self.o_key, self.o_value]),
            SameTable([self.f_key, self.f_value]),
            SameTable([self.o_key, self.o_value]),
            SameOrientation([self.f_key, self.f_value]),
            SameOrientation([self.o_key, self.o_value]),
        ]
        super().__init__(
            "lookup",
            "{FV} = LOOKUP({FK}, {OK}, {OV})",
            source,
            filters,
            {Equal()},
            self.f_value,
        )


class FuzzyLookup(ConstraintTemplate):
    o_key = Variable("OK", vector=True, types=numeric)
    o_value = Variable("OV", vector=True)
    f_key = Variable("FK", vector=True, types=numeric)
    f_value = Variable("FV", vector=True)

    def __init__(self):
        variables = [self.o_key, self.o_value, self.f_key, self.f_value]
        # source = Source(variables)
        source = ConstraintSource(
            variables, Ordered(), {Ordered.x.name: self.o_key.name}
        )
        filters = [
            SameType([self.o_value, self.f_value]),
            NotPartial(variables),
            SameLength([self.f_key, self.f_value]),
            SameLength([self.o_key, self.o_value]),
            SameTable([self.f_key, self.f_value]),
            SameTable([self.o_key, self.o_value]),
            SameOrientation([self.f_key, self.f_value]),
            SameOrientation([self.o_key, self.o_value]),
        ]
        print_format = "{FV} = FUZZY-LOOKUP({FK}, {OK}, {OV})"
        super().__init__(
            "fuzzy-lookup", print_format, source, filters, {Equal()}, self.f_value
        )


class ConditionalAggregate(ConstraintTemplate):
    o_key = Variable("OK", vector=True, types=discrete)
    result = Variable("R", vector=True, types=numeric)
    f_key = Variable("FK", vector=True, types=discrete)
    values = Variable("V", vector=True, types=numeric)

    def __init__(self, operation: Operation, default=0):
        self._default = default
        self._operation = operation
        name = operation.name
        variables = [self.o_key, self.result, self.f_key, self.values]
        all_diff = AllDifferent()
        source = ConstraintSource(variables, all_diff, {all_diff.x.name: "OK"})
        filters = [
            SameLength([self.o_key, self.result]),
            SameLength([self.f_key, self.values]),
            SameTable([self.f_key, self.values]),
            Not(SameTable([self.f_key, self.o_key])),
            # SameTable([self.o_key, self.result]),  # TODO think about this
            NotPartial([self.o_key]),
            SameType([self.f_key, self.o_key]),
            SameOrientation([self.o_key, self.result]),
            SameOrientation([self.f_key, self.values]),
        ]
        p_format = "{R} = " + name.upper() + "IF({FK}={OK}, {V})"
        super().__init__(
            "{}-if".format(name.lower()),
            p_format,
            source,
            filters,
            {Lookup()},
            self.result,
        )

    @property
    def operation(self) -> Operation:
        return self._operation

    @property
    def default(self):
        return self._default

    @classmethod
    def instance(cls, operation: Operation):
        return ConditionalAggregate(operation)

    @classmethod
    def instances(cls):
        return list(cls.instance(op) for op in Operation if not op == Operation.PRODUCT)


class ConditionalAggregate2(ConstraintTemplate):
    ok1 = Variable("OK1", vector=True, types=discrete)
    ok2 = Variable("OK2", vector=True, types=discrete)
    result = Variable("R", vector=True, types=numeric)
    fk1 = Variable("FK1", vector=True, types=discrete)
    fk2 = Variable("FK2", vector=True, types=discrete)
    values = Variable("V", vector=True, types=numeric)

    def __init__(self, operation: Operation, default=0):
        self._default = default
        self._operation = operation
        name = operation.name
        variables = [self.ok1, self.ok2, self.result, self.fk1, self.fk2, self.values]
        source = Source(variables)

        filters = [
            SameLength([self.ok1, self.ok2, self.result]),
            SameTable([self.ok1, self.ok2, self.result]),
            SameOrientation([self.ok1, self.ok2, self.result]),
            Neighbors([self.ok1, self.ok2]),

            SameLength([self.fk1, self.fk2, self.values]),
            SameTable([self.fk1, self.fk2, self.values]),
            SameOrientation([self.fk1, self.fk2, self.values]),
            Neighbors([self.fk1, self.fk2]),

            Not(SameTable([self.ok1, self.fk1])),

            NotPartial([self.ok1, self.ok2, self.fk1, self.fk2]),
            SameType([self.ok1, self.fk1]),
            SameType([self.ok2, self.fk2]),
        ]

        p_format = "{R} = " + name.upper() + "IF({FK1},{FK2}={OK1},{OK2}, {V})"
        super().__init__(
            "{}-if2".format(name.lower()),
            p_format,
            source,
            filters,
            None,
            self.result,
        )

    @property
    def operation(self) -> Operation:
        return self._operation

    @property
    def default(self):
        return self._default

    @classmethod
    def instances(cls):
        return list(cls(op) for op in Operation if not op == Operation.PRODUCT)


class RunningTotal(ConstraintTemplate):
    acc = Variable("A", vector=True, types=numeric)
    pos = Variable("P", vector=True, types=numeric)
    neg = Variable("N", vector=True, types=numeric)

    def __init__(self):
        variables = [self.acc, self.pos, self.neg]
        source = Source(variables)
        filters = [
            SameLength(variables),
            SizeFilter(variables, length=2),
            NotPartial(variables),
        ]
        super().__init__(
            "running-total",
            "{A} = PREV({A}) + {P} - {N}",
            source,
            filters,
            {Equal()},
            self.acc,
        )


class ForeignOperation(ConstraintTemplate):
    f_key = Variable("FK", vector=True, types=discrete)
    o_key = Variable("OK", vector=True, types=discrete)
    result = Variable("R", vector=True, types=numeric)
    f_value = Variable("FV", vector=True, types=numeric)
    o_value = Variable("OV", vector=True, types=numeric)

    def __init__(self, name: str, operation: Operation):
        self._operation = operation
        foreign = [self.f_key, self.result, self.f_value]
        original = [self.o_key, self.o_value]
        variables = foreign + original
        foreign_key = ForeignKey()
        source = ConstraintSource(
            variables,
            foreign_key,
            {foreign_key.pk.name: "OK", foreign_key.fk.name: "FK"},
        )
        filters = [
            SameLength(foreign),
            SameTable(foreign),
            SameOrientation(foreign),
            NotPartial(variables),
            SameLength(original),
            SameTable(original),
            SameOrientation(original),
        ]
        super().__init__(
            "foreign-" + name.lower(),
            "{R} = " + name.upper() + "({FV}, {FK}={OK} | {OV})",
            source,
            filters,
            None,
            self.result,
        )

    @property
    def operation(self):
        return self._operation


class ForeignProduct(ForeignOperation):
    def __init__(self):
        super().__init__("PRODUCT", Operation.PRODUCT)


class VectorOperation(ConstraintTemplate):
    result = Variable("R", vector=True, types=numeric)
    first = Variable("O1", vector=True, types=numeric)
    second = Variable("O2", vector=True, types=numeric)

    def __init__(
        self, name, p_format, source, filters, symmetric=False, depends_on=None
    ):
        self._symmetric = symmetric
        super().__init__(name, p_format, source, filters, depends_on, self.result)

    @property
    def symmetric(self):
        return self._symmetric

    @classmethod
    def list_variables(cls):
        return [cls.result, cls.first, cls.second]


class Product(VectorOperation):
    def __init__(self):
        variables = self.list_variables()
        source = Source(variables)
        filters = [SameLength(variables), NotPartial(variables)]
        super().__init__("product", "{R} = {O1} * {O2}", source, filters, True)


class Diff(VectorOperation):
    def __init__(self):
        variables = self.list_variables()
        source = Source(variables)
        filters = [
            SameLength(variables),
            NotPartial(variables),
            SameOrientation(variables),
        ]
        super().__init__("difference", "{R} = {O1} - {O2}", source, filters)


class PercentualDiff(VectorOperation):
    def __init__(self):
        variables = self.list_variables()
        source = Source(variables)
        filters = [
            SameLength(variables),
            NotPartial(variables),
            SameOrientation(variables),
        ]
        super().__init__(
            "percentual-diff",
            "{R} = ({O1} - {O2}) / {O2}",
            source,
            filters,
            False,
            {Equal()},
        )


class Projection(ConstraintTemplate):
    result = Variable("R", vector=True)
    projected = Variable("P")

    def __init__(self):
        variables = [self.result, self.projected]
        source = Source(variables)
        filters = [
            SameLength(variables),
            SameOrientation(variables),
            SameTable(variables),
            SameType(variables),
            SizeFilter([self.projected], vectors=2),
            Partial([self.projected]),
        ]
        super().__init__(
            "project", "{R} = PROJECT({P})", source, filters, None, self.result
        )


class SumProduct(ConstraintTemplate):
    result = Variable("R", vector=True, types=numeric)
    first = Variable("O1", vector=True, types=numeric)
    second = Variable("O2", vector=True, types=numeric)

    def __init__(self):
        variables = [self.result, self.first, self.second]
        source = Source(variables)
        filters = [
            SameLength([self.first, self.second]),
            NotPartial(variables),
            SizeFilter([self.first, self.second], length=2),
            SizeFilter([self.result], rows=1, cols=1),
            SizeFilter([self.result], rows=1, cols=1, max_size=True),
        ]
        super().__init__(
            "sum-product",
            "{R} = SUMPRODUCT({O1}, {O2})",
            source,
            filters,
            None,
            self.result,
        )


class MutualExclusivity(ConstraintTemplate):
    x = Variable("X", vector=False, types=integer)

    def __init__(self, orientation):
        variables = [self.x]
        self.orientation = orientation
        source = Source(variables)
        filters = [
            NotPartial(variables),
            SizeFilter(variables, vectors=2, max_size=False),
        ]
        o_string = "row" if Orientation.is_horizontal(orientation) else "column"
        super().__init__(
            "xor-{}".format(o_string),
            "XOR({{X}}, {})".format(o_string),
            source,
            filters,
        )

    def test_data(self, data: numpy.ndarray):
        if Orientation.is_vertical(self.orientation):
            data = data.T

        for r in range(data.shape[0]):
            for c in range(data.shape[1]):
                if data[r, c] not in (0, 1):
                    return False
            if data[r, :].sum() != 1:
                return False
        return True

    @staticmethod
    def instances():
        return [MutualExclusivity(Orientation.horizontal)]


class MutualExclusiveVector(ConstraintTemplate):
    x = Variable("X", vector=True, types=discrete)

    def __init__(self):
        variables = [self.x]
        source = Source(variables)
        filters = [SizeFilter(variables, length=4, max_size=False)]
        super().__init__("xor-vec", "ONLY-ONE({X})", source, filters)

    @staticmethod
    def test_data(data):
        data = data.squeeze()
        if len(data.shape) > 1:
            return ValueError("Expected vector, got matrix")
        symbols = {}
        for e in data:
            if e not in symbols:
                if len(symbols) == 2:
                    return False
                symbols[e] = 0
            symbols[e] += 1
        return len(symbols) == 2 and any(v == 1 for v in symbols.values())


# class BooleanCondition(ConstraintTemplate):
#     condition = Variable("C", vector=True, types=integer)
#     result = Variable("R", vector=True, types=integer)
#
#     def __init__(self):


class Equal(ConstraintTemplate):
    first = Variable("O1", vector=True)
    second = Variable("O2", vector=True)

    def __init__(self):
        variables = [self.first, self.second]
        source = Source(variables)
        filters = [SameLength(variables), SameType(variables)]
        super().__init__("equal", "{O1} = {O2}", source, filters)


class EqualGroup(ConstraintTemplate):
    x = Variable("X")

    def __init__(self):
        variables = [self.x]
        source = Source(variables)
        filters = [SizeFilter(variables, vectors=2)]
        super().__init__("equal-group", "EQUAL({X})", source, filters)


class DateDifference(VectorOperation):
    def __init__(self):
        variables = self.list_variables()
        source = Source(variables)
        filters = [SameLength(variables)]
        super().__init__("date-difference", "DIFF({Date1}, {Date2}) = {Difference}", source, filters, symmetric=True)

