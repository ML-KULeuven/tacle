import json
import random
import string
from collections import OrderedDict

import numpy as np
import time

import workflow
import os
import itertools

from core.template import Rank, Aggregate
from core.group import GType
from runtime_rendering import ScatterData


class TableSpec:
    def __init__(self, rows):
        self.rows = rows  # int
        self.block_types = list()  # [(size, b_type)]

    @property
    def cols(self):
        return sum(size for size, _ in self.block_types)

    def __hash__(self):
        return hash((self.rows, tuple(self.block_types)))

    def __eq__(self, other):
        if not isinstance(other, TableSpec):
            return False
        return self.rows == other.rows and self.block_types == other.block_types

    def __repr__(self):
        return "rows: {}, blocks: {}".format(self.rows, self.block_types)

    @property
    def name(self):
        assert(all(b == self.block_types[0] for b in self.block_types))
        size, b_type = self.block_types[0]
        type_name = "i" if b_type == GType.int else "s"
        return "r{}-{}{}x{}".format(self.rows, type_name, len(self.block_types), size)

    def add_block(self, size, b_type):
        self.block_types.append((size, b_type))
        return self

    @staticmethod
    def parse(input_string):
        _, row_string, blocks_string = input_string.split("-")
        rows = int(row_string[1:])
        type_string = blocks_string[0]
        if type_string == "i":
            b_type = GType.int
        elif type_string == "s":
            b_type = GType.string
        else:
            raise RuntimeError("Unexpected type: {}".format(type_string))
        block_count, block_size = (int(s) for s in blocks_string[1:].split("x"))
        table = TableSpec(rows)
        for _ in range(block_count):
            table.add_block(block_size, b_type)
        return table


class SpeedTestId:
    def __init__(self, tables):
        self.tables = tables

    def __hash__(self, *args, **kwargs):
        return hash(tuple(self.tables))

    def __eq__(self, other):
        if not isinstance(other, SpeedTestId):
            return False
        return self.tables == other.tables

    def __repr__(self):
        return "tables: {}".format(self.tables)

    @property
    def name(self):
        return "_".join("T-{}".format(table.name) for table in self.tables)

    @staticmethod
    def parse(input_string):
        table_parts = input_string.split("_")
        return SpeedTestId(list(TableSpec.parse(table_part) for table_part in table_parts))


def get_constraints():
    from core.learning import ordered_constraints
    return ordered_constraints(workflow.get_constraint_list())


def generate_random(test_id: SpeedTestId):
    column_data = list()

    max_rows = 0
    for table in test_id.tables:
        for size, b_type in table.block_types:
            for _ in range(size):
                max_rows = max(max_rows, table.rows)
                if b_type == GType.int:
                    column_data.append(np.random.randint(1, 1000, table.rows))
                elif b_type == GType.string:
                    letter = lambda: random.choice(string.ascii_lowercase)
                    word = lambda: ''.join(letter() for _ in range(np.random.randint(5, 15)))
                    column_data.append([word() for _ in range(table.rows)])
                else:
                    raise RuntimeError("Unexpected column type {}".format(b_type))

    to_print = list()
    for i in range(max_rows):
        row = list(str(column_data[col][i]) if len(column_data[col]) > i else "" for col in range(len(column_data)))
        to_print.append(row)
    return to_print


def generate_file(path, data_function, test_id: SpeedTestId, prefix):
    name = "{}_{}".format(prefix, test_id.name)
    csv_path = os.path.join(path, "{}.csv".format(name))
    blocks_path = os.path.join(path, "{}.txt".format(name))
    with open(csv_path, "w") as file:
        data = data_function(test_id)
        print("\n".join(",".join(row) for row in data), file=file)
        file.close()
    with open(blocks_path, "w") as file:
        print(json.dumps(generate_blocks(test_id)), file=file)
        file.close()
    return csv_path, blocks_path


def generate_blocks(test_id: SpeedTestId):
    content = dict()
    # Generate tables
    tables = []
    index = 1
    for i, table in enumerate(test_id.tables):
        bounds = [1, table.rows, index, index + table.cols - 1]
        index += table.cols
        tables.append({"Name": "T{}".format(i + 1), "Bounds": bounds, "Orientation": "Column"})
    content["Tables"] = tables

    # Generate groups
    blocks = []
    for i, table in enumerate(test_id.tables):
        index = 1
        for size, _ in table.block_types:
            blocks.append({"Table": "T{}".format(i + 1), "Bounds": [":", index, index + size - 1]})
            index += size
    content["Groups"] = blocks
    return content


def clear_folder(path):
    folder = path
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def generate_experiments():
    # Configuration
    gtype = GType.int
    min_power = 1
    default = 2 ** 3
    block_power = 5
    number_power = 6
    size_power = 12
    min_table = 2

    increment = lambda p_min, p_max: list(2 ** p for p in range(p_min, p_max + 1))

    # Vary number of vectors
    cat_1 = []
    for cols in increment(min_power, number_power):
        rows = default
        tables = [TableSpec(rows).add_block(cols, gtype), TableSpec(rows).add_block(min_table, gtype)]
        test_id = SpeedTestId(tables)
        cat_1.append(test_id)

    # Vary vector size
    cat_2 = []
    for rows in increment(min_power, size_power):
        cols = default
        tables = [TableSpec(rows).add_block(cols, gtype), TableSpec(rows).add_block(min_table, gtype)]
        cat_2.append(SpeedTestId(tables))

    # Vary block sizes
    cat_3 = []
    vectors = 2 ** block_power
    for block_size in reversed(increment(0, block_power)):
        if block_size <= vectors:
            rows = default
            table = TableSpec(rows)
            for _ in range(int(vectors / block_size)):
                table.add_block(block_size, gtype)
            cat_3.append(SpeedTestId([table, TableSpec(rows).add_block(min_table, gtype)]))

    return {"cat1": cat_1, "cat2": cat_2, "cat3": cat_3}


