#!/usr/bin/env python3
# coding: utf-8
import argparse, os, csv, json, re

PLACEHOLDER_UNDEFINED = 'NaN'
resulting_database_filename_CSV = 'results.csv'

DATA_ROW_FIELDS = [
	'Database Identifier',
	'Database Name',
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
parser.add_argument('databases', nargs='?', default='labs/', help='The path containing the databases to unite.')
parser.add_argument('--verbose', '-v', action='count', default=0, help='Turn on verbose mode.')
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

missing_files = []
for raw_database_folder_name in databases_list:
	database_config_file_name = os.path.join(os.path.expanduser(args.databases),raw_database_folder_name,'config.json')
	csv_database = os.path.join(os.path.expanduser(args.databases),raw_database_folder_name,'results.csv')
	if not os.path.exists(database_config_file_name):
		missing_files.append(database_config_file_name)
	if not os.path.exists(csv_database):
		missing_files.append(csv_database)
if len(missing_files) != 0:
	log_this('Some required files are missing:', level=1, override=True)
	log_this(*missing_files, sep='\n', level=1, override=True)
	exit()

for raw_database_folder_name in databases_list:
	log_this('#'*80, level=2)
	log_this('Getting database {} now.'.format(raw_database_folder_name), level=2)

	#get database label and name
	database_config_file_name = os.path.join(os.path.expanduser(args.databases),raw_database_folder_name,'config.json')
	with open(database_config_file_name, 'r', encoding='utf-8') as database_config_file:
		database_config = json.load(database_config_file)
		database_identifier = database_config['identifier']
		database_name = database_config['name']

	csv_database_file_name = os.path.join(os.path.expanduser(args.databases),raw_database_folder_name,'results.csv')
	with open(csv_database_file_name, 'r', encoding='utf-8') as database_file_CSV:
		database_file_reader_CSV = csv.DictReader(database_file_CSV)
		for sample_data in database_file_reader_CSV:
			sample_data["Database Identifier"] = database_identifier
			sample_data["Database Name"] = database_name
			write_to_csv(
				resulting_database_filename_CSV,
				DATA_ROW_FIELDS,
				sample_data
			)
