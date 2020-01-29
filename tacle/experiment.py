import os

from core.template import *
from pandas import json

import workflow
from legacy.group import Bounds
from engine.util import local


class ConstraintCounter:
    def __init__(self, solutions):
        self._relevant = set()
        self._tracking = set()
        self._additional = set()
        for constraint in solutions:
            for solution in solutions[constraint]:
                self._tracking.add((constraint, frozenset(solution.items())))
                self._relevant.add((constraint, frozenset(solution.items())))

    @property
    def relevant(self):
        return self._relevant

    @property
    def additional(self):
        return self._additional

    @property
    def missed(self):
        return self._tracking

    def register(self, constraint: ConstraintTemplate, solution):
        s_strings = frozenset(
            {name: str(group) for name, group in solution.items()}.items()
        )
        if (constraint.name, s_strings) in self._relevant:
            self._tracking.remove((constraint.name, s_strings))
        elif is_excel_constraint(constraint):
            self._additional.add((constraint.name, s_strings))

    def count(self, found=None, relevant=None, supported=False):
        relevant_list = self._relevant
        if supported is True:
            relevant_list = list(
                r
                for r, _ in relevant_list
                if r in [c.name for c in excel_constraints()]
            )
        if relevant is True and found is True:
            return len(relevant_list) - len(self._tracking)
        elif relevant is True and found is False:
            return len(self._tracking)
        elif relevant is True and found is None:
            return len(relevant_list)
        elif relevant is False and found is True:
            return len(self._additional)
        elif relevant is None and found is True:
            return len(relevant_list) - len(self._tracking) + len(self._additional)
        raise Exception("Unknown")


class Experiment:
    def __init__(self, name):
        super().__init__()
        self._name = name
        self._run = False
        self._running_times = []
        self._cells = None
        self._tables = None
        self._vectors = None
        self._counter = None
        self.manager = None

    @property
    def name(self):
        return self._name

    @property
    def cells(self):
        self.run()
        return self._cells

    @property
    def tables(self):
        self.run()
        return self._tables

    @property
    def vectors(self):
        return self._vectors

    @property
    def counter(self):
        self.run()
        return self._counter

    def running_times(self, amount=10):
        while len(self._running_times) < amount:
            self._run = False
            self.run()
        return self._running_times[0:9]

    def run(self):
        if not self._run:
            csv_file, config_file = self._get_csv_file(), self._get_config_file()
            learning_task = workflow.task(csv_file, config_file, manager=self.manager)
            solutions = learning_task.run()
            # print(*learning_task.constraints, sep="\t")
            # print(*["{:.3f}".format(learning_task.time(c)) for c in learning_task.constraints], sep="\t")
            #
            self._running_times.append(learning_task.total_time())
            self.count_constraints(solutions)
            self.measure_size(config_file)
        self._run = True

    def measure_size(self, config_file):
        with open(config_file) as file:
            tables = json.load(file)["Tables"]
            cell_count = 0
            vector_count = 0
            for table in tables:
                bounds = Bounds(table["Bounds"])
                cell_count += bounds.columns() * bounds.rows()
                if "Orientation" not in table or table["Orientation"].lower() == "none":
                    vector_count += bounds.columns() + bounds.rows()
                elif table["Orientation"].lower()[0:3] == "row":
                    vector_count += bounds.rows()
                elif table["Orientation"].lower()[0:3] == "col":
                    vector_count += bounds.columns()
                else:
                    raise Exception(
                        "Unexpected orientation: {}".format(table["Orientation"])
                    )
                self._cells = cell_count
                self._vectors = vector_count
            self._tables = len(tables)

    def count_constraints(self, solutions):
        truth_file = self._get_truth_file()
        with open(truth_file) as file:
            json_data = json.load(file)
            self._counter = ConstraintCounter(
                {**json_data["Essential"], **json_data["Non-trivial"]}
            )
            for constraint in solutions.solutions:
                for solution in solutions.get_solutions(constraint):
                    self._counter.register(constraint, solution)

    def _get_csv_file(self):
        csv_file = local("data/csv/{}.csv".format(self.name))
        if not os.path.isfile(csv_file):
            return None
        return csv_file

    def _get_config_file(self):
        config_file = local("data/groups/{}.txt".format(self.name))
        if not os.path.isfile(config_file):
            return None
        return config_file

    def _get_truth_file(self):
        truth_file = local("data/truth/{}.txt".format(self.name))
        if not os.path.isfile(truth_file):
            return None
        return truth_file


def excel_constraints():
    return (
        Aggregate.instances()
        + ConditionalAggregate.instances()
        + [
            Series(),
            Rank(),
            Lookup(),
            FuzzyLookup(),
            RunningTotal(),
            Product(),
            Diff(),
            SumProduct(),
            ForeignProduct(),
            Equal(),
            PercentualDiff(),
            Projection(),
        ]
    )


def is_excel_constraint(c: ConstraintTemplate):
    return c in excel_constraints()
