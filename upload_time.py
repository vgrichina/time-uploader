import csv

def parse_time(csvFile):
	reader = csv.reader(open(csvFile, "r"))
	i = 0
	for row in reader:
		if i == 2:
			columnNames = row
			firstRow = False
		if i > 3:
			yield { name: value for name, value in zip(columnNames, row)}

		i += 1


for t in parse_time("time.txt"):
	print t