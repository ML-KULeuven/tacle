import time

from .solutions import Solutions
from legacy.parser import get_groups_tables
from tacle.util import printing


class LearningTask:
    def __init__(self, csv_file, groups_file, manager, constraints):
        self._manager = manager
        self._groups = list(get_groups_tables(csv_file, groups_file))
        # self._solutions = Solutions()
        self._constraints = ordered_constraints(constraints)
        self._times = dict()

    @property
    def constraints(self):
        return self._constraints

    @property
    def manager(self):
        return self._manager

    def run(self):
        supported = []
        unsupported_assignment = []
        unsupported_solving = []
        for constraint in self.constraints:
            if not self.manager.supports_assignments_for(constraint):
                unsupported_assignment.append(constraint)
            elif not self.manager.supports_solving_for(constraint):
                unsupported_solving.append(constraint)
            else:
                supported.append(constraint)

        print_concise = printing.get(__name__, on=False)

        if len(unsupported_assignment) > 0:
            print_concise.form(
                "No assignment strategy for: {}",
                ", ".join(str(c) for c in unsupported_assignment),
            )
        if len(unsupported_solving) > 0:
            print_concise.form(
                "No solving strategies for: {}",
                ", ".join(str(c) for c in unsupported_solving),
            )
        if len(unsupported_assignment) > 0 or len(unsupported_solving) > 0:
            print_concise.nl()

        print_verbose = printing.get("detail", print_concise, on=False)
        solutions = Solutions()
        for constraint in self.constraints:
            print_verbose.write(constraint.name, end=" ")
            t_start = time.time()
            assignments = self.manager.find_assignments(
                constraint, self._groups, solutions
            )
            t_assign = time.time()
            solutions.add(
                constraint,
                self.manager.find_solutions(constraint, assignments, solutions),
            )
            t_end = time.time()
            assignment_time = t_assign - t_start
            solving_time = t_end - t_assign
            self._times[constraint] = (assignment_time, solving_time)
            if print_verbose.on():
                print_verbose.form(
                    "[assignment time: {assign:.3f}, solving time: {solve:.3f}]",
                    assign=assignment_time,
                    solve=solving_time,
                )
            if len(solutions.get_solutions(constraint)) > 0:
                print_concise.write(
                    lambda: "\n".join(
                        [
                            "\t" + constraint.to_string(s)
                            for s in solutions.get_solutions(constraint)
                        ]
                    )
                )
            if len(solutions.get_solutions(constraint)) > 0 or print_verbose.on():
                print_concise.nl()

        print_verbose.write(lambda: "Total: {0:.3f}".format(self.total_time()))
        return solutions

    def total_time(self):
        return sum(self.time(c) for c in self.constraints)

    def time(self, constraint):
        assign, solve = self._times[constraint]
        return assign + solve


def ordered_constraints(constraints):
    ordered = []
    found = set()
    spill = constraints
    while len(spill) > 0:
        new_spill = []
        for constraint in constraints:
            if constraint.depends_on().issubset(found):
                ordered.append(constraint)
                found.add(constraint)
            else:
                spill.append(constraint)
        if len(new_spill) == len(spill):
            raise Exception("Dependency order is not a DAG")
        spill = new_spill
    return ordered
