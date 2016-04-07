import argparse
import os

from pandas import json

import print_truth
import workflow
from core.constraint import Constraint
from engine.util import local

files = ["bmi", "age_department_sumif", "average_ablebits", "columnwise-sum-rows", "examples", "expenses",
         "external_revenue", "fbi_offenses",
         "financial_result", "fruits", "help_lookup", "household", "inventory", "multsum",
         "paper_supply", "price_weight", "repair", "rides", "sales_blanks", "school", "score",
         "shares", "sum_if_double_condition", "sum_table_from_guide", "sumif_blanks", "sumif_example",
         "sumif_games_toys", "sumif_region", "sumif_uk", "sumproduct", "week_2_busn_store_2"]


def main():
    categories = {"essential constraints": "Essential"}
    accuracies = {n: [] for n in categories}
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
                    accuracies[c_name].append(c.present_count())
                    print("\tAccuracy for {}: {:.2%} ({} of {})".format(c_name, c.accuracy(), *c.present_count()))
                    if len(c.not_found) > 0:
                        print()
                        print("\tMissing:")
                        for cons_name, sol in c.not_found:
                            print("\t\t%s: %s" % (cons_name, sol))
            print()
        elif groups_file is not None:
            with open(truth_file, "w+") as f:
                print("{\n\t\"Essential\":\n\t\t{\n\n\t\t}\n}", file=f, flush=True)
                print_truth.main(name)
    for n, accuracy in accuracies.items():
        accuracy_t = [(p, c) for p, c in accuracy if c > 0]
        present = sum([t[0] for t in accuracy_t])
        count = sum([t[1] for t in accuracy_t])

        not_zero = len(accuracy_t)
        if not_zero > 0:
            per_file = sum([p / c for p, c in accuracy_t]) / not_zero
            total = present / count
        else:
            per_file = 1
            total = 1
        print("{} accuracy per file ({} of {} files): {:.2%}".format(n.capitalize(), not_zero, len(accuracy), per_file))
        print("Total {} accuracy: {:.2%} ({} of {})".format(n, total, present, count))


class CategoryCounter:
    def __init__(self, constraint_json):
        self._constraints = constraint_json
        self._not_found = []
        self._not_present = []
        self._count = 0
        for constraint in constraint_json:
            self._count += len(constraint_json[constraint])
            for solution in constraint_json[constraint]:
                self._not_found.append((constraint, solution))
        self._present = 0

    @property
    def not_found(self):
        return self._not_found

    @property
    def not_present(self):
        return self._not_present

    def count(self, constraint: Constraint, solution):
        s_strings = {name: str(group) for name, group in solution.items()}
        if constraint.name in self._constraints and s_strings in self._constraints[constraint.name]:
            self._present += 1
            self._not_found.remove((constraint.name, s_strings))
        else:
            self._not_present.append((constraint.name, s_strings))

    def accuracy(self):
        return (self._present / self._count) if self._count > 0 else 1

    def present_count(self):
        return self._present, self._count

if __name__ == '__main__':
    main()
