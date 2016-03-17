from enum import Enum


class Bounds:
	def __init__(self, bounds_list):
		self.bounds = bounds_list

	def subset(self, data):
		top_row = self.bounds[0] - 1
		bottom_row = self.bounds[1]
		left_column = self.bounds[2] - 1
		right_column = self.bounds[3]
		return data[top_row:bottom_row, left_column:right_column]

	def rows(self):
		return self.bounds[1] - self.bounds[0] + 1

	def columns(self):
		return self.bounds[3] - self.bounds[2] + 1

	def __repr__(self):
		return str(self.bounds)


class Table:
	def __init__(self, data, rows, columns):
		self.data = data
		self.rows = rows
		self.columns = columns

	def __repr__(self):
		repr_str = "Data: " + str(self.data) + " Rows: " + str(self.rows) + " Column: " + str(self.columns)
		return repr_str


class GType(Enum):
	int = 0
	float = 1
	string = 2


class Group:
	def __init__(self, table, bounds, row):
		self.table = table
		self.bounds = bounds
		self.row = row
		self.data = self._get_group_data()
		self.dtype = self.infer_type()

	def __repr__(self):
		repr_str = "Table: " + str(self.table) + " Bounds: " + str(self.bounds) + " Row: " + str(self.row)
		return repr_str

	def _get_group_data(self):
		data = self.table.data
		bounds = self.bounds
		return bounds.subset(data)

	def get_group_data(self):
		return self.data

	@staticmethod
	def _infer_type_scalar(val):
		try:
			val = int(val)
			return 0
		except:
			try:
				val = float(val)
				return 1
			except:
				return 2

	def infer_type(self):
		flat = self.data.flatten()
		dtype = max(list(map(self._infer_type_scalar, flat)))
		if dtype == 0:
			return GType.int
		if dtype == 1:
			return GType.float
		else:
			return GType.string

	def length(self):
		return self.bounds.columns() if self.row else self.bounds.rows()

	def columns(self):
		return self.bounds.columns()

	def rows(self):
		return self.bounds.rows()
