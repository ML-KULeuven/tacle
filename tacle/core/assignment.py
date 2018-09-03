from typing import List, Dict, Set

from constraint import Problem

from tacle import indexing
from tacle.indexing import Typing
from tacle.parse.parser import GType
from .group import Group, Orientation
from .solutions import Solutions


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
    def __init__(self, variables):
        # type: (List[Variable]) -> None
        self._variables = variables

    @property
    def variables(self):
        return self._variables

    def candidates(self, groups, solutions, filters):
        return self._complete([{}], groups, filters, solutions)

    def _complete(self, assignments, groups, filters, solutions):
        result = []

        # TODO type as constraint

        def try_assignment():
            problem = Problem()

            for variable in self.variables:
                candidates = [assignment[variable.name]] if variable.name in assignment else groups
                domain = list([g for g in candidates if any(st in variable.types for st in
                                                            (Typing.as_legacy_type(gt) for gt in g.vector_types))])
                if len(domain) == 0:
                    return variable.name in assignment, []
                problem.addVariable(variable.name, domain)

            for f in filters:
                variables = list([v.name for v in f.variables])

                def c_j(ff, vv):
                    return lambda *args: ff.test_relaxed({vv[i]: args[i] for i in range(len(args))}, solutions)

                problem.addConstraint(c_j(f, variables), variables)

            return True, list(problem.getSolutions())

        for assignment in assignments:
            resume, candidate_solutions = try_assignment()
            if not resume:
                return []
            result += candidate_solutions
        return result

    def depends_on(self) -> Set:
        return set()


class ConstraintSource(Source):
    def __init__(self, variables, constraint, dictionary):
        super().__init__(variables)
        self._constraint = constraint
        self.dictionary = dictionary

    @property
    def constraint(self):
        return self._constraint

    def candidates(self, groups, solutions, filters):
        assignments = [{self.dictionary[k]: v for k, v in s.items()} for s in solutions.get_solutions(self.constraint)]
        return self._complete(assignments, groups, filters, solutions)

    def depends_on(self):
        return {self.constraint}


class Filter:
    def __init__(self, variables: List[Variable]):
        self._variables = variables

    @property
    def variables(self):
        return self._variables

    def test(self, assignment: Dict[str, Group], solutions):
        raise NotImplementedError()

    def test_relaxed(self, assignment, solutions):
        return self.test(assignment, solutions)

    def is_relaxed(self):
        return False

    def test_same(self, assignment, f):
        groups = list([assignment[v.name] for v in self.variables])
        result = all(f(groups[i]) == f(groups[j]) for i in range(len(groups)) for j in range(i + 1, len(groups)))
        return result

    def test_all(self, assignment, f):
        groups = list([assignment[v.name] for v in self.variables])
        result = all(f(g) for g in groups)
        return result

    @staticmethod
    def rows(block):
        if isinstance(block, Group):
            return block.rows()
        elif isinstance(block, indexing.Block):
            return block.rows()
        else:
            raise ValueError()

    @staticmethod
    def cols(block):
        if isinstance(block, Group):
            return block.columns()
        elif isinstance(block, indexing.Block):
            return block.columns()
        else:
            raise ValueError()

    @staticmethod
    def vector_length(block):
        if isinstance(block, Group):
            return block.length()
        elif isinstance(block, indexing.Block):
            return block.vector_length()
        else:
            raise ValueError()

    @staticmethod
    def vector_count(block):
        if isinstance(block, Group):
            return block.vectors()
        elif isinstance(block, indexing.Block):
            return block.vector_count()
        else:
            raise ValueError()

    @staticmethod
    def table(block):
        if isinstance(block, Group):
            return block.table.name  # DEPRECATED
        elif isinstance(block, indexing.Block):
            return block.table.name
        else:
            raise ValueError()

    @staticmethod
    def orientation(block):
        if isinstance(block, Group):
            return indexing.Orientation.horizontal if block.row else indexing.Orientation.vertical
        elif isinstance(block, indexing.Block):
            return block.orientation
        else:
            raise ValueError()

    @staticmethod
    def block_type(block):
        if isinstance(block, Group):
            if block.dtype == GType.float:
                return Typing.float
            elif block.dtype == GType.int:
                return Typing.int
            elif block.dtype == GType.string:
                return Typing.string
            else:
                raise ValueError()
        elif isinstance(block, indexing.Block):
            return block.type
        else:
            raise ValueError()


class Not(Filter):
    def __init__(self, original_filter: Filter):
        super().__init__(original_filter.variables)
        self._original_filter = original_filter

    def test(self, assignment, solutions):
        return not self._original_filter.test(assignment, solutions)


