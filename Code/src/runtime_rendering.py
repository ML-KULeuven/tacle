import matplotlib.pyplot as plt
import numpy


class ScatterData:
    colors = ["black", "green"]
    markers = ["o", "v"]

    def __init__(self, title, x_data):
        self.title = title
        self.x = x_data
        self.data = []
        self.limits = None, None

    def add_data(self, name, data):
        self.data.append((name, data))
        return self

    @property
    def size(self):
        return len(self.data)

    def x_lim(self, limits):
        self.limits = limits, self.limits[1]

    def y_lim(self, limits):
        self.limits = self.limits[0], limits

    def render(self, ax, lines=True, log_x=True, log_y=True):
        plots = []
        for i in range(self.size):
            title, times = self.data[i]
            x_data = self.x(times) if callable(self.x) else self.x
            plots.append(ax.scatter(x_data, times, color=self.colors[i], marker=self.markers[i], s=40))
            if lines:
                ax.plot(x_data, times, color=self.colors[i])

        ax.legend(plots, (title for title, _ in self.data), loc="lower right")

        if log_x:
            ax.set_xscale('log')
        if log_y:
            ax.set_yscale('log')

        x_lim, y_lim = self.limits
        if x_lim is not None:
            ax.set_xlim(x_lim)
        if y_lim is not None:
            ax.set_ylim(y_lim)

        ax.set_ylabel("Runtime")
        ax.set_xlabel(self.title)


def plot(file, *args):
    fig = plt.figure()
    fig.set_size_inches(12, 12)

    subplots = len(args)
    cols = numpy.ceil(numpy.sqrt(subplots))
    rows = numpy.ceil(subplots / cols)

    for i in range(subplots):
        ax = fig.add_subplot(cols, rows, i + 1)
        args[i].render(ax)

    if file is None:
        plt.show()
    else:
        plt.savefig(file, format="pdf")
