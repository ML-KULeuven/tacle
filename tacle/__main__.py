import argparse
import logging
from tacle import learn_from_csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("csv_file", help="CSV file to learn constraints from")
    parser.add_argument("-v", "--verbose", help="Increase the verbosity level", action="store_true")
    parser.add_argument("-d", "--debug", help="Increase the verbosity level to debug-level", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    constraints = learn_from_csv(args.csv_file)
    print(*list(map(str, constraints)), sep="\n")
