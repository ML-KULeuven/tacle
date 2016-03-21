import os
import tempfile

import re

from numpy import transpose

from constraint import ConstraintVisitor, SumColumn, Constraint, Variable
from engine import Engine, local, run_command
from group import Group


class MinizincGroupGenerationVisitor(ConstraintVisitor):
	def __init__(self, engine, groups: {Group}):
		super().__init__()
		self.engine = engine
		self.groups = groups

	def visit_sum_column(self, constraint: SumColumn):
		data = self.generate_data() + self.generate_constraints(local("minizinc/group/sum_column.mzn"), constraint)
		model_file = TempFile(data, "mzn")
		assignments = self.parse_assignments(constraint.get_variables(), self.engine.execute(model_file.name))
		model_file.delete()
		return [{v: self.groups[int(g) - 1] for v, g in assignment.items()} for assignment in assignments]

	def generate_data(self):
		parts = [
			"int: nG = " + str(len(self.groups)) + ";",
			self._group_data("nG", "int", "g_length", Group.length, self.groups),
			self._group_data("nG", "int", "g_columns", Group.columns, self.groups),
			self._group_data("nG", "int", "g_rows", Group.rows, self.groups),
			self._group_data("nG", "bool", "g_numeric", Group.is_numeric, self.groups),
			self._group_data("nG", "bool", "g_row_orientation", Group.row_oriented, self.groups),
		]
		return "\n".join(parts) + "\n\n"

	def generate_constraints(self, constraint_file, constraint):
		variables = constraint.get_variables()
		with open(constraint_file) as file:
			parts = [
				"int: nV = " + str(len(variables)) + ";",
				self._group_data("nV", "bool", "v_numeric", Variable.is_numeric, variables),
				self._group_data("nV", "bool", "v_vector", Variable.is_vector, variables),
				"array [1..nV] of var int: assign;",
				file.read(),
				"solve satisfy;"
			]
			return "\n".join(parts) + "\n\n"

	@staticmethod
	def _group_data(size, dtype, name, method, collection):
		fstring = "array [1..{}] of " + dtype + ": {} = [{}];"
		return fstring.format(size, name, ", ".join([str(method(el)).lower() for el in collection]))

	@staticmethod
	def parse_assignments(variables, output):
		filter_pattern = re.compile(r"assign.*")
		assigns = filter(lambda l: bool(filter_pattern.match(l)), output.splitlines())
		pattern = re.compile(r".*\[" + ", ".join(["(\d+)"] * len(variables)) + "\].*")
		assignments = []
		for line in assigns:
			match = pattern.match(line)
			assignments.append({var.get_name(): match.group(i + 1) for i, var in enumerate(variables)})
		print(assignments)
		return assignments


class MinizincConstraintVisitor(ConstraintVisitor):
	def __init__(self, engine, assignments: [{Group}]):
		super().__init__()
		self.engine = engine
		self.assignments = assignments

	def visit_sum_column(self, constraint: SumColumn):
		for assignment in self.assignments:
			data_file = TempFile(self.generate_data(assignment), "dzn")
			orientation = "row" if assignment["X"].row else "column"
			model_file = local("minizinc/constraint/sum_column_{}.mzn".format(orientation))
			print("OUTPUT:")
			print(self.engine.execute(model_file, data_file=data_file.name))

	def generate_data(self, assignment: {Group}):
		x_group = assignment["X"]
		y_group = assignment["Y"]
		parts = [
			"x_columns = {};".format(x_group.columns()),
			"x_rows = {};".format(x_group.rows()),
			"y_vectors = {};".format(y_group.vectors()),
			"y_length = {};".format(y_group.length()),
			"is_same_group = {};".format(str(x_group == y_group).lower()),
			"x_data = {};".format(self.generate_group(x_group)),
			"y_data = {};".format(self.generate_group(y_group, vectorize=True))
		]
		return "\n".join(parts)

	@staticmethod
	def generate_group(group, vectorize=False):
		data = group.get_group_data()
		if vectorize and not group.row:
			data = transpose(data)
		group_data = " | ".join([", ".join(map(str, column)) for column in data.tolist()])
		return "[| {} |]".format(group_data)


class Minizinc(Engine):
	def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
		return MinizincGroupGenerationVisitor(self, groups).visit(constraint)

	def find_constraints(self, constraint: Constraint, assignments: [{Group}]) -> [{Group}]:
		return MinizincConstraintVisitor(self, assignments).visit(constraint)

	@staticmethod
	def execute(model_file, data_file=None):
		command = ["mzn-gecode", "-a"] + ([] if data_file is None else ["-d", data_file]) + [model_file]
		print(" ".join(command))
		return run_command(command)


class TempFile:
	def __init__(self, content, extension):
		self.file = tempfile.NamedTemporaryFile("w+", delete=False, suffix=("." + extension))
		print(content, file=self.file)
		self.file.close()
		self.name = self.file.name

	def delete(self):
		os.remove(self.file.name)
