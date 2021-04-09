#!/usr/bin/env python3
# coding: utf-8

import re, csv, argparse, json, logging, sys

parser = argparse.ArgumentParser(argument_default=False, description="Clean raw lab data and create container for the web app.")
parser.add_argument("--verbose", "-v", action="count", default=0, help="Turn on verbose mode.")
parser.add_argument("--quiet", "-q", action="store_true", help="Only return data but no log messages.")
parser.add_argument("--log", help="Logfile path. If omitted, stdout is used.")
parser.add_argument("--debug", "-d", action="store_true", help="Log all messages including debug.")
parser.add_argument("--results", default="results.csv", help="The location of the sample data CSV.")
parser.add_argument("--ignore", nargs="+", default=["analytical360"], help="Ignore these labs.")
parser.add_argument("--components", default="active_components.json", help="The component metadata file.")
parser.add_argument("--sample-types", default="sample_types.json", help="The sample type metadata file.")
parser.add_argument("--outfile", type=argparse.FileType("w", encoding="utf-8"), default=sys.stdout, help="The file in which to save the generated DB to.")
args = parser.parse_args()

if args.quiet:
    loglevel = 100
elif args.debug:
    loglevel = logging.DEBUG
elif args.verbose:
    loglevel = logging.INFO
else:
    loglevel = logging.WARNING

if args.log:
    logging.basicConfig(filename=args.log, filemode="a", level=loglevel)
else:
    logging.basicConfig(level=loglevel)

logging.debug("Loading configurations . . .")

db_activeComponents = {}
with open(args.components, "r", encoding="utf-8") as activeComponentsJSON:
	activeComponents = json.load(activeComponentsJSON)
for componentType in activeComponents.keys():
	if componentType not in db_activeComponents.keys():
		db_activeComponents[componentType] = []
	for component in activeComponents[componentType]:
		db_component = {
			"id": component["id"],
			"name": component["name"],
			"color": component["color"],
		}
		db_activeComponents[componentType].append(db_component)

with open(args.sample_types, "r", encoding="utf-8") as sampleTypeJSON:
	sample_types = json.load(sampleTypeJSON)

dbContainer = {
	"labs": {},
	"components": db_activeComponents,
}

with open(args.results, "r", encoding="utf-8") as resultsCSV:
	resultsCSV_reader = csv.DictReader(resultsCSV)
	logging.info("Entering main CSV parsing loop . . .")
	for row in resultsCSV_reader:
		if row["Database Identifier"] in args.ignore:
			continue
		elif row["Database Name"] not in dbContainer["labs"]:
			dbContainer["labs"][row["Database Name"]] = {}
		if row["Sample Type"] in sample_types:
			if sample_types[row["Sample Type"]] not in dbContainer["labs"][row["Database Name"]]:
				dbContainer["labs"][row["Database Name"]][sample_types[row["Sample Type"]]] = []
		else:
			continue
		sample_data = {
			"Sample Name": row["Sample Name"]
		}
		for componentType in activeComponents.keys():
			for component in activeComponents[componentType]:
				if component["id"] in row:
					sample_data[component["id"]] = row[component["id"]]
		dbContainer["labs"][row["Database Name"]][sample_types[row["Sample Type"]]].append(
			sample_data
		)

	logging.debug("Finished main loop.")

logging.info("Writing finished structure to file.")
print("db=", end="", file=args.outfile)
print(json.dumps(dbContainer, separators=(",", ":")), file=args.outfile)

print("Done!")
