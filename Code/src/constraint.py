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
		Constraint.__init__(self, "Y = SUM(X)", ["X", "Y"])

	def accept(self, visitor):
		return visitor.visit_sum_column(self)


class ConstraintVisitor:
	def __init__(self):
		pass

	def visit(self, constraint: Constraint):
		return constraint.accept(self)

	def visit_sum_column(self, constraint: SumColumn):
		raise NotImplementedError()
