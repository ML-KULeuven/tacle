import random
import numpy
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import DecisionTreeClassifier
from ml_experiment import cross_validation_split, construct_data
from train_semantic.train_tf_idf_dataset import create_tf_idf_vector
from train_semantic.train_word2vector_dataset import create_word2vec_vector
from train_semantic.ml_models import train_model


def GridSearchDT(directory, vector):
    parameter = {
        'max_features': [50, 100, 150, 200, 250],
        'max_depth': [2, 4, 6, 8, 10],
    }

    # cross_validation
    k = 4  # k-fold

    train_test_split = cross_validation_split(directory, k)

    for max_features in parameter['max_features']:
        for max_depth in parameter['max_depth']:

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

                construct_data(directory, training_set)
                if vector == 'tf-idf':
                    X_train, y_train = create_tf_idf_vector("ML/word_vector.csv")
                elif vector == 'word2vec':
                    X_train, y_train = create_word2vec_vector("ML/word_vector.csv")
                else:
                    raise Exception("Vector conversion type no found!")

                construct_data(directory, validation_set)
                if vector == 'tf-idf':
                    X_val, y_val = create_tf_idf_vector("ML/word_vector.csv")
                elif vector == 'word2vec':
                    X_val, y_val = create_word2vec_vector("ML/word_vector.csv")
                else:
                    raise Exception("Vector conversion type no found!")

                dt = DecisionTreeClassifier(
                    criterion='gini',
                    max_depth=max_depth,
                    max_features=max_features,
                    random_state=1,
                    class_weight='balanced')

                score, report = train_model(dt, X_train, X_val, y_train, y_val)
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

            print(f"Decision tree: {dt.get_params()}")
            # print(f"Average Accuracy is: {avg_acc}")

            f = open('decisiontree.csv', 'a+')
            f.write(f"{max_depth}, {max_features}, {avg_acc}, {avg_precision}, {avg_recall}, {avg_support}\n")
            f.close()
            print("#########################################################")
            print("#########################################################")


def GridSearchSVM(directory, vector):
    parameter = {
        'C': [0.1, 1, 10],
        'gamma': [2, 1, 0.1, 0.01, 0.001, 0.0001, 0.00001]
    }

    # cross_validation
    k = 4  # k-fold

    train_test_split = cross_validation_split(directory, k)

    for gamma in parameter['gamma']:
        for C in parameter['C']:
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

                construct_data(directory, training_set)
                if vector == 'tf-idf':
                    X_train, y_train = create_tf_idf_vector("ML/word_vector.csv")
                elif vector == 'word2vec':
                    X_train, y_train = create_word2vec_vector("ML/word_vector.csv")
                else:
                    raise Exception("Vector conversion type no found!")

                construct_data(directory, validation_set)
                if vector == 'tf-idf':
                    X_val, y_val = create_tf_idf_vector("ML/word_vector.csv")
                elif vector == 'word2vec':
                    X_val, y_val = create_word2vec_vector("ML/word_vector.csv")
                else:
                    raise Exception("Vector conversion type no found!")

                svm = SVC(gamma=gamma, C=C, class_weight={1: 10}, random_state=1)

                score, report = train_model(svm, X_train, X_val, y_train, y_val)
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

            print(f"SVM Model: {svm.get_params()}")
            # print(f"Average Accuracy is: {avg_acc}")

            f = open('svmClassifier.csv', 'a+')
            f.write(f"{C}, {gamma}, {avg_acc}, {avg_precision}, {avg_recall}, {avg_support}\n")
            f.close()
            print("#########################################################")
            print("#########################################################")


