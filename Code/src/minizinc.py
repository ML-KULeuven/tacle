import os
import re
import tempfile

from numpy import transpose

from constraint import ConstraintVisitor, SumColumn, Constraint, Variable, SumRow, Permutation, Series, AllDifferent
from engine import Engine, local, run_command
from group import Group

unsatisfiable_pattern = re.compile(r".*UNSATISFIABLE.*")
error_pattern = re.compile(r".*error.*")


class MinizincCodeGenerator:
	def __init__(self):
		self.group_properties = []
		self.add_group_property("int", "g_length", Group.length)
		self.add_group_property("int", "g_columns", Group.columns)
		self.add_group_property("int", "g_rows", Group.rows)
		self.add_group_property("bool", "g_numeric", Group.is_numeric)
		self.add_group_property("bool", "g_row_orientation", Group.row_oriented)

		self.variable_properties = []
		self.add_variable_property("bool", "v_numeric", Variable.is_numeric)
		self.add_variable_property("bool", "v_vector", Variable.is_vector)

	def add_group_property(self, var_type, name, f_extractor):
		self.group_properties.append((var_type, name, f_extractor))

	def add_variable_property(self, var_type, name, f_extractor):
		self.variable_properties.append((var_type, name, f_extractor))

	def generate_group_properties(self, groups):
		declaration = "int: nG = " + str(len(groups)) + ";"
		data = map(lambda t: self._generate_array("nG", t[0], t[1], t[2], groups), self.group_properties)
		return "\n".join([declaration] + list(data)) + "\n\n"

	def generate_constraints(self, constraint, constraint_file):
		variables = constraint.get_variables()
		declaration = "int: nV = " + str(len(variables)) + ";"
		data = map(lambda t: self._generate_array("nV", t[0], t[1], t[2], variables), self.variable_properties)
		assign_array = "array [1..nV] of var int: assign;"
		with open(constraint_file) as file:
			return "\n".join([declaration, assign_array] + list(data) + [file.read(), "solve satisfy;"]) + "\n\n"

	def generate_data(self, assignment, variables):
		parts = []
		for variable in variables:
			group = assignment[variable.name]
			to_vector = variable.is_vector()
			if variable.is_vector():
				parts += [
					"{}_vectors = {};".format(variable.name.lower(), group.vectors()),
					"{}_length = {};".format(variable.name.lower(), group.length()),
				]
			else:
				parts += [
					"{}_columns = {};".format(variable.name.lower(), group.columns()),
					"{}_rows = {};".format(variable.name.lower(), group.rows()),
				]
			data = self._generate_group_data(group, to_vector=to_vector)
			parts.append("{}_data = {};".format(variable.name.lower(), data))
		return "\n".join(parts)

	@staticmethod
	def _generate_array(size, var_type, name, f_extractor, elements):
		fstring = "array [1..{}] of " + var_type + ": {} = [{}];"
		return fstring.format(size, name, ", ".join([str(f_extractor(el)).lower() for el in elements]))

	@staticmethod
	def _generate_group_data(group, to_vector=False):
		data = group.get_group_data()
		if to_vector and not group.row:
			data = transpose(data)
		group_data = " | ".join([", ".join(map(str, column)) for column in data.tolist()])
		return "[| {} |]".format(group_data)


class MinizincOutputParser:
	def __init__(self, variables):
		self.variables = variables

	def parse_assignments(self, groups, output):
		filter_pattern = re.compile(r"assign.*")
		assigns = filter(lambda l: bool(filter_pattern.match(l)), output.splitlines())
		pattern = re.compile(r".*\[" + ", ".join(["(\d+)"] * len(self.variables)) + "\].*")
		assignments = []
		for line in assigns:
			match = pattern.match(line)
			assignments.append({var.get_name(): match.group(i + 1) for i, var in enumerate(self.variables)})
		return [{v: groups[int(g) - 1] for v, g in assignment.items()} for assignment in assignments]

	def parse_solutions(self, assignment, output):
		v_patterns = [r"{}\[(\d+):(\d+)\]".format(v.name) for v in self.variables]
		results = []
		column_pattern = re.compile(r"" + "\n".join(v_patterns))
		for match in column_pattern.finditer(output):
			solution = {}
			for i, v in enumerate(self.variables):
				b = (int(match.group(1 + 2 * i)), int(match.group(2 + 2 * i)))
				solution[v.name] = assignment[v.name].vector_subset(b[0], b[1])
			results.append(solution)
		return results


