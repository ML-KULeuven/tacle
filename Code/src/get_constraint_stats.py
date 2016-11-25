import os
from collections import defaultdict
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
    stats_absolute              = defaultdict(int)
    stats_fraction_aux          = defaultdict(set)
    number_of_files_in_category = defaultdict(int)
    all_constraints = set()
    all_categories  = set()
    with open("data/data.txt", "r") as catetoriesfile:
        categories = json.load(catetoriesfile)
    for filename in filenames:
        with open(folder+filename, "r", encoding="UTF-8") as afile:
            category    = get_category(filename,categories)
            all_categories.add(category)
            number_of_files_in_category[category] += 1
            raw         = json.load(afile)
            constraints = raw['Essential']
            for key, value in constraints.items():
                print("key",key,"value",value)
                stats_absolute[(category,key)] += 1
                stats_fraction_aux[(category,key)].add(filename)
                all_constraints.add(key)
    stats_fraction = defaultdict(float)
    for (category,key), value in stats_fraction_aux.items():
        stats_fraction[(category,key)] = len(value)/number_of_files_in_category[category]

   #print(stats_absolute)
   #print(stats_fraction)
   #print(number_of_files_in_category)
    
    print("constraint," + ",".join(all_categories))
    for constraint in all_constraints:
        print(constraint, end=",")
        for category in all_categories:
            print("{:.2f}".format(stats_fraction[(category,constraint)]),end=",")
        print()
    
    print("constraint," + ",".join(all_categories))
    for constraint in all_constraints:
        print(constraint, end=",")
        for category in all_categories:
            print(stats_absolute[(category,constraint)],end=",")
        print()




if __name__ == "__main__":
    main()
