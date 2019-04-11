from typing import Dict, TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from .template import ConstraintTemplate
    from .group import Group


class Constraint(object):
    def __init__(self, template, assignment):
        # type: (ConstraintTemplate, Dict[str, object]) -> None
        self.template = template  # type: ConstraintTemplate
        self.assignment = assignment  # type: Dict[str, Group]

    def is_formula(self):
        return self.template.is_formula()

    def __getattr__(self, item):
        # type: (str) -> Group
        if item.startswith("__") or item in ["template", "assignment"]:
            return super().__getattribute__(item)
        from core.assignment import Variable
        return self[item.name] if isinstance(item, Variable) else self[item]

    def __getitem__(self, item):
        # type: (Union[str, int]) -> Group
        from core.assignment import Variable
        if isinstance(item, str) and item in self.assignment:
            return self.assignment[item]
        elif isinstance(item, int):
            return self.assignment[self.template.variables[item].name]
        elif isinstance(item, Variable):
            return self.assignment[item.name]
        raise AttributeError("No attribute called {}".format(item))

    def __repr__(self):
        return "Constraint({}, {})".format(repr(self.template), self.assignment)

    def __str__(self):
        return self.template.to_string(self.assignment)


class Solutions:
    def __init__(self):
        self.solutions = {}
        self.properties = {}
        self.canon_map = dict()
        self.constraints = []  # type: List[Constraint]

    def add(self, template, solutions):
        solutions_l = list(solutions)
        self.solutions[template] = solutions_l
        solution_set = set(self._to_tuple(template, solution) for solution in solutions_l)
        self.properties[template] = solution_set
        for solution in solutions_l:
            self.constraints.append(Constraint(template, solution))

    def get_solutions(self, template):
        return self.solutions.get(template, [])

    def has_solution(self, template, solution):
        return self._to_tuple(template, solution) in self.properties[template]

    def has(self, template, keys, values):
        return self.has_solution(template, {k.name: v for k, v in zip(keys, values)})

    @staticmethod
    def _to_tuple(template, solution):
        try:
            return tuple(solution[v.name] for v in template.variables)
        except KeyError as e:
            raise RuntimeError("No value for {} in solution {}".format(e.args[0], solution))

    def set_canon(self, canon_map):
        self.canon_map = canon_map

                  

