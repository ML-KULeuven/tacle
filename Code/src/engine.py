import os
import subprocess

import re

from constraint import *
from group import *


class Engine:
	def __init__(self):
		super().__init__()

	def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
		raise NotImplementedError()


def run_command(command):
	p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	return iter(p.stdout.readline, b'')


class IDPGroupGenerationVisitor(ConstraintVisitor):
	def __init__(self, engine, groups: [Group]):
		super().__init__()
		self.engine = engine
		self.groups = groups

	def visit_sum_column(self, constraint: Constraint) -> [{}]:
		return self.extract_assignment(constraint.get_variables(), ["test_group_assign.idp"])

	def extract_assignment(self, variables, files):
		assignments = []
		assign_pattern = re.compile(r".*assign = .*")
		patterns = [(var, re.compile(r"assign = \{.*\"" + var + "\"->\"(G\d+)\".*\}")) for var in variables]
		for bytes in self.engine.execute_local(files):
			line = bytes.decode("utf-8")
			if assign_pattern.match(line):
				a = {}
				for var, pattern in patterns:
					match = pattern.match(line)
					if match is not None:
						a[var] = match.group(1)
				assignments.append(a)


class IDP(Engine):
	def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
		visitor = IDPGroupGenerationVisitor(self, groups)
		return visitor.visit(constraint)

	def execute_local(self, files: []):
		return self.execute([os.path.dirname(os.path.realpath(__file__)) + "/../" + file for file in files])

	def execute(self, files: []):
		return run_command(["idp"] + files)
