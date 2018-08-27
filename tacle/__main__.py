import argparse
import logging

from tacle import learn_from_csv, filter_constraints, tables_from_csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("csv_file", help="CSV file to learn constraints from")
    parser.add_argument("-f", "--filter", nargs='+', type=str,
                        help="Specify which constraint templates are allowed, e.g. \"sum (row)\", \"sum*\","
                             "<formula> or <f> for all formulas"
                             "and <constraint> or <c> for all constraints")
    parser.add_argument("-g", "--group", help="Group constraints by type", action="store_true")
    parser.add_argument("-v", "--verbose", help="Increase the verbosity level", action="store_true")
    parser.add_argument("-d", "--debug", help="Increase the verbosity level to debug-level", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    constraints = learn_from_csv(args.csv_file)
    tables = tables_from_csv(args.csv_file)
    if args.filter is not None:
        constraints = filter_constraints(constraints, *args.filter)
    if args.group:
        groups = dict()
        for constraint in constraints:
            if constraint.template.name not in groups:
                groups[constraint.template.name] = []
            groups[constraint.template.name].append(constraint)
        for name in sorted(groups.keys()):
            print(name, *list(map(str, groups[name])), sep="\n\t")
    else:
        print(*list(map(str, constraints)), sep="\n")
