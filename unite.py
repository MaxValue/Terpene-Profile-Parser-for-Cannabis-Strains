#!/usr/bin/env python3
# coding: utf-8
import argparse, os, csv, json, re

PLACEHOLDER_UNDEFINED = 'NaN'
resulting_database_filename_CSV = 'results.csv'
resulting_database_filename_JSON = 'results.json'

DATA_ROW_FIELDS = [
	'Database',
	'Test Result UID',
	'Sample Name',
	'Sample Type',
	'Receipt Time',
	'Test Time',
	'Post Time',
	'Provider',
	'cis-Nerolidol',
	'trans-Nerolidol',
	'trans-Nerolidol 1',
	'trans-Nerolidol 2',
	'trans-Ocimene',
	'3-Carene',
	'Camphene',
	'Caryophyllene Oxide',
	'Eucalyptol',
	'Geraniol',
	'Guaiol',
	'Isopulegol',
	'Linalool',
	'Ocimene',
	'Terpinolene',
	'alpha-Bisabolol',
	'alpha-Humulene',
	'alpha-Pinene',
	'alpha-Terpinene',
	'beta-Caryophyllene',
	'beta-Myrcene',
	'beta-Ocimene',
	'beta-Pinene',
	'delta-Limonene',
	'gamma-Terpinene',
	'p-Cymene',
	'delta-9 THC-A',
	'delta-9 THC',
	'delta-8 THC',
	'THC-A',
	'THCV',
	'CBN',
	'CBD-A',
	'CBD',
	'delta-9 CBG-A',
	'delta-9 CBG',
	'CBG-A',
	'CBG',
	'CBC',
	'Moisture Content',
]

parser = argparse.ArgumentParser(argument_default=False, description='Unite multiple databases.')
parser.add_argument('databases', default='labs/', help='The path containing the databases to unite.')
parser.add_argument('--verbose', '-v', action='count', default=0, help='Turn on verbose mode.')
parser.add_argument('--json', action='store_true', help='Export as JSON.')
parser.add_argument('--csv', action='store_true', help='Export as CSV.')
parser.add_argument('--placeholder-csv', default='', help='CSV only: The placeholder to use when no value is present.')
args = parser.parse_args()

def log_this(*msg, sep=' ', end='\n', level=3, override=False):
	msg = sep.join([str(x) for x in msg])
	if level <= args.verbose or override:
		if level == 1:
			print('INFO {}'.format(msg), end=end)
		elif level == 2:
			print('DETAIL {}'.format(msg), end=end)
		elif level == 3:
			print('DEBUG {}'.format(msg), end=end)

def write_to_csv(filepath, fieldnames, data):
	if os.path.exists(filepath):
		writeheader = False
	else:
		writeheader = True
	with open(filepath, 'a', encoding='utf-8') as writefile:
		writefile_writer = csv.DictWriter(writefile, fieldnames=fieldnames, restval=args.placeholder_csv, lineterminator='\n')
		if writeheader:
			writefile_writer.writeheader()
		if type(data) != list:
			data = [data]
		for data_row in data:
			writefile_writer.writerow(data_row)

databases_list = sorted(os.listdir(os.path.expanduser(args.databases)))
main_database = {'databases':{}}

missing_files = []
for raw_database_folder_name in databases_list:
	json_database = os.path.join(os.path.expanduser(args.databases),raw_database_folder_name,'results.json')
	csv_database = os.path.join(os.path.expanduser(args.databases),raw_database_folder_name,'results.csv')
	if args.json and not os.path.exists(json_database):
		missing_files.append(json_database)
	if args.csv and not os.path.exists(csv_database):
		missing_files.append(csv_database)
if len(missing_files) != 0:
	log_this('Some required files are missing:', level=1, override=True)
	log_this(*missing_files, sep='\n', level=1, override=True)
	exit()

for raw_database_folder_name in databases_list:
	log_this('#'*80, level=2)
	log_this('Getting database {} now.'.format(raw_database_folder_name), level=2)

	#get database label
	label = raw_database_folder_name.title()

	if args.json:
		json_database_file_name = os.path.join(os.path.expanduser(args.databases),raw_database_folder_name,'results.json')
		with open(json_database_file_name, 'r', encoding='utf-8') as database_file_JSON:
			database_file_reader_JSON =json.load(database_file_JSON)
			database_name = database_file_reader_JSON['name']
			if database_name not in main_database['databases']:
				main_database['databases'][database_name] = {}
			for sample_type in database_file_reader_JSON['samples'].keys():
				if sample_type not in main_database['databases'][database_name]:
					main_database['databases'][database_name][sample_type] = []
				for sample_data in database_file_reader_JSON['samples'][sample_type]:
					for sample_data_field in list(sample_data.keys()):
						remove_key = False
						if sample_data[sample_data_field] == PLACEHOLDER_UNDEFINED:
							remove_key = True
						if sample_data_field not in DATA_ROW_FIELDS:
							remove_key = True
						if remove_key:
							del sample_data[sample_data_field]
					if sample_data != {}:
						main_database['databases'][database_name][sample_type].append(sample_data)

	if args.csv:
		csv_database_file_name = os.path.join(os.path.expanduser(args.databases),raw_database_folder_name,'results.csv')
		with open(csv_database_file_name, 'r', encoding='utf-8') as database_file_CSV:
			database_file_reader_CSV = csv.DictReader(database_file_CSV)
			for sample_data in database_file_reader_CSV:
				sample_data["Database"] = label
				write_to_csv(
					resulting_database_filename_CSV,
					DATA_ROW_FIELDS,
					sample_data
				)

if args.json:
	with open(resulting_database_filename_JSON, 'w', encoding='utf-8') as resulting_database_file_JSON:
		resulting_database_file_JSON.write('databasesContainer=')
		json.dump(main_database, resulting_database_file_JSON, separators=(',', ':'), sort_keys=True)
