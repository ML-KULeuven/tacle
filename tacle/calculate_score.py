import spacy
import re
from spacy.tokens import Doc
from collections import OrderedDict


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


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]

template_lst = []
word_lst = []


def clean_word(word):
    word = re.sub('[-]+', '_', word)
    word = re.sub('[\W]+', '', word)
    word = re.sub('[_]+', ' ', word)
    return word


def clean_word2(template):
    template = re.sub('[- ]+', '_', template)
    template = re.sub('[\W]+', '', template)
    template = re.sub('[_]+', ' ', template)
    return template


def read_dictionary(dictionary= "../dictionary.txt"):
    with open(dictionary, 'r+') as reader:
        for line in reader.readlines():
            # reading the keys
            text = line.split("\t")
            key = clean_word2(text[0])
            template_lst.append(key)

            # reading the words
            words = text[1].split(",")
            for w in words:
                word_lst.append(clean_word2(w))

    # print(template_lst)
    # print(word_lst)


def read_word_dump(dictionary="../word_dump.txt"):
    word_dict = DefaultListOrderedDict()

    with open(dictionary, 'r+') as reader:
        for line in reader.readlines():
            # reading the keys
            text = line.split("\t")
            word = clean_word2(text[0])

            # reading the words
            templates = text[1].split(",")
            for template in templates:
                word_dict[word].append(clean_word(template))
    print(word_dict)
    return word_dict


def store_in_csv():
    import csv

    fieldnames = ['constraint', 'similarity_score']
    writer = csv.DictWriter(open("../similarity_score.csv", 'w'), fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()

    word_dict = read_word_dump()

    #Calculating ranking score
    with open('../dictionary.txt', 'r+') as reader:
        for line in reader.readlines():
            #reading the keys
            text = line.split("\t")
            template = clean_word(text[0])

            # for each constraints counting ranking score
            score = 0
            word_count = 0

            #reading the words
            words = text[1].split(",")
            for t in words:
                t = clean_word(t)

                word_count += 1
                if template in word_dict[t]:
                    score += (word_dict[t].index(template)+1)
                else:
                    print("{} is not in the list of {}".format(template, t))
            if score == 0:
                pass
            else:
                score = score/word_count

            print("{} --> {}".format(template, score))
            writer.writerow({'constraint': '{}'.format(template), 'similarity_score': '{}'.format(score)})


if __name__ == "__main__":
    read_dictionary()
    # read_word_dump()
    store_in_csv()
