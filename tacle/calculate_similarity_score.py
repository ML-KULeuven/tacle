import spacy
import re
from spacy.tokens import Doc


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


template_lst = []
word_lst = []


def read_dictionary(dictionary= "dictionary.txt"):
    with open(dictionary, 'r+') as reader:
        for line in reader.readlines():
            # reading the keys
            text = line.split("\t")
            text[0] = re.sub('[- ]', '_', text[0])
            key = re.sub('[\W]+', '', text[0])
            key = re.sub('[_]+', ' ', key)
            template_lst.append(key)

            # reading the words
            words = text[1].split(",")
            for t in words:
                t = re.sub('[-]+', '_', t)
                t = re.sub('[\W]+', '', t)
                t = re.sub('[_]+', ' ', t)
                word_lst.append(t)

    print(template_lst)
    print(word_lst)


def calculate_simirarity():
    nlp = spacy.load("en_core_web_lg")
    nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)

    dict1 = dict()
    word_dict = my_dictionary()

    for words in word_lst:
        if words:
            word_token = nlp(words)
            for token in word_token:
                if token.dep_ == "amod":
                    for key in template_lst:
                        key_tokens = nlp("".join(key))
                        dict1[re.sub('[\W]+', '', key_tokens.text)] = key_tokens.similarity(token)
                    break
                elif token.dep_ == "ROOT":
                    for key in template_lst:
                        key_tokens = nlp("".join(key))
                        dict1[re.sub('[\W]+', '', key_tokens.text)] = key_tokens.similarity(token)

            sorted_dict1 = ((k, dict1[k]) for k in sorted(dict1, key=dict1.get, reverse=True))
            temp = []
            for k, v in sorted_dict1:
                # print(k, v)
                temp.append(k)
            # word_dict.add(re.sub('[\W]+', '_', words), temp)
            word_dict.add(words, temp)
            # print("{}: {} --> {}".format(word_token.text, word_token.vector_norm, temp))
            dict1.clear()

    return word_dict


def store_in_csv():
    import csv

    fieldnames = ['constraint', 'similarity_score']
    writer = csv.DictWriter(open("chunk_sim.csv", 'w'), fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()

    word_dict = calculate_simirarity()

    #Calculating ranking score
    with open('dictionary.txt', 'r+') as reader:
        for line in reader.readlines():
            #reading the keys
            text = line.split("\t")
            text[0] = re.sub('[- ]', '_', text[0])
            key = re.sub('[\W]+', '', text[0])
            key = re.sub('[_]+', ' ', key)

            # for each constraints counting ranking score
            score = 0
            word_count = 0

            #reading the words
            words = text[1].split(",")
            for t in words:
                t = re.sub('[-]+', '_', t)
                t = re.sub('[\W]+', '', t)
                t = re.sub('[_]+', ' ', t)

                word_count += 1
                if key in word_dict[t]:
                    score += (word_dict[t].index(key)+1)
                else:
                    print("{} is not in the list".format(key))
            if score == 0:
                pass
            else:
                score = word_count/score

            print("{} --> {}".format(key, score))
            writer.writerow({'constraint': '{}'.format(key), 'similarity_score': '{}'.format(score)})


if __name__ == "__main__":
    read_dictionary()
    store_in_csv()
