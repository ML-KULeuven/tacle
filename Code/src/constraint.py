class Variable:
	def __init__(self, name, vector=False, numeric=False):
		self.name = name
		self.vector = vector
		self.numeric = numeric

	def __str__(self):
		return self.name + "[Var]"

	def get_name(self):
		return self.name

	def is_vector(self):
		return self.vector

	def is_numeric(self):
		return self.numeric


class Constraint:
	def __init__(self, name, variables):
		self.name = name
		self.variables = variables

	def accept(self, visitor):
		raise NotImplementedError()

	def get_variables(self):
		return self.variables

	def __str__(self):
		return self.name


class SumColumn(Constraint):
	def __init__(self):
		variables = [Variable("X", numeric=True), Variable("Y", vector=True, numeric=True)]
		Constraint.__init__(self, "{Y} = SUM({X})", variables)

	def accept(self, visitor):
		return visitor.visit_sum_column(self)

	def to_string(self, assignment):
		return self.name.format(**assignment)


class ConstraintVisitor:
	def __init__(self):
		pass

	def visit(self, constraint: Constraint):
		return constraint.accept(self)

	def visit_sum_column(self, constraint: SumColumn):
		raise NotImplementedError()
