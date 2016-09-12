import matplotlib.pyplot as plt

number_vectors = [("Runtime",
                   [0.013, 0.028, 0.171, 2.475, 37.709, 637.579])]
vector_size = [("Runtime",
                [2.738, 2.727, 2.475, 2.475, 2.373, 1.603, 0.899, 0.375, 0.408, 0.479, 0.589, 0.837, 1.253]),
               ("Runtime without RANK",
                [2.735, 2.724, 2.471, 2.47, 2.367, 1.595, 0.883, 0.348, 0.358, 0.373, 0.385, 0.446, 0.5])]
number_blocks = [("Runtime aggregate constraints",
                  [1.66, 0.783, 0.291, 0.167, 0.046]),
                 ("Runtime non-aggregate constraints",
                  [36.051, 37.729, 37.974, 48.377, 90.721])]


def x(length):
    return [2 ** power for power in range(length)]


def plot(data):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    # fig.set_size_inches(8, 2)  TODO Check out

    colors = ["black", "green"]
    plots = []
    for i in range(len(data)):
        title, times = data[i]
        plots.append(ax.scatter(x(len(times)), times, color=colors[i]))
        ax.plot(x(len(times)), times, color=colors[i])

    ax.legend(plots, (title for title, _ in data), loc="lower left")

    ax.set_yscale('log')
    ax.set_xscale('log')

    plt.show()

plot(number_vectors)
plot(vector_size)
plot(number_blocks)
