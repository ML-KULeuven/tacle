import os
from typing import Union

from pandas import json

import print_truth
import workflow
from core.constraint import *
from engine.util import local

files = ["bmi", "age_department_sumif", "average_ablebits", "columnwise-sum-rows", "examples", "expenses",
         "external_revenue", "fbi_offenses",
         "financial_result", "fruits", "help_lookup", "household", "inventory", "multsum",
         "paper_supply", "price_weight", "repair", "rides", "sales_blanks", "school", "score",
         "shares", "sum_if_double_condition", "sum_table_from_guide", "sumif_blanks", "sumif_example",
         "sumif_games_toys", "sumif_region", "sumif_uk", "sumproduct", "week_2_busn_store_2"]


def is_excel_constraint(c: Constraint):
    return isinstance(c, Aggregate) or isinstance(c, ConditionalAggregate) or isinstance(c, Series) \
        or isinstance(c, Rank) or isinstance(c, Lookup) or isinstance(c, FuzzyLookup) or isinstance(c, RunningTotal) \
        or isinstance(c, Product) or isinstance(c, SumProduct) or isinstance(c, ForeignProduct) or isinstance(c, Equal)


constraint_map = {c.name: c for c in workflow.constraint_list}


def print_constraints(prefix, constraints):
    if len(constraints) > 0:
        print()
        for cons_name, sol in constraints:
            print("\t{prefix}:\t{constraint}: {solution}".format(prefix=prefix, constraint=cons_name, solution=sol))


def main():
    categories = {"essential constraints": "Essential"}
    cat_counters = {n: [] for n in categories}
    for name in files:
        print(name)
        csv_file = local("data/csv/{}.csv".format(name))
        if not os.path.isfile(csv_file):
            raise Exception("File not found: {}".format(csv_file))
        groups_file = local("data/groups/{}.txt".format(name))
        silent = True
        if not os.path.isfile(groups_file):
            with open(groups_file, "w+") as f:
                print("{\n\t\"Tables\":\n\t\t[\n\n\t\t]\n}", file=f, flush=True)
            groups_file = None
            silent = False
        solutions = workflow.main(csv_file, groups_file, False, silent=True, parse_silent=silent)
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
                    total, hits, expected = calc_accuracy(c, per_file=False)
                    print("\tAccuracy for {}: {:.2%} ({} of {})".format(c_name, total, hits, expected))
                    ratio, r, expected = calc_redundancy(c, per_file=False)
                    print("\tRedundancy {}: {:.2%} ({} over {})".format(c_name, ratio, r, expected))

                    print_constraints("MISSING", c.not_found)
                    redundant = CategoryCounter.filter_constraints(c.not_present, is_excel_constraint)
                    print_constraints("REDUNDANT", redundant)
            print()
        elif groups_file is not None:
            with open(truth_file, "w+") as f:
                print("{\n\t\"Essential\":\n\t\t{\n\n\t\t}\n}", file=f, flush=True)
                print_truth.main(name)
    for n in categories:
        per_file, not_zero, file_count = calc_accuracy(cat_counters[n], per_file=True)
        total, hits, expected = calc_accuracy(cat_counters[n], per_file=False)
        print("{} accuracy per file ({} of {} files): {:.2%}".format(n.capitalize(), not_zero, file_count, per_file))
        print("Total {} accuracy: {:.2%} ({} of {})".format(n, total, hits, expected))

        per_file, not_zero, file_count = calc_redundancy(cat_counters[n], per_file=True)
        ratio, r, expected = calc_redundancy(cat_counters[n], per_file=False)
        print("{} redundancy per file ({} of {} files): {:.2%}".format(n.capitalize(), not_zero, file_count, per_file))
        print("Redundancy {}: {:.2%} ({} over {})".format(n, ratio, r, expected))


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

    def count(self, constraint: Constraint, solution):
        s_strings = frozenset({name: str(group) for name, group in solution.items()}.items())
        if (constraint.name, s_strings) in self._constraints:
            self._present += 1
            self._not_found.remove((constraint.name, s_strings))
        else:
            self._not_present.add((constraint.name, s_strings))

    @staticmethod
    def filter_constraints(constraints, test_f):
        return list(c for c in constraints if test_f(constraint_map[c[0]]))


def calc_accuracy(counters: Union[List[CategoryCounter], CategoryCounter], per_file=False):
    if isinstance(counters, CategoryCounter):
        counters = [counters]
    filtered = [(counter.hits, counter.expected) for counter in counters if counter.expected > 0]
    if len(filtered) == 0:
        return 1.0, 0.0, 0.0
    elif per_file:
        return sum(hits / exp for hits, exp in filtered) / len(filtered), len(filtered), len(counters)
    else:
        hits = sum(hits for hits, _ in filtered)
        expected = sum(exp for _, exp in filtered)
        return hits / expected, hits, expected


def calc_redundancy(counters: Union[List[CategoryCounter], CategoryCounter], per_file=False):
    if isinstance(counters, CategoryCounter):
        counters = [counters]
    filtered = [(len(CategoryCounter.filter_constraints(counter.not_present, is_excel_constraint)), counter.expected)
                for counter in counters if counter.expected > 0]
    if len(filtered) == 0:
        return 1.0, 0.0, 0.0
    elif per_file:
        return sum(r / (exp + r) for r, exp in filtered) / len(filtered), len(filtered), len(counters)
    else:
        r = sum(r for r, _ in filtered)
        expected = sum(exp for _, exp in filtered)
        return r / (expected + r), r, expected

if __name__ == '__main__':
    main()
