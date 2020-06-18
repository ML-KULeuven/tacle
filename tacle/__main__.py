import argparse
import logging

from .indexing import Orientation
from tacle import learn_from_csv, filter_constraints, tables_from_csv

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("csv_file", help="CSV file to learn constraints from")
    parser.add_argument(
        "-f",
        "--filter",
        nargs="+",
        type=str,
        help='Specify which constraint templates are allowed, e.g. "sum (row)", "sum*",'
        "<formula> or <f> for all formulas"
        "and <constraint> or <c> for all constraints",
    )
    parser.add_argument(
        "-g", "--group", help="Group constraints by type", action="store_true"
    )
    parser.add_argument(
        "-v", "--verbose", help="Increase the verbosity level", action="store_true"
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Increase the verbosity level to debug-level",
        action="store_true",
    )
    parser.add_argument("--virtual", help="Add virtual blocks", action="store_true")
    parser.add_argument(
        "-t", "--tables_only", help="Show only tables", action="store_true"
    )
    parser.add_argument(
        "-o", "--orientation", type=str, help="Show only tables", default=None
    )
    parser.add_argument(
        "--solve_timeout",
        type=float,
        help="Timeout for solving per constraint",
        default=None,
    )
    parser.add_argument(
        "--min_cells", type=int, help="Minimum number of cells per table", default=None
    )
    parser.add_argument(
        "--min_rows", type=int, help="Minimum number of rows per table", default=None
    )
    parser.add_argument(
        "--min_columns",
        type=int,
        help="Minimum number of columns per table",
        default=None,
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    tables = tables_from_csv(
        args.csv_file, args.orientation, args.min_cells, args.min_rows, args.min_columns
    )

    if args.verbose or args.debug or args.tables_only:
        for table in tables:
            print("Table {}, {}".format(table.name, table.range))
            for orientation in table.orientations:
                print(
                    ", ".join(
                        "{} {}-{} ({})".format(
                            "Columns"
                            if orientation == Orientation.vertical
                            else "Rows",
                            block.relative_range.vector_index(orientation),
                            block.relative_range.vector_index(orientation)
                            + block.relative_range.vector_count(orientation),
                            block.type,
                        )
                        for block in table.blocks
                        if block.orientation == orientation
                    )
                )
            print()

    if not args.tables_only:
        logger.info(
            "\n".join(
                "{}: {}".format(table, ", ".join(map(str, table.blocks)))
                for table in tables
            )
        )
        constraints = learn_from_csv(
            args.csv_file,
            virtual=args.virtual,
            solve_timeout=args.solve_timeout,
            tables=tables,
        )

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
