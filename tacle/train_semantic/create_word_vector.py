import re
from spacy.tokens import Doc
import spacy


class WhitespaceTokenizer(object):
    def __init__(self, vocab):
        self.vocab = vocab

    def __call__(self, text):
        words = text.split(' ')
        # All tokens 'own' a subsequent space character in this tokenizer
        spaces = [True] * len(words)
        return Doc(self.vocab, words=words, spaces=spaces)


nlp = spacy.load("en_core_web_lg")
nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)


def clean(string):
    string = re.sub('[- ]', '_', string)
    string = re.sub('[\W]+', '', string)
    string = re.sub('[_]+', ' ', string)
    return string


def create_word_vector(file):
    vector_file = open('C:/Users/safat/OneDrive/Desktop/Thesis/Ranking_based_automation/sementic-tacle/word_vector.csv', 'a+')

    with open(file, "r") as reader:
        for line in reader.readlines():
            text = line.split("\t")
            word_list = text[1].strip().split(",")

            for word in word_list:
                word = clean(word.strip())
                if word:
                    word_token = nlp(word.strip())
                else:
                    continue

                if word_token and word_token.vector_norm:
                    for token in word_token:
                        if token.dep_ == "amod":
                            write_line = f"{word},{token},{token.vector.flatten()},{text[0]}"
                            vector_file.write(write_line + "\n")
                            break
                        elif token.pos_ in ['ADJ', 'DET']:
                            write_line = f"{word},{token},{token.vector.flatten()},{text[0]}"
                            vector_file.write(write_line + "\n")
                            break
                        elif token.dep_ == "ROOT":
                            write_line = f"{word},{token},{token.vector.flatten()},{text[0]}"
                            vector_file.write(write_line + "\n")
                            break


    # Close the file
    vector_file.close()


if __name__ == "__main__":
    create_word_vector("C:/Users/safat/OneDrive/Desktop/Thesis/Ranking_based_automation/sementic-tacle/class_mapping.txt")