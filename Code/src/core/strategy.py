from core.constraint import Constraint
from core.group import Group


class AssignmentStrategy:
    def applies_to(self, constraint):
        raise NotImplementedError()

    def apply(self, constraint: Constraint, groups: [Group], solutions):
        raise NotImplementedError()


class DictAssignmentStrategy(AssignmentStrategy):
    def __init__(self):
        self.strategies = {}

    def add_strategy(self, constraint: Constraint, strategy_f):
        self.strategies[constraint] = strategy_f

    def applies_to(self, constraint):
        return constraint in self.strategies

    def apply(self, constraint: Constraint, groups: [Group], solutions):
        return self.strategies[constraint](constraint, groups, solutions)


class SolvingStrategy:
    def applies_to(self, constraint):
        raise NotImplementedError()

    def apply(self, constraint: Constraint, assignments: [{Group}], solutions):
        raise NotImplementedError()


class DictSolvingStrategy(SolvingStrategy):
    def __init__(self):
        self.strategies = {}

    def add_strategy(self, constraint: Constraint, strategy_f):
        self.strategies[constraint] = strategy_f

    def applies_to(self, constraint):
        return constraint in self.strategies

    def apply(self, constraint: Constraint, assignments: [{Group}], solutions):
        return self.strategies[constraint](constraint, assignments, solutions)


class StrategyManager:
    def __init__(self):
        super().__init__()
        self.assignment_strategies = []
        self.solving_strategies = []

    def add_assignment_strategy(self, strategy: AssignmentStrategy):
        self.assignment_strategies.append(strategy)

    def add_solving_strategy(self, strategy: SolvingStrategy):
        self.solving_strategies.append(strategy)

    def find_assignments(self, constraint: Constraint, groups: [Group], solutions) -> [[Group]]:
        for strategy in self.assignment_strategies:
            if strategy.applies_to(constraint):
                return strategy.apply(constraint, groups, solutions)
        raise Exception("No assignment handler for {}".format(constraint))

    def supports_assignments_for(self, constraint: Constraint):
        for strategy in self.assignment_strategies:
            if strategy.applies_to(constraint):
                return True
        return False

    def find_solutions(self, constraint: Constraint, assignments: [{Group}], solutions) -> [{(Group, int)}]:
        for strategy in self.solving_strategies:
            if strategy.applies_to(constraint):
                return strategy.apply(constraint, assignments, solutions)
        raise Exception("No solving handler for {}".format(constraint))

    def supports_solving_for(self, constraint: Constraint):
        for strategy in self.solving_strategies:
            if strategy.applies_to(constraint):
                return True
        return False
