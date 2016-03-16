import csv
import json


class Parser:
	def __init__(self):
		pass

	def parse(self, filename):
		with open(filename, "r") as file:
			reader = csv.reader(file)
			return list(reader)
		# for row in reader:
		# print row


class Bounds:
	def __init__(self, bounds_list):
		self.bounds = bounds_list

	def subset(self, data):
		return data[self.bounds[0] - 1:self.bounds[1]][self.bounds[2] - 1:self.bounds[3]]

	def rows(self):
		return self.bounds[1] - self.bounds[0] + 1

	def columns(self):
		return self.bounds[3] - self.bounds[2] + 1


class Table:
	def __init__(self, data, rows, columns):
		self.data = data
		self.rows = rows
		self.columns = columns


class Group:
	def __init__(self, table, bounds, row):
		self.table = table
		self.bounds = bounds
		self.row = row


def main(csv_file, groups_file):
	parser = Parser()
	data = parser.parse(csv_file)
	tables = {}
	groups = []
	with open(groups_file, "r") as group_file:
		json_data = json.load(group_file)
		for table_description in json_data["Tables"]:
			bounds = Bounds(table_description["Bounds"])
			tables[table_description["Name"]] = Table(bounds.subset(data), bounds.rows(), bounds.columns())
		for group_description in json_data["Groups"]:
			table = tables[group_description["Table"]]
			groups.append(create_group(group_description["Bounds"], table))


def create_group(bounds_list, table):
	if bounds_list[0] == ":":
		return Group(table, Bounds([1, table.rows] + bounds_list[1:3]), False)
	elif bounds_list[2] == ":":
		return Group(table, Bounds(bounds_list[0:2] + [1, table.columns]), True)
	else:
		raise Exception("Could not create group")


def arg_parser():
	import argparse
	p = argparse.ArgumentParser()
	p.add_argument('csv_file')
	p.add_argument('groups_file')
	return p


if __name__ == '__main__':
	main(**vars(arg_parser().parse_args()))
