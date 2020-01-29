import re
from os import system

import numpy as np

from core.template import Aggregate, Operation
from legacy.group import GType, Orientation
from core.strategy import DictSolvingStrategy
from functools import partial

# use --quiet=1 to get only the optimal model


class AspSolvingStrategy(DictSolvingStrategy):
    def call_clingo(self, tmp_filename, asp_file):
        system(
            "clingo --quiet=1 {tmp_filename} asp/{asp_file} > tmp/asp_output".format(
                tmp_filename=tmp_filename, asp_file=asp_file
            )
        )

    def __init__(self):
        super().__init__()

        def aggregate_columns(aggregate, constraint, assignments, solutions):
            solutions = []
            print("Processing col {aggregate}...".format(aggregate=aggregate))
            for i, xy_dict in enumerate(assignments):
                X = xy_dict["X"]
                Y = xy_dict["Y"]
                #     print(X,Y,i)
                if X.row == False:
                    SAT = self.handle_aggregate_column_data_in_column(
                        X, Y, i, aggregate
                    )
                    if SAT:
                        selected_y, x_positions = SAT
                        #     print("X COLUMN GROUP","SAT","X",X,"X Positions: ",x_positions,"Y",Y,"selected y vector",selected_y, sep="\n")
                        solution = {
                            "X": X.vector_subset(min(x_positions), max(x_positions)),
                            "Y": Y.vector_subset(selected_y, selected_y),
                        }
                        solutions.append(solution)
                else:  # X.row == True
                    SAT = self.handle_aggregate_column_data_in_rows(X, Y, i, aggregate)
                    if SAT:
                        start, end, selected_y = SAT
                        #     print("SAT",start,end,selected_y, X,Y)
                        solution = {
                            "X": X.vector_subset(start, end),
                            "Y": Y.vector_subset(selected_y, selected_y),
                        }
                        solutions.append(solution)
            return solutions

        def aggregate_rows(aggregate, constraint, assignments, solutions):
            print("Processing row {aggregate}...".format(aggregate=aggregate))
            solutions = []
            for i, xy_dict in enumerate(assignments):
                X = xy_dict["X"]
                Y = xy_dict["Y"]
                if X.row == False:
                    SAT = self.handle_aggregate_row_data_in_column(X, Y, i, aggregate)
                    if SAT:
                        start, end, selected_y = SAT
                        solution = {
                            "X": X.vector_subset(start, end),
                            "Y": Y.vector_subset(selected_y, selected_y),
                        }
                        solutions.append(solution)
                else:  # X.row == True
                    SAT = self.handle_aggregate_row_data_in_rows(X, Y, i, aggregate)
                    if SAT:
                        selected_y, x_positions = SAT
                        solution = {
                            "X": X.vector_subset(min(x_positions), max(x_positions)),
                            "Y": Y.vector_subset(selected_y, selected_y),
                        }
                        solutions.append(solution)
            return solutions

        for aggregate in Aggregate.instances():
            if aggregate.operation != Operation.COUNT:
                f = (
                    aggregate_columns
                    if aggregate.orientation == Orientation.VERTICAL
                    else aggregate_rows
                )
                self.add_strategy(
                    aggregate, partial(f, aggregate.operation.name.lower())
                )

    def handle_aggregate_row_data_in_column(self, X, Y, i, aggregate):
        processed = self.agg_data_processing(X, Y, i, "row")
        if processed is None:
            return None
        tmp_filename, test_file, Xdata, Ydata = processed
        rows, cols = Xdata.shape
        print("range(0..{}).".format(rows - 1), file=test_file)
        test_file.close()
        self.call_clingo(
            tmp_filename,
            "/{aggregate}/row_{aggregate}_col_data.asp".format(aggregate=aggregate),
        )
        with open("tmp/asp_output", "r") as output:
            output_str = output.read()
            return self.process_start_end_output(output_str)

    def handle_aggregate_row_data_in_rows(self, X, Y, i, aggregate):
        return self.handle_aggregate_column_data_in_column(
            X, Y, i, aggregate, direction="row"
        )  # symmetric in the ASP representation

    @staticmethod
    def yid(idint):
        return "vy" + str(idint)

    @staticmethod
    def xid(idint):
        return "vx" + str(idint)

    @staticmethod
    def generate_Y_asp(Ydata, idfun, test_file):
        for i, vs in enumerate(Ydata):
            print(
                "rel_Y({pos},{vid}).".format(pos=i, vid=idfun(i)),
                end=" ",
                file=test_file,
            )
            for j, v in enumerate(vs):
                print(
                    "element_Y({vid},{pos},{val}).".format(
                        vid=idfun(i), pos=j, val=int(v)
                    ),
                    end=" ",
                    file=test_file,
                )
            print(" ", file=test_file)

    @staticmethod
    def generate_X_asp(Xdata, idfun, test_file):
        for i, vs in enumerate(Xdata):
            print(
                "rel_X({pos},{vid}).".format(pos=i, vid=idfun(i)),
                end=" ",
                file=test_file,
            )
            for j, v in enumerate(vs):
                print(
                    "element_X({vid},{pos},{val}).".format(
                        vid=idfun(i), pos=j, val=int(v)
                    ),
                    end=" ",
                    file=test_file,
                )
            print(" ", file=test_file)

    @staticmethod
    def scale_data(X, Y, Xdata, Ydata):
        if Y.dtype == GType.float or X.dtype == GType.float:
            X_digits_max = np.max(compute_digits_after_period(Xdata.flatten()))
            Y_digits_max = np.max(compute_digits_after_period(Ydata.flatten()))
            scale = np.power(10, max(X_digits_max, Y_digits_max))
            Ydata = scale * Ydata.astype(np.float32)
            Xdata = scale * Xdata.astype(np.float32)
            Ydata = Ydata.astype(int)
            Xdata = Xdata.astype(int)
            return Xdata, Ydata
        else:
            return Xdata, Ydata

    def agg_data_processing(self, X, Y, i, direction):
        tmp_filename, test_file, Xdata, Ydata = self.preprocess(
            self, X, Y, i, direction
        )
        Xdata, Ydata = self.scale_data(X, Y, Xdata, Ydata)
        if X == Y:  # handle intersection case
            self.generate_Y_asp(Ydata, self.xid, test_file)
        elif (
            X.overlaps_with(Y) and np.array_equal(Xdata.T, Ydata) and X.row != Y.row
        ):  # X is a transpose of Y
            return None
        else:
            self.generate_Y_asp(Ydata, self.yid, test_file)

        #       print("TEST", X.overlaps_with(Y) and X !=Y,X.bounds, Y.bounds, "TABLE",X.table, Y.table, X, Y, np.array_equal(Xdata,Ydata))
        self.generate_X_asp(Xdata, self.xid, test_file)
        return tmp_filename, test_file, Xdata, Ydata

    def handle_aggregate_column_data_in_rows(self, X, Y, i, aggregate):
        processed = self.agg_data_processing(X, Y, i, "col")
        if processed is None:
            return None
        tmp_filename, test_file, Xdata, Ydata = processed
        rows, cols = Xdata.shape
        print("range(0..{}).".format(rows - 1), file=test_file)
        test_file.close()
        # print(tmp_filename)
        self.call_clingo(
            tmp_filename,
            "/{aggregate}/col_{aggregate}_row_data.asp".format(aggregate=aggregate),
        )
        with open("tmp/asp_output", "r") as output:
            output_str = output.read()
            return self.process_start_end_output(output_str)

    @staticmethod
    def preprocess(self, X, Y, i, direction):
        tmp_filename = "tmp/{direction}_asp_tmp{i}.asp".format(i=i, direction=direction)
        # print(tmp_filename)
        test_file = open(tmp_filename, "w")
        Xdata = X.get_group_data()
        Ydata = Y.get_group_data()
        if X.row == False:
            Xdata = Xdata.T
        if Y.row == False:
            Ydata = Ydata.T
        return tmp_filename, test_file, Xdata, Ydata

    def handle_aggregate_column_data_in_column(
        self, X, Y, i, aggregate, direction="col"
    ):
        processed = self.agg_data_processing(X, Y, i, direction)
        if processed is None:
            return None
        tmp_filename, test_file, Xdata, Ydata = processed

        max_shift = X.bounds.columns() - Y.length()
        print("range(0..{max_shift}).".format(max_shift=max_shift), file=test_file)

        test_file.close()
        self.call_clingo(
            tmp_filename,
            "/{aggregate}/col_{aggregate}_col_data.asp".format(aggregate=aggregate),
        )
        with open("tmp/asp_output", "r") as output:
            output_str = output.read()
            return self.process_aggregate_column_in_column_output(output_str)

    @staticmethod
    def process_aggregate_column_in_column_output(output):
        if "UNSATISFIABLE" in output:
            return None
        # print(output)
        shift = re.search(r"shift\((?P<shift>\d+)\)", output)
        shift = int(shift.group("shift"))
        selected_y = (
            int(
                re.search(r"selected_Y\(v[xy](?P<selected>\d+)\)", output).group(
                    "selected"
                )
            )
            + 1
        )  # here it starts from zero, but not in the table representation
        positions = map(
            lambda x: int(x) + 1 + shift,
            re.findall(r"y_vector\((?P<pos>\d+),\d+\)", output),
        )
        x_positions = list(positions)
        return selected_y, x_positions

    @staticmethod
    def process_start_end_output(output):
        if "UNSATISFIABLE" in output:
            return None
        # print(output)
        start = re.search(r"start\((?P<start>\d+)\)", output)
        start = int(start.group("start")) + 1
        end = re.search(r"end\((?P<end>\d+)\)", output)
        end = int(end.group("end")) + 1
        selected_y = (
            int(
                re.search(r"selected_Y\(v[xy](?P<selected>\d+)\)", output).group(
                    "selected"
                )
            )
            + 1
        )
        return start, end, selected_y


def compute_digits_after_period(number):
    str_num = str(number)
    if "." not in str_num:
        return 0
    before, after = str_num.split(".")
    return len(after)


compute_digits_after_period = np.vectorize(compute_digits_after_period)

# return selected_y+1, x_positions
