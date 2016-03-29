import re
from os import system

import numpy as np

from core.constraint import SumColumn, SumRow
from core.group import GType
from core.strategy import DictSolvingStrategy


class AspSolvingStrategy(DictSolvingStrategy):
    def __init__(self):
        super().__init__()

        def sum_columns(constraint, assignments, solutions):
            solutions = []
            print("Processing col sum...")
            for i,xy_dict in enumerate(assignments):
              X = xy_dict["X"]
              Y = xy_dict["Y"]
              if X.row == False:
                SAT = self.handle_sum_column_data_in_column(X,Y,i)
                if SAT:
                  selected_y, x_positions = SAT
                  print("X COLUMN GROUP","SAT","X",X,"X Positions: ",x_positions,"Y",Y,"selected y vector",selected_y, sep="\n")
                  solution = {"X":X.vector_subset(min(x_positions),max(x_positions)),"Y":Y.get_vector(selected_y)}
                  solutions.append(solution)
              else: #X.row == True
                SAT = self.handle_sum_column_data_in_rows(X,Y,i)
                if SAT:
                  print("X ROW GROUP","SAT","X",X,"Y",Y,sep="\n")
                  solutions.append(solution)

        def sum_rows(constraint, assignments, solutions):
            print("Processing row sum...")
            for i, xy_dict in enumerate(assignments):
                X = xy_dict["X"]
                Y = xy_dict["Y"]
                if X.row == False:
                    SAT = self.handle_sum_row_data_in_column(X, Y, i)
                    if SAT:
                        print("COLUMN DATA SAT")
                        print("X", X, "Y", Y, sep="\n")
                        print("X row", X.row, "Y row", Y.row, sep="\n")
                else:  # X.row == True
                    SAT = self.handle_sum_row_data_in_rows(X, Y, i)
                    if SAT:
                        print("ROW DATA SAT")

        self.add_strategy(SumColumn(), sum_columns)
        self.add_strategy(SumRow(), sum_rows)

    def handle_sum_row_data_in_column(self, X, Y, i):
        tmp_filename, test_file, Xdata, Ydata = self.sum_data_processing(X, Y, i)
        test_file.close()

        system("clingo {tmp_filename} asp/row_sum_col_data.asp 0 > tmp/asp_output".format(tmp_filename=tmp_filename))
        with open("tmp/asp_output", "r") as output:
            output_str = output.read()
            return self.process_sum_row_in_col_output(output_str)

    def handle_sum_row_data_in_rows(self, X, Y, i):
        # TODO SYMMETRIC CASE, NO NEED TO IMPLEMENT
        return False

    def process_sum_row_in_col_output(self, output_str):
        if "UNSATISFIABLE" in output_str:
            return None
        print(output_str)
        return True

    @staticmethod
    def yid(idint):
        return "vy" + str(idint)

    @staticmethod
    def xid(idint):
        return "vx" + str(idint)

    @staticmethod
    def generate_Y_asp(Ydata, idfun, test_file):
        for i, vs in enumerate(Ydata):
            print("rel_Y({pos},{vid}).".format(pos=i, vid=idfun(i)), end=" ", file=test_file)
            for j, v in enumerate(vs):
                print("element_Y({vid},{pos},{val}).".format(vid=idfun(i), pos=j, val=int(v)), end=" ", file=test_file)
            print(" ", file=test_file)

    @staticmethod
    def generate_X_asp(Xdata, idfun, test_file):
        for i, vs in enumerate(Xdata):
            print("rel_X({pos},{vid}).".format(pos=i, vid=idfun(i)), end=" ", file=test_file)
            for j, v in enumerate(vs):
                print("element_X({vid},{pos},{val}).".format(vid=idfun(i), pos=j, val=int(v)), end=" ", file=test_file)
            print(" ", file=test_file)

    @staticmethod
    def scale_data(X, Y, Xdata, Ydata):
        if Y.dtype == GType.float or X.dtype == GType.float:
            Ydata = 100 * Ydata.astype(np.float32)
            Xdata = 100 * Xdata.astype(np.float32)
            Ydata = Ydata.astype(int)
            Xdata = Xdata.astype(int)
            return Xdata, Ydata
        else:
            return Xdata, Ydata

    def sum_data_processing(self, X, Y, i):
        tmp_filename, test_file, Xdata, Ydata = self.preprocess(self, X, Y, i)
        Xdata, Ydata = self.scale_data(X, Y, Xdata, Ydata)
        self.generate_Y_asp(Ydata, self.yid, test_file)
        self.generate_X_asp(Xdata, self.xid, test_file)
        return tmp_filename, test_file, Xdata, Ydata

    def handle_sum_column_data_in_rows(self, X, Y, i):
        tmp_filename, test_file, Xdata, Ydata = self.sum_data_processing(X, Y, i)
        test_file.close()

        system("clingo {tmp_filename} asp/col_sum_row_data.asp 0 > tmp/asp_output".format(tmp_filename=tmp_filename))
        with open("tmp/asp_output", "r") as output:
            output_str = output.read()
            return self.process_sum_column_in_row_output(output_str)
            # return self.process_sum_column_in_column_output(output_str)

    @staticmethod
    def preprocess(self, X, Y, i):
        tmp_filename = "tmp/asp_tmp{i}.asp".format(i=i)
        # print(tmp_filename)
        test_file = open(tmp_filename, "w")
        Xdata = X.get_group_data()
        Ydata = Y.get_group_data()
        if X.row == False:
            Xdata = Xdata.T
        if Y.row == False:
            Ydata = Ydata.T
        return tmp_filename, test_file, Xdata, Ydata

    def handle_sum_column_data_in_column(self, X, Y, i):
        tmp_filename, test_file, Xdata, Ydata = self.sum_data_processing(X, Y, i)

        max_shift = X.bounds.columns() - Y.length()
        print("range(0..{max_shift}).".format(max_shift=max_shift), file=test_file)

        test_file.close()

        system("clingo {tmp_filename} asp/check_sum.asp 0 > tmp/asp_output".format(tmp_filename=tmp_filename))
        with open("tmp/asp_output", "r") as output:
            output_str = output.read()
            return self.process_sum_column_in_column_output(output_str)

    @staticmethod
    def process_sum_column_in_column_output(output):
        if "UNSATISFIABLE" in output:
            return None
        shift = re.search(r'shift\((?P<shift>\d+)\)', output)
        shift = int(shift.group("shift"))
        selected_y = int(re.search(r"selected_Y\(vy(?P<selected>\d+)\)", output).group("selected"))
        print("selected", selected_y)
        print("shift", shift)
        positions = map(lambda x: int(x) + 1 + shift, re.findall(r"y_vector\((?P<pos>\d+),\d+\)", output))
        x_positions = list(positions)
        return selected_y + 1, x_positions

    @staticmethod
    def process_sum_column_in_row_output(output):
        if "UNSATISFIABLE" in output:
            return None
            # shift = re.search(r'shift\((?P<shift>\d+)\)', output)
            # shift = int(shift.group("shift"))
            # selected_y =  int(re.search(r"selected_Y\(vy(?P<selected>\d+)\)",output).group("selected"))
            # print("selected",selected_y)
            # print("shift",shift)
            # positions   = map(lambda x: int(x)+1+shift, re.findall(r"y_vector\((?P<pos>\d+),\d+\)",output))
            # x_positions = list(positions)
        print(output)
        return True
# return selected_y+1, x_positions
