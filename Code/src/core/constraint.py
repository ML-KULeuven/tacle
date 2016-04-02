from typing import List

from core.assignment import Source, Filter, Variable, SameLength, ConstraintSource, NotSubgroup, SameTable, \
    SameOrientation, SameType
from core.group import GType


class Constraint:
    def __init__(self, name, print_format, source: Source, filters: List[Filter]):
        self.name = name
        self.print_format = print_format
        self.source = source
        self._filters = filters

    @property
    def filters(self):
        return self._filters

    @property
    def variables(self):
        return self.source.variables

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


integer = {GType.int}
numeric = {GType.int, GType.float}
textual = {GType.string}
discrete = {GType.string, GType.int}


class SumColumn(Constraint):
    def __init__(self):
        variables = [Variable("X", types=numeric), Variable("Y", vector=True, types=numeric)]
        filters = []
        super().__init__("column-sum", "{Y} = SUM({X}, col)", Source(variables), filters)


class SumRow(Constraint):
    def __init__(self):
        variables = [Variable("X", types=numeric), Variable("Y", vector=True, types=numeric)]
        filters = []
        super().__init__("row-sum", "{Y} = SUM({X}, row)", Source(variables), filters)


class Permutation(Constraint):
    x = Variable("X", types=numeric)

    def __init__(self):
        filters = []
        variables = [self.x]
        super().__init__("permutation", "PERMUTATION({X})", Source(variables), filters)


class Series(Constraint):
    x = Variable("X", types=numeric)

    def __init__(self):
        filters = []
        variables = [self.x]
        super().__init__("series", "SERIES({X})", Source(variables), filters)


class AllDifferent(Constraint):
    x = Variable("X", types=discrete)

    def __init__(self):
        filters = []
        variables = [self.x]
        super().__init__("all-different", "ALLDIFFERENT({X})", Source(variables), filters)


class Rank(Constraint):
    x = Variable("X", vector=True, types=numeric)
    y = Variable("Y", vector=True, types=integer)

    def __init__(self):
        variables = [self.x, self.y]
        filters = [SameLength(variables)]
        super().__init__("rank", "{Y} = RANK({X})", Source(variables), filters)


class ForeignKey(Constraint):
    pk = Variable("PK", vector=True, types=discrete)
    fk = Variable("FK", vector=True, types=discrete)

    def __init__(self):
        variables = [self.pk, self.fk]
        source = ConstraintSource(variables, AllDifferent(), {"X": "PK"})
        filters = [NotSubgroup([self.pk, self.fk]), SameType(variables)]
        super().__init__("foreign-key", "{FK} -> {PK}", source, filters)


class Lookup(Constraint):
    o_key = Variable("OK", vector=True, types=discrete)
    o_value = Variable("OV", vector=True)
    f_key = Variable("FK", vector=True, types=discrete)
    f_value = Variable("FV", vector=True)

    def __init__(self):
        variables = [self.o_key, self.o_value, self.f_key, self.f_value]
        source = ConstraintSource(variables, ForeignKey(), {"PK": "OK", "FK": "FK"})
        filters = [SameLength([self.f_key, self.f_value]), SameLength([self.o_key, self.o_value]),
                   SameTable([self.f_key, self.f_value]), SameTable([self.o_key, self.o_value]),
                   SameOrientation([self.f_key, self.f_value]), SameOrientation([self.o_key, self.o_value])]
        super().__init__("lookup", "{FV} = LOOKUP({FK}, {OK}, {OV})", source, filters)


class SumIf(Constraint):
    o_key = Variable("OK", vector=True, types=textual)
    result = Variable("R", vector=True, types=numeric)
    f_key = Variable("FK", vector=True, types=textual)
    values = Variable("V", vector=True, types=numeric)

    def __init__(self):
        variables = [self.o_key, self.result, self.f_key, self.values]
        foreign_key = ForeignKey()
        source = ConstraintSource(variables, foreign_key, {foreign_key.pk.name: "OK", foreign_key.fk.name: "FK"})
        filters = [SameLength([self.o_key, self.result]), SameLength([self.f_key, self.values]),
                   SameTable([self.o_key, self.result]), SameTable([self.f_key, self.values]),
                   SameOrientation([self.o_key, self.result]), SameOrientation([self.f_key, self.values])]
        super().__init__("sum-if", "{R} = SUM({FK}={OK}, {V})", source, filters)


class RunningTotal(Constraint):
    acc = Variable("A", vector=True, types=numeric)
    pos = Variable("P", vector=True, types=numeric)
    neg = Variable("N", vector=True, types=numeric)

    def __init__(self):
        variables = [self.acc, self.pos, self.neg]
        source = Source(variables)
        filters = [SameLength(variables)]
        super().__init__("running-total", "{A} = PREV({A}) + {P} - {N}", source, filters)


class ForeignProduct(Constraint):
    f_key = Variable("FK", vector=True, types=discrete)
    o_key = Variable("OK", vector=True, types=discrete)
    result = Variable("R", vector=True, types=numeric)
    f_value = Variable("FV", vector=True, types=numeric)
    o_value = Variable("OV", vector=True, types=numeric)

    def __init__(self):
        foreign = [self.f_key, self.result, self.f_value]
        original = [self.o_key, self.o_value]
        variables = foreign + original
        foreign_key = ForeignKey()
        source = ConstraintSource(variables, foreign_key, {foreign_key.pk.name: "OK", foreign_key.fk.name: "FK"})
        filters = [SameLength(foreign), SameTable(foreign), SameOrientation(foreign),
                   SameLength(original), SameTable(original), SameOrientation(original)]
        super().__init__("foreign-product", "{R} = PRODUCT({FV}, {FK}={OK} | {OV})", source, filters)
