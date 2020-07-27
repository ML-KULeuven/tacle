""""
Run through all .json file in the folder
INPUT: directory address
OUTPUT: create a dictionary by mapping each templates to its header word
"""

import glob
import os
import shutil
import argparse
import logging
import json
import re

from collections import OrderedDict

logger = logging.getLogger(__name__)


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


def main(directory):
    text_dict = DefaultListOrderedDict()
    with open('.\dictionary.txt', 'r+') as reader:
        for line in reader.readlines():
            text = line.split("\t")
            key = text[0].strip(": ")
            words = text[1].split(",")
            for t in words:
                t = re.sub('[\W]+', '', t)
                text_dict[key].append(t)

    os.chdir(directory)
    for json_file in glob.glob("*.json"):
        print(json_file)
        with open(json_file) as file:
            to_python = json.load(file)
            header = to_python["header"]

            for template in header:
                if template["word"]:
                    text_dict[template["template"]].append(re.sub('[- ]', '_', template["word"]))

    f = open("../dictionary.txt", "w+")
    for k in text_dict.keys():
        # f.write("{}:\t {}\t\k".format(k, list(set(text_dict[k]))))
        f.write("{}:\t {}\t\n".format(k, text_dict[k]))
    f.close()


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    return p


if __name__ == '__main__':
    main(**vars(arg_parser().parse_args()))
