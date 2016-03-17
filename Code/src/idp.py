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

	def visit_sum_column(self, constraint: Constraint) -> [{}]:
		return self.extract_assignment(constraint.get_variables(), ["test_group_assign.idp"])

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


class IDP(Engine):
	def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
		group_dictionary = {}
		for i, g in enumerate(groups):
			group_dictionary["G" + str(i + 1)] = g
		print(group_dictionary.keys())
		visitor = IDPGroupGenerationVisitor(self, group_dictionary)
		return [{k: group_dictionary[n] for k, n in dictionary.items()} for dictionary in visitor.visit(constraint)]

	def execute_local(self, files: []):
		return self.execute([os.path.dirname(os.path.realpath(__file__)) + "/../" + file for file in files])

	def execute(self, files: []):
		return run_command(["idp"] + files)
