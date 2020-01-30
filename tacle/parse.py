import csv
from openpyxl import load_workbook


def parse_csv(csv_file):
    data = []
    with open(csv_file) as f:
        csv_reader = csv.reader(f, delimiter=",")
        max_length = 0
        for row in csv_reader:
            max_length = max(max_length, len(row))
            data.append(row)

    # Fill rows to max length
    for i in range(len(data)):
        data[i] += ["" for _ in range(max_length - len(data[i]))]

    return data


def parse_xlx(xlx_file, sheet=None):
    wb = load_workbook(filename=xlx_file)
    if sheet:
        sheet = wb[sheet]
    else:
        sheet = wb.active
    data = list(sheet.values)
    return [["" if v is None else v for v in row] for row in data]


def parse_file(filename: str, sheet=None):
    if filename.endswith(".csv"):
        return parse_csv(filename)
    else:
        return parse_xlx(filename, sheet)
