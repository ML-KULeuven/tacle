import json
import random
import string
import numpy as np
import time

import workflow
import os
import itertools

from core.group import GType


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


def generate_random(test_id: SpeedTestId):
    column_data = list()

    max_rows = 0
    for table in test_id.tables:
        for size, b_type in table.block_types:
            for _ in range(size):
                max_rows = max(max_rows, table.rows)
                if b_type == GType.int:
                    column_data.append(np.random.randint(1, 100, table.rows))
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
    for i, table in enumerate(test_id.tables):
        bounds = [1, table.rows, table.cols * i + 1, table.cols * (i + 1)]
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

    return [cat_3]


def setup_experiments(experiments):
    path = "../data/speed_tests"
    clear_folder(path)

    paths = dict()
    for test_id in experiments:
        paths[test_id] = generate_file(path, generate_random, test_id, "random")
    return paths


def print_table(categories, tasks):
    print()
    print("Test", "Total", *[c for c in tasks[categories[0][0]][0].constraints], sep="\t")
    for category in categories:
        for test_id in category:
            row = [test_id.name]
            results = tasks[test_id]
            numbers = [list(task.total_time() for task in results)]
            for c in results[0].constraints:
                numbers.append(list(task.time(c) for task in results))
            for data_points in numbers:
                row.append("{avg:.3f}".format(avg=np.average(data_points), std=np.std(data_points)))
            print(*row, sep="\t")
        print()


def main():
    # ID: cols, rows, blocks, int | str | float

    categories = generate_experiments()
    experiments = set(itertools.chain(*categories))

    runs = 1
    tasks = {test_id: [] for test_id in experiments}
    path = "../experiments"
    log_file_path = os.path.join(path, "{}.log".format(time.strftime("%Y%m%d_%H%M%S")))

    with open(log_file_path, "w") as log_file:
        for run in range(runs):
            paths = setup_experiments(experiments)
            for test_id, (csv_path, blocks_path) in paths.items():
                task = workflow.task(csv_path, blocks_path)
                task.run()
                # print("Test", *["{}".format(str(c)) for c in task.constraints], sep="\t")
                # print(test_id.name(), *["{:.3f}".format(task.time(c)) for c in task.constraints], sep="\t")
                # print()
                tasks[test_id].append(task)
                constraint_times = [task.time(c) for c in task.constraints]
                print(run, test_id.name, task.total_time())
                print(run, test_id.name, task.total_time(), *constraint_times, file=log_file, sep="\t")
        log_file.close()

    print_table(categories, tasks)


if __name__ == "__main__":
    main()
