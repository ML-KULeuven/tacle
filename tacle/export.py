import argparse
import json

import workflow
from experiment import is_excel_constraint


def main(csv_file, tables_file):
    solutions = workflow.main(csv_file, tables_file, False, True)
    constraints = {}
    for constraint in solutions.solutions:
        if is_excel_constraint(constraint) and len(solutions.get_solutions(constraint)) > 0:
            constraints[constraint.name] = [{k: str(v) for k, v in sol.items()} for sol in solutions.get_solutions(constraint)]
    print(json.dumps(constraints))


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('csv_file')
    p.add_argument('tables_file')
    return p


if __name__ == '__main__':
    main(**vars(arg_parser().parse_args()))
