import numpy as np
from os.path import join
from os import system


def generate_files(path,prefix,generate_function):
    file_list = []
    system("rm {folder}/*".format(folder=join(path,prefix)))
    for cols in np.arange(10,11,5):
        for rows in np.arange(10,210,10):
            filename = "{prefix}_{rows}_{cols}.csv".format(prefix=prefix,cols=cols,rows=rows)
            full_path = join(path, prefix, filename)
            with open(full_path, "w") as output:
                content = generate_function(cols,rows)
                print(content,file=output)
            file_list.append(full_path)
    return file_list


def generate_ones(cols,rows):
    single_row = ",".join(["1"]*cols)
    multiple_rows = "\n".join([single_row]*rows)
    return multiple_rows


def generate_random(cols,rows):
    def single_row():
        return ",".join(map(lambda x: str(x),np.random.randint(1,1000,cols)))
    multiple_rows = "\n".join([single_row() for x in range(rows)])
    return multiple_rows


def main():
    path_to_CSVs = "../data/csv/synthetic/"
    files_to_execute = []
    files_to_execute += generate_files(path_to_CSVs, "ones", generate_ones)    #comment this line out to run only on random spreadsheets
    files_to_execute += generate_files(path_to_CSVs, "random", generate_random)
    for i,filename in enumerate(files_to_execute):
        if i == 5:
            command = "python3 workflow.py -t {filename}".format(filename=filename)
            print('executing: "{command}"'.format(command=command))
            system(command)
    

if __name__ == "__main__":
    main()
