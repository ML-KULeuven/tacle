import numpy
from pandas import json

from draw import Plotter
from engine.util import local
from experiment import Experiment, ConstraintCounter


def main():
    info = [
        ("Tables", lambda e: e.tables, "grey", lambda x: str(x)),
        # ("Vectors", lambda e: e.vectors, "cyan", lambda x: str(x)),
        ("Cells", lambda e: e.cells, "black", lambda x: str(x)),
        ("Intended Constraints", lambda e: e.counter.count(relevant=True, supported=True), "magenta", lambda x: str(x)),
        ("Recall", lambda e: recall(e.counter), "green", lambda x: "{:.2f}".format(x)),
        ("Recall Supported", lambda e: recall(e.counter, True), "lightgreen", lambda x: "{:.2f}".format(x)),
        ("Precision", lambda e: precision(e.counter), "yellow", lambda x: "{:.2f}".format(x)),
        ("Runtime", lambda e: numpy.average(e.running_times(1)), "red", lambda x: "{:.2f}s".format(x))
    ]

    with open(local("data/data.txt")) as data_file:
        data_json = json.load(data_file)
        categories = ["Exercises", "Tutorials", "Data"]
        stats = {}
        for category in categories:
            files = data_json[category]
            stats[category] = []
            for file in files:
                experiment = Experiment(file)
                print(file)
                for accident in experiment.counter.additional:
                    print("\tADDITIONAL:\t{}".format(accident))
                for missing in experiment.counter.missed:
                    print("\tMISSING:\t{}".format(missing))
                entry = {t[0]: t[1](experiment) for t in info}
                entry["relevant.found"] = experiment.counter.count(relevant=True, found=True)
                entry["extra.found"] = experiment.counter.count(relevant=False, found=True)
                stats[category].append(entry)

        maximal = {t[0]: max(max(stats[t[0]] for stats in cat_stats) for cat_stats in stats.values()) for t in info}
        colors = dict(zip(categories, ["red", "yellow", "black", "green"]))

        print("\n" * 2)
        max_label = list(t[3](maximal[t[0]]) for t in info)
        global_plot = Plotter("comparison", list(t[0] for t in info), upper=max_label)
        test = {"Exercises": (30, 2), "Tutorials": (46, 21), "Data": (6, 0)}
        for category, cat_stats in [(cat, stats[cat]) for cat in categories]:
            print(category)
            plotter = Plotter("benchmark_" + category)
            averages = []
            errors = []
            for name, f, color, pretty in info:
                plotter.add_category(name, list(stats[name] / maximal[name] for stats in cat_stats), color)
                result_string = "\tAverage {name}: {average} - total: {total}"
                average = numpy.average(list(stats[name] for stats in cat_stats))
                averages.append(average / maximal[name])
                errors.append(numpy.std(list(stats[name] for stats in cat_stats)) / maximal[name])
                total = sum(stats[name] for stats in cat_stats)
                print(result_string.format(name=name.lower(), average=pretty(average), total=pretty(total)))
            relevant = sum(stats["relevant.found"] for stats in cat_stats)
            print("\tRelevant found: {}".format(relevant))
            extra = sum(stats["extra.found"] for stats in cat_stats)
            print("\tExtra found: {}".format(extra))

            relevant_expected, extra_expected = test[category]
            if relevant_expected != relevant:
                print("ERROR ({}): found {} instead of {} relevant constraints"
                      .format(category, relevant, relevant_expected))

            if extra_expected != extra:
                print("ERROR ({}): found {} instead of {} extra constraints"
                      .format(category, extra, extra_expected))

            global_plot.add_category(category, averages, colors[category], errors, "green")
            plotter.plot()
        global_plot.plot()


def recall(counter: ConstraintCounter, supported=False):
    rel = counter.count(relevant=True, supported=supported)
    if rel == 0:
        return 1.0
    return counter.count(relevant=True, found=True) / rel


def precision(counter: ConstraintCounter):
    found = counter.count(found=True)
    if found == 0:
        return 1.0
    return counter.count(relevant=True, found=True) / found


if __name__ == '__main__':
    main()