import csv
import re
import json
import urllib2
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


def filter_time(timeSeq, pattern, lastTime):
	for entry in timeSeq:
		if re.match(pattern, entry["Description"]):
			whenTime = datetime.strptime(entry["When"], DATE_FORMAT)	
			if whenTime > lastTime:
				yield entry

def upload_entry(time, spentOn, comments, serverParams, uploadParams):
	print json.dumps({
			"project_id": uploadParams["projectId"],
			"spent_on": spentOn,
			"hours": time,
			"activity_id": uploadParams["activityId"],
			"comments": comments
		})
	req = urllib2.Request(serverParams["url"] + "/time_entries.json",
		json.dumps({
			"time_entry": {
				"project_id": uploadParams["projectId"],
				"spent_on": spentOn,
				"hours": time,
				"activity_id": uploadParams["activityId"],
				"comments": comments
			}
		}),
		{'Content-Type': 'application/json', "X-Redmine-API-Key": serverParams["key"]}
	)
	res = urllib2.urlopen(req)
	res.close()

def upload_time(timeSeq, serverParams, uploadParams):
	if not "projectId" in uploadParams:
		uploadParams["projectId"] = json.loads(
			urllib2.urlopen(serverParams["url"] + "/projects/" + uploadParams["projectKey"] + ".json?key=" + serverParams["key"]).read())["project"]["id"]
	for entry in timeSeq:
		# TODO: Grouping
		upload_entry(0.5, entry["When"].split(" ")[0], entry["Description"], serverParams, uploadParams)

		uploadParams["lastTime"] = entry["When"]


def do_all_uploads(timeFile, configFile):
	with open(configFile) as f:
		config = json.loads(f.read())
	for uploadParams in config["uploads"]:
		try:
			filteredTime = filter_time(parse_time(timeFile), uploadParams["pattern"],
				datetime.strptime(uploadParams["lastTime"], DATE_FORMAT) if "lastTime" in uploadParams else datetime.min)

			upload_time(filteredTime, config["server"], uploadParams)
		finally:
			with open(configFile, "w") as f:
				f.write(json.dumps(config, indent = 4))

do_all_uploads("time.txt", "upload_time.json")