def setup_experiments(experiments):
    path = "../data/speed_tests"
    clear_folder(path)

    paths = dict()
    for test_id in experiments:
        paths[test_id] = generate_file(path, generate_random, test_id, "random")
    return paths


def tasks_to_table(categories, tasks):
    tables = OrderedDict()
    for c_name, category in categories.items():
        table = OrderedDict()
        for test_id in category:
            results = tasks[test_id]
            numbers = OrderedDict()
            numbers["total"] = list(task.total_time() for task in results)
            for c in results[0].constraints:
                numbers[c] = list(task.time(c) for task in results)
            table[test_id] = numbers
        tables[c_name] = table
    return tables


def runs_to_table(categories, runs):
    tables = OrderedDict()
    for c_name, category in categories.items():
        table = OrderedDict()
        for test_id in category:
            results = runs[test_id]
            series = OrderedDict()
            series["total"] = results[0]
            for c, values in zip(get_constraints(), results[1:]):
                series[c] = values
            table[test_id] = series
        tables[c_name] = table
    return tables


def import_log_file(log_file):
    runs = dict()
    with open(log_file, "r") as file:
        for line in file:
            if line[0:3] != "Run":
                line = line.rstrip("\n")
                run, name, *rest = line.split("\t")
                test_id = SpeedTestId.parse(name)
                if int(run) == 0:
                    runs[test_id] = [[] for _ in range(len(rest))]
                for i, value in enumerate(rest):
                    runs[test_id][i].append(float(value))
    return runs


def print_tables(tables):
    for c_name, table in tables.items():
        print(c_name)
        print("Test", "Total", *get_constraints(), sep="\t")
        for test_id in table:
            row = [test_id.name]
            for times in table[test_id].values():
                row.append("{avg:.3f}".format(avg=np.average(times), std=np.std(times)))
            print(*row, sep="\t")
        print()


def draw_figures(tables):
    scatters = []

    if "cat1" in tables:
        table = tables["cat1"]
        scatter_1 = ScatterData("(a) Number of vectors", list(test_id.tables[0].cols for test_id in table))
        scatter_1.add_data("All constraints", list(np.average(series["total"]) for series in table.values()))
        scatter_1.x_lim((10**0, 10**2))
        scatter_1.y_lim((10**-2, 10**2))
        scatters.append(scatter_1)

    if "cat2" in tables:
        table = tables["cat2"]
        scatter_2 = ScatterData("(b) Vector size", list(test_id.tables[0].rows for test_id in table))
        total_run_times = list(np.average(series["total"]) for series in table.values())
        rank_run_times = list(np.average(series[Rank()]) for series in table.values())
        no_rank_run_times = list(total - rank for total, rank in zip(total_run_times, rank_run_times))
        scatter_2.add_data("All constraints", total_run_times)
        scatter_2.add_data("Without RANK", no_rank_run_times)
        scatter_2.x_lim((10**0, 10**4))
        scatter_2.y_lim((10**-2, 10**2))
        scatters.append(scatter_2)

    if "cat3" in tables:
        table = tables["cat3"]

        number_of_blocks = list(len(test_id.tables[0].block_types) for test_id in table)
        scatter_3 = ScatterData("(c) Number of blocks (aggregates)", number_of_blocks)
        total_times = list(np.average(series["total"]) for series in table.values())
        aggregates = list(sum(np.average(series[c]) for c in Aggregate.instances()) for series in table.values())
        non_aggregates = list(total - aggregate for total, aggregate in zip(total_times, aggregates))
        scatter_3.add_data("All constraints", total_times)
        scatter_3.add_data("Aggregate constraints", aggregates)
        scatter_3.add_data("Non-aggregate constraints", non_aggregates)
        scatter_3.x_lim((10**0, 10**2))
        scatter_3.y_lim((10**-2, 10**2))
        scatters.append(scatter_3)

    from runtime_rendering import plot
    path = "../experiments"
    plot(os.path.join(path, "scatter_plots.pdf"), *scatters)


def get_tables(categories, import_file=None, runs=1):
    path = "../experiments"
    if import_file is None:
        experiments = set(itertools.chain(*categories.values()))
        tasks = {test_id: [] for test_id in experiments}
        log_file_path = os.path.join(path, "{}.log".format(time.strftime("%Y%m%d_%H%M%S")))

        with open(log_file_path, "w") as log_file:
            for run in range(runs):
                paths = setup_experiments(experiments)
                for test_id, (csv_path, blocks_path) in paths.items():
                    task = workflow.task(csv_path, blocks_path)
                    task.run()
                    tasks[test_id].append(task)
                    constraint_times = [task.time(c) for c in task.constraints]
                    print(run, test_id.name, task.total_time())
                    print("Run", "Name", "Total time", *[str(c) for c in task.constraints], file=log_file, sep="\t")
                    print(run, test_id.name, task.total_time(), *constraint_times, file=log_file, sep="\t")
            log_file.close()

        print("Log file", log_file_path)
        tables = tasks_to_table(categories, tasks)
    else:
        log_file_path = os.path.join(path, import_file)
        tables = runs_to_table(categories, import_log_file(log_file_path))
    return tables


def main():
    # ID: cols, rows, blocks, int | str | float
    import_file = "20160925_195326.log"
    tables = get_tables(generate_experiments(), import_file=import_file)  # import_file="20160914_141603.log")
    print_tables(tables)
    draw_figures(tables)


if __name__ == "__main__":
    main()
