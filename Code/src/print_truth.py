import argparse
import os

import workflow
from engine.util import local


def main(name):
    csv_file = local("data/csv/{}.csv".format(name))
    if not os.path.isfile(csv_file):
        raise Exception("File not found: {}".format(csv_file))
    groups_file = local("data/groups/{}.txt".format(name))
    if not os.path.isfile(groups_file):
        groups_file = None
    solutions = workflow.main(csv_file, groups_file, False, silent=True)
    for constraint in solutions.solutions:
        sols = solutions.get_solutions(constraint)
        if len(sols) > 0:
            print_solutions(constraint, sols)


def print_solutions(constraint, solutions):
    sols_s = ["{%s}" % ", ".join(["\"%s\": \"%s\"" % (k, str(v)) for k, v in sol.items()]) for sol in solutions]
    print("\t\t\t\"%s\": [%s]," % (constraint.name, ", ".join(sols_s)))


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('name')
    return p


if __name__ == '__main__':
    main(**vars(arg_parser().parse_args()))
