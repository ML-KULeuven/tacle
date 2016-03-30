from typing import List

from core.assignment import Source, Filter, Variable, SameLength, ConstraintSource, NotSubgroup, SameTable, \
    SameOrientation


class Constraint:
    def __init__(self, name, print_format, source: Source, filters: List[Filter]):
        self.name = name
        self.print_format = print_format
        self.source = source
        self._filters = filters
#         self._filters += [create_variable_filter(v) for v in self.variables]

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


class SumColumn(Constraint):
    def __init__(self):
        variables = [Variable("X", numeric=True), Variable("Y", vector=True, numeric=True)]
        filters = []
        super().__init__("column-sum", "{Y} = SUM({X}, col)", Source(variables), filters)


class SumRow(Constraint):
    def __init__(self):
        variables = [Variable("X", numeric=True), Variable("Y", vector=True, numeric=True)]
        filters = []
        super().__init__("row-sum", "{Y} = SUM({X}, row)", Source(variables), filters)


class Permutation(Constraint):
    x = Variable("X", numeric=True)

    def __init__(self):
        filters = []
        variables = [self.x]
        super().__init__("permutation", "PERMUTATION({X})", Source(variables), filters)


class Series(Constraint):
    x = Variable("X", numeric=True)

    def __init__(self):
        filters = []
        variables = [self.x]
        super().__init__("series", "SERIES({X})", Source(variables), filters)


class AllDifferent(Constraint):
    x = Variable("X", textual=True)

    def __init__(self):
        filters = []
        variables = [self.x]
        super().__init__("all-different", "ALLDIFFERENT({X})", Source(variables), filters)


class Rank(Constraint):
    x = Variable("X", vector=True, numeric=True)
    y = Variable("Y", vector=True, integer=True)

    def __init__(self):
        variables = [self.x, self.y]
        filters = [SameLength(variables)]
        super().__init__("rank", "{Y} = RANK({X})", Source(variables), filters)


class ForeignKey(Constraint):
    pk = Variable("PK", vector=True, textual=True)
    fk = Variable("FK", vector=True, textual=True)

    def __init__(self):
        variables = [self.pk, self.fk]
        source = ConstraintSource(variables, AllDifferent(), {"X": "PK"})
        filters = [NotSubgroup([self.pk, self.fk])]
        super().__init__("foreign-key", "{FK} -> {PK}", source, filters)


class Lookup(Constraint):
    o_key = Variable("OK", vector=True, textual=True)
    o_value = Variable("OV", vector=True)
    f_key = Variable("FK", vector=True, textual=True)
    f_value = Variable("FV", vector=True)

    def __init__(self):
        variables = [self.o_key, self.o_value, self.f_key, self.f_value]
        source = ConstraintSource(variables, ForeignKey(), {"PK": "OK", "FK": "FK"})
        filters = [SameLength([self.f_key, self.f_value]), SameLength([self.o_key, self.o_value]),
                   SameTable([self.f_key, self.f_value]), SameTable([self.o_key, self.o_value]),
                   SameOrientation([self.f_key, self.f_value]), SameOrientation([self.o_key, self.o_value])]
        super().__init__("lookup", "{FV} = LOOKUP({FK}, {OK}, {OV})", source, filters)


class SumIf(Constraint):
    o_key = Variable("OK", vector=True, textual=True)
    result = Variable("R", vector=True, numeric=True)
    f_key = Variable("FK", vector=True, textual=True)
    values = Variable("V", vector=True, numeric=True)

    def __init__(self):
        variables = [self.o_key, self.result, self.f_key, self.values]
        foreign_key = ForeignKey()
        source = ConstraintSource(variables, foreign_key, {foreign_key.pk.name: "OK", foreign_key.fk.name: "FK"})
        filters = [SameLength([self.o_key, self.result]), SameLength([self.f_key, self.values]),
                   SameTable([self.o_key, self.result]), SameTable([self.f_key, self.values]),
                   SameOrientation([self.o_key, self.result]), SameOrientation([self.f_key, self.values])]
        super().__init__("sum-if", "{R} = SUM({FK}={OK}, {V})", source, filters)


class RunningTotal(Constraint):
    acc = Variable("A", vector=True, numeric=True)
    pos = Variable("P", vector=True, numeric=True)
    neg = Variable("N", vector=True, numeric=True)

    def __init__(self):
        variables = [self.acc, self.pos, self.neg]
        source = Source(variables)
        filters = [SameLength(variables)]
        super().__init__("running-total", "{A} = PREV({A}) + {P} - {N}", source, filters)
