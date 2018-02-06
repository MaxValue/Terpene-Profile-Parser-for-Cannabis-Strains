#!/usr/bin/env python3
# coding: utf-8
#
"""
TODO:
sample type
fix terpene parsing

get list of files
for each file
	get raw terpenes
	parse terpenes
	add to database


"""
import re, os, csv, argparse
from lxml import html

parser = argparse.ArgumentParser(description="Clean raw weed data.")
parser.add_argument("database", nargs='?', default="database_dump/", help="The location of the database dump.")
parser.add_argument("-d", "--debug", action="store_true", help="Turns on debug mode.")
args = parser.parse_args()

def log_this(msg):
	if args.debug:
		print(msg)

log_this("Loading configurations . . .")

RAW_DATABASE_DUMP_PATH = args.database

terpene_names = [
	"Linalool",
	"Caryophyllene oxide",
	"Myrcene",
	"beta-Pinene",
	"Limonene",
	"Terpinolene",
	"alpha-Pinene",
	"Humulene",
	"Caryophyllene",
	"TERPENE-TOTAL"
]

# Matches strings like "   <    343459.30032   %    Limonene    "
# re_terpen = re.compile(r"^<?\s*(?P<percentage>\d+(.\d+)?)\s*%\s*(?P<name>[-\s\w]+?)\s*$", re.IGNORECASE)
re_terpen = re.compile(r"^\s*(?P<percentage>(<|>)?\s*\d+(\.\d+)?)\s*%\s*(?P<name>("+r"|".join(terpene_names)+r"))\s*$", re.IGNORECASE)

# Matches strings like: "    Test   Result     UID    :    jfkgbnFGBFG34394129_fkgljh345_345dfgdg    "
re_sample_id = re.compile(r"^\s*Test\s*Result\s*UID\s*:?\s*(?P<uid>\w+)\s*$", re.IGNORECASE)
# Matches strings like: "   Date   Tested   "
re_sample_time_europe = re.compile(r"^\s*Date\s*(Test[a-zA-Z_]*\s*)?:?\s*(?P<date>\s*(?P<day>(0?[0-9]|1[0-9]|3[0-1]))\s*[-\./:]?\s*(?P<month>(0?[0-9]|1[0-2]))\s*[-\./:]?\s*(?P<year>2\d{3}))\s*$", re.IGNORECASE)
re_sample_time_trumpland = re.compile(r"^\s*Date\s*(Test[a-zA-Z_]*\s*)?:?\s*(?P<date>\s*(?P<month>(0?[0-9]|1[0-2]))\s*[-\./:]?\s*(?P<day>(0?[0-9]|1[0-9]|3[0-1]))\s*[-\./:]?\s*(?P<year>2\d{3}))\s*$", re.IGNORECASE)
re_sample_time_intl = re.compile(r"^\s*Date\s*(Test[a-zA-Z_]*\s*)?:?\s*(?P<date>\s*(?P<year>2\d{3})\s*[-\./:]?\s*(?P<month>(0?[0-9]|1[0-2]))\s*[-\./:]?\s*(?P<day>(0?[0-9]|1[0-9]|3[0-1])))\s*$", re.IGNORECASE)
# Finds the text of the first header in the page content:
xpath_sample_name = """//div[@class='maincontent']/*[
													self::h1
													or self::h2
													or self::h3
													or self::h4
													or self::h5
													or self::h6
												][1]/text()"""

# Finds text of all headers which text content starts with the words "available from", ignoring the case
xpath_sample_vendor = """//div[@class='maincontent']//*[
													self::h1
													or self::h2
													or self::h3
													or self::h4
													or self::h5
													or self::h6
												][
													starts-with(
																translate(
																			normalize-space(text()),
																			'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
																			'abcdefghijklmnopqrstuvwxyz'
																),
																'available from'
													)
												]/following-sibling::*//a/text()"""

# Finds text of all headers which text content starts with the words "test result uid", ignoring the case
xpath_sample_id = """//div[@class='maincontent']/*[
													self::h1
													or self::h2
													or self::h3
													or self::h4
													or self::h5
													or self::h6
												][
													starts-with(
																translate(
																			normalize-space(text()),
																			'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
																			'abcdefghijklmnopqrstuvwxyz'
																),
																'test result uid'
													)
												]/text()"""

# Finds text of all headers which text content starts with the words "date", ignoring the case
xpath_sample_time = """//div[@class='maincontent']/*[
													self::h1
													or self::h2
													or self::h3
													or self::h4
													or self::h5
													or self::h6
												][
													starts-with(
																translate(
																			normalize-space(text()),
																			'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
																			'abcdefghijklmnopqrstuvwxyz'
																),
																'date'
													)
												]/text()"""

