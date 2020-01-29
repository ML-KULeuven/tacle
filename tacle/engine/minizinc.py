import re

from numpy import transpose

from tacle.core.template import *
from legacy.group import Group, GType
from tacle.core.strategy import DictAssignmentStrategy, DictSolvingStrategy
from .util import local, run_command, TempFile

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
        data = map(
            lambda t: self._generate_array("nG", t[0], t[1], t[2], groups),
            self.group_properties,
        )
        return "\n".join([declaration] + list(data)) + "\n\n"

    def generate_constraints(self, constraint, constraint_file):
        variables = constraint.get_variables()
        declaration = "int: nV = " + str(len(variables)) + ";"
        data = map(
            lambda t: self._generate_array("nV", t[0], t[1], t[2], variables),
            self.variable_properties,
        )
        assign_array = "array [1..nV] of var int: assign;"
        with open(constraint_file) as file:
            return (
                "\n".join(
                    [declaration, assign_array]
                    + list(data)
                    + [file.read(), "solve satisfy;"]
                )
                + "\n\n"
            )

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
        return fstring.format(
            size, name, ", ".join([str(f_extractor(el)).lower() for el in elements])
        )

    @staticmethod
    def _generate_group_data(group, to_vector=False):
        data = group.get_group_data()
        if to_vector and not group.row:
            data = transpose(data)
        group_data = " | ".join(
            [
                ", ".join(
                    map(
                        lambda dp: MinizincCodeGenerator.to_string(group.dtype, dp),
                        column,
                    )
                )
                for column in data.tolist()
            ]
        )
        return "[| {} |]".format(group_data)

    @staticmethod
    def to_string(gtype, data_point):
        if gtype == GType.int or gtype == GType.float:
            return str(data_point)
        elif gtype == GType.string:
            return '"' + str(data_point) + '"'
        raise ValueError("Unexpected GType: " + str(gtype))


class MinizincOutputParser:
    def __init__(self, variables):
        self.variables = variables

    def parse_assignments(self, groups, output):
        filter_pattern = re.compile(r"assign.*")
        assigns = filter(lambda l: bool(filter_pattern.match(l)), output.splitlines())
        pattern = re.compile(
            r".*\[" + ", ".join([r"(\d+)"] * len(self.variables)) + "].*"
        )
        assignments = []
        for line in assigns:
            match = pattern.match(line)
            assignments.append(
                {
                    var.get_name(): match.group(i + 1)
                    for i, var in enumerate(self.variables)
                }
            )
        return [
            {v: groups[int(g) - 1] for v, g in assignment.items()}
            for assignment in assignments
        ]

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


class MinizincAssignmentStrategy(DictAssignmentStrategy):
    def __init__(self):
        super().__init__()

        def aggregate_columns(constraint, groups, solutions):
            return self._get_assignments(
                groups, constraint, local("minizinc/group/sum_column.mzn")
            )

        def aggregate_rows(constraint, groups, solutions):
            return self._get_assignments(
                groups, constraint, local("minizinc/group/sum_row.mzn")
            )

        def rank(constraint, groups, solutions):
            # TODO Implementation not finished
            return self._get_assignments(
                groups, constraint, local("minizinc/group/rank.mzn")
            )

        for aggregate in Aggregate.instances():
            f = (
                aggregate_columns
                if aggregate.orientation == Orientation.VERTICAL
                else aggregate_rows
            )
            self.add_strategy(aggregate, f)

    def applies_to(self, constraint):
        return constraint in self.strategies

    def apply(self, constraint: ConstraintTemplate, groups: [Group], solutions):
        return self.strategies[constraint](constraint, groups, solutions)

    @staticmethod
    def _get_assignments(groups, constraint, filename):
        generator = MinizincCodeGenerator()
        parser = MinizincOutputParser(constraint.get_variables())
        data = generator.generate_group_properties(
            groups
        ) + generator.generate_constraints(constraint, filename)
        model_file = TempFile(data, "mzn")
        assignments = parser.parse_assignments(groups, execute(model_file.name)[0])
        model_file.delete()
        return assignments


class MinizincSolvingStrategy(DictSolvingStrategy):
    def __init__(self):
        super().__init__()

        def sum_columns(constraint, assignments, solutions):
            filename = "minizinc/constraint/sum_column_{}.mzn"
            assignment_tuples = [
                (a, local(filename.format("row" if a["X"].row else "column")))
                for a in assignments
            ]
            results = [
                self._find_constraints(a, f, constraint) for a, f in assignment_tuples
            ]
            return [item for solutions in results for item in solutions]

        def sum_rows(constraint, assignments, solutions):
            filename = "minizinc/constraint/sum_row_{}.mzn"
            assignment_tuples = [
                (a, local(filename.format("row" if a["X"].row else "column")))
                for a in assignments
            ]
            results = [
                self._find_constraints(a, f, constraint) for a, f in assignment_tuples
            ]
            return [item for solutions in results for item in solutions]

        self.add_strategy(
            Aggregate.instance(Orientation.VERTICAL, Operation.SUM), sum_columns
        )
        self.add_strategy(
            Aggregate.instance(Orientation.HORIZONTAL, Operation.SUM), sum_rows
        )

    @staticmethod
    def _find_constraints(assignment, file, constraint):
        generator = MinizincCodeGenerator()
        parser = MinizincOutputParser(constraint.get_variables())
        results = []
        data_file = TempFile(
            generator.generate_data(assignment, constraint.get_variables()), "dzn"
        )
        output, command = execute(file, data_file=data_file.name)
        if error_pattern.search(output):
            print("ERROR:\n{}\n".format(command), output)
        elif not unsatisfiable_pattern.search(output):
            results += parser.parse_solutions(assignment, output)
            data_file.delete()
        return results


def execute(model_file, data_file=None):
    command = (
        ["mzn-gecode", "-a"]
        + ([] if data_file is None else ["-d", data_file])
        + [model_file]
    )
    return run_command(command), " ".join(command)
