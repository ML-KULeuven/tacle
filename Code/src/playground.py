import numpy
from pandas import json

from draw import Plotter
from engine.util import local
from experiment import Experiment, ConstraintCounter


def main():
    with open(local("data/data.txt")) as data_file:
        data_json = json.load(data_file)
        categories = ["Exercises", "Tutorials", "Data"]
        log = {}
        for category in data_json:
            name = category["Category"]
            files = category["Files"]
            log[name] = []
            for file in files:
                experiment = Experiment(file)
                print(file)
                for accident in experiment.counter.additional:
                    print("\tADDITIONAL:\t{}".format(accident))
                log[name].append(experiment)

        info = [
            ("Tables", lambda e: e.tables, "grey", lambda x: str(x)),
            #("Vectors", lambda e: e.vectors, "cyan", lambda x: str(x)),
            ("Cells", lambda e: e.cells, "black", lambda x: str(x)),
            ("Relevant Constraints", lambda e: e.counter.count(relevant=True), "magenta", lambda x: str(x)),
            ("Recall", lambda e: recall(e.counter), "green", lambda x: "{:.2f}".format(x)),
            ("Recall Supported", lambda e: recall(e.counter, True), "lightgreen", lambda x: "{:.2f}".format(x)),
            ("Precision", lambda e: precision(e.counter), "yellow", lambda x: "{:.2f}".format(x)),
            ("Runtime", lambda e: numpy.average(e.running_times(1)), "red", lambda x: "{:.2f}s".format(x))
        ]

        maximal = {name: max(max(f(e) for e in experiments) for experiments in log.values()) for name, f, _, _ in info}
        colors = dict(zip(categories, ["red", "yellow", "black", "green"]))

        print("\n" * 2)
        max_label = list(t[3](maximal[t[0]]) for t in info)
        global_plot = Plotter("comparison", list(t[0] for t in info), upper=max_label)
        for category, experiments in [(cat, log[cat]) for cat in categories]:
            print(category)
            plotter = Plotter("benchmark_" + category)
            averages = []
            errors = []
            for name, f, color, pretty in info:
                plotter.add_category(name, list(f(e) / maximal[name] for e in experiments), color)
                result_string = "\tAverage {name}: {average} - total: {total}"
                average = numpy.average(list(f(e) for e in experiments))
                averages.append(average / maximal[name])
                errors.append(numpy.std(list(f(e) for e in experiments)) / maximal[name])
                total = sum(f(e) for e in experiments)
                print(result_string.format(name=name.lower(), average=pretty(average), total=pretty(total)))
            print("\tRelevant found: {}".format(sum(e.counter.count(relevant=True, found=True) for e in experiments)))
            print("\tExtra found: {}".format(sum(e.counter.count(relevant=False, found=True) for e in experiments)))
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