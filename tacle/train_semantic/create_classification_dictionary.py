import glob
import os
from collections import OrderedDict
import json


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


template_words = []
classification_dictionary = DefaultListOrderedDict()


def read_constraint_word(directory):
    os.chdir("data/"+directory+"/truth")
    for json_file in glob.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
            headers = data['header']
            for header in headers:
                template_words.append(header['word'])


def create_classification_dictionary(file):
    with open(file, "r") as reader:
        for line in reader.readlines():
            text = line.split("\t")
            word = text[0].strip(":")

            if word in template_words:
                classification_dictionary[1].append(word)
            else:
                classification_dictionary[0].append(word)


if __name__ == "__main__":
    path = os.getcwd()

    directory = ['real_dataset', 'tacle_benchmark_data']
    filename = 'word_dump.txt'

    f = open("C:/Users/safat/OneDrive/Desktop/Thesis/Ranking_based_automation/sementic-tacle/class_mapping.txt", "a+")

    for folder in directory:
        read_constraint_word(folder)
        os.chdir(path)
        create_classification_dictionary("data/"+folder+"/"+filename)
        os.chdir(path)

    for class_value, word_list in classification_dictionary.items():
        f.write("{}:\t {}\t\n".format(class_value, word_list))

    f.close()