# Finds text of all list items which are preceeded by the words "terpen" and "profil", ignoring the case
xpath_raw_terpenes = """//*[
								contains(
										translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
										'terpen'
								)
								and contains(
										translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
										'profil'
								)
							]/following-sibling::*[1]//li//text()"""

sample_database = {}
non_uid_samples_counter = 0
non_name_samples_counter = 0
non_time_samples_counter = 0
non_provider_samples_counter = 0
non_percentage_terpene_profiles = 0
europe = 0
trump = 0
intl = 0

log_this("Loading file list . . .")

#os.chdir(os.path.expanduser(RAW_DATABASE_DUMP_PATH))
#file_list = os.walk(os.getcwd()).__next__()[2]
file_list = os.walk(os.path.expanduser(RAW_DATABASE_DUMP_PATH)).__next__()[2]

print("Before we start, a heads up:",
		"I will try to extract any Terpene Profiles present as exact as possible. Samples with ppm or mg units are skipped.",
		"If i don't find a suitable terpene profile or none at all, i will INFOrm you.",
		"If one Terpene is present multiple times, i will take the first occurence and print an ERROR.",
		"If a Terpene is missing from the Terpene profile, i will not know it and say nothing.",
		"If the Test UID could not be extracted i will make one up and print an ERROR.",
		"If the sample name could not be extracted i will use the UID as name and print an ERROR.",
		"If the Test Date could not be extracted i will make one up and print an ERROR.",
		"If the producer of the sample could not be extracted i will make one up and print an ERROR.",
		"Please contact me if you wish this to be different or change the code yourself.",
		sep="\n")
if input("\nDo you want to start? (y/n) ") != "y":
	exit("Aborted.")

log_this("Creating database file . . .")

