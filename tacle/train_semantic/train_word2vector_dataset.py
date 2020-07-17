import pandas as pd
from sklearn.utils import shuffle
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from ml_models import train_knn, train_logisticReg, train_naiveBayes, train_decisionTree


def create_dataset():
    df = pd.read_csv("C:/Users/safat/OneDrive/Desktop/Thesis/Ranking_based_automation/sementic-tacle/word_vector.csv",
                     sep=",",
                     lineterminator=":",
                     names=['word', 'root', 'vector', 'template_class'])
    df = shuffle(df, random_state=42)
    df = df.dropna()

    vector = df['vector'].values
    word = df['word'].values
    cls = df['template_class'].values
    vector_file = open('C:/Users/safat/OneDrive/Desktop/Thesis/Ranking_based_automation/sementic-tacle/training/vectors.csv', 'a+')

    for i, v in enumerate(vector):
        # print(f"{type(v)}, {i}, {v}")
        v = v[1:-2]
        vec_list = [number.strip() for number in v.split(" ") if number]
        vec = ",".join(vec_list)
        data_line = f"{vec},{int(cls[i])}\n"
        vector_file.write(data_line)

    vector_file.close()


def explore_data(df):
    print(df['class'].value_counts())
    print(df.groupby('class').mean())
    print(df.dtypes)

    class_mean = df.groupby('class').mean().transpose()
    class_mean.plot()
    plt.show()

    print(df.isna().any())

    X = df.drop('class', axis=1)
    corr = X.corr()
    corr['name'] = [f"vec{i}" for i in range(300)]
    corr = corr.set_index("name")
    print(corr[corr.iloc[:, :] > .7].index.tolist())
    print(corr[corr.iloc[:, :] > .7].columns.tolist())



if __name__ == "__main__":
    # create_dataset()
    column_name = [f"vec{i}" for i in range(300)]
    column_name.append("class")

    df = pd.read_csv("C:/Users/safat/OneDrive/Desktop/Thesis/Ranking_based_automation/sementic-tacle/training/vectors.csv",sep=",", names=column_name)
    explore_data(df)

    # prepare train_test data set for training
    X = df.drop('class', axis=1)
    y = df['class']
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=.3, stratify=y)

    # train_knn(X_train, X_test, y_train, y_test)
    # train_logisticReg(X_train, X_test, y_train, y_test)
    # train_naiveBayes(X_train, X_test, y_train, y_test)
    # train_decisionTree(X_train, X_test, y_train, y_test)






