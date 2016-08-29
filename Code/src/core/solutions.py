class Solutions:
    def __init__(self):
        self.solutions = {}
        self.properties = {}
        self.canon_map = dict()

    def add(self, constraint, solutions):
        solutions_l = list(solutions)
        self.solutions[constraint] = solutions_l
        solution_set = set(self._to_tuple(constraint, solution) for solution in solutions_l)
        self.properties[constraint] = solution_set

    def get_solutions(self, constraint):
        return self.solutions.get(constraint, [])

    def has_solution(self, constraint, solution):
        return self._to_tuple(constraint, solution) in self.properties[constraint]

    def has(self, constraint, keys, values):
        return self.has_solution(constraint, {k.name: v for k, v in zip(keys, values)})

    @staticmethod
    def _to_tuple(constraint, solution):
        return tuple(solution[v.name] for v in constraint.variables)

    def set_canon(self, canon_map):
        self.canon_map = canon_map

                  