class MinizincGroupGenerationVisitor(ConstraintVisitor):
	def __init__(self, engine, groups: {Group}, solutions):
		super().__init__()
		self.engine = engine
		self.groups = groups
		self.solutions = solutions

	def visit_sum_column(self, constraint: SumColumn):
		return self._get_assignments(constraint, local("minizinc/group/sum_column.mzn"))

	def visit_sum_row(self, constraint: SumRow):
		return self._get_assignments(constraint, local("minizinc/group/sum_row.mzn"))

	def visit_permutation(self, constraint: Permutation):
		pass

	def visit_series(self, constraint: Series):
		pass

	def visit_all_different(self, constraint: AllDifferent):
		pass

	def visit_rank(self, constraint: AllDifferent):
		return self._get_assignments(constraint, local("minizinc/group/rank.mzn"))

	def _get_assignments(self, constraint, filename):
		generator = MinizincCodeGenerator()
		parser = MinizincOutputParser(constraint.get_variables())
		data = generator.generate_group_properties(self.groups) + generator.generate_constraints(constraint, filename)
		model_file = TempFile(data, "mzn")
		assignments = parser.parse_assignments(self.groups, self.engine.execute(model_file.name)[0])
		model_file.delete()
		return assignments


class MinizincConstraintVisitor(ConstraintVisitor):
	def __init__(self, engine, assignments: [{Group}]):
		super().__init__()
		self.engine = engine
		self.assignments = assignments

	def visit_sum_column(self, constraint: SumColumn):
		filename = "minizinc/constraint/sum_column_{}.mzn"
		assignment_tuples = [(a, local(filename.format("row" if a["X"].row else "column"))) for a in self.assignments]
		results = [self._find_constraints(a, f, constraint) for a, f in assignment_tuples]
		return [item for solutions in results for item in solutions]

	def visit_sum_row(self, constraint: SumRow):
		filename = "minizinc/constraint/sum_row_{}.mzn"
		assignment_tuples = [(a, local(filename.format("row" if a["X"].row else "column"))) for a in self.assignments]
		results = [self._find_constraints(a, f, constraint) for a, f in assignment_tuples]
		return [item for solutions in results for item in solutions]

	def visit_permutation(self, constraint: Permutation):
		pass

	def visit_rank(self, constraint: AllDifferent):
		pass

	def visit_all_different(self, constraint: AllDifferent):
		pass

	def visit_series(self, constraint: Series):
		pass

	def _find_constraints(self, assignment, file, constraint):
		generator = MinizincCodeGenerator()
		parser = MinizincOutputParser(constraint.get_variables())
		results = []
		data_file = TempFile(generator.generate_data(assignment, constraint.get_variables()), "dzn")
		output, command = self.engine.execute(file, data_file=data_file.name)
		if error_pattern.search(output):
			print("ERROR:\n{}\n".format(command), output)
		elif not unsatisfiable_pattern.search(output):
			results += parser.parse_solutions(assignment, output)
			data_file.delete()
		return results


class Minizinc(Engine):
	def supports_group_generation(self, constraint: Constraint):
		return constraint in [SumColumn(), SumRow()]

	def supports_constraint_search(self, constraint: Constraint):
		return constraint in [SumColumn(), SumRow()]

	def generate_groups(self, constraint: Constraint, groups: [Group], solutions) -> [[Group]]:
		return MinizincGroupGenerationVisitor(self, groups, {}).visit(constraint)

	def find_constraints(self, constraint: Constraint, assignments: [{Group}], solutions) -> [{Group}]:
		return MinizincConstraintVisitor(self, assignments).visit(constraint)

	@staticmethod
	def execute(model_file, data_file=None):
		command = ["mzn-gecode", "-a"] + ([] if data_file is None else ["-d", data_file]) + [model_file]
		return run_command(command), " ".join(command)


class TempFile:
	def __init__(self, content, extension):
		self.file = tempfile.NamedTemporaryFile("w+", delete=False, suffix=("." + extension))
		print(content, file=self.file)
		self.file.close()
		self.name = self.file.name

	def delete(self):
		os.remove(self.file.name)
