import glob
import os
import re
import argparse
import json
import logging
from collections import OrderedDict

from tacle.indexing import Orientation
from tacle import learn_from_file, filter_constraints, tables_from_csv, save_json_file

logger = logging.getLogger(__name__)


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


def main(directory, file_list=None):
    text_dict = DefaultListOrderedDict()
    mycwd = os.getcwd()

    if not file_list:
        json_list = list(glob.glob("*.json"))
    else:
        json_list = []
        for csv_file in file_list:
            file = (os.path.basename(csv_file.rstrip(os.sep)).split("."))[-2]
            file = file + ".json"
            json_list.append(file)

    with open('dictionary.txt', 'r+') as reader:
        for line in reader.readlines():
            text = line.split("\t")
            key = text[0].strip(": ")
            words = text[1].split(",")
            for t in words:
                # t= re.sub('[-]', '_', t)
                t = re.sub('[\W]+', '', t)
                text_dict[key].append(t)

    os.chdir(directory)
    os.chdir("truth")
    for json_file in json_list:
        # print(json_file)

        with open(json_file) as f:
            data = json.load(f)
            all_header = data['header']
            for header in all_header:
                if header['FalsePositive'] == "No":
                    text_dict[header['template']].append(re.sub('[- ]', '_', header['word']))

    os.chdir(mycwd)

    f = open("dictionary.txt", "w+")
    for k in text_dict.keys():
        f.write("{}:\t {}\t\n".format(k, text_dict[k]))
    f.close()


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('directory')
    return p


if __name__ == '__main__':
    main(**vars(arg_parser().parse_args()))
