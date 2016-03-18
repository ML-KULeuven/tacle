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
		files = [local("idp/group/assign.idp"), local("idp/group/sum_column.idp")]
		structure = self.create_structure(constraint)
		return self.extract_assignment(constraint.get_variables(), files, structure)

	def extract_assignment(self, variables, files, structure):
		assignments = []
		assign_pattern = re.compile(r".*assign = .*")
		patterns = [(var, re.compile(r'.*assign = .*"' + var.get_name() + '"->"(G\d+)".*')) for var in variables]
		for line in iter(self.engine.execute(files, structure).splitlines()):
			if assign_pattern.match(line):
				a = {}
				for var, pattern in patterns:
					match = pattern.match(line)
					if match is not None:
						a[var.get_name()] = match.group(1)
				assignments.append(a)
		return assignments

	def create_structure(self, constraint: Constraint):
		variables = constraint.get_variables()
		groups = self.groups

		def lambda_filter(f):
			return map(Variable.get_name, filter(f, variables))

		parts = [
			self._structure("Var", [v.get_name() for v in variables]),
			"\n".join([v.get_name() + " = " + v.get_name() for v in variables]),
			self._structure("vector", lambda_filter(Variable.is_vector)),
			self._structure("numeric", lambda_filter(Variable.is_numeric)),
			self._structure("Num", ["1.." + str(max(map(lambda g: max(g.columns(), g.rows()), groups.values())))]),
			self._structure("Group", list(groups.keys())), self._group_structure("g_length", Group.length),
			self._group_structure("g_columns", Group.columns), self._group_structure("g_rows", Group.rows),
			self._structure("g_numeric", [k for k, g in groups.items() if g.is_numeric()])
		]
		return "\nstructure S : VConstraint {\n" + "\n".join(parts) + "\n}"

	@staticmethod
	def _structure(name, members):
		return name + " = {" + "; ".join(members) + "}"

	def _group_structure(self, name, method):
		return self._structure(name, ["(" + k + ", " + str(method(g)) + ")" for k, g in self.groups.items()])


class IDP(Engine):
	def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
		group_dictionary = {}
		for i, g in enumerate(groups):
			group_dictionary["G" + str(i + 1)] = g
		visitor = IDPGroupGenerationVisitor(self, group_dictionary)
		assignments = visitor.visit(constraint)
		print("Assignments:\n", [list(d.values()) for d in assignments])
		return [{k: group_dictionary[n] for k, n in dictionary.items()} for dictionary in assignments]

	def execute_local(self, files: [], structure):
		return self.execute([local(file) for file in files], structure)

	def execute(self, files: [], structure):
		data = "\n".join(["include \"" + file + "\"" for file in files])
		return run_command(["idp"], input_data=data + structure)


def local(filename):
	return os.path.dirname(os.path.realpath(__file__)) + "/../" + filename
