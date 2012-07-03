import csv
import re
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d %H:%M:%S +0000"

def parse_time(csvFile):
	reader = csv.reader(open(csvFile, "r"), skipinitialspace = True)
	i = 0
	for row in reader:
		if i == 2:
			columnNames = row
			firstRow = False
		if i > 3:
			yield { name: value for name, value in zip(columnNames, row)}

		i += 1


def filter_time(timeSeq, pattern, startTime):
	for entry in timeSeq:
		if re.match(pattern, entry["Description"]):
			whenTime = datetime.strptime(entry["When"], DATE_FORMAT)	
			if whenTime >= startTime:
				yield entry

for t in filter_time(parse_time("time.txt"), ".*Reader.*", datetime.strptime("2012-05-30 13:59:58 +0000", DATE_FORMAT)):
	print t