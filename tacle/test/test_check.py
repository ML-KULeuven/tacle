import numpy as np

from tacle.engine.evaluate import check_template, evaluate_template
from tacle.indexing import Orientation
from tacle.core.template import Aggregate, Operation


def test_sum():
    template = Aggregate(Orientation.horizontal, Operation.SUM)
    x = np.array([[5, 6, 7], [10, 20, 30]])

    print(evaluate_template(template, {template.x: x}))

    y = np.sum(x, 1)

    assert check_template(template, {template.x: x, template.y: y})
