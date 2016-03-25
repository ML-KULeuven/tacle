import os
import re
import tempfile

from numpy import transpose

from constraint import ConstraintVisitor, SumColumn, Constraint, Variable, SumRow, Permutation, Series, AllDifferent
from engine import Engine, local, run_command
from group import Group

unsatisfiable_pattern = re.compile(r".*UNSATISFIABLE.*")
error_pattern = re.compile(r".*error.*")


class MinizincGroupGenerationVisitor(ConstraintVisitor):
  def __init__(self, engine, groups: {Group}, solutions):
    super().__init__()
    self.engine = engine
    self.groups = groups
    self.solutions = solutions

  def visit_sum_column(self, constraint: SumColumn):
    return self.generate_groups(constraint, local("minizinc/group/sum_column.mzn"))

  def visit_sum_row(self, constraint: SumRow):
    return self.generate_groups(constraint, local("minizinc/group/sum_row.mzn"))

  def visit_permutation(self, constraint: Permutation):
    pass

  def visit_series(self, constraint: Series):
    pass

  def visit_all_different(self, constraint: AllDifferent):
    pass

  def generate_groups(self, constraint, filename):
    data = self.generate_data() + self.generate_constraints(filename, constraint)
    model_file = TempFile(data, "mzn")
    assignments = self.parse_assignments(constraint.get_variables(), self.engine.execute(model_file.name)[0])
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
  def _group_data(size, var_type, name, method, collection):
    fstring = "array [1..{}] of " + var_type + ": {} = [{}];"
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
    return assignments


class MinizincConstraintVisitor(ConstraintVisitor):
  def __init__(self, engine, assignments: [{Group}]):
    super().__init__()
    self.engine = engine
    self.assignments = assignments

  def visit_sum_column(self, constraint: SumColumn):
    filename = "minizinc/constraint/sum_column_{}.mzn"
    assignment_tuples = [(a, local(filename.format("row" if a["X"].row else "column"))) for a in self.assignments]
    results = [self.find_constraints(a, f, constraint) for a, f in assignment_tuples]
    return [item for solutions in results for item in solutions]

  def visit_sum_row(self, constraint: SumRow):
    filename = "minizinc/constraint/sum_row_{}.mzn"
    assignment_tuples = [(a, local(filename.format("row" if a["X"].row else "column"))) for a in self.assignments]
    results = [self.find_constraints(a, f, constraint) for a, f in assignment_tuples]
    return [item for solutions in results for item in solutions]

  def visit_permutation(self, constraint: Permutation):
    pass

  def find_constraints(self, assignment, file, constraint):
    results = []
    data_file = TempFile(self.generate_data(assignment, constraint.get_variables()), "dzn")
    output, command = self.engine.execute(file, data_file=data_file.name)
    if error_pattern.search(output):
      print("ERROR:\n{}\n".format(command), output)
    elif not unsatisfiable_pattern.search(output):
      print(output)
      results += self.parse_results(constraint.get_variables(), assignment, output)
      data_file.delete()
    return results

  def generate_data(self, assignment: {Group}, variables: [Variable]):
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
      parts.append("{}_data = {};".format(variable.name.lower(), self.generate_group(group, to_vector=to_vector)))
    return "\n".join(parts)

  @staticmethod
  def generate_group(group, to_vector=False):
    data = group.get_group_data()
    if to_vector and not group.row:
      data = transpose(data)
    group_data = " | ".join([", ".join(map(str, column)) for column in data.tolist()])
    return "[| {} |]".format(group_data)

  @staticmethod
  def parse_results(variables, assignment, output):
    v_patterns = [r"{}\[(\d+):(\d+)\]".format(v.name) for v in variables]
    results = []
    column_pattern = re.compile(r"" + "\n".join(v_patterns))
    for match in column_pattern.finditer(output):
      solution = {}
      for i, v in enumerate(variables):
        b = (int(match.group(1 + 2 * i)), int(match.group(2 + 2 * i)))
        solution[v.name] = assignment[v.name].vector_subset(b[0], b[1])
      results.append(solution)
    return results


class Minizinc(Engine):
  def supports_group_generation(self, constraint: Constraint):
    return constraint in [SumColumn(), SumRow()]

  def supports_constraint_search(self, constraint: Constraint):
    return constraint in [SumColumn(), SumRow()]

  def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
    return MinizincGroupGenerationVisitor(self, groups, {}).visit(constraint)

  def find_constraints(self, constraint: Constraint, assignments: [{Group}]) -> [{Group}]:
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
