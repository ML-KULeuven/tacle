# TaCle: Tabular Constraint Learner
TaCLe is a constraint learner designed for usage in spreadsheets and tabular data.

## Installation

    pip install tacle
    
## Using TaCLe

### Running TaCLe from command line
TaCLe can be used from command line to analyze a CSV file:

    python -m tacle data/magic_ice_cream.csv
    
This returns a list of constraints in the file:

    ALLDIFFERENT(T2[:, 1])
    ALLDIFFERENT(T1[:, 4])
    ALLDIFFERENT(T1[:, 5])
    ALLDIFFERENT(T1[:, 6])
    T1[:, 1] -> T2[:, 1]
    T1[:, 6] = SUM(T1[:, 3:5], row)

**Filter output**

If you are interested in specific types of constraints, you can filter the output:

    python -m tacle data/magic_ice_cream.csv -f "foreign-key"  # Report only foreign keys
    python -m tacle data/magic_ice_cream.csv -f "<f>"  # Report only formulas -- use <c> for only constraints

**Tables**

To view the tables that TaCLe finds in a file you can run:

    python -m tacle data/magic_ice_cream.csv -t


This returns the tables and blocks found by TaCLe:

    Table T1, (1:9, 0:7)
    Columns 0-2 (string), Columns 2-6 (int), Columns 6-7 (string)
    
    Table T2, (11:15, 0:2)
    Columns 0-1 (string), Columns 1-2 (int)


## Papers
Read more about how TaCLe works in one of our two papers [journal version](https://link.springer.com/article/10.1007/s10994-017-5640-x), [demo paper](https://dl.acm.org/citation.cfm?id=3133193).
