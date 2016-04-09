import print_truth
from accuracy import files, main, CategoryCounter, is_excel_constraint
from no_stdout import no_stdout

with no_stdout():
    counters = main()
for i in range(len(files)):
    counter = counters["essential constraints"][i]
    if len(list(CategoryCounter.filter_constraints(counter.not_present, is_excel_constraint))) > 0:
        print(files[i])
        print_truth.main(files[i])
        print()
