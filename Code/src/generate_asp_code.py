from parser import get_groups_tables
from pprint import pprint


groups, tables = get_groups_tables("data/examples.csv", "data/examples.groups")
#pprint(groups)
for group in groups:
# print(group.table.data)
  print(group.get_group_data())
# break
#pprint(tables)
