_printers = dict()


def get(topic, parent=None, on=True):
    if parent is not None:
        topic = "{}.{}".format(parent.topic, topic)
    if topic not in _printers:
        state = State(on)
        _printers[topic] = Printer(topic, state)
    return _printers[topic]


def write(topic, print_f, end="\n"):
    if topic not in _printers:
        raise Exception("No printer found for {}".format(topic))
    get(topic).print(print_f, end=end)


def disable(topic):
    get(topic).disable()


def enable(topic):
    get(topic).enable()


class State:
    def __init__(self, on=True):
        self.on = on

    def copy(self):
        return State(self.on)


class Printer:
    def __init__(self, topic, state):
        self._topic = topic
        self._states = [state]

    @property
    def topic(self):
        return self._topic

    def write(self, print_f, end="\n"):
        if self.on():
            print(print_f() if callable(print_f) else print_f, end=end)
        return self

    def form(self, format_string, *args, **kwargs):
        return self.write(lambda: format_string.format(*args, **kwargs))

    def nl(self):
        return self.write("")

    def disable(self):
        self._state().on = False
        return self

    def enable(self):
        self._state().on = True
        return self

    def save(self):
        self._states.append(self._state().copy())
        return self

    def restore(self):
        if len(self._states) > 1:
            self._states.pop()
        return self

    def on(self):
        return self._state().on

    def _state(self):
        return self._states[-1]
