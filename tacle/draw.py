import matplotlib.pyplot as plt
import numpy as np


class Plotter:
    def __init__(self, output=None, labels=None, upper=None):
        super().__init__()
        self._categories = []
        self._output = output
        self._labels = labels
        self._upper = upper

    def add_category(self, name, data, color, errors=None, e_color=None):
        self._categories.append((name, data, color, errors, e_color))

    def plot(self):
        cat_count = len(self._categories)
        data_length = len(self._categories[0][1])
        ind = np.array(range(data_length))
        width = 0.1

        fig = plt.figure()
        ax = fig.add_subplot(111)
        fig.set_size_inches(8, 2)
        bars = []
        for i in range(cat_count):
            _, data, color, e, ec = self._categories[i]
            if e is not None:
                bars.append(plt.bar(ind + i * width, data, width=width, color=color, yerr=e, ecolor=ec))
            else:
                bars.append(plt.bar(ind + i * width, data, width=width, color=color))
        plt.xticks(ind + (cat_count - 1) * width)
        labels = list(label.replace(" ", "\n") for label in self._labels) \
            if self._labels is not None else range(1, data_length + 1)
        ax.set_xticklabels(labels)
        plt.ylabel("Spreadsheet average in percent")
        plt.yticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
        lgd = plt.legend((bar[0] for bar in bars), (category[0] for category in self._categories), loc='upper center',
                         bbox_to_anchor=(0.5, -0.2), ncol=cat_count)

        if self._upper is not None:
            upper_ax = ax.twiny()
            upper_ax.set_xlim(ax.get_xlim())
            upper_ax.set_xticks(ind + (cat_count - 1) * width)
            upper_ax.set_xticklabels(self._upper)
            upper_ax.set_xlabel("Maximum across all spreadsheets")

        plt.plot()
        ax.set_ylim(ymin=0, ymax=1)
        if self._output is None:
            self._output = plt.show()
        else:
            name = "{}.pdf".format(self._output.replace(" ", "_").replace("\n", "_").lower())
            plt.savefig(name, format="pdf", bbox_extra_artists=(lgd,), bbox_inches='tight')


def main():
    m = [[0.05, 0.05, 0.05, 0.06, 0.06, 0.06, 0.05, 0.05, 0.05, 0.05],
         [0.07, 0.08, 0.08, 0.09, 0.10, 0.09, 0.07, 0.07, 0.08, 0.07],
         [0.02, 0.02, 0.02, 0.02, 0.02, 0.01, 0.01, 0.01, 0.02, 0.02],
         [0.08, 0.08, 0.07, 0.08, 0.08, 0.08, 0.07, 0.08, 0.07, 0.07],
         [2.67, 2.68, 2.66, 2.97, 2.77, 2.67, 2.69, 2.69, 2.68, 2.66],
         [0.12, 0.13, 0.12, 0.13, 0.13, 0.13, 0.12, 0.12, 0.12, 0.12],
         [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
         [8.39, 8.73, 8.48, 9.72, 9.12, 8.56, 8.54, 8.24, 8.28, 8.41],
         [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
         [0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06],
         [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
         [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
         [0.05, 0.05, 0.06, 0.06, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05],
         [0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03],
         [0.09, 0.11, 0.10, 0.08, 0.09, 0.09, 0.09, 0.10, 0.09, 0.09],
         [0.09, 0.09, 0.09, 0.08, 0.09, 0.08, 0.09, 0.09, 0.09, 0.10],
         [0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04],
         [0.07, 0.07, 0.08, 0.07, 0.08, 0.07, 0.07, 0.07, 0.07, 0.08],
         [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
         [0.05, 0.05, 0.05, 0.04, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05],
         [1.68, 1.72, 1.69, 1.80, 1.74, 1.72, 1.69, 1.72, 1.68, 1.72],
         [0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08],
         [0.10, 0.10, 0.10, 0.11, 0.12, 0.10, 0.11, 0.11, 0.11, 0.10],
         [0.08, 0.08, 0.09, 0.09, 0.09, 0.08, 0.09, 0.08, 0.08, 0.08],
         [0.03, 0.03, 0.02, 0.03, 0.03, 0.03, 0.03, 0.02, 0.03, 0.03],
         [0.04, 0.04, 0.04, 0.04, 0.05, 0.04, 0.04, 0.04, 0.05, 0.04],
         [0.06, 0.05, 0.05, 0.06, 0.06, 0.05, 0.05, 0.05, 0.06, 0.05],
         [0.04, 0.04, 0.04, 0.04, 0.05, 0.04, 0.04, 0.04, 0.04, 0.04],
         [0.03, 0.03, 0.04, 0.04, 0.04, 0.04, 0.04, 0.03, 0.04, 0.03],
         [0.02, 0.02, 0.02, 0.02, 0.03, 0.02, 0.02, 0.02, 0.03, 0.02],
         [1.53, 1.53, 1.54, 1.65, 1.70, 1.53, 1.53, 1.56, 1.56, 1.54],
         [0.05, 0.05, 0.05, 0.06, 0.06, 0.05, 0.05, 0.05, 0.05, 0.05]]
    mean = np.mean(m, 1)
    ind = np.array(range(32))

    fig = plt.figure()
    fig.set_size_inches(8, 2)
    width = 0.7
    plt.bar(ind, mean, width=width, color="grey", yerr=np.std(m, 1), ecolor="black")
    plt.xticks([])
    plt.ylim(0, 10)
    plt.ylabel("Runtime (s)")
    # eb = plt.errorbar(ind, mean, yerr=.1, color='b')
    plt.plot()
    plt.savefig("testmatplotlib.pdf", format="pdf")


if __name__ == '__main__':
    main()
