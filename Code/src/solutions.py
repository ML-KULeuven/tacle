class Solutions:
    def __init__(self):
        self.solutions = {}
        self.properties = {}

    def add(self, constraint, solutions):
        self.solutions[constraint] = solutions
        if len(constraint.get_variables()) == 1:
            self.properties[constraint] = [a[constraint.get_variables()[0].name] for a in solutions]

    def get_solutions(self, constraint):
        return self.solutions.get(constraint, [])

    def get_property_groups(self, constraint):
        return self.properties.get(constraint, [])