with open("non_vendor_samples.txt", "w", encoding="utf-8") as non_vendor_samples_file:
	non_vendor_samples_file_writer = csv.DictWriter(non_vendor_samples_file, fieldnames=["Filename"],lineterminator="\n")
	non_vendor_samples_file_writer.writeheader()
	with open("non_date_samples.txt", "w", encoding="utf-8") as non_time_samples_file:
		non_time_samples_file_writer = csv.DictWriter(non_time_samples_file, fieldnames=["Filename"],lineterminator="\n")
		non_time_samples_file_writer.writeheader()
		with open("non_name_samples.txt", "w", encoding="utf-8") as non_name_samples_file:
			non_name_samples_file_writer = csv.DictWriter(non_name_samples_file, fieldnames=["Filename","Replacement Name"],lineterminator="\n")
			non_name_samples_file_writer.writeheader()
			with open("non_uid_samples.txt", "w", encoding="utf-8") as non_uid_samples_file:
				non_uid_samples_file_writer = csv.DictWriter(non_uid_samples_file, fieldnames=["Filename","Replacement UID"],lineterminator="\n")
				non_uid_samples_file_writer.writeheader()
				with open("results.csv", "w", encoding="utf-8") as sample_database_file:
					sample_database_writer = csv.DictWriter(sample_database_file, fieldnames=["Test Result UID","Test Result Name","Test Result Date","Provider"]+terpene_names,lineterminator="\n")
					sample_database_writer.writeheader()
					log_this("Entering main loop . . .")
					for raw_sample_file_name in file_list:
						log_this("#"*80)

						log_this("Parsing sample file {} now.".format(raw_sample_file_name))
						#DEBUG: response = requests.get('http://archive.analytical360.com/m/archived/144582')
						with open(os.path.join(os.path.expanduser(RAW_DATABASE_DUMP_PATH),raw_sample_file_name),encoding="utf-8") as raw_sample_file:
							tree = html.fromstring(raw_sample_file.read())
							#DEBUG: tree = html.fromstring(response.content)

						for sample_id_candidate in tree.xpath(xpath_sample_id):
							re_sample_id_match = re_sample_id.match(sample_id_candidate)
							if re_sample_id_match:
								sample_id = re_sample_id_match.group("uid")
								log_this("Has UID {}.".format(sample_id))
								break
						else:
							non_uid_samples_counter += 1
							sample_id = "MAX{:0>15}".format(non_uid_samples_counter)
							non_uid_samples_file_writer.writerow({"Filename":raw_sample_file_name,"Replacement UID":sample_id})
							log_this("ERROR: Did not find an UID for this sample! I will use {}.".format(sample_id))

						raw_sample_name = tree.xpath(xpath_sample_name)
						if len(raw_sample_name) == 0:
							non_name_samples_counter += 1
							sample_name = sample_id
							non_name_samples_file_writer.writerow({"Filename":raw_sample_file_name,"Replacement Name":sample_name})
							log_this("ERROR: Did not find a name for this sample! I will use {}.".format(sample_name))
						else:
							sample_name = raw_sample_name[0]
							log_this("Has sample name {}.".format(sample_name))

						found_time = False
						raw_sample_time = tree.xpath(xpath_sample_time)
						if not len(raw_sample_time) == 0:
							re_sample_time_trumpland_match = re_sample_time_trumpland.match(raw_sample_time[0])
							re_sample_time_europe_match = re_sample_time_europe.match(raw_sample_time[0])
							re_sample_time_intl_match = re_sample_time_intl.match(raw_sample_time[0])
							if re_sample_time_trumpland_match:
								found_time = True
								trump += 1
								sample_time = "{year}-{month:0>2}-{day:0>2}".format(year=re_sample_time_trumpland_match.group("year"),month=re_sample_time_trumpland_match.group("month"),day=re_sample_time_trumpland_match.group("day"))
							elif re_sample_time_europe_match:
								found_time = True
								europe += 1
								sample_time = "{year}-{month:0>2}-{day:0>2}".format(year=re_sample_time_europe_match.group("year"),month=re_sample_time_europe_match.group("month"),day=re_sample_time_europe_match.group("day"))
							elif re_sample_time_intl_match:
								found_time = True
								intl += 1
								sample_time = "{year}-{month:0>2}-{day:0>2}".format(year=re_sample_time_intl_match.group("year"),month=re_sample_time_intl_match.group("month"),day=re_sample_time_intl_match.group("day"))
						if not found_time:
							non_time_samples_counter += 1
							sample_time = "1970-04-20"
							non_time_samples_file_writer.writerow({"Filename":raw_sample_file_name})

						#provider
						raw_sample_provider = tree.xpath(xpath_sample_vendor)
						if len(raw_sample_provider) == 0:
							non_provider_samples_counter += 1
							sample_provider = "United States Government"
							non_vendor_samples_file_writer.writerow({"Filename":raw_sample_file_name})
							log_this("ERROR: No provider found for {}.".format(raw_sample_file_name))
						else:
							sample_provider = raw_sample_provider[0].strip()
							log_this("Sample provided by {}.".format(sample_provider))

						sample_data = {"Test Result UID":sample_id,"Test Result Name":sample_name,"Test Result Date":sample_time,"Provider":sample_provider}

						# found_terpen = False
						# raw_terpenes = tree.xpath(xpath_raw_terpenes)
						# if not len(raw_terpenes) == 0:
						# 	for raw_terpen in raw_terpenes:
						# 		re_terpen_match = re_terpen.match(raw_terpen)
						# 		if re_terpen_match:
						# 			found_terpen = True
						# 			normalized_name = re_terpen_match.group("name") # TODO: we could do levenshtein- and typewriterdistance (en-US) here
						# 			log_this("Found terpene {}!".format(normalized_name))
						# 			if normalized_name in sample_data:
						# 				log_this("ERROR: Data regarding terpene {} is already in recorded for sample {}. Skipping.".format(normalized_name,sample_id))
						# 			else:
						# 				sample_data[normalized_name] = re_terpen_match.group("percentage")
						# 		else:
						# 			log_this("ERROR: Terpene candidate {candidate} of sample file {filename} having sample UID {uid} did NOT match known/expected terpene names!".format(candidate=raw_terpen,filename=raw_sample_file_name,uid=sample_id))


						# 	log_this("INFO: Did not find Terpene Profile Data for sample file {filename} having sample UID {uid}.".format(filename=raw_sample_file_name,uid=sample_id))

						# if not found_terpen and not set(terpene_names).issubset(set(sample_data.keys())):
						# 	non_percentage_terpene_profiles += 1
						# 	log_this("Saving UID {} to database file.".format(sample_id))
						# 	sample_database_writer.writerow(sample_data)
						# else:

print("Results:",
	"parsed {} files.".format(len(file_list)),
	"{} samples did not have UID.".format(non_uid_samples_counter),
	"{} samples did not have a name.".format(non_name_samples_counter),
	"{} samples did not have a date.".format(non_time_samples_counter),
	#"{} samples did use american dates.".format(trump),
	#"{} samples did use european dates.".format(europe),
	#"{} samples did use international dates.".format(intl),
	"{} samples did not have percentage values for terpenes or no terpene profile at all.".format(non_percentage_terpene_profiles),
	sep="\n")
log_this("All files have been processed. Please check for any lines starting with 'ERROR: '. Those couldn't be parsed correctly. Sorry for that.")
log_this("Also, note the lines starting with 'INFO: '.")
log_this("Keep vaping ;)")
