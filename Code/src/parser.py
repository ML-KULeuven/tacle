import json
import numpy as np
import pandas as pd

from group import Bounds, Table, Group


def parse(filename):
    with open(filename, "r") as file:
        data = np.array(pd.read_csv(file, header=None))
        return data


def get_groups_tables(csv_file, groups_file):
    data = parse(csv_file)
    tables = {}
    groups = []
    with open(groups_file, "r") as group_file:
        json_data = json.load(group_file)
        for table_description in json_data["Tables"]:
            bounds = Bounds(table_description["Bounds"])
            data_subset = bounds.subset(data)
            name = table_description["Name"]
            tables[name] = Table(name, data_subset, bounds.rows(), bounds.columns())
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
