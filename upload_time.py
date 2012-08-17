#!/usr/bin/env python
import sys
import csv
import re
import json
import urllib2
import requests
from datetime import datetime
from itertools import *

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



def upload_entry_redmine(time, spentOn, comments, serverParams, uploadParams):
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

def upload_entry_jira(time, spentOn, comments, serverParams, uploadParams):
    issueId = re.search(uploadParams["issuePattern"], comments).group(0)
    print "issueId = " + issueId

    worklog = {
        "started": spentOn + "T12:00:00.000-0000",
        "timeSpent" : str(time) + "h",
        "comment": comments
    }
    print worklog

    r = requests.post(serverParams["url"] + "/rest/api/2/issue/" + issueId + "/worklog",
        data = json.dumps(worklog),
        headers = {'Content-Type': 'application/json'},
        auth = (serverParams["username"], serverParams["password"])
    )
    r.raise_for_status()

def upload_entry(time, spentOn, comments, serverParams, uploadParams):
    if serverParams["type"] == "jira":
        upload_entry_jira(time, spentOn, comments, serverParams, uploadParams)
    else:
        upload_entry_redmine(time, spentOn, comments, serverParams, uploadParams)

def process_upload_params(uploadParams):
    if not "issuePattern" in uploadParams and "projectId" in uploadParams:
        uploadParams["projectId"] = json.loads(
            urllib2.urlopen(serverParams["url"] + "/projects/" + uploadParams["projectKey"] + ".json?key=" + serverParams["key"]).read())["project"]["id"]

def upload_time(timeSeq, serverParams, uploadParams):
    process_upload_params(uploadParams)

    entriesByDate = groupby(((entry["When"].split(" ")[0], entry["Description"], entry["When"]) for entry in timeSeq), lambda x : x[0])
    for key, entries in entriesByDate:
        entriesByDesc = groupby(entries, lambda x : x[1])

        for key, entries in entriesByDesc:
            entries = list(entries)
            upload_entry(len(entries) * 0.5, entries[-1][0], entries[-1][1], serverParams, uploadParams)
            uploadParams["lastTime"] = entries[-1][2]


def do_all_uploads(timeFile, configFile):
    with open(configFile) as f:
        config = json.loads(f.read())
    for uploadParams in config["uploads"]:
        try:
            pattern = uploadParams["pattern"] if "pattern" in uploadParams else uploadParams["issuePattern"]

            filteredTime = filter_time(parse_time(timeFile), pattern,
                datetime.strptime(uploadParams["lastTime"], DATE_FORMAT) if "lastTime" in uploadParams else datetime.min)

            upload_time(filteredTime, config["server"], uploadParams)
        finally:
            with open(configFile, "w") as f:
                f.write(json.dumps(config, indent = 4))

if len(sys.argv) < 3:
    sys.exit("Usage: %s <time CSV file from Pomodoro> <JSON config file>" % sys.argv[0])


do_all_uploads(sys.argv[1], sys.argv[2])
