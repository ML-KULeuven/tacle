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
