import argparse
import numpy
import os, glob
import random

from directory_run import main as run_tacle
from map_template import main as create_dictionary
from train_semantic.create_classification_dictionary import class_annotation as class_annotation
from train_semantic.create_word_vector import create_word_vector as create_wordvsclass_dataset
from train_semantic.train_tf_idf_dataset import create_tf_idf_vector
from train_semantic.train_word2vector_dataset import create_word2vec_vector
from train_semantic.ml_models import train_decisionTree, train_weightedSVM, train_RandomForest


def arg_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument("file_directory", help="Directory where program can find all the data file")
    parser.add_argument(
        "-s", "--semantic", help="Run in semantic mode", action="store_true"
    )
    parser.add_argument(
        "-r", "--random", help="Run in random mode", action="store_true"
    )
    parser.add_argument(
        "-v", "--vector",
        type=str,
        help="Specify the mode for word to vector conversion: word2vec or tf-idf",
        default='word2vec'
    )
    parser.add_argument(
        "-c", "--classifier", type=str, help="Specify the classifier for training", default='dt'
    )
    parser.add_argument(
        "-sc", "--score", type=str, help="Specify the scoring method", default=None
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Increase the verbosity level to debug-level",
        action="store_true",
    )
    parser.add_argument(
        "-o", "--orientation", type=str, help="Show only tables", default=None
    )
    parser.add_argument(
        "--min_cells", type=int, help="Minimum number of cells per table", default=None
    )
    parser.add_argument(
        "--min_rows", type=int, help="Minimum number of rows per table", default=None
    )
    parser.add_argument(
        "--min_columns",
        type=int,
        help="Minimum number of columns per table",
        default=None,
    )
    return parser


# Split a dataset into k folds
def cross_validation_split(directory, folds=5):
    mycwd = os.getcwd()
    dataset = list()
    os.chdir(directory)
    for csv_file in glob.glob("*.csv"):
        dataset.append(csv_file)
    os.chdir(mycwd)

    random.seed(1)
    dataset_split = list()
    dataset_copy = sorted(list(dataset))
    fold_size = int(len(dataset) / folds)
    for i in range(folds):
        fold = list()
        while len(fold) < fold_size:
            index = random.randrange(len(dataset_copy))
            fold.append(dataset_copy.pop(index))
        dataset_split.append(fold)

    return dataset_split


def construct_data(directory, dataset):
    files = glob.glob('ML/*')
    for f in files:
        # print(f)
        os.remove(f)

    # run_tacle will create file.json in header folder word_dump.txt in the background
    open('word_dump.txt', 'w').close()  # clear and create new word_dump.txt file
    run_tacle(directory, semantic=True, csv_list=dataset)

    # create dictionary.txt collecting header words from .json file either from "header" or "truth"
    open('dictionary.txt', 'w').close()
    create_dictionary(directory, dataset)

    # map words to class 0 and 1
    open('ML/class_mapping.txt', 'w').close()
    class_annotation(directory, dataset)

    # convert header word to vector
    open('ML/word_vector.csv', 'w').close()
    open('ML/vectors.csv', 'w').close()
    create_wordvsclass_dataset('ML/class_mapping.txt')


if __name__ == '__main__':
    args = arg_parser().parse_args()

    #cross_validation
    k = 4 #k-fold
    train_test_split = cross_validation_split(args.file_directory, k)

    cv_acc = []
    cv_recall = []
    cv_precision = []
    cv_support = []
    cv_total =[]

    for i in range(len(train_test_split)):
        training_set = []
        validation_set = train_test_split[i]
        training_set += [train_test_split[j] for j in range(k) if j != i]
        training_set = [val for sublist in training_set for val in sublist]
        print(f"Size of training datasheet: {len(training_set)}: {training_set}")
        print(f"Size of validation datasheet: {len(validation_set)}: {validation_set}")

        construct_data(args.file_directory, training_set)
        if args.vector == 'tf-idf':
            X_train, y_train = create_tf_idf_vector("ML/word_vector.csv")
        elif args.vector == 'word2vec':
            X_train, y_train = create_word2vec_vector("ML/word_vector.csv")
        else:
            raise Exception("Vector conversion type no found!")

        construct_data(args.file_directory, validation_set)
        if args.vector == 'tf-idf':
            X_val, y_val = create_tf_idf_vector("ML/word_vector.csv")
        elif args.vector == 'word2vec':
            X_val, y_val = create_word2vec_vector("ML/word_vector.csv")
        else:
            raise Exception("Vector conversion type no found!")

        if args.classifier == 'svm':
            score, report = train_weightedSVM(X_train, X_val, y_train, y_val)
        elif args.classifier == 'dt':
            score, report = train_decisionTree(X_train, X_val, y_train, y_val)
        elif args.classifier == 'rf':
            score, report = train_RandomForest(X_train, X_val, y_train, y_val)
        else:
            raise Exception("Classifier not specified!")

        cv_acc.append(score)
        cv_precision.append(float(report.split('\n')[3].split()[1]))
        cv_recall.append(float(report.split('\n')[3].split()[2]))
        cv_support.append(float(report.split('\n')[3].split()[4]))
        cv_total.append(int(report.split('\n')[3].split()[4]) + int(report.split('\n')[2].split()[4]))

    avg_acc = numpy.sum((numpy.array(cv_acc) * numpy.array(cv_total))) / numpy.sum(numpy.array(cv_total))
    avg_precision = numpy.sum((numpy.array(cv_precision) * numpy.array((cv_support)))) / numpy.sum(numpy.array((cv_support)))
    avg_recall = numpy.sum((numpy.array(cv_recall) * numpy.array((cv_support)))) / numpy.sum(numpy.array((cv_support)))
    avg_support = numpy.mean(numpy.array(cv_support))

    print(f"Weighted-average cv accuracy: {avg_acc}, \n"
          f"Weighted-average cv precision: {avg_precision}, \n"
          f"Weighted-average cv recall: {avg_recall}, \n"
          f"Weighted-average cv support: {avg_support}\n")
