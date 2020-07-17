import argparse
import glob
import os
import re
import json


import spacy
from spacy.tokens.doc import Doc
from collections import OrderedDict


template_synonym = {
    'sum col': 'cumulative',
    'difference': 'difference',
    'sum row': 'cumulative',
    'max row': 'maximum',
    'min row': 'minimum',
    'product row': 'multiplication',
    'product': 'multiplication',
    'sum product': 'cumulative',
    'rank': 'rank',
    'foreign key': 'foreign key',
    'lookup': 'look up',
    'running total': 'cumulative',
    'series': 'serial',
    'sum if': 'conditional summation',
    'max if': 'conditional maximum',
    'max col': 'maximum',
    'xor vec': 'xor - vec',
    'min col': 'minimum',
    'average col': 'average',
}


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


class my_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()
        # Function to add key:value

    def add(self, key, value):
        self[key] = value


class WhitespaceTokenizer(object):
    def __init__(self, vocab):
        self.vocab = vocab

    def __call__(self, text):
        words = text.split(' ')
        # All tokens 'own' a subsequent space character in this tokenizer
        spaces = [True] * len(words)
        return Doc(self.vocab, words=words, spaces=spaces)


def create_template_dictionary(directory):
    template_dict = DefaultListOrderedDict()

    os.chdir(directory)
    for json_file in glob.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
            headers = data['header']
            for header in headers:
                if header['FalsePositive'] == "No":
                    template_dict[header['template'].lower()].append(header['word'].lower())

    f = open("dictionary.txt", "w+")
    for k in template_dict.keys():
        f.write("{}:\t {}\t\n".format(k, list(filter(None, set(template_dict[k])))))
    f.close()


def clean_text(string):
    # Use \d+ to grab digits
    pattern = re.compile(r"[a-zA-Z0-9_]")

    # Use match on the pattern and column
    num = re.match(pattern, string)
    print(num)
    if num is not None:
        return int(num.group(0))


def clean(string):
    string = string.replace('\\n', ' ')
    string = re.sub('[- ]', '_', string)
    string = re.sub('[\W]+', '', string)
    string = re.sub('[_]+', ' ', string)
    return string


def replace():
    pass


def read_dictionary(file):
    template_lst = []
    word_lst = []

    with open(file) as reader:
        for line in reader.readlines():
            text = line.split("\t")
            template = clean(text[0]).strip()
            words = text[1].strip().split(",")

            template_lst.append(template)

            # reading the words
            for word in words:
                word = clean(word.strip())
                word_lst.append(word)

    print(template_lst)
    print(word_lst)

    # replace template name with other synonym
    template_lst = [clean(template_synonym[template]).strip()
                    if template in template_synonym.keys()
                    else template
                    for template in template_lst]

    return template_lst, word_lst


nlp = spacy.load("en_core_web_lg")
nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)


def naive_rank_template(template_lst, word_lst):
    template_score_dict = dict()
    word_template_dict = my_dictionary()

    for word in word_lst:
        # word = clean(word.strip())
        if word:
            word_token = nlp(word.strip())

        else:
            continue

        if word_token and word_token.vector_norm:
            for key in template_lst:
                key_tokens = nlp("".join(key))
                # clean(key_tokens.text).strip()
                template_score_dict[clean(key_tokens.text).strip()] = key_tokens.similarity(word_token)

            template_sorted_dict = ((k, template_score_dict[k]) for k in sorted(template_score_dict, key=template_score_dict.get, reverse=True))

            temp = []
            for k, v in template_sorted_dict:
                # print(k, v)
                temp.append(k)

            # word_dict.add(re.sub('[\W]+', '_', words), temp)
            word_template_dict.add(word, temp)
            # print("{}: {} --> {}".format(word_token.text, word_token.vector_norm, temp))
            template_score_dict.clear()

    return word_template_dict


def rank_template(template_lst, word_lst):
    template_score_dict = dict()
    word_template_dict = my_dictionary()

    for word in word_lst:
        # word = clean(word.strip())
        if word:
            word_token = nlp(word.strip())
        else:
            continue

        if word_token and word_token.vector_norm:
            for token in word_token:
                if token.dep_ == "amod":
                    for key in template_lst:
                        key_tokens = nlp("".join(key))
                        # clean(key_tokens.text).strip()
                        template_score_dict[clean(key_tokens.text).strip()] = key_tokens.similarity(token)
                    break
                elif token.pos_ in ['ADJ', 'DET']:
                    for key in template_lst:
                        key_tokens = nlp("".join(key))
                        template_score_dict[clean(key_tokens.text).strip()] = key_tokens.similarity(token)
                    break
                elif token.dep_ == "ROOT":
                    for key in template_lst:
                        key_tokens = nlp("".join(key))
                        template_score_dict[clean(key_tokens.text).strip()] = key_tokens.similarity(token)

            template_sorted_dict = ((k, template_score_dict[k]) for k in sorted(template_score_dict, key=template_score_dict.get, reverse=True))

            temp = []
            for k, v in template_sorted_dict:
                # print(k, v)
                temp.append(k)

            # word_dict.add(re.sub('[\W]+', '_', words), temp)
            word_template_dict.add(word, temp)
            # print("{}: {} --> {}".format(word_token.text, word_token.vector_norm, temp))
            template_score_dict.clear()

    return word_template_dict


def calculate_semantic_score(file):
    template_lst, word_lst = read_dictionary(file)
    # word_template_dict = rank_template(template_lst, word_lst)
    word_template_dict = naive_rank_template(template_lst, word_lst)
    number_of_template = len(template_lst)
    combined_score = 0
    no_of_template_not_found = 0

    with open(file, 'r+') as reader:
        for line in reader.readlines():
            text = line.split("\t")
            template = clean(text[0]).strip()
            # substituting template with it's synomym
            template = clean(template_synonym[template]).strip() if template in template_synonym.keys() else template

            # for each constraints counting ranking score
            score = 0

            #reading the words
            words = text[1].split(",")
            word_count = len(words)

            for word in words:
                word = clean(word).strip()
                if word and word in word_template_dict.keys() and template in word_template_dict[word]:
                    score += (word_template_dict[word].index(template)+1)
                else:
                    word_count -= 1
                    print("{} is not in the list of {}".format(template, word))
            if score == 0:
                no_of_template_not_found +=1
                pass
            else:
                score = (score/word_count)/number_of_template

            print("{} --> {}".format(template, score))
            combined_score += score

    print(f"Combined Score: {combined_score}, Number of Template not found {no_of_template_not_found}")
    print(f"Overall score: {combined_score/(number_of_template-no_of_template_not_found)}")


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('directory', help="Directory to run TaCLe")
    return p


if __name__ == '__main__':
    # create "dictionary.txt" from all .json file
    # create_template_dictionary(**vars(arg_parser().parse_args()))

    # read_dictionary('data/native_tacle_header/dictionary.txt')

    calculate_semantic_score('data/native_tacle_header/dictionary.txt')

    # template_lst, word_lst = read_dictionary('data/native_tacle_header/dictionary.txt')
    # word_dict = rank_template(template_lst, word_lst)