import os
import time

from pandas import json

import print_truth
import workflow
from core.template import *
from engine.util import local

exercises = [
    "baltimore",
    "bedrijfsresultaten",
    "belgium",
    "bmi",
    "expenses",
    "price_weight",
    "rides",
    "score",
    "shares",
]

tutorials = [
    "sumif_region",
    "age_department_sumif",
    "average_ablebits",
    "fruits",
    "help_lookup",
    "household",
    "inventory",
    "multsum",
    "paper_supply",
    "repair",
    "sales_blanks",
    "school",
    "sum_if_double_condition",
    "sum_table_from_guide",
    "sumif_blanks",
    "sumif_diskettes",
    "sumif_example",
    "sumif_games_toys",
    "sumif_uk",
    "sumproduct",
    "week_2_busn_store_2",
]

real = [
    # glance - missing
    "external_revenue",
    "financial_result",
    "fbi_offenses_corr",
    "pattern_mining",
    "exps_tias"
]

files = ["exps_tias"]  # exercises + tutorials + real


def excel_constraints():
    return Aggregate.instances() + ConditionalAggregate.instances() +\
        [Series(), Rank(), Lookup(), FuzzyLookup(), RunningTotal(), Product(), Diff(), SumProduct(),
         ForeignProduct(), Equal(), PercentualDiff(), Projection()]


def is_excel_constraint(c: ConstraintTemplate):
    return c in excel_constraints()


constraint_map = {c.name: c for c in workflow.get_default_templates()}


def print_constraints(prefix, constraints):
    if len(constraints) > 0:
        print()
        for cons_name, sol in constraints:
            print("\t{prefix}:\t{constraint}: {solution}".format(prefix=prefix, constraint=cons_name, solution=sol))


def main():
    categories = {"essential constraints": "Essential"}
    cat_counters = {n: [] for n in categories}
    measures = [("accuracy", calc_accuracy), ("expected accuracy", calc_expected_accuracy),
                ("redundancy", calc_redundancy)]
    speed = []

    for name in files:
        print(name)
        csv_file = local("data/csv/{}.csv".format(name))
        if not os.path.isfile(csv_file):
            raise Exception("File not found: {}".format(csv_file))
        groups_file = local("data/groups/{}.txt".format(name))
        silent = False  # TODO True
        if not os.path.isfile(groups_file):
            with open(groups_file, "w+") as f:
                print("{\n\t\"Tables\":\n\t\t[\n\n\t\t]\n}", file=f, flush=True)
            groups_file = None
            silent = False
        t_before = time.time()
        solutions = workflow.main(csv_file, groups_file, False, silent=True, parse_silent=silent)
        t_elapsed = time.time() - t_before
        speed.append(t_elapsed)
        print("\tTook: {:.2f} seconds".format(t_elapsed))
        truth_file = local("data/truth/{}.txt".format(name))
        # constraint_map = {c.name: c for c in workflow.constraint_list}
        if os.path.isfile(truth_file):
            with open(truth_file) as f:
                json_data = json.load(f)
                counters = {n: CategoryCounter(json_data[k]) for n, k in categories.items()}
                for constraint in solutions.solutions:
                    for solution in solutions.get_solutions(constraint):
                        for counter in counters.values():
                            counter.count(constraint, solution)
                for c_name, c in counters.items():
                    cat_counters[c_name].append(c)
                    for m_name, m_func in measures:
                        res, actual, expected = m_func([c], per_file=False)
                        print("\t{} for {}: {:.2%} ({} of {})"
                              .format(m_name.capitalize(), c_name, res, actual, expected))

                    print_constraints("MISSING", c.not_found)
                    redundant = CategoryCounter.filter_constraints(c.not_present, is_excel_constraint)
                    print_constraints("REDUNDANT", redundant)
            print()
        elif groups_file is not None:
            with open(truth_file, "w+") as f:
                print("{\n\t\"Essential\":\n\t\t{\n\n\t\t}\n}", file=f, flush=True)
                print_truth.main(name)
    for n in categories:
        print("Time elapsed: {:.2f}s (total), {:.2f}s (average)".format(sum(speed), numpy.average(speed)))
        for m_name, m_func in measures:
            res, not_zero, file_count = m_func(cat_counters[n], per_file=True)
            print("{} {} per file ({} of {} files): {:.2%}".format(n.capitalize(), m_name, not_zero, file_count, res))
            res, actual, expected = m_func(cat_counters[n], per_file=False)
            print("Total {} {}: {:.2%} ({} of {})".format(n, m_name, res, actual, expected))
            print()
    return cat_counters


class CategoryCounter:
    def __init__(self, constraint_json):
        self._constraints = set()
        self._not_found = set()
        self._not_present = set()
        self._count = 0
        for constraint in constraint_json:
            self._count += len(constraint_json[constraint])
            for solution in constraint_json[constraint]:
                self._not_found.add((constraint, frozenset(solution.items())))
                self._constraints.add((constraint, frozenset(solution.items())))
        self._present = 0

    @property
    def constraints(self):
        return self._constraints

    @property
    def hits(self):
        return self._present

    @property
    def expected(self):
        return self._count

    @property
    def not_found(self):
        return self._not_found

    @property
    def not_present(self):
        return self._not_present

    def count(self, constraint: ConstraintTemplate, solution):
        s_strings = frozenset({name: str(group) for name, group in solution.items()}.items())
        if (constraint.name, s_strings) in self._constraints:
            self._present += 1
            self._not_found.remove((constraint.name, s_strings))
        else:
            self._not_present.add((constraint.name, s_strings))

    @staticmethod
    def filter_constraints(constraints, test_f):
        return list(c for c in constraints if test_f(constraint_map[c[0]]))


def calc_accuracy(counters: List[CategoryCounter], per_file=False):
    return calc_ratio(counters, lambda c: c.hits, lambda c: c.expected, per_file)


def calc_expected_accuracy(counters: List[CategoryCounter], per_file=False):
    exp_f = lambda c: c[0] in constraint_map and is_excel_constraint(constraint_map[c[0]])
    return calc_ratio(counters, lambda c: c.hits, lambda c: len([x for x in c.constraints if exp_f(x)]), per_file)


def calc_redundancy(counters: List[CategoryCounter], per_file=False):
    count_f = lambda c: len(CategoryCounter.filter_constraints(c.not_present, is_excel_constraint))
    return calc_ratio(counters, count_f, lambda c: c.expected + count_f(c), per_file)


def calc_ratio(counters: List[CategoryCounter], ex_f1, ex_f2, per_file):
    tuples = [(ex_f1(c), ex_f2(c)) for c in counters]
    filtered = [t for t in tuples if t[1] > 0]
    if len(filtered) == 0:
        return 1.0, 0.0, 0.0
    elif per_file:
        return sum(t[0] / t[1] for t in filtered) / len(filtered), len(filtered), len(counters)
    else:
        s1 = sum(x for x, _ in filtered)
        s2 = sum(x for _, x in filtered)
        return s1 / s2, s1, s2


if __name__ == '__main__':
    main()
