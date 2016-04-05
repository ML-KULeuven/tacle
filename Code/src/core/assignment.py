from typing import List, Dict

from constraint import Problem
from core.group import Group, GType


class Variable:
    def __init__(self, name, vector=False, types={GType.int, GType.float, GType.string}):
        self.name = name
        self.vector = vector
        if len(types) == 0:
            raise Exception("At least one type must be supported")
        self._types = types

    @property
    def types(self):
        return self._types

    def __str__(self):
        return self.name + "[Var]"

    def get_name(self):
        return self.name

    def is_vector(self):
        return self.vector

    def is_numeric(self):
        return GType.string not in self.types

    def is_textual(self):
        return len(self.types) == 1 and GType.string in self.types

    def is_integer(self):
        return len(self.types) == 1 and GType.int in self.types


class Source:
    def __init__(self, variables: List[Variable]):
        self._variables = variables

    @property
    def variables(self):
        return self._variables

    def candidates(self, groups, solutions, filters):
        return self._complete([{}], self.variables, groups, filters)

    def _complete(self, assignments, v_unassigned, groups, filters):
        result = []

        def try_assignment():
            problem = Problem()

            for variable in self.variables:
                candidates = [assignment[variable.name]] if variable.name in assignment else groups
                domain = list([g for g in candidates if g.dtype in variable.types])
                if len(domain) == 0:
                    return variable.name in assignment, []
                problem.addVariable(variable.name, domain)

            for f in filters:
                variables = list([v.name for v in f.variables])

                def c_j(ff, vv):
                    return lambda *args: ff.test({vv[i]: args[i] for i in range(len(args))})

                problem.addConstraint(c_j(f, variables), variables)

            return True, list(problem.getSolutions())

        for assignment in assignments:
            resume, solutions = try_assignment()
            if not resume:
                return []
            result += solutions
        return result


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

    def test(self, assignment: Dict[str, Group]):
        raise NotImplementedError()

    def test_same(self, assignment, f):
        groups = list([assignment[v.name] for v in self.variables])
        return all(f(groups[i]) == f(groups[j]) for i in range(len(groups)) for j in range(i + 1, len(groups)))


class Not(Filter):
    def __init__(self, original_filter: Filter):
        super().__init__(original_filter.variables)
        self._original_filter = original_filter

    def test(self, assignment):
        return not self._original_filter.test(assignment)


class NoFilter(Filter):
    def test(self, assignment: Dict[str, Group]):
        return True


class SameLength(Filter):
    def test(self, assignment: Dict[str, Group]):
        return self.test_same(assignment, Group.length)


class SameTable(Filter):
    def test(self, assignment: Dict[str, Group]):
        return self.test_same(assignment, lambda g: g.table)


class SameOrientation(Filter):
    def test(self, assignment: Dict[str, Group]):
        return self.test_same(assignment, lambda g: g.row)


class SameType(Filter):
    def test(self, assignment: Dict[str, Group]):
        return self.test_same(assignment, lambda g: g.dtype)


class SizeFilter(Filter):
    def __init__(self, variables, rows=None, cols=None, length=None):
        super().__init__(variables)
        self._rows = rows
        self._cols = cols
        self._length = length

    def test(self, assignment: Dict[str, Group]):
        groups = list([assignment[v.name] for v in self.variables])
        return all(self._rows is None or g.rows() >= self._rows for g in groups) \
            and all(self._cols is None or g.columns() >= self._cols for g in groups) \
            and all(self._length is None or g.length() >= self._length for g in groups)


class NotSubgroup(Filter):
    def test(self, assignment: Dict[str, Group]):
        if len(self.variables) != 2:
            raise RuntimeError("Expected two variables, got {}".format(len(self.variables)))
        return not assignment[self.variables[0].name].is_subgroup(assignment[self.variables[1].name])
