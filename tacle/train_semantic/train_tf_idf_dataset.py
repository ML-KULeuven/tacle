import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from sklearn.feature_extraction.text import TfidfVectorizer
#from ml_models import train_knn, train_logisticReg, train_naiveBayes, train_decisionTree


def create_tf_idf_vector(file):
    df = pd.read_csv(file,
                     sep=",",
                     lineterminator=":",
                     names=['text', 'root_word', 'vector', 'template_class'])
    df = shuffle(df, random_state=42)
    df = df.dropna()
    df = df.drop('vector', axis=1)

    X = df['text']
    y = df['template_class']


    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=.3, stratify=y)

    tv = TfidfVectorizer(max_features=300)
    X_train = tv.fit_transform(X_train)
    X_train = pd.DataFrame(X_train.toarray(), columns=tv.get_feature_names()).add_prefix('TFIDF_')

    X_test = tv.transform(X_test)
    X_test = pd.DataFrame(X_test.toarray(), columns=tv.get_feature_names()).add_prefix('TFIDF_')

    return X_train, X_test, y_train, y_test
    """
    tv = TfidfVectorizer(max_features=17)
    X = tv.fit_transform(X)
    X = pd.DataFrame(X.toarray(), columns=tv.get_feature_names()).add_prefix('TFIDF_')

    return X, y


if __name__ == '__main__':
    X_train, X_test, y_train, y_test= create_tf_idf_vector("C:/Users/safat/OneDrive/Desktop/Thesis/Ranking_based_automation/sementic-tacle/training/word_vector.csv")

    # train_knn(X_train, X_test, y_train, y_test)
    # train_logisticReg(X_train, X_test, y_train, y_test)
    # train_naiveBayes(X_train, X_test, y_train, y_test)
    train_decisionTree(X_train, X_test, y_train, y_test)