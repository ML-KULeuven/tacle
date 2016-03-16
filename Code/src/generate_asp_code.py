from parser import get_groups_tables
from pprint import pprint

def get_group_data(group):
  data   = group.table.data
  bounds = group.bounds 
  return bounds.subset(data)


groups, tables = get_groups_tables("data/examples.csv", "data/examples.groups")
#pprint(groups)
for group in groups:
  print(get_group_data(group))
  break
#pprint(tables)
