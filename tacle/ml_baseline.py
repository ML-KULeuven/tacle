import numpy

from train_semantic.train_tf_idf_dataset import create_tf_idf_vector
from train_semantic.train_word2vector_dataset import create_word2vec_vector
from train_semantic.ml_models import train_naiveBayes
from ml_experiment import cross_validation_split, construct_data


def baseline(file_directory,vector):
    # cross_validation
    k = 4  # k-fold
    train_test_split = cross_validation_split(file_directory, k)

    cv_acc = []
    cv_recall = []
    cv_precision = []
    cv_support = []
    cv_total = []

    for i in range(len(train_test_split)):
        training_set = []
        validation_set = train_test_split[i]
        training_set += [train_test_split[j] for j in range(k) if j != i]
        training_set = [val for sublist in training_set for val in sublist]
        print(f"Size of training datasheet: {len(training_set)}: {training_set}")
        print(f"Size of validation datasheet: {len(validation_set)}: {validation_set}")

        construct_data(file_directory, training_set)
        if vector == 'tf-idf':
            X_train, y_train = create_tf_idf_vector("ML/word_vector.csv")
        elif vector == 'word2vec':
            X_train, y_train = create_word2vec_vector("ML/word_vector.csv")
        else:
            raise Exception("Vector conversion type no found!")

        construct_data(file_directory, validation_set)
        if vector == 'tf-idf':
            X_val, y_val = create_tf_idf_vector("ML/word_vector.csv")
        elif vector == 'word2vec':
            X_val, y_val = create_word2vec_vector("ML/word_vector.csv")
        else:
            raise Exception("Vector conversion type no found!")

        score, report = train_naiveBayes(X_train, X_val, y_train, y_val)

        print("=======================================================================================")
        print("=======================================================================================")

        cv_acc.append(score)
        cv_precision.append(float(report.split('\n')[3].split()[1]))
        cv_recall.append(float(report.split('\n')[3].split()[2]))
        cv_support.append(float(report.split('\n')[3].split()[4]))
        cv_total.append(int(report.split('\n')[3].split()[4]) + int(report.split('\n')[2].split()[4]))

    avg_acc = numpy.sum((numpy.array(cv_acc) * numpy.array(cv_total))) / numpy.sum(numpy.array(cv_total))
    avg_precision = numpy.sum((numpy.array(cv_precision) * numpy.array((cv_support)))) / numpy.sum(
        numpy.array((cv_support)))
    avg_recall = numpy.sum((numpy.array(cv_recall) * numpy.array((cv_support)))) / numpy.sum(
        numpy.array((cv_support)))
    avg_support = numpy.mean(numpy.array(cv_support))

    print(f"Weighted Average cv accuracy: {avg_acc}, \n"
          f"Weight-Average cv precision: {avg_precision}, \n"
          f"Weighted-Average cv recall: {avg_recall}, \n"
          f"Average cv support: {avg_support}\n")


if __name__ == '__main__':
    for vector in ['tf-idf']:
        baseline('data', vector)