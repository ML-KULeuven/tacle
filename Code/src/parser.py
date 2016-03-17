import json
import numpy as np
import pandas as pd
from enum import Enum


class Parser:
        def __init__(self):
                pass

        def parse(self, filename):
                with open(filename, "r") as file:
                        data = np.array(pd.read_csv(file))
                        return data


class Bounds:
        def __init__(self, bounds_list):
                self.bounds = bounds_list

        def subset(self, data):
                top_row = self.bounds[0] - 1
                bottom_row = self.bounds[1]
                left_column = self.bounds[2] - 1
                right_column = self.bounds[3]
                return data[top_row:bottom_row, left_column:right_column]

        def rows(self):
                return self.bounds[1] - self.bounds[0] + 1

        def columns(self):
                return self.bounds[3] - self.bounds[2] + 1

        def __repr__(self):
                return str(self.bounds)


class Table:
        def __init__(self, data, rows, columns):
                self.data = data
                self.rows = rows
                self.columns = columns

        def __repr__(self):
                repr_str = "Data: " + str(self.data) + " Rows: " + str(self.rows) + " Column: " + str(self.columns)
                return repr_str

class GType(Enum):
    int    = 0
    float  = 1
    string = 2

class Group:

        def __init__(self, table, bounds, row):
                self.table  = table
                self.bounds = bounds
                self.row    = row
                self.data   = self._get_group_data()
                self.dtype  = self.infer_type()

        def __repr__(self):
                repr_str = "Table: " + str(self.table) + " Bounds: " + str(self.bounds) + " Row: " + str(self.row)
                return repr_str

        def _get_group_data(self):
                data = self.table.data
                bounds = self.bounds
                return bounds.subset(data)

        def get_group_data(self):
                return self.data
        
        @staticmethod
        def _infer_type_scalar(val):
            try:
                val = int(val)
                return 0
            except:
                try:
                    val = float(val)
                    return 1
                except:
                    return 2

        def infer_type(self):
            flat = self.data.flatten()
            dtype = max(list(map(self._infer_type_scalar,flat)))
            if dtype == 0:
                return GType.int
            if dtype == 1:
                return GType.float
            else:
                return GType.string




def get_groups_tables(csv_file, groups_file):
        parser = Parser()
        data = parser.parse(csv_file)
        tables = {}
        groups = []
        with open(groups_file, "r") as group_file:
                json_data = json.load(group_file)
                for table_description in json_data["Tables"]:
                        bounds = Bounds(table_description["Bounds"])
                        data_subset = bounds.subset(data)
                        tables[table_description["Name"]] = Table(data_subset, bounds.rows(), bounds.columns())
                for group_description in json_data["Groups"]:
                        table = tables[group_description["Table"]]
                        groups.append(create_group(group_description["Bounds"], table))
        return groups


def create_group(bounds_list, table):
        if bounds_list[0] == ":":
                return Group(table, Bounds([1, table.rows] + bounds_list[1:3]), False)
        elif bounds_list[2] == ":":
                return Group(table, Bounds(bounds_list[0:2] + [1, table.columns]), True)
        else:
                raise Exception("Could not create group")


def arg_parser():
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument('csv_file')
        p.add_argument('groups_file')
        return p


if __name__ == '__main__':
        get_groups_tables(**vars(arg_parser().parse_args()))
