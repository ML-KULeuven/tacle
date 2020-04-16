from typing import Dict, TYPE_CHECKING, List, Union


if TYPE_CHECKING:
    from .template import ConstraintTemplate
    from tacle.indexing import Block


class Importer:
    def __init__(self):
        from tacle.workflow import get_default_templates

        self.name_to_template = {t.name: t for t in get_default_templates()}

    def import_template(self, name):
        return self.name_to_template[name]

    def import_constraint(self, name, assignment):
        return Constraint(self.import_template(name), assignment)


class Constraint(object):
    importer = None

    def __init__(self, template, assignment):
        # type: (ConstraintTemplate, Dict[str, Block]) -> None
        self.template = template  # type: ConstraintTemplate
        self.assignment = assignment  # type: Dict[str, Block]

    def is_formula(self):
        return self.template.is_formula()

    def predict(self, input_matrix):
        from tacle.engine import evaluate

        variables = [
            v
            for i, v in enumerate(self.template.variables)
            if v != self.template.target
        ]
        if len(variables) == 1 and input_matrix.shape[1] > 1:
            assignment = {variables[0]: input_matrix}
        else:
            assignment = {v.name: input_matrix[:, i] for i, v in variables}
        return evaluate.evaluate_template(self.template, assignment)

    def __getattr__(self, item):
        # type: (str) -> Block
        if item.startswith("__") or item in ["template", "assignment", "predict"]:
            return super().__getattribute__(item)
        from tacle.core.assignment import Variable

        return self[item.name] if isinstance(item, Variable) else self[item]

    def __getitem__(self, item):
        # type: (Union[str, int]) -> Block
        from tacle.core.assignment import Variable

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

    def to_dict(self):
        return {"name": self.template.name, "assignment": self.assignment}

    @staticmethod
    def from_dict(constraint_dict):
        if Constraint.importer is None:
            Constraint.importer = Importer()
        return Constraint.importer.import_constraint(
            constraint_dict["name"], constraint_dict["assignment"]
        )


class Solutions:
    def __init__(self):
        self.solutions = {}
        self.properties = {}
        self.canon_map = dict()
        self.constraints = []  # type: List[Constraint]

    def add(self, template, solutions):
        solutions_l = list(solutions)
        self.solutions[template] = solutions_l
        solution_set = set(
            self._to_tuple(template, solution) for solution in solutions_l
        )
        self.properties[template] = solution_set
        for solution in solutions_l:
            self.constraints.append(Constraint(template, solution))

    def get_solutions(self, template):
        return self.solutions.get(template, [])

    def has_solution(self, template, solution):
        return self._to_tuple(template, solution) in self.properties.get(template, [])

    def has(self, template, keys, values):
        return self.has_solution(template, {k.name: v for k, v in zip(keys, values)})

    @staticmethod
    def _to_tuple(template, solution):
        try:
            return tuple(solution[v.name] for v in template.variables)
        except KeyError as e:
            raise RuntimeError(
                "No value for {} in solution {}".format(e.args[0], solution)
            )

    def set_canon(self, canon_map):
        self.canon_map = canon_map
