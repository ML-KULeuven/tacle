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

	def accept(self, visitor):
		raise NotImplementedError()

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
		return not(self == other)


class SumColumn(Constraint):
	def __init__(self):
		variables = [Variable("X", numeric=True), Variable("Y", vector=True, numeric=True)]
		super().__init__("column-sum", "{Y} = SUM({X}, col)", variables)

	def accept(self, visitor):
		return visitor.visit_sum_column(self)


class SumRow(Constraint):
	def __init__(self):
		variables = [Variable("X", numeric=True), Variable("Y", vector=True, numeric=True)]
		super().__init__("row-sum", "{Y} = SUM({X}, row)", variables)

	def accept(self, visitor):
		return visitor.visit_sum_row(self)


class Permutation(Constraint):
	def __init__(self):
		super().__init__("permutation", "PERMUTATION({X})", [Variable("X", numeric=True)])

	def accept(self, visitor):
		return visitor.visit_permutation(self)


class Series(Constraint):
	def __init__(self):
		super().__init__("series", "SERIES({X})", [Variable("X", numeric=True)])

	def accept(self, visitor):
		return visitor.visit_series(self)


class AllDifferent(Constraint):
	def __init__(self):
		super().__init__("all-different", "ALLDIFFERENT({X})", [Variable("X", textual=True)])

	def accept(self, visitor):
		return visitor.visit_all_different(self)


class Rank(Constraint):
	def __init__(self):
		variables = [Variable("X", vector=True, numeric=True), Variable("Y", vector=True, integer=True)]
		super().__init__("rank", "{Y} = RANK({X})", variables)

	def accept(self, visitor):
		return visitor.visit_rank(self)


class ForeignKey(Constraint):
	pk = Variable("PK", vector=True, textual=True)
	fk = Variable("FK", vector=True, textual=True)

	def __init__(self):
		super().__init__("foreign-key", "{FK} -> {PK}", [self.pk, self.fk])

	def accept(self, visitor):
		return visitor.visit_foreign_key(self)


class ConstraintVisitor:
	def __init__(self):
		pass

	def visit(self, constraint: Constraint):
		return constraint.accept(self)

	def visit_sum_column(self, constraint: SumColumn):
		raise NotImplementedError()

	def visit_sum_row(self, constraint: SumRow):
		raise NotImplementedError()

	def visit_permutation(self, constraint: Permutation):
		raise NotImplementedError()

	def visit_series(self, constraint: Series):
		raise NotImplementedError()

	def visit_all_different(self, constraint: AllDifferent):
		raise NotImplementedError()

	def visit_rank(self, constraint: AllDifferent):
		raise NotImplementedError()

	def visit_foreign_key(self, constraint: ForeignKey):
		raise NotImplementedError()
