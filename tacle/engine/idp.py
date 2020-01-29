import re

from tacle.core.template import *
from legacy.group import *
from tacle.core.strategy import DictAssignmentStrategy
from .util import run_command, local


class IdpAssignmentStrategy(DictAssignmentStrategy):
    def __init__(self):
        super().__init__()

        def sum_column(constraint, groups, solutions):
            files = [local("idp/group/assign.idp"), local("idp/group/sum_column.idp")]
            structure = self.create_structure(constraint, groups)
            return self.extract_assignment(constraint.get_variables(), files, structure)

    @staticmethod
    def extract_assignment(variables, files, structure):
        assignments = []
        assign_pattern = re.compile(r".*assign = .*")
        patterns = [
            (var, re.compile(r'.*assign = .*"' + var.get_name() + r'"->"(G\d+)".*'))
            for var in variables
        ]
        for line in iter(execute(files, structure).splitlines()):
            if assign_pattern.match(line):
                a = {}
                for var, pattern in patterns:
                    match = pattern.match(line)
                    if match is not None:
                        a[var.get_name()] = match.group(1)
                assignments.append(a)
        return assignments

    def create_structure(self, constraint: ConstraintTemplate, groups):
        variables = constraint.get_variables()

        def lambda_filter(f):
            return map(Variable.get_name, filter(f, variables))

        parts = [
            self._structure("Var", [v.get_name() for v in variables]),
            "\n".join([v.get_name() + " = " + v.get_name() for v in variables]),
            self._structure("vector", lambda_filter(Variable.is_vector)),
            self._structure("numeric", lambda_filter(Variable.is_numeric)),
            self._structure(
                "Num",
                [
                    "1.."
                    + str(
                        max(map(lambda g: max(g.columns(), g.rows()), groups.values()))
                    )
                ],
            ),
            self._structure("Group", list(groups.keys())),
            self._group_structure("g_length", Group.length, groups),
            self._group_structure("g_columns", Group.columns, groups),
            self._group_structure("g_rows", Group.rows, groups),
            self._structure(
                "g_numeric", [k for k, g in groups.items() if g.is_numeric()]
            ),
        ]
        return "\nstructure S : VConstraint {\n" + "\n".join(parts) + "\n}"

    @staticmethod
    def _structure(name, members):
        return name + " = {" + "; ".join(members) + "}"

    def _group_structure(self, name, method, groups):
        return self._structure(
            name, ["(" + k + ", " + str(method(g)) + ")" for k, g in groups.items()]
        )


def execute(files: [], structure):
    data = "\n".join(['include "' + file + '"' for file in files])
    return run_command(["idp"], input_data=data + structure)
