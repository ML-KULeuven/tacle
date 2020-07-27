import numpy as np
import matplotlib.pyplot as plt

from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import MultinomialNB, GaussianNB
from sklearn.metrics import roc_curve, roc_auc_score, accuracy_score
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import cross_val_score
from sklearn.svm import SVC, LinearSVC
from sklearn.decomposition import PCA


def train_model(classifier, X_train, X_test, y_train, y_test ):
    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("Test set accuracy: {:.2f}".format(acc))
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    return acc, classification_report(y_test, y_pred)


def train_knn(X_train, X_test, y_train, y_test):
    # knn = KNeighborsClassifier(n_neighbors=6)
    # knn.fit(X_train, y_train)
    # print(knn.score(X_test, y_test))

    # Setup arrays to store train and test accuracies
    neighbors = np.arange(1, 9)
    train_accuracy = np.empty(len(neighbors))
    test_accuracy = np.empty(len(neighbors))

    # Loop over different values of k
    for i, k in enumerate(neighbors):
        # Setup a k-NN Classifier with k neighbors: knn
        knn = KNeighborsClassifier(n_neighbors=k)

        # Fit the classifier to the training data
        knn.fit(X_train, y_train)

        # Compute accuracy on the training set
        train_accuracy[i] = knn.score(X_train, y_train)

        # Compute accuracy on the testing set
        test_accuracy[i] = knn.score(X_test, y_test)

    # Generate plot
    plt.title('k-NN: Varying Number of Neighbors')
    plt.plot(neighbors, test_accuracy, label='Testing Accuracy')
    plt.plot(neighbors, train_accuracy, label='Training Accuracy')
    plt.legend()
    plt.xlabel('Number of Neighbors')
    plt.ylabel('Accuracy')
    plt.show()


def train_logisticReg(X_train, X_test, y_train, y_test):
    logreg = LogisticRegression()
    logreg.fit(X_train, y_train)
    y_pred = logreg.predict(X_test)

    # Compute and print the confusion matrix and classification report
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    # Compute predicted probabilities: y_pred_prob
    y_pred_prob = logreg.predict_proba(X_test)[:, 1]

    # Generate ROC curve values: fpr, tpr, thresholds
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_prob)

    # Plot ROC curve
    plt.plot([0, 1], [0, 1], 'k--')
    plt.plot(fpr, tpr)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.show()

    # Compute and print AUC score
    print("AUC: {}".format(roc_auc_score(y_test, y_pred_prob)))


def train_naiveBayes(X_train, X_test, y_train, y_test):
    #mnb = MultinomialNB()
    mnb = GaussianNB()
    mnb.fit(X_train, y_train)
    y_pred = mnb.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    # Compute and print the confusion matrix and classification report
    print("Accuracy:", metrics.accuracy_score(y_test, y_pred))
    print(confusion_matrix(y_test, y_pred))
    print(report)

    return acc, report


def train_decisionTree(X_train, X_test, y_train, y_test):
    # Instantiate a DecisionTreeClassifier 'dt' with a maximum depth of 6
    dt = DecisionTreeClassifier(criterion='gini',
                                random_state=1,
                                class_weight='balanced',
                                max_depth=4,
                                max_features=100)
    dt.fit(X_train, y_train)
    y_pred = dt.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    print("Test set accuracy: {:.2f}".format(acc))
    print(confusion_matrix(y_test, y_pred))
    print(report)

    return acc, report


def train_RandomForest(X_train, X_test, y_train, y_test):
    rfr = RandomForestClassifier(
        n_estimators=80,
        max_depth=20,
        min_samples_split=2,
        max_features=50,
        class_weight='balanced',
        random_state=1
    )
    rfr.fit(X_train, y_train)
    y_pred = rfr.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    print("Test set accuracy: {:.2f}".format(acc))
    print(confusion_matrix(y_test, y_pred))
    print(report)

    return acc, report


