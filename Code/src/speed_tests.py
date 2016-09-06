import json
import random
import string
import numpy as np
import time

import workflow
import os
import itertools

from core.group import GType


class SpeedTestId:
    def __init__(self, cols, rows, blocks, types):
        self.cols = cols
        self.rows = rows
        self.blocks = blocks
        self.types = types

    def __hash__(self, *args, **kwargs):
        return hash((self.cols, self.rows, tuple(self.blocks), tuple(self.types)))

    def __eq__(self, other):
        if not isinstance(other, SpeedTestId):
            return False
        return self.cols == other.cols and self.rows == other.rows and self.blocks == other.blocks \
            and self.types == other.types

    def __repr__(self):
        return "c{} r{} b{}".format(self.cols, self.rows, self.blocks)

    @property
    def name(self):
        assert(all(b == self.blocks[0] for b in self.blocks))
        return "c{}_r{}_b{}".format(self.cols, self.rows, "{}x{}".format(len(self.blocks), self.blocks[0]))


def generate_random(test_id: SpeedTestId):
    column_data = []

    for column_type in test_id.types:
        if column_type == GType.int:
            column_data.append(np.random.randint(1, 1000, test_id.rows))
        elif column_type == GType.string:
            letter = lambda: random.choice(string.ascii_lowercase)
            word = lambda: ''.join(letter() for _ in range(np.random.randint(5, 15)))
            column_data.append([word() for _ in range(test_id.rows)])
        else:
            raise RuntimeError("Unexpected column type {}".format(column_type))

    return list(list(str(column_data[col][row]) for col in range(test_id.cols)) for row in range(test_id.rows))


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
    bounds = [1, test_id.rows, 1, test_id.cols]
    content["Tables"] = [{"Name": "T1", "Bounds": bounds, "Orientation": "Column"}]

    # Generate groups
    index = 1
    blocks = []
    for block_size in test_id.blocks:
        blocks.append({"Table": "T1", "Bounds": [":", index, index + block_size - 1]})
        index += block_size
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


def generate_experiments(default_power=3, min_power=0, max_power=6, block_power=5, gtype=GType.int):
    # Build increments
    default = 2 ** 3
    increments = list(2 ** p for p in range(min_power, max_power + 1))

    # Vary number of vectors
    cat_1 = []
    for cols in increments:
        rows = default
        cat_1.append(SpeedTestId(cols, rows, [cols], [gtype] * cols))

    # Vary vector size
    cat_2 = []
    for rows in increments:
        cols = default
        cat_2.append(SpeedTestId(cols, rows, [cols], [gtype] * cols))

    # Vary block sizes
    cat_3 = []
    vectors = 2 ** block_power
    for block_size in reversed(increments):
        if block_size <= vectors:
            cols = vectors
            rows = default
            cat_3.append(SpeedTestId(cols, rows, [block_size] * int(vectors / block_size), [gtype] * cols))

    return [cat_1, cat_2, cat_3]


def setup_experiments(experiments):
    path = "../data/speed_tests"
    clear_folder(path)

    paths = dict()
    for test_id in experiments:
        paths[test_id] = generate_file(path, generate_random, test_id, "random")
    return paths


def main():
    # ID: cols, rows, blocks, int | str | float

    categories = generate_experiments(default_power=3, max_power=5)
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


if __name__ == "__main__":
    main()
