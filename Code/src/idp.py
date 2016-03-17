import os
import re

from constraint import *
from group import *
from engine import Engine, run_command


class IDPGroupGenerationVisitor(ConstraintVisitor):
	def __init__(self, engine, groups: {Group}):
		super().__init__()
		self.engine = engine
		self.groups = groups

	def visit_sum_column(self, constraint: SumColumn) -> [{}]:
		print(self.create_structure("Nothing"))
		return self.extract_assignment(constraint.get_variables(), ["idp/group/assign.idp", "idp/group/sum_column.idp"])

	def extract_assignment(self, variables, files):
		assignments = []
		assign_pattern = re.compile(r".*assign = .*")
		patterns = [(var, re.compile(r'.*assign = .*"' + var + '"->"(G\d+)".*')) for var in variables]
		for line in [b.decode("utf-8") for b in self.engine.execute_local(files)]:
			if assign_pattern.match(line):
				a = {}
				for var, pattern in patterns:
					match = pattern.match(line)
					if match is not None:
						a[var] = match.group(1)
				assignments.append(a)
		return assignments

	def create_structure(self, constraint_structure):
		"""
		Num = {1..100}
		Group = {G1; G2; G3; G4; G5; G6; G7}
		g_length = {(G1, 4); (G2, 4); (G3, 4); (G4, 4); (G5, 4); (G6, 5); (G7, 4)}
		g_columns = {(G1, 1); (G2, 1); (G3, 6); (G4, 1); (G5, 2); (G6, 5); (G7, 5)}
		g_rows = {(G1, 4); (G2, 4); (G3, 4); (G4, 4); (G5, 4); (G6, 4); (G7, 4)}
		g_numeric = {G1; G3; G5; G6; G7}
		"""
		groups = "{" + "; ".join(list(self.groups.keys())) + "}"
		length = self.extract_tuple("g_length", Group.length)
		columns = self.extract_tuple("g_columns", Group.columns)
		rows = self.extract_tuple("g_numeric", Group.rows)
		return "\n".join([groups, length, columns, rows, constraint_structure])

	def extract_tuple(self, name, f):
		length = name + " = {" + "; ".join(["(" + k + ", " + str(f(g)) + ")" for k, g in self.groups.items()]) + "}"
		return length


class IDP(Engine):
	def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
		group_dictionary = {}
		for i, g in enumerate(groups):
			group_dictionary["G" + str(i + 1)] = g
		visitor = IDPGroupGenerationVisitor(self, group_dictionary)
		assignments = visitor.visit(constraint)
		print([list(d.values()) for d in assignments])
		return [{k: group_dictionary[n] for k, n in dictionary.items()} for dictionary in assignments]

	def execute_local(self, files: []):
		return self.execute([os.path.dirname(os.path.realpath(__file__)) + "/../" + file for file in files])

	def execute(self, files: []):
		return run_command(["idp"] + files)