def GridSearchRF(directory, vector):
    random.seed(1)

    list_max_features = [300, 250, 200, 150, 100, 50, 40, 30, 20, 10]
    list_n_estimators = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
    list_max_depth = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    list_min_samples_split = [2, 4, 6, 8, 10]


    # cross_validation
    k = 4  # k-fold

    train_test_split = cross_validation_split(directory, k)

    for n in range(25):
        cv_acc = []
        cv_recall = []
        cv_precision = []
        cv_support = []
        cv_total = []

        n_estimators = random.choice(list_n_estimators)
        max_depth = random.choice(list_max_depth)
        min_samples_split = random.choice(list_min_samples_split)
        max_features = random.choice(list_max_features)

        for i in range(len(train_test_split)):
            training_set = []
            validation_set = train_test_split[i]
            training_set += [train_test_split[j] for j in range(k) if j != i]
            training_set = [val for sublist in training_set for val in sublist]

            construct_data(directory, training_set)
            if vector == 'tf-idf':
                X_train, y_train = create_tf_idf_vector("ML/word_vector.csv")
            elif vector == 'word2vec':
                X_train, y_train = create_word2vec_vector("ML/word_vector.csv")
            else:
                raise Exception("Vector conversion type no found!")

            construct_data(directory, validation_set)
            if vector == 'tf-idf':
                X_val, y_val = create_tf_idf_vector("ML/word_vector.csv")
            elif vector == 'word2vec':
                X_val, y_val = create_word2vec_vector("ML/word_vector.csv")
            else:
                raise Exception("Vector conversion type no found!")

            rfr = RandomForestClassifier(
                            n_estimators=n_estimators,
                            max_depth=max_depth,
                            min_samples_split=min_samples_split,
                            max_features=max_features,
                            class_weight='balanced',
                            random_state=1
            )

            score, report = train_model(rfr, X_train, X_val, y_train, y_val)
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

        print(f"Random Forest: {rfr.get_params()}")
        # print(f"Average Accuracy is: {avg_acc}")

        f = open('rfClassifier.csv', 'a+')
        f.write(f"{n_estimators}, "
                f"{max_depth}, "
                f"{min_samples_split}, "
                f"{max_features}, "
                f"{avg_acc}, {avg_precision}, {avg_recall}, {avg_support}\n")
        f.close()
        print("#########################################################")
        print("#########################################################")


def GridSearchLinearSVM(directory, vector):
    parameter = {
        'loss': ['hinge', 'squared_hinge'],
        'C': [0.1, 1, 10],
    }

    # cross_validation
    k = 4  # k-fold

    train_test_split = cross_validation_split(directory, k)

    for loss in parameter['loss']:
        for C in parameter['C']:
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

                construct_data(directory, training_set)
                if vector == 'tf-idf':
                    X_train, y_train = create_tf_idf_vector("ML/word_vector.csv")
                elif vector == 'word2vec':
                    X_train, y_train = create_word2vec_vector("ML/word_vector.csv")
                else:
                    raise Exception("Vector conversion type no found!")

                construct_data(directory, validation_set)
                if vector == 'tf-idf':
                    X_val, y_val = create_tf_idf_vector("ML/word_vector.csv")
                elif vector == 'word2vec':
                    X_val, y_val = create_word2vec_vector("ML/word_vector.csv")
                else:
                    raise Exception("Vector conversion type no found!")

                svm = LinearSVC(loss=loss, C=C, class_weight={1: 10}, random_state=1)

                score, report = train_model(svm, X_train, X_val, y_train, y_val)
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

            print(f"Linear SVM: {svm.get_params()}")
            # print(f"Average Accuracy is: {avg_acc}")

            f = open('linearsvmClassifier.csv', 'a+')
            f.write(f"{loss}, {C}, {avg_acc}, {avg_precision}, {avg_recall}, {avg_support}\n")
            f.close()
            print("#########################################################")
            print("#########################################################")


if __name__ == '__main__':
    # GridSearchDT('data', 'word2vec')
    # GridSearchSVM('data', 'word2vec')
    # GridSearchRF('data', 'word2vec')
    # GridSearchLinearSVM('data', 'word2vec')

    classifiers = [GridSearchDT('data', 'word2vec'),
                  GridSearchSVM('data', 'word2vec'),
                  GridSearchRF('data', 'word2vec'),
                  GridSearchLinearSVM('data', 'word2vec')]

    for classifier in classifiers:
        classifier
        print("\n \n \n")