def train_weightedSVM(X_train, X_test, y_train, y_test):
    clf_weights = SVC(gamma=0.001, class_weight={1: 10}, C=1)
    clf_weights.fit(X_train, y_train)

    y_pred_weights = clf_weights.predict(X_test)
    acc = accuracy_score(y_test, y_pred_weights)
    report = classification_report(y_test, y_pred_weights)
    print("Test set accuracy: {:.2f}".format(acc))
    print(confusion_matrix(y_test, y_pred_weights))
    print(report)

    return acc, report


def train_LinearSVM(X_train, X_test, y_train, y_test):
    clf_weights = LinearSVC(loss='hinge', C=1, class_weight={1: 10}, random_state=1)
    clf_weights.fit(X_train, y_train)

    y_pred_weights = clf_weights.predict(X_test)
    acc = accuracy_score(y_test, y_pred_weights)
    report = classification_report(y_test, y_pred_weights)

    print("Test set accuracy: {:.2f}".format(acc))
    print(confusion_matrix(y_test, y_pred_weights))
    print(report)

    return acc, report


def plot_svm(X, y, clf, wclf):
    # plot the samples
    plt.scatter(X[:, 0], X[:, 1], c=y, cmap=plt.cm.Paired, edgecolors='k')

    # plot the decision functions for both classifiers
    ax = plt.gca()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # create grid to evaluate model
    xx = np.linspace(xlim[0], xlim[1], 30)
    yy = np.linspace(ylim[0], ylim[1], 30)
    YY, XX = np.meshgrid(yy, xx)
    xy = np.vstack([XX.ravel(), YY.ravel()]).T

    # get the separating hyperplane
    Z = clf.decision_function(xy).reshape(XX.shape)

    # plot decision boundary and margins
    a = ax.contour(XX, YY, Z, colors='k', levels=[0], alpha=0.5, linestyles=['-'])

    # get the separating hyperplane for weighted classes
    Z = wclf.decision_function(xy).reshape(XX.shape)

    # plot decision boundary and margins for weighted classes
    b = ax.contour(XX, YY, Z, colors='r', levels=[0], alpha=0.5, linestyles=['-'])

    plt.legend([a.collections[0], b.collections[0]], ["non weighted", "weighted"],
               loc="upper right")
    plt.show()


def plot_weightedSVM(X_train, X_test, y_train, y_test):
    class_1_index = y_train.index[y_train == 1].tolist()
    class_0_index = y_train.index[y_train == 0].tolist()

    sample_weight_last_ten = [0 for i in range(358)]
    for i in class_1_index:
        sample_weight_last_ten[i] = 0.001

    for i in class_0_index:
        sample_weight_last_ten[i] = 10

    print(sample_weight_last_ten)
    print(len(sample_weight_last_ten))

    sample_weight_last_ten = list(filter(lambda a: a != 0, sample_weight_last_ten))
    print(sample_weight_last_ten)

    print(X_train.shape)
    print(y_train.shape)
    print(len(sample_weight_last_ten))

    pca = PCA(n_components=2)
    X_train = pca.fit_transform(X_train)

    # fit the model
    #clf_weights = SVC(kernel='linear', class_weight={1:10})
    clf_weights = SVC(gamma=1, class_weight={1: 10})
    clf_weights.fit(X_train, y_train)

    #clf_no_weights = SVC(kernel='linear', C=1.0)
    clf_no_weights = SVC(gamma=1)
    clf_no_weights.fit(X_train, y_train)

    plot_svm(X_train, y_train, clf_no_weights, clf_weights)

    y_pred_weights = clf_weights.predict(X_test)
    acc = accuracy_score(y_test, y_pred_weights)
    print("Test set accuracy: {:.2f}".format(acc))
    print(confusion_matrix(y_test, y_pred_weights))
    print(classification_report(y_test, y_pred_weights))

    y_pred_no_weights = clf_no_weights.predict(X_test)
    acc = accuracy_score(y_test, y_pred_no_weights)
    print("Test set accuracy: {:.2f}".format(acc))
    print(confusion_matrix(y_test, y_pred_no_weights))
    print(classification_report(y_test, y_pred_no_weights))

    plt.show()





