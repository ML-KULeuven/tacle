from typing import List

from constraint import Problem, FunctionConstraint, RecursiveBacktrackingSolver
from core.group import Group


class Variable:
    def __init__(self, name, vector=False, numeric=False, textual=False, integer=False):
        self.name = name
        self.vector = vector
        self.numeric = numeric
        self.integer = integer
        self.textual = textual

    def __str__(self):
        return self.name + "[Var]"

    def get_name(self):
        return self.name

    def is_vector(self):
        return self.vector

    def is_numeric(self):
        return self.numeric

    def is_integer(self):
        return self.integer

    def is_textual(self):
        return self.textual


class Source:
    def __init__(self, variables: List[Variable]):
        self._variables = variables

    @property
    def variables(self):
        return self._variables

    def candidates(self, groups, solutions, filters):
        return self._complete([{}], self.variables, groups, filters)

    @staticmethod
    def _complete(assignments, v_unassigned, groups, filters):
        result = []
        for assignment in assignments:
            problem = Problem()

            for variable in assignment:
                problem.addVariable(variable, [assignment[variable]])

            for variable in v_unassigned:
                domain = groups
                if variable.is_numeric():
                    domain = list(filter(Group.is_numeric, domain))
                if variable.is_integer():
                    domain = list(filter(Group.is_integer, domain))
                if variable.is_textual():
                    domain = list(filter(Group.is_textual, domain))
                domain = list(domain)
                if len(domain) == 0:
                    return []
                problem.addVariable(variable.name, domain)

            for f in filters:
                variables = list([v.name for v in f.variables])

                def c_j(ff, vv):
                    return lambda *args: ff.test({vv[i]: args[i] for i in range(len(args))})

                problem.addConstraint(c_j(f, variables), variables)

            result += list(problem.getSolutions())
        return result
        #return [dict({v_unassigned[i]: l[i] for i in range(len(v_unassigned))}, **assignment)
        #        for l in itertools.permutations(groups, len(v_unassigned))
        #        for assignment in assignments]


class ConstraintSource(Source):
    def __init__(self, variables, constraint, dictionary):
        super().__init__(variables)
        self.constraint = constraint
        self.dictionary = dictionary

    def candidates(self, groups, solutions, filters):
        v_assigned = {v for v in self.dictionary.values()}
        assignments = [{self.dictionary[k]: v for k, v in s.items()} for s in solutions.get_solutions(self.constraint)]
        v_unassigned = [v for v in self.variables if v.name not in v_assigned]
        return self._complete(assignments, v_unassigned, groups, filters)


class Filter:
    def __init__(self, variables: List[Variable]):
        self._variables = variables

    @property
    def variables(self):
        return self._variables

    def test(self, assignment):
        raise NotImplementedError()

    def test_same(self, assignment, f):
        groups = list([assignment[v.name] for v in self.variables])
        return all(f(groups[i]) == f(groups[j]) for i in range(len(groups)) for j in range(i + 1, len(groups)))


class NoFilter(Filter):
    def test(self, assignment):
        return True


class SameLength(Filter):
    def test(self, assignment):
        return self.test_same(assignment, Group.length)


class SameTable(Filter):
    def test(self, assignment):
        return self.test_same(assignment, lambda g: g.table)


class SameOrientation(Filter):
    def test(self, assignment):
        return self.test_same(assignment, lambda g: g.row)


class NotSubgroup(Filter):
    def test(self, assignment):
        if len(self.variables) != 2:
            raise RuntimeError("Expected two variables, got {}".format(len(self.variables)))
        return not assignment[self.variables[0].name].is_subgroup(assignment[self.variables[1].name])
