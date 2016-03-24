from constraint import Constraint, ConstraintVisitor, Series, SumColumn, AllDifferent, SumRow, Permutation
from engine import Engine
from group import Group


class InternalGroupGenerationVisitor(ConstraintVisitor):
	def __init__(self, groups):
		super().__init__()
		self.groups = groups

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


class InternalConstraintVisitor(ConstraintVisitor):
	def __init__(self, assignments):
		super().__init__()
		self.assignments = assignments

	def visit_series(self, constraint: Series):
		results = []
		variable = constraint.get_variables()[0]
		for group in [assignment[variable.name] for assignment in self.assignments]:
				for i in range(group.vectors()):
					if self.test_list(group.get_vector(i)):
						results.append({variable.name: group.vector_subset(i, i)})
		return results

	def visit_sum_column(self, constraint: SumColumn):
		pass

	def visit_all_different(self, constraint: AllDifferent):
		results = []
		variable = constraint.get_variables()[0]
		for group in [assignment[variable.name] for assignment in self.assignments]:
			for i in range(group.vectors()):
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
			for i in range(group.vectors()):
				if self.test_set(group.get_vector(i)):
					results.append({variable.name: group.vector_subset(i, i)})
		return results

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
		return InternalGroupGenerationVisitor(groups).visit(constraint)

	def find_constraints(self, constraint: Constraint, assignments: [{Group}], solutions) -> [{(Group, int)}]:
		return InternalConstraintVisitor(assignments).visit(constraint)

	def supports_group_generation(self, constraint: Constraint):
		return constraint in [Permutation(), AllDifferent(), Series()]

	def supports_constraint_search(self, constraint: Constraint):
		return constraint in [Permutation(), AllDifferent(), Series()]
