""""
Run through all .csv file in the directory given by user
INPUT: directory, min_rows(optional), min_cols(optional)

If no "AttributeError" during runtime
    place into directory/Accept folder
    place header files in directory/header folder
Else
    place into directory/TacleRejected folder
"""
# TODO adopt when truth file not exists
import glob
import json
import os
import shutil
import argparse
import logging
import time
import numpy
from collections import OrderedDict

from tacle.indexing import Orientation
from tacle import learn_from_file, filter_constraints, tables_from_csv, save_json_file

logger = logging.getLogger(__name__)


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


def main(directory, semantic=True, min_rows=None, min_columns=None, min_cells=None, orientation=None):
    time_per_file = []
    ctime = 0
    count_file = 0

    os.chdir(directory)
    for csv_file in glob.glob("*.csv"):
        start_time = time.time()
        count_file += 1
        if len(time_per_file) < count_file:
            time_per_file.append({'file': csv_file, 'time': 0})
        print(csv_file)

        json_file = (os.path.basename(csv_file.rstrip(os.sep)).split("."))[-2]

        truth_location = directory+"/truth/"

        with open(truth_location + json_file + '.json') as f:
            data = json.load(f)
            settings = data['settings']

            if not min_rows:
                min_rows = None if settings[0]['min_rows'] == 'null' else settings[0]['min_rows']
            if not min_columns:
                min_columns = None if settings[0]['min_columns'] == 'null' else settings[0]['min_columns']
            if not min_cells:
                min_cells = None if settings[0]['min_cells'] == 'null' else settings[0]['min_cells']
            if not orientation:
                orientation = None if settings[0]['orientation'] == 'null' else settings[0]['orientation']

        tables = tables_from_csv(csv_file,
                                 min_rows=min_rows,
                                 min_columns=min_columns,
                                 min_cells=min_cells,
                                 orientation=orientation)

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
            raise AttributeError("Attribute isn't right")
            continue
            current = directory + "/" + csv_file
            destination = directory + "/projection_reject/" + csv_file
            shutil.move(current, destination)
            continue
        except ValueError:
            raise ValueError("Value isn't right")
            continue
            current = directory + "/" + csv_file
            destination = directory + "/any_reject/" + csv_file
            shutil.move(current, destination)
            continue

        text_dict = DefaultListOrderedDict()
        save_json_file(constraints, text_dict, csv_file)
        print(*list(map(str, constraints)), sep="\n")

        end_time = time.time()
        ctime += (end_time - start_time)
        file_execution_time = (end_time - start_time)
        time_per_file[count_file-1]['time'] += file_execution_time

        """Move file one directory to other"""
        """
        current = directory + "/" + csv_file
        destination = directory + "/Accept/" + csv_file
        shutil.move(current, destination)
        """
    print(f"Average time {ctime / count_file}")
    # print(time_per_file)

    return time_per_file


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('directory', help="Directory to run TaCLe")
    p.add_argument(
        "-s", "--semantic", help="Run in semantic mode", action="store_true"
    )
    p.add_argument("--min_rows", type=int)
    p.add_argument("--min_columns", type=int)
    return p


if __name__ == '__main__':
    open('word_dump.txt', 'w').close()  # clear and create new word_dump.txt file

    #file run multiple time and record time
    n = 10
    file_time = []
    dictionary = dict()
    for i in range(n):
        dictionary = main(**vars(arg_parser().parse_args()))
        returned_file_time = [file['time'] for file in dictionary]
        if len(file_time) != len(returned_file_time):
            file_time = numpy.array(returned_file_time)
        else:
            file_time += numpy.array(returned_file_time)

    file_average_time = file_time / n
    for index, file in enumerate(dictionary):
        file['time'] = file_average_time[index]

    print(dictionary)

    # main(**vars(arg_parser().parse_args()))  # run through the whole directory of data


    """
    average = 0
    for i in range(10):
        ex_time = main(**vars(arg_parser().parse_args()))
        average += ex_time

    print(f"The average time for 10 run: {average/10}")
    """
