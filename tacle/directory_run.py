""""
Run through all .csv file in the folder
INPUT: directory, min_rows, min_cols

If no "AttributeError" during runtime
    place into directory/Accept folder
    place header files in directory/header folder
Else
    place into directory/TacleRejected folder
"""

import glob
import os
import shutil
import argparse
import logging
from collections import OrderedDict

from tacle.indexing import Orientation
from tacle import learn_from_file, filter_constraints, tables_from_csv, save_json_file

logger = logging.getLogger(__name__)


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


def main(directory, min_rows=None, min_columns=None, semantic=True):
    os.chdir(directory)
    for csv_file in glob.glob("*.csv"):
        print(csv_file)
        tables = tables_from_csv(csv_file, min_rows=min_rows, min_columns=min_columns)

        """"
        #Print Table
        for table in tables:
            print("Table {}, {} \n".format(table.name, table.range))
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
        

        logger.info(
            "\n".join(
                "{}: {}".format(table, ", ".join(map(str, table.blocks)))
                for table in tables
            )
        )
        """
        try:
            constraints = learn_from_file(
                csv_file,
                virtual=None,
                solve_timeout=None,
                tables=tables,
                semantic=semantic,
            )
        except AttributeError:
            print(AttributeError)
            continue
            current = directory + "/" + csv_file
            destination = directory + "/projection_reject/" + csv_file
            shutil.move(current, destination)
            continue
        except ValueError:
            print(ValueError)
            continue
            current = directory + "/" + csv_file
            destination = directory + "/any_reject/" + csv_file
            shutil.move(current, destination)
            continue

        text_dict = DefaultListOrderedDict()
        save_json_file(constraints, text_dict, csv_file)
        print(*list(map(str, constraints)), sep="\n")


        """Move file one directory to other"""
        """
        current = directory + "/" + csv_file
        destination = directory + "/Accept/" + csv_file
        shutil.move(current, destination)
        """




def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    p.add_argument("--min_rows", type=int)
    p.add_argument("--min_columns", type=int)
    return p


if __name__ == '__main__':
    main(**vars(arg_parser().parse_args()))
