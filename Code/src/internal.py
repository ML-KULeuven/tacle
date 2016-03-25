import numpy

from constraint import Constraint, ConstraintVisitor, Series, SumColumn, AllDifferent, SumRow, Permutation, Rank
from engine import Engine
from group import Group


class InternalGroupGenerationVisitor(ConstraintVisitor):
	def __init__(self, groups, solutions):
		super().__init__()
		self.groups = groups
		self.solutions = solutions

	def visit_series(self, constraint: Series):
		return [{constraint.get_variables()[0].name: g} for g in filter(Group.is_integer, self.groups)]

	def visit_sum_column(self, constraint: SumColumn):
		pass

	def visit_all_different(self, constraint: AllDifferent):
		return [{constraint.get_variables()[0].name: g} for g in filter(Group.is_textual, self.groups)]

	def visit_sum_row(self, constraint: SumRow):
		pass

	def visit_permutation(self, constraint: Permutation):
		return [{constraint.get_variables()[0].name: g} for g in filter(Group.is_integer, self.groups)]

	def visit_rank(self, constraint: AllDifferent):
		assignments = []
		for y_group in self.solutions.get_property_groups(Permutation()):
			for x_group in filter(Group.is_numeric, self.groups):
				if x_group.length() == y_group.length():
					assignments.append({"Y": y_group, "X": x_group})
		return assignments


class InternalConstraintVisitor(ConstraintVisitor):
	def __init__(self, assignments):
		super().__init__()
		self.assignments = assignments

	def visit_series(self, constraint: Series):
		results = []
		variable = constraint.get_variables()[0]
		for group in [assignment[variable.name] for assignment in self.assignments]:
				for i in range(1, group.vectors() + 1):
					if self.test_list(group.get_vector(i)):
						results.append({variable.name: group.vector_subset(i, i)})
		return results

	def visit_sum_column(self, constraint: SumColumn):
		pass

	def visit_all_different(self, constraint: AllDifferent):
		results = []
		variable = constraint.get_variables()[0]
		for group in [assignment[variable.name] for assignment in self.assignments]:
			for i in range(1, group.vectors() + 1):
				vector = group.get_vector(i)
				if len(set(vector)) == len(vector):
					results.append({variable.name: group.vector_subset(i, i)})
		return results

	def visit_sum_row(self, constraint: SumRow):
		pass

	def visit_permutation(self, constraint: Permutation):
		results = []
		variable = constraint.get_variables()[0]
		for group in [assignment[variable.name] for assignment in self.assignments]:
			for i in range(1, group.vectors() + 1):
				if self.test_set(group.get_vector(i)):
					results.append({variable.name: group.vector_subset(i, i)})
		return results

	def visit_rank(self, constraint: AllDifferent):
		solutions = []
		for assignment in self.assignments:
			y_group = assignment["Y"]
			x_group = assignment["X"]
			for i in range(1, y_group.vectors() + 1):
				for j in range(1, x_group.vectors() + 1):
					x_v = x_group.vector_subset(j, j)
					y_v = y_group.vector_subset(i, i)
					if not x_v.overlaps_with(y_v):
						indices = numpy.argsort(x_group.get_vector(j)) + 1
						if all(indices[::-1] == y_group.get_vector(i)):
							solutions.append({"X": x_v, "Y": y_v})
		return solutions

	@staticmethod
	def test_set(vector):
		number_set = set(range(1, len(vector) + 1))
		for i in range(len(vector)):
			if not vector[i] in number_set:
				return False
			number_set.remove(vector[i])
		return True

	@staticmethod
	def test_list(vector):
		for i in range(len(vector)):
			if not vector[i] == i + 1:
				return False
		return True


class Internal(Engine):
	def generate_groups(self, constraint: Constraint, groups: [Group], solutions) -> [[Group]]:
		return InternalGroupGenerationVisitor(groups, solutions).visit(constraint)

	def find_constraints(self, constraint: Constraint, assignments: [{Group}], solutions) -> [{(Group, int)}]:
		return InternalConstraintVisitor(assignments).visit(constraint)

	def supports_group_generation(self, constraint: Constraint):
		return constraint in [Permutation(), AllDifferent(), Series(), Rank()]

	def supports_constraint_search(self, constraint: Constraint):
		return constraint in [Permutation(), AllDifferent(), Series(), Rank()]
