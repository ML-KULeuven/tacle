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


def read_constraint_word(directory, file_list):
    path = os.getcwd()
    os.chdir(directory)
    if not file_list:
        json_list = list(glob.glob("*.json"))
    else:
        json_list = []
        for csv_file in file_list:
            file = (os.path.basename(csv_file.rstrip(os.sep)).split("."))[-2]
            file = file + ".json"
            json_list.append(file)
    # print(json_list)

    for json_file in json_list:
        with open(json_file) as f:
            data = json.load(f)
            headers = data['header']
            for header in headers:
                template_words.append(header['word'])

    os.chdir(path)


def create_classification_dictionary(file):
    path = os.getcwd()
    with open(file, "r") as reader:
        for line in reader.readlines():
            text = line.split("\t")
            word = text[0].strip(":")

            if word in template_words:
                classification_dictionary[1].append(word)
            else:
                classification_dictionary[0].append(word)

    os.chdir(path)


def class_annotation(directory, file_list=None):
    f = open("ML/class_mapping.txt", "a+")
    read_constraint_word(directory+"/truth", file_list)
    create_classification_dictionary("word_dump.txt")
    for class_value, word_list in classification_dictionary.items():
        f.write("{}:\t {}\t\n".format(class_value, word_list))
    f.close()

    template_words.clear()
    classification_dictionary.clear()





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