class If(Filter):
    def __init__(self, if_filter: Filter, then_filter: Filter, else_filter: Filter=None):
        if else_filter is None:
            else_filter = NoFilter([])
        variables = set(if_filter.variables).union(set(then_filter.variables)).union(set(else_filter.variables))
        super().__init__(variables)
        self._if_filter = if_filter
        self._then_filter = then_filter
        self._else_filter = else_filter

    @property
    def if_filter(self):
        return self._if_filter

    @property
    def then_filter(self):
        return self._then_filter

    @property
    def else_filter(self):
        return self._else_filter

    def test(self, assignment: Dict[str, Group], solutions):
        if self.if_filter.test(assignment, solutions):
            return self.then_filter.test(assignment, solutions)
        else:
            return self.else_filter.test(assignment, solutions)


class NoFilter(Filter):
    def test(self, assignment: Dict[str, Group], solutions):
        return True


class SameLength(Filter):
    def test(self, assignment: Dict[str, Group], solutions):
        return self.test_same(assignment, SameLength.vector_length)


class SameTable(Filter):
    def test(self, assignment: Dict[str, Group], solutions):
        return self.test_same(assignment, SameTable.table)


class SameOrientation(Filter):
    def test(self, assignment: Dict[str, Group], solutions):
        return self.test_same(assignment, SameOrientation.orientation)


class SameType(Filter):
    def test(self, assignment: Dict[str, Group], solutions):
        return self.test_same(assignment, SameType.block_type)


class SizeFilter(Filter):
    def __init__(self, variables, rows=None, cols=None, length=None, vectors=None, max_size=False):
        super().__init__(variables)
        self._rows = rows
        self._cols = cols
        self._length = length
        self._vectors = vectors
        self._max_size = max_size

    def test(self, assignment: Dict[str, Group], solutions):
        groups = list([assignment[v.name] for v in self.variables])
        op = (lambda x, y: x <= y) if self._max_size else (lambda x, y: x >= y)
        return all(self._rows is None or op(self.rows(g), self._rows) for g in groups) \
            and all(self._cols is None or op(self.cols(g), self._cols) for g in groups) \
            and all(self._length is None or op(self.vector_length(g), self._length) for g in groups) \
            and all(self._vectors is None or op(self.vector_count(g), self._vectors) for g in groups)

    def test_relaxed(self, assignment: Dict[str, Group], solutions):
        if self._max_size:
            # Max size can not be enforced at the super-block level
            groups = list([assignment[v.name] for v in self.variables])
            valid = all(self._rows is None or self.orientation(g) == indexing.Orientation.horizontal
                        or self.rows(g) <= self._rows for g in groups)\
                and all(self._cols is None or self.orientation(g) == indexing.Orientation.vertical
                        or self.cols(g) <= self._cols for g in groups)\
                and all(self._length is None or self.vector_length(g) <= self._length for g in groups)
            return valid
        else:
            return self.test(assignment, solutions)

    def is_relaxed(self):
        return self._max_size


class OrientationFilter(Filter):
    def __init__(self, variables, orientation):
        self._orientation = orientation
        super().__init__(variables)

    @property
    def orientation(self):
        return self._orientation

    def test(self, assignment: Dict[str, Group], solutions):
        return self.test_all(assignment, lambda g: g.row == (self.orientation == Orientation.HORIZONTAL))


class NotPartial(Filter):
    @staticmethod
    def has_blanks(block):
        if isinstance(block, Group):
            return block.is_partial
        elif isinstance(block, indexing.Block):
            return block.has_blanks
        else:
            raise ValueError()

    def test(self, assignment: Dict[str, Group], solutions):
        return not any([self.has_blanks(assignment[v.name]) for v in self.variables])


class Partial(Filter):
    def test(self, assignment: Dict[str, Group], solutions):
        return all([NotPartial.has_blanks(assignment[v.name]) for v in self.variables])


class NotSubgroup(Filter):
    def test(self, assignment: Dict[str, Group], solutions):
        if len(self.variables) != 2:
            raise RuntimeError("Expected two variables, got {}".format(len(self.variables)))
        return not assignment[self.variables[0].name].is_subgroup(assignment[self.variables[1].name])


class SatisfiesConstraint(Filter):
    def __init__(self, variables, constraint, mapping):
        super().__init__(variables)
        self._constraint = constraint
        self._mapping = mapping

    @property
    def constraint(self):
        return self._constraint

    @property
    def mapping(self):
        return self._mapping

    def test(self, assignment: Dict[str, Group], solutions: Solutions):
        variables = self.constraint.variables
        return solutions.has(self.constraint, variables, {assignment[self.mapping[v.name]] for v in variables})

