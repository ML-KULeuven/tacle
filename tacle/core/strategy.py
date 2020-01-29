import multiprocessing
import time

from .template import ConstraintTemplate
from tacle.indexing import Block


class AssignmentStrategy:
    def applies_to(self, constraint):
        raise NotImplementedError()

    def apply(self, constraint: ConstraintTemplate, groups: [Block], solutions):
        raise NotImplementedError()


class DictAssignmentStrategy(AssignmentStrategy):
    def __init__(self):
        self.strategies = {}

    def add_strategy(self, constraint: ConstraintTemplate, strategy_f):
        self.strategies[constraint] = strategy_f

    def applies_to(self, constraint):
        return constraint in self.strategies

    def apply(self, constraint: ConstraintTemplate, groups: [Block], solutions):
        return self.strategies[constraint](constraint, groups, solutions)


class SolvingStrategy(object):
    def applies_to(self, constraint):
        raise NotImplementedError()

    def apply(self, constraint: ConstraintTemplate, assignments: [{Block}], solutions):
        raise NotImplementedError()


class DictSolvingStrategy(SolvingStrategy):
    def __init__(self):
        self.strategies = {}

    def add_strategy(self, constraint: ConstraintTemplate, strategy_f):
        self.strategies[constraint] = strategy_f

    def applies_to(self, constraint):
        return constraint in self.strategies

    # def adapt_assignment(self, constraint, assignment):
    #     variable_name = None
    #     adapted_block = None
    #     for v, block in assignment.items():
    #         if isinstance(block, indexing.Block) and block.virtual:
    #             if constraint.target and constraint.target.name == v:
    #                 try:
    #                     adapted_block = block.set_data(evaluate_template(constraint, assignment))
    #                     variable_name = v
    #                 except UnsupportedFormula:
    #                     return None
    #                 except InvalidArguments:
    #                     return None
    #             else:
    #                 return None
    #     if adapted_block is not None:
    #         return {v: b if v != variable_name else adapted_block for v, b, in assignment.items()}
    #     return assignment

    def apply(self, constraint: ConstraintTemplate, assignments: [{Block}], solutions):
        # if self.virtual:
        #     new_assignments = []
        #     for assignment in assignments:
        #         adapted = self.adapt_assignment(constraint, assignment)
        #         if adapted is not None:
        #             new_assignments.append(adapted)
        #     assignments = new_assignments
        return self.strategies[constraint](constraint, assignments, solutions)


class StrategyManager(object):
    def __init__(self, timeout=None):
        self.assignment_strategies = []
        self.solving_strategies = []
        self.timeout = timeout

    def add_assignment_strategy(self, strategy: AssignmentStrategy):
        self.assignment_strategies.append(strategy)

    def add_solving_strategy(self, strategy: SolvingStrategy):
        self.solving_strategies.append(strategy)

    def find_assignments(
        self, constraint: ConstraintTemplate, groups: [Block], solutions
    ) -> [[Block]]:
        for strategy in self.assignment_strategies:
            if strategy.applies_to(constraint):
                return strategy.apply(constraint, groups, solutions)
        raise Exception("No assignment handler for {}".format(constraint))

    def supports_assignments_for(self, constraint: ConstraintTemplate):
        for strategy in self.assignment_strategies:
            if strategy.applies_to(constraint):
                return True
        return False

    def find_solutions(
        self, constraint: ConstraintTemplate, assignments: [{Block}], solutions
    ) -> [{(Block, int)}]:
        for strategy in self.solving_strategies:
            if strategy.applies_to(constraint):
                if self.timeout is not None:

                    def async_call(c, a, s, q):
                        found = list(strategy.apply(c, a, s))
                        q.put(found)

                    queue = multiprocessing.Queue()
                    p = multiprocessing.Process(
                        target=async_call,
                        args=(constraint, assignments, solutions, queue),
                    )
                    p.start()

                    p.join(self.timeout)

                    result = []
                    while True:
                        if not queue.empty():
                            result += queue.get()
                        else:
                            p.terminate()
                            p.join()
                            break
                        time.sleep(0.01)  # Give tasks a chance to put more data in
                        if not p.is_alive():
                            break

                    return result
                else:
                    return strategy.apply(constraint, assignments, solutions)
        raise Exception("No solving handler for {}".format(constraint))

    def supports_solving_for(self, constraint: ConstraintTemplate):
        for strategy in self.solving_strategies:
            if strategy.applies_to(constraint):
                return True
        return False
