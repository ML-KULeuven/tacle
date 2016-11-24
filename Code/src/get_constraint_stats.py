import os
import json

def get_category(filename, categories):
    for key, value in categories.items():
        if filename[:-4] in value:
            return key
    print(filename)
    raise Exception("that shouldn't have happened")

def main():
    folder    = "data/truth/"
    filenames = set(os.listdir(folder)) - set(['examples.txt','fbi_offenses.txt',"columnwise-sum-rows.txt",'exps.txt'])
    with open("data/data.txt", "r") as catetoriesfile:
        categories = json.load(catetoriesfile)
    for filename in filenames:
        with open(folder+filename, "r", encoding="UTF-8") as afile:
            category = get_category(filename,categories)
            print(category)
      #     print(json.load(afile))

if __name__ == "__main__":
    main()
