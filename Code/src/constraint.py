class Variable:
    def __init__(self, name, vector=False, numeric=False, textual=True, integer=False):
        self.name = name
        self.vector = vector
        self.numeric = numeric
        self.integer = integer
        self.textual = textual

    def __str__(self):
        return self.name + "[Var]"

    def get_name(self):
        return self.name

    def is_vector(self):
        return self.vector

    def is_numeric(self):
        return self.numeric

    def is_integer(self):
        return self.numeric

    def is_textual(self):
        return self.textual


class Constraint:
    def __init__(self, name, print_format, variables):
        self.name = name
        self.print_format = print_format
        self.variables = variables

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
        super().__init__("column-sum", "{Y} = SUM({X}, col)", variables)


class SumRow(Constraint):
    def __init__(self):
        variables = [Variable("X", numeric=True), Variable("Y", vector=True, numeric=True)]
        super().__init__("row-sum", "{Y} = SUM({X}, row)", variables)


class Permutation(Constraint):
    def __init__(self):
        super().__init__("permutation", "PERMUTATION({X})", [Variable("X", numeric=True)])


class Series(Constraint):
    def __init__(self):
        super().__init__("series", "SERIES({X})", [Variable("X", numeric=True)])


class AllDifferent(Constraint):
    def __init__(self):
        super().__init__("all-different", "ALLDIFFERENT({X})", [Variable("X", textual=True)])


class Rank(Constraint):
    def __init__(self):
        variables = [Variable("X", vector=True, numeric=True), Variable("Y", vector=True, integer=True)]
        super().__init__("rank", "{Y} = RANK({X})", variables)


class ForeignKey(Constraint):
    pk = Variable("PK", vector=True, textual=True)
    fk = Variable("FK", vector=True, textual=True)

    def __init__(self):
        super().__init__("foreign-key", "{FK} -> {PK}", [self.pk, self.fk])


class Lookup(Constraint):
    o_key = Variable("OK", vector=True, textual=True)
    o_value = Variable("OV", vector=True)
    f_key = Variable("FK", vector=True, textual=True)
    f_value = Variable("FV", vector=True)

    def __init__(self):
        variables = [self.o_key, self.o_value, self.f_key, self.f_value]
        super().__init__("lookup", "{FV} = LOOKUP({FK}, {OK}, {OV})", variables)

