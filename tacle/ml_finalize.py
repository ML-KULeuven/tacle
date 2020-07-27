import glob
import os

from ml_experiment import construct_data
from train_semantic.train_word2vector_dataset import create_word2vec_vector
from train_semantic.ml_models import train_decisionTree, train_RandomForest, train_LinearSVM, train_weightedSVM


def create_dataset(directory):
    mycwd = os.getcwd()
    dataset = list()
    os.chdir(directory)
    for csv_file in glob.glob("*.csv"):
        dataset.append(csv_file)
    os.chdir(mycwd)

    construct_data(directory, dataset)


if __name__ == '__main__':
    directory = 'data'
    # create_dataset(directory)

    X_train, y_train = create_word2vec_vector("ML/word_vector.csv")
    # train_decisionTree(X_train, X_train, y_train, y_train)
    train_weightedSVM(X_train, X_train, y_train, y_train)
