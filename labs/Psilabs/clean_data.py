#!/usr/bin/env python3
# coding: utf-8
#
'''
TODO:
test metadata
Normalization:
	cannabinoids total
	sample type
	test metadata

use skip_this_file more
'''
DATA_ROW_FIELDS = [
	'Test Result UID',
	'Sample Name',
	'Sample Type',
	'Receipt Time',
	'Test Time',
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
import re, os, csv, argparse, json, urllib, datetime
from lxml import html
from lxml import etree
import dateparser.search as dateparser_search

parser = argparse.ArgumentParser(argument_default=False, description='Clean raw lab data.')
parser.add_argument('database', nargs='?', default='downloader/database_dump/', help='The location of the database dump.')
parser.add_argument('--verbose', '-v', action='count', default=0, help='Turn on verbose mode.')
parser.add_argument('--json', action='store_true', help='Export as JSON.')
parser.add_argument('--csv', action='store_true', help='Export as CSV.')
group_logType = parser.add_mutually_exclusive_group()
group_logType.add_argument('--log-csv', default=True, action='store_true', help='Write logs to CSV.')
group_logType.add_argument('--log-html', default=False, action='store_true', help='Write logs to HTML.')
parser.add_argument('--no-cleanup', action='store_true', help='Do not delete existing result files (logs included).')
parser.add_argument('--no-logfiles', action='store_true', help='Do not create log files for logging errors.')
parser.add_argument('--force-terpenes', action='store_true', help='Skip all samples without a terpene profile.')
parser.add_argument('--force-cannabinoids', action='store_true', help='Skip all samples without a cannabinoid profile.')
parser.add_argument('--placeholder-csv', default='', help='CSV only: The placeholder to use when no value is present.')
args = parser.parse_args()

def get_single_value(tree, xpath, fallback=None, fallback_file=False, fallback_data={}, join_multi=False):
	raw_value = tree.xpath(xpath)
	if len(raw_value) == 1:
		if type(raw_value[0]) == str or type(raw_value[0]) == etree._ElementUnicodeResult:
			return raw_value[0].strip()
		else:
			return raw_value[0]
	else:
		if join_multi == False:
			if fallback_file:
				write_to_logfile(
					filepath=fallback_file,
					fieldnames=sorted(fallback_data.keys()),
					data=fallback_data
				)
			return fallback
		else:
			if type(join_multi) == str:
				return join_multi.join(raw_value).strip()
			else:
				return ''.join(raw_value).strip()

def normalize_number(numberstring, base=10, comma=False, separator=False, compress=False):
	dots = numberstring.count('.')
	commas = numberstring.count(',')
	# multiple = more than 1
	# single = 1
	# zero = 0
	## multiple commas, multiple dots:		ERROR
	if commas > 1 and dots > 1:
		raise ValueError("could not convert string to float: '{}'".format(numberstring))
	# AMERICAN
	## multiple commas, single dot:			remove commas, float
	## multiple commas, zero dots:			remove commas, float (int)
	## no commas, single dot:				float
	if (commas > 1 and dots <= 1) or (commas == 0 and dots == 1):
		decimal = '.'
	# EUROPEAN
	## single comma, multiple dots:			remove dots, float
	## zero commas, multiple dots:			remove dots, float (int)
	## single comma, no dots:				float
	if (dots > 1 and commas <= 1) or (dots == 0 and commas == 1):
		decimal = ','
	numberstring = re.sub(r'[^0-9{}]'.format(decimal), '', numberstring)
	numberstring = numberstring.replace(decimal, '.')
	result = float(numberstring)
	if compress:
		if result == '0.0':
			return '0'
		elif result.startswith('0.'):
			return result[1:]
	return result

def csv_escape(data):
	return '"{}"'.format(data)

def log_this(*msg, sep=' ', end='\n', level=3, override=False):
	msg = sep.join([str(x) for x in msg])
	if level <= args.verbose or override:
		if level == 1:
			print('INFO {}'.format(msg), end=end)
		elif level == 2:
			print('DETAIL {}'.format(msg), end=end)
		elif level == 3:
			print('DEBUG {}'.format(msg), end=end)

def write_to_logfile(filepath, fieldnames, data, title=False, override=False):
	if (not args.no_logfiles) or override:
		if args.log_csv:
			write_to_csv(
				filepath=filepath+'.csv',
				fieldnames=fieldnames,
				data=data
			)
		elif args.log_html:
			write_to_html(
				filepath=filepath+'.html',
				fieldnames=fieldnames,
				data=data,
				title=title
			)

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

def write_to_html(filepath, fieldnames, data, title=False):
	if os.path.exists(filepath):
		template_filepath = filepath
		writeheader = False
	else:
		template_filepath = 'template.html'
		writeheader = True
	with open(template_filepath, 'r', encoding='utf-8') as template_file:
		tree = html.fromstring(template_file.read())
	table = tree.get_element_by_id('results')
	if 'Filename' in fieldnames:
		pass
		fieldnames.insert(fieldnames.index('Filename')+1, 'Analytical360')
	if writeheader:
		if title:
			table.xpath('caption')[0].text = str(title)
			tree.get_element_by_id('title').text = str(title)
		row_header = table.xpath('thead/tr')[0]
		for fieldname in fieldnames:
			fieldname_element = etree.Element('th')
			fieldname_element.text = str(fieldname)
			row_header.append(fieldname_element)
	tbody = table.xpath('tbody')[0]
	if type(data) != list:
		data = [data]
	for data_row in data:
		row_body = etree.Element('tr')
		for fieldname in fieldnames:
			fieldname_element = etree.Element('td')
			if fieldname in data_row:
				if fieldname == 'Filename':
					link = etree.Element('a')
					link.attrib['href'] = 'file://{}'.format(os.path.join(os.getcwd(),args.database,data_row[fieldname]))
					link.text = data_row[fieldname]
					fieldname_element.append(link)
				else:
					fieldname_element.text = str(data_row[fieldname])
			else:
				if fieldname == 'Analytical360' and 'Filename' in data_row:
					link = etree.Element('a')
					link.attrib['href'] = online_URL
					link.text = 'Analytical360'
					fieldname_element.append(link)
				else:
					#fieldname_element.text = ''
					pass
			row_body.append(fieldname_element)
		tbody.append(row_body)
	with open(filepath, 'wb') as writefile:
		writefile.write(html.tostring(tree))

def test_match(xpath_here):
	matches = tree.xpath(xpath_here)
	if len(matches) > 0:
		log_this('match!', level=3, override=True)
	for i in matches:
		log_this('tag: {}'.format(i.tag), level=3, override=True)
		log_this('attribs: {}'.format(i.attrib), level=3, override=True)

log_this('Loading configurations . . .', level=1)

xpath_provider_page = """"""

xpath_festival_page = """"""

# Finds the list items of the terpene test
xpath_terpenes_1 =				'/html/body/ui-view/div/md-content/ui-view/div/md-content/div/md-card[@ng-if="Sample.details.terpeneTestComplete"]/div/div/md-table-container/table[thead/tr[th[1][text()="Terpene"]][th[2][text()="Amount"]]]/tbody/tr'

# Finds the amount of total terpenes present in the sample
xpath_terpenes_total =			'/html/body/ui-view/div/md-content/ui-view/div/md-content/div/md-card[@ng-if="Sample.details.terpeneTestComplete"]/md-card-header/md-card-header-text/span[text()=" Total Terpenes "]/preceding-sibling::span[@class="md-title"]/text()'

# Finds the list items of the cannabinoid test
xpath_cannabinoids_1 =			'/html/body/ui-view/div/md-content/ui-view/div/md-content/div/md-card[@ng-if="Sample.details.potencyTestComplete"]/div/div/md-table-container/table[thead/tr[th[1][text()="Cannabinoid"]][th[2][text()="Amount"]][th[3][text()="Uncertainty"]]]/tbody/tr'

# Finds the amount of total THC present in the sample
xpath_thc_total =				'/html/body/ui-view/div/md-content/ui-view/div/md-content/div/md-card[@ng-if="Sample.details.potencyTestComplete"]/md-card-header/md-card-header-text/span[text()="Total THC"][@ng-show="Sample.details.totalTHC"]/preceding-sibling::span[1][@ng-show="Sample.details.totalTHC"]/text()'

# Finds the amount of total CBD present in the sample
xpath_cbd_total =				'/html/body/ui-view/div/md-content/ui-view/div/md-content/div/md-card[@ng-if="Sample.details.potencyTestComplete"]/md-card-header/md-card-header-text/span[text()="Total CBD"][@ng-show="Sample.details.totalCBD"]/preceding-sibling::span[1][@ng-show="Sample.details.totalCBD"]/text()'

# Finds the type of the sample
xpath_sample_type =				'/html/body/ui-view/div/md-content/ui-view/div/md-content/div[1]/md-card[1]/md-card-header/md-card-header-text/span[1][following-sibling::span[1][@class="md-title"]]/text()'

# Finds the name of the sample
xpath_sample_name =				'/html/body/ui-view/div/md-content/ui-view/div/md-content/div[1]/md-card[1]/md-card-header/md-card-header-text/span[@class="md-title"]/text()'

# Finds the provider of the sample
xpath_sample_provider =			'/html/body/ui-view/div/md-content/ui-view/div/md-content/div[1]/md-card[1]/md-card-header/md-card-header-text/span[@class="md-subhead"][@ng-if="Sample.details.clientInformation.clientId"]/a/text()'
xpath_sample_provider_anon =	'/html/body/ui-view/div/md-content/ui-view/div/md-content/div[1]/md-card[1]/md-card-header/md-card-header-text/span[@class="md-subhead"][@ng-if="!Sample.details.clientInformation.clientId"]/text()'

xpath_test_uid = """/html/body/ui-view/div/md-content/ui-view/div/md-content/div/md-card/md-card-content/a[
						starts-with(
							translate(
								normalize-space(@href),
								'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
								'abcdefghijklmnopqrstuvwxyz'
							),
							'/results/samples/edit/'
						)
					]/@href"""

# Finds the timestamp of the test of the sample
xpath_time_tested =				'/html/body/ui-view/div/md-content/ui-view/div/md-content/div[2]/md-card[1]/md-card-content/md-list/md-list-item/span/h3[following-sibling::p[text()="Date Tested"]]/text()'
# Finds the timestamp of receipt of the sample
xpath_time_received =			'/html/body/ui-view/div/md-content/ui-view/div/md-content/div[2]/md-card[1]/md-card-content/md-list/md-list-item/span/h3[following-sibling::p[text()="Date Received"]]/text()'

terpenes = {
	'3-Carene':				re.compile(r'^(3|Three|Tri)[-_/\s.]*Carene$',					re.IGNORECASE),
	'Camphene':				re.compile(r'^Camphene$',										re.IGNORECASE),
	'Caryophyllene Oxide':	re.compile(r'^Caryophyllene[-_/\s.]*Oxide$',					re.IGNORECASE),
	'Eucalyptol':			re.compile(r'^Eucalyptol$',										re.IGNORECASE),
	'Farnesene': 			re.compile(r'^Farnesene$',										re.IGNORECASE),
	'Geraniol':				re.compile(r'^Geraniol$',										re.IGNORECASE),
	'Guaiol':				re.compile(r'^Guaiol$',											re.IGNORECASE),
	'Isopulegol':			re.compile(r'^Isopulegol$',										re.IGNORECASE),
	'Linalool':				re.compile(r'^Linalool$',										re.IGNORECASE),
	'Ocimene':				re.compile(r'^Ocimene$',										re.IGNORECASE),
	'Terpinolene':			re.compile(r'^Terpinolene$',									re.IGNORECASE),
	'alpha-Bisabolol':		re.compile(r'^(alpha|A|α)[-_/\s.]*Bisabolol$',					re.IGNORECASE),
	'alpha-Humulene':		re.compile(r'^(alpha|A|α)?[-_/\s.]*Humulene$',					re.IGNORECASE),
	'alpha-Pinene':			re.compile(r'^(alpha|A|α)[-_/\s.]*Pinene$',						re.IGNORECASE),
	'beta-Pinene':			re.compile(r'^(beta|B|β)[-_/\s.]*Pinene$',						re.IGNORECASE),
	'alpha-Terpinene':		re.compile(r'^(alpha|A|α)[-_/\s.]*Terpinene$',					re.IGNORECASE),
	'beta-Caryophyllene':	re.compile(r'^(beta|B|β)?[-_/\s.]*Caryophyllene$',				re.IGNORECASE),
	'beta-Myrcene':			re.compile(r'^(beta|B|β)?[-_/\s.]*Myrcene$',					re.IGNORECASE),
	'beta-Ocimene':			re.compile(r'^(beta|B|β)[-_/\s.]*Ocimene$',						re.IGNORECASE),
	'cis-Nerolidol':		re.compile(r'^(cis)[-_/\s.]*Nerolidol$',						re.IGNORECASE),
	'delta-Limonene':		re.compile(r'^(delta|D|δ)?[-_/\s.]*Limonene$',					re.IGNORECASE),
	'gamma-Terpinene':		re.compile(r'^(gamma|G|Y|γ)[-_/\s.]*Terpinene$',				re.IGNORECASE),
	'p-Cymene':				re.compile(r'^(p)[-_/\s.]*Cymene$',								re.IGNORECASE),
	'trans-Nerolidol':		re.compile(r'^(trans)[-_/\s.]*Nerolidol$',						re.IGNORECASE),
	'trans-Nerolidol 1':	re.compile(r'^(trans)[-_/\s.]*Nerolidol[-_/\s.]*1$',			re.IGNORECASE),
	'trans-Nerolidol 2':	re.compile(r'^(trans)[-_/\s.]*Nerolidol[-_/\s.]*2$',			re.IGNORECASE),
	'trans-Ocimene':		re.compile(r'^(trans)[-_/\s.]*Ocimene$',						re.IGNORECASE),
}
terpenes['Terpene TOTAL'] = re.compile(r'^(Terpene[-_/\s.]*TOTAL|Total[-_/\s.]*[-_/\s.]*Terpenes)',re.IGNORECASE)

cannabinoids = {
	'delta-9 THC-A':		re.compile(r'^(delta|Δ|∆)[-_/\s.]*9[-_/\s.]*THC[-_/\s.]*A$',	re.IGNORECASE),
	'delta-9 THC':			re.compile(r'^(delta|Δ|∆)[-_/\s.]*9[-_/\s.]*THC$',				re.IGNORECASE),
	'CBN':					re.compile(r'^CBN$',											re.IGNORECASE),
	'CBD-A':				re.compile(r'^CBD[-_/\s.]*A$',									re.IGNORECASE),
	'CBD':					re.compile(r'^CBD$',											re.IGNORECASE),
	'CBG-A':				re.compile(r'^CBG[-_/\s.]*A$',									re.IGNORECASE),
	'CBG':					re.compile(r'^CBG$',											re.IGNORECASE),
	'delta-9 CBG-A':		re.compile(r'^(delta|Δ|∆)[-_/\s.]*9[-_/\s.]*CBG[-_/\s.]*A$',	re.IGNORECASE),
	'delta-9 CBG':			re.compile(r'^(delta|Δ|∆)[-_/\s.]*9[-_/\s.]*CBG$',				re.IGNORECASE),
	'CBC':					re.compile(r'^CBC$',											re.IGNORECASE),
	'THCV':					re.compile(r'^THCV$',											re.IGNORECASE),
	'delta-8 THC':			re.compile(r'^(delta|Δ|∆)[-_/\s.]*8[-_/\s.]*THC$',				re.IGNORECASE),
	'Moisture Content':		re.compile(r'^Moisture[-_/\s.]*[-_/\s.]+Content$',				re.IGNORECASE),
	'THC-A':				re.compile(r'^THC[-_/\s.]*A$',									re.IGNORECASE),
}
cannabinoids['THC TOTAL'] = re.compile(r'^THC[-_/\s.]*TOTAL',								re.IGNORECASE)
cannabinoids['delta-9 THC TOTAL'] = re.compile(r'^(delta|Δ|∆)[-_/\s.]*9[-_/\s.]*THC[-_/\s.]*TOTAL$',re.IGNORECASE)
cannabinoids['CBD TOTAL'] = re.compile(r'^CBD[-_/\s.]*TOTAL',								re.IGNORECASE)
cannabinoids['CBG TOTAL'] = re.compile(r'^CBG[-_/\s.]*TOTAL',								re.IGNORECASE)
cannabinoids['Activated TOTAL'] = re.compile(r'^Activated[-_/\s.]*TOTAL',					re.IGNORECASE)
cannabinoids['Cannabinoids TOTAL'] = re.compile(r'^TOTAL[-_/\s.]*CANNABINOIDS',				re.IGNORECASE)

sample_types = {
	'Flower':				re.compile(r'^Flowers?$',										re.IGNORECASE),
	'Concentrate':			re.compile(r'^Concentrates?$',									re.IGNORECASE),
	'Edible':				re.compile(r'^Edibles?$',										re.IGNORECASE),
	'Liquid':				re.compile(r'^Liquids?$',										re.IGNORECASE),
	'Topical':				re.compile(r'^Topicals?$',										re.IGNORECASE),
}
sample_types['Edible Concentrate'] = re.compile(r'^Edible[-_/\s.]*Concentrate$',			re.IGNORECASE)
sample_types['Infusion'] =				re.compile(r'^Infusion$',							re.IGNORECASE)

re_test_uid = re.compile(r'^/results/samples/edit/(?P<uid>[_a-zA-Z0-9]+)$')

# Parses an american timestamp into its meaningful parts
re_date =			re.compile(r'^(?P<date>\s*(?P<month>(0?[0-9]|1[0-2]))\s*[-\./:]?\s*(?P<day>(0?[0-9]|1[0-9]|2[0-9]|3[0-1]))\s*[-\./:]?\s*(?P<year>(2\d{3}|[013-9][0-9])))$', re.IGNORECASE)

# Match a percentage value
re_percentageValue = re.compile(r'^[0-9.,]+\s*%$')
# Match a percentage value
re_zeroPercentageValue = re.compile(r'^<\s*[0-9.,]+\s*%$')
# Match a percentage value at the beginning of the string
re_percentageValueBeginning = re.compile(r'^[0-9.,]+\s*%')
# Match a (zero) percentage value at the beginning of the string
re_zeroPercentageValueBeginning = re.compile(r'^<\s*[0-9.,]+\s*%')

database = {
}

# database = {
# 	"name": "Psilabs",
# 	"samples": []
# }

providers = []
sample_types_all = []
empty_terpenes_counter = 0
empty_cannabinoid_counter = 0

logfile_cannabinoids_nonNumber = 'log-cannabinoid-no_number'
logfile_cannabinoids_noname = 'log-cannabinoid-noname'
logfile_cannabinoids_oneMatchMultipleTypes = 'log-cannabinoid-one_match_multiple_types'
logfile_cannabinoids_unknown = 'log-cannabinoid_unknown'
logfile_cannabinoids_allNoMatch = 'log-cannabinoids_all_did_not_match'
logfile_cannabinoids_multipleMatchSameType = 'log-cannabinoids-multiple_match_same_type'
logfile_cannabinoids_noneFound = 'log-cannabinoids-none_found'
logfile_cannabinoids_notPercentage = 'log-cannabinoids-non_percentage'
logfile_cbd_total_nonNumber = 'log-cbd_total-no_number'
logfile_cbd_total_noneFound = 'log-cbd_total-none_found'
logfile_cbd_total_notPercentage = 'log-cbd_total-not_percentage'
logfile_name_noneFound = 'log-name-none_found'
logfile_provider_noneFound = 'log-provider-none_found'
logfile_terpenes_nonNumber = 'log-terpene-no_number'
logfile_terpenes_noname = 'log-terpene-noname'
logfile_terpenes_notPercentage = 'log-terpene-non_percentage'
logfile_terpenes_oneMatchMultipleTypes = 'log-terpene-one_match_multiple_types'
logfile_terpenes_unknown = 'log-terpene-unknown'
logfile_terpenes_allNoMatch = 'log-terpenes-all_did_not_match'
logfile_terpenes_multipleMatchSameType = 'log-terpenes-multiple_match_same_type'
logfile_terpenes_noneFound = 'log-terpenes-none_found'
logfile_terpenes_total_nonNumber = 'log-terpenes_total-no_number'
logfile_terpenes_total_noneFound = 'log-terpenes_total-none_found'
logfile_terpenes_total_notPercentage = 'log-terpenes_total-not_percentage'
logfile_thc_total_nonNumber = 'log-thc_total-no_number'
logfile_thc_total_noneFound = 'log-thc_total-none_found'
logfile_thc_total_notPercentage = 'log-thc_total-not_percentage'
logfile_time_received_noneFound = 'log-time_received-none_found'
logfile_time_received_notDate = 'log-time_received-not_date'
logfile_time_tested_noneFound = 'log-time_tested-none_found'
logfile_time_tested_notDate = 'log-time_tested-not_date'
logfile_type_noneFound = 'log-type-none_found'
logfile_type_unknown = 'log-type-unknown'
logfile_uid_noneFound = 'log-uid-none_found'
sample_database_CSVfile = 'results.csv'
sample_database_JSONfile = 'results.json'

result_files = [
	logfile_cannabinoids_noname,
	logfile_terpenes_noname,
	logfile_cannabinoids_multipleMatchSameType,
	logfile_cannabinoids_oneMatchMultipleTypes,
	logfile_terpenes_multipleMatchSameType,
	logfile_cannabinoids_oneMatchMultipleTypes,
	logfile_cannabinoids_unknown,
	logfile_cannabinoids_allNoMatch,
	logfile_terpenes_allNoMatch,
	logfile_cannabinoids_noneFound,
	logfile_terpenes_noneFound,
	logfile_cannabinoids_notPercentage,
	logfile_type_unknown,
	logfile_terpenes_unknown,
	logfile_cbd_total_nonNumber,
	logfile_cbd_total_noneFound,
	logfile_cbd_total_notPercentage,
	logfile_name_noneFound,
	logfile_cannabinoids_nonNumber,
	logfile_terpenes_total_nonNumber,
	logfile_terpenes_nonNumber,
	logfile_terpenes_total_notPercentage,
	logfile_terpenes_notPercentage,
	logfile_provider_noneFound,
	logfile_terpenes_total_noneFound,
	logfile_thc_total_nonNumber,
	logfile_thc_total_noneFound,
	logfile_thc_total_notPercentage,
	logfile_time_received_noneFound,
	logfile_time_received_notDate,
	logfile_time_tested_noneFound,
	logfile_time_tested_notDate,
	logfile_type_noneFound,
	logfile_uid_noneFound,
	sample_database_CSVfile,
	sample_database_JSONfile,
]
if input('\nDo you want to delete the old result and log files? (y/n) ').lower() == 'y':
	for filename in result_files:
		if os.path.exists(filename+'.html'):
			os.remove(filename+'.html')
		elif os.path.exists(filename+'.csv'):
			os.remove(filename+'.csv')

log_this('Before we start, a heads up:',
		'I will try to extract any terpene and cannabinoid profiles present as exact as possible. Samples which have values in ppm or mg units are skipped.',
		'If a specific terpene is not present, I will ignore it for that page',
		sep='\n',
		level=1,
		override=True)
if input('\nDo you want to start? (y/n) ').lower() != 'y':
	exit('Aborted.')

if args.json:
	with open(sample_database_JSONfile, "w", encoding="utf-8") as databases_file:
		databases_file.write('{"name":"Psilabs"')
		databases_file.write(',"samples":{')

log_this('Entering main loop . . .', level=1)

type_folders = sorted(os.listdir(os.path.expanduser(args.database)))
is_first_type = True
for type_index, type_folder in enumerate(type_folders):
	is_first_sample = True
	file_list = sorted(os.listdir(os.path.join(os.path.expanduser(args.database),type_folder)))
	if args.json:
		with open(sample_database_JSONfile, "a", encoding="utf-8") as databases_file:
			if not is_first_type:
				databases_file.write(',')
			databases_file.write('"{}":['.format(type_folder))
			is_first_type = False
	for file_index, file_name in enumerate(file_list):
		raw_sample_file_name = os.path.join(type_folder, file_name)
		log_this('#'*80, level=2)

		log_this('Parsing sample file {} now.'.format(raw_sample_file_name), level=2)
		with open(os.path.join(os.path.expanduser(args.database),raw_sample_file_name),encoding='utf-8') as raw_sample_file:
			tree = html.fromstring(raw_sample_file.read())

		skip_this_file = False


		# 0 Test Data terpenes
		raw_terpenes_1 = tree.xpath(xpath_terpenes_1)
		terpenes_data = {}
		non_percentage_numbers = False
		# if len(raw_terpenes_1) > 0:
		# 	log_this('{}: both terpenes queries match!', level=3)
		if 0 == len(raw_terpenes_1):
			log_this('no terpenes: {}'.format(raw_sample_file_name), level=3)
			write_to_logfile(
				filepath=logfile_terpenes_noneFound,
				fieldnames=['Filename'],
				data={'Filename':raw_sample_file_name}
			)
		else:
			for i, raw_terpene in enumerate(raw_terpenes_1, 1):

				# AMOUNT
				raw_terpene_amount = get_single_value(
					tree=raw_terpene,
					xpath='td[2]/text()',
					fallback=''
				)
				terpene_amount_match = re_percentageValue.match(raw_terpene_amount)
				terpene_zeroamount_match = re_zeroPercentageValue.match(raw_terpene_amount)
				if terpene_amount_match:
					terpene_amount_match_object = terpene_amount_match
					try:
						terpene_amount = normalize_number(
							numberstring=raw_terpene_amount[terpene_amount_match.start():terpene_amount_match.end()]
						)
					except ValueError as e:
						log_this('terpenes number error', level=1)
						write_to_logfile(
							filepath=logfile_terpenes_nonNumber,
							fieldnames=['Filename','List Index', 'Amount'],
							data={'Filename':raw_sample_file_name, 'List Index':i, 'Amount':raw_terpene_amount}
						)
						continue
				elif terpene_zeroamount_match:
					terpene_amount_match_object = terpene_zeroamount_match
					terpene_amount = 0.0
				else:
					non_percentage_numbers = True
					log_this('non percentage terpenes', level=3)
					write_to_logfile(
						filepath=logfile_terpenes_notPercentage,
						fieldnames=['Filename','List Index'],
						data={'Filename':raw_sample_file_name, 'List Index':i}
					)
					continue

				# NAME
				## TODO: we could do levenshtein- and typewriterdistance (en-US) here
				original_terpene_name = get_single_value(
					tree=raw_terpene,
					xpath='td[1]/text()',
					fallback=''
				)
				regex_matched = False
				for terpene_name in terpenes.keys():
					terpene_regex = terpenes[terpene_name]
					log_this('trying regex {}'.format(terpene_regex.pattern), level=3)
					terpene_match = terpene_regex.match(original_terpene_name)
					if terpene_match:
						log_this('{} terp matched {} regex'.format(original_terpene_name, terpene_regex), level=3)
						if regex_matched:
							log_this('terpene matches multiple patterns', level=1)
							# Match more than one regex?
							write_to_logfile(
								filepath=logfile_terpenes_oneMatchMultipleTypes,
								fieldnames=['Filename', 'List Index', 'Terpene'],
								data={'Filename':raw_sample_file_name,'List Index':i,'Terpene':terpene_name}
							)
							skip_this_file = True
						else:
							log_this('Regex matched first time', level=3)
							regex_matched = True
						if terpene_name in terpenes_data:
							log_this('{}: Terpene already recorded: {}'.format(raw_sample_file_name, terpene_name), level=1)
							# Multiple match same regex?
							write_to_logfile(
								filepath=logfile_terpenes_multipleMatchSameType,
								fieldnames=['Filename', 'List Index', 'Terpene'],
								data={'Filename':raw_sample_file_name,'List Index':i,'Terpene':terpene_name}
							)
							skip_this_file = True
						else:
							terpenes_data[terpene_name] = terpene_amount

				if original_terpene_name is None:
					log_this('terpene name empty', level=1)
					write_to_logfile(
						filepath=logfile_terpenes_noname,
						fieldnames=['Filename', 'List Index'],
						data={'Filename':raw_sample_file_name, 'List Index':i}
					)
				elif not regex_matched:
					log_this('{}: terpene did not match anything: {}'.format(raw_sample_file_name, original_terpene_name), level=1)
					# Match none?
					write_to_logfile(
						filepath=logfile_terpenes_unknown,
						fieldnames=['Filename', 'Terpene', 'List Index'],
						data={'Filename':raw_sample_file_name, 'Terpene':terpene_name, 'List Index':i}
					)
			if terpenes_data == {}:
				log_this('{}: no terpenes were added'.format(raw_sample_file_name), level=3)
				write_to_logfile(
					filepath=logfile_terpenes_allNoMatch,
					fieldnames=['Filename', 'Amount'],
					data={'Filename':raw_sample_file_name, 'Amount':len(raw_terpenes_1)}
				)
		if args.force_terpenes and terpenes_data == {}:
			skip_this_file = True

		# 1 Test Data Terpenes Total
		terpene_total = None
		raw_terpene_total = get_single_value(
			tree=tree,
			xpath=xpath_terpenes_total,
			fallback='',
			fallback_file=logfile_terpenes_total_noneFound,
			fallback_data={'Filename':raw_sample_file_name}
		)
		terpene_amount_match = re_percentageValue.match(raw_terpene_total)
		if terpene_amount_match:
			try:
				terpene_total = normalize_number(
					numberstring=raw_terpene_total
				)
			except ValueError as e:
				write_to_logfile(
					filepath=logfile_terpenes_total_nonNumber,
					fieldnames=['Filename', 'Amount'],
					data={'Filename':raw_sample_file_name, 'Amount':raw_terpene_total}
				)
		else:
			write_to_logfile(
				filepath=logfile_terpenes_total_notPercentage,
				fieldnames=['Filename', 'Amount'],
				data={'Filename':raw_sample_file_name, 'Amount':raw_terpene_total}
			)
			continue

		# 1 Test Data Cannabinoids
		raw_cannabinoids_1 = tree.xpath(xpath_cannabinoids_1)
		cannabinoid_data = {}
		# if len(raw_cannabinoids_1) > 0:
		# 	log_this('{}: both cannabinoid queries match!', level=3)
		if 0 == len(raw_cannabinoids_1):
			log_this('{}: no potency'.format(raw_sample_file_name), level=3)
			write_to_logfile(
				filepath=logfile_cannabinoids_noneFound,
				fieldnames=['Filename'],
				data={'Filename':raw_sample_file_name}
			)
		else:
			for i, raw_cannabinoid in enumerate(raw_cannabinoids_1, 1):

				# AMOUNT
				raw_cannabinoid_amount = get_single_value(
					tree=raw_cannabinoid,
					xpath='td[2]/text()',
					fallback=''
				)
				cannabinoid_amount_match = re_percentageValue.match(raw_cannabinoid_amount)
				if cannabinoid_amount_match:
					try:
						cannabinoid_amount = normalize_number(
							numberstring=raw_cannabinoid_amount[cannabinoid_amount_match.start():cannabinoid_amount_match.end()]
						)
					except ValueError as e:
						log_this('{}: cannabinoid number error'.format(raw_sample_file_name), level=1)
						write_to_logfile(
							filepath=logfile_cannabinoids_nonNumber,
							fieldnames=['Filename','List Index', 'Amount'],
							data={'Filename':raw_sample_file_name, 'List Index':i, 'Amount':raw_cannabinoid_amount}
						)
						continue
				else:
					log_this('{}: non percentage cannabinoid'.format(raw_sample_file_name), level=3)
					write_to_logfile(
						filepath=logfile_cannabinoids_notPercentage,
						fieldnames=['Filename','List Index'],
						data={'Filename':raw_sample_file_name, 'List Index':i}
					)
					continue

				# NAME
				## TODO: we could do levenshtein- and typewriterdistance (en-US) here
				original_cannabinoid_name = get_single_value(
					tree=raw_cannabinoid,
					xpath='td[1]/text()',
					fallback=''
				)

				log_this('####################NEW CANNABINOID: {} #####################'.format(original_cannabinoid_name), level=3)
				regex_matched = False
				for cannabinoid_name in cannabinoids.keys():
					cannabinoid_regex = cannabinoids[cannabinoid_name]
					log_this('trying regex {}'.format(cannabinoid_regex.pattern), level=3)
					cannabinoid_match = cannabinoid_regex.match(original_cannabinoid_name)
					if cannabinoid_match:
						log_this('{} cnbnd matched {} regex'.format(original_cannabinoid_name, cannabinoid_regex.pattern), level=3)
						if regex_matched:
							log_this('{}: Cannabinoid matches multiple patterns'.format(raw_sample_file_name), level=1)
							# Match more than one regex?
							write_to_logfile(
								filepath=logfile_cannabinoids_oneMatchMultipleTypes,
								fieldnames=['Filename', 'List Index', 'Cannabinoid'],
								data={'Filename':raw_sample_file_name,'List Index':i,'Cannabinoid':cannabinoid_name}
							)
							skip_this_file = True
						else:
							log_this('Regex matched first time', level=3)
							regex_matched = True
						if cannabinoid_name in cannabinoid_data:
							log_this('{}: Cannabinoid already recorded: {}'.format(raw_sample_file_name, cannabinoid_name), level=1)
							# Multiple items match same regex
							write_to_logfile(
								filepath=logfile_cannabinoids_multipleMatchSameType,
								fieldnames=['Filename', 'List Index', 'Cannabinoid'],
								data={'Filename':raw_sample_file_name,'List Index':i,'Cannabinoid':cannabinoid_name}
							)
							skip_this_file = True
						else:
							cannabinoid_data[cannabinoid_name] = cannabinoid_amount

				if original_cannabinoid_name is None:
					log_this('{}: cannabinoid name empty'.format(raw_sample_file_name), level=1)
					write_to_logfile(
						filepath=logfile_cannabinoids_noname,
						fieldnames=['Filename', 'List Index'],
						data={'Filename':raw_sample_file_name, 'List Index':i}
					)
				elif not regex_matched:
					log_this('{}: cannabinoid did not match anything: {}'.format(raw_sample_file_name, original_cannabinoid_name), level=3)
					# Match none?
					write_to_logfile(
						filepath=logfile_cannabinoids_unknown,
						fieldnames=['Filename', 'Cannabinoid', 'List Index'],
						data={'Filename':raw_sample_file_name, 'Cannabinoid':cannabinoid_name, 'List Index':i}
					)
			if cannabinoid_data == {}:
				log_this('{}: no cannabinoids were added'.format(raw_sample_file_name), level=3)
				write_to_logfile(
					filepath=logfile_cannabinoids_allNoMatch,
					fieldnames=['Filename', 'Amount'],
					data={'Filename':raw_sample_file_name, 'Amount':len(raw_cannabinoids_1)}
				)
		if args.force_cannabinoids and cannabinoid_data == {}:
			skip_this_file = True

		# 2 Test Data THC Total
		thc_total = None
		raw_thc_total = get_single_value(
			tree=tree,
			xpath=xpath_thc_total,
			fallback='',
			fallback_file=logfile_thc_total_noneFound,
			fallback_data={'Filename':raw_sample_file_name}
		)
		thc_amount_match = re_percentageValue.match(raw_thc_total)
		if thc_amount_match:
			try:
				thc_total = normalize_number(
					numberstring=raw_thc_total
				)
			except ValueError as e:
				write_to_logfile(
					filepath=logfile_thc_total_nonNumber,
					fieldnames=['Filename', 'Amount'],
					data={'Filename':raw_sample_file_name, 'Amount':raw_thc_total}
				)
		else:
			write_to_logfile(
				filepath=logfile_thc_total_notPercentage,
				fieldnames=['Filename', 'Amount'],
				data={'Filename':raw_sample_file_name, 'Amount':raw_thc_total}
			)

		# 3 Test Data CBD Total
		cbd_total = None
		raw_cbd_total = get_single_value(
			tree=tree,
			xpath=xpath_cbd_total,
			fallback='',
			fallback_file=logfile_cbd_total_noneFound,
			fallback_data={'Filename':raw_sample_file_name}
		)
		cbd_amount_match = re_percentageValue.match(raw_cbd_total)
		if cbd_amount_match:
			try:
				cbd_total = normalize_number(
					numberstring=raw_cbd_total
				)
			except ValueError as e:
				write_to_logfile(
					filepath=logfile_cbd_total_nonNumber,
					fieldnames=['Filename', 'Amount'],
					data={'Filename':raw_sample_file_name, 'Amount':raw_cbd_total}
				)
		else:
			write_to_logfile(
				filepath=logfile_cbd_total_notPercentage,
				fieldnames=['Filename', 'Amount'],
				data={'Filename':raw_sample_file_name, 'Amount':raw_cbd_total}
			)
		# 2 Sample Type
		sample_type = None
		raw_sample_type = get_single_value(
			tree=tree,
			xpath=xpath_sample_type,
			fallback='',
			fallback_file=logfile_type_noneFound,
			fallback_data={'Filename':raw_sample_file_name}
		)
		if raw_sample_type:
			regex_matched = False
			for sampletype_name in sample_types.keys():
				sampletype_regex = sample_types[sampletype_name]
				log_this('trying regex {}'.format(sampletype_regex), level=3)
				sampletype_match = sampletype_regex.match(raw_sample_type)
				if sampletype_match:
					log_this('{} sample type matched {} regex'.format(raw_sample_type, sampletype_regex), level=3)
					if regex_matched:
						log_this('Regex matched before', level=1)
						# Match more than one regex?
						write_to_logfile(
							filepath='sample_type_one_matches_multiple_types',
							fieldnames=['Filename', 'Sample Type'],
							data={'Filename':raw_sample_file_name,'Sample Type':sampletype_name}
						)
						skip_this_file = True
					else:
						log_this('Regex matched first time', level=3)
						regex_matched = True
						sample_type = sampletype_name
		# if not os.path.exists(os.path.join(args.database, sample_type)):
		# 	os.makedirs(os.path.join(os.path.expanduser(args.database),sample_type), exist_ok=True)
		if not regex_matched:
			log_this('sample type did not match anything: {}'.format(raw_sample_type), level=1)
			# Match none?
			write_to_logfile(
				filepath=logfile_type_unknown,
				fieldnames=['Filename', 'Sample Type', 'Xpath'],
				data={'Filename':raw_sample_file_name, 'Sample Type':raw_sample_type, 'Xpath':xpath_sample_type}
			)

		# 3 Sample Name
		sample_name = get_single_value(
			tree=tree,
			xpath=xpath_sample_name,
			fallback_file=logfile_name_noneFound,
			fallback_data={'Filename':raw_sample_file_name}
		)

		# 4 Sample Provider
		sample_provider = get_single_value(
			tree=tree,
			xpath=xpath_sample_provider,
			fallback=get_single_value(
				tree=tree,
				xpath=xpath_sample_provider_anon,
				fallback_file=logfile_provider_noneFound,
				fallback_data={'Filename':raw_sample_file_name}
			)
		)
		if sample_provider == 'Anonymous':
			sample_provider = None
		elif sample_provider is not None:
			if sample_provider not in providers:
				providers.append(sample_provider)
			sample_provider = str(providers.index(sample_provider) + 1)

		# 5 Test UID
		test_uid = None
		raw_test_uid = get_single_value(
			tree=tree,
			xpath=xpath_test_uid,
			fallback='',
			fallback_file=logfile_uid_noneFound,
			fallback_data={'Filename':raw_sample_file_name}
		)
		test_uid_match = re_test_uid.match(raw_test_uid)
		if test_uid_match:
			test_uid = test_uid_match.group('uid')

		# 6 Test Time
		test_time = None
		raw_test_time = get_single_value(
			tree=tree,
			xpath=xpath_time_tested,
			fallback=''
		)
		re_date_match = re_date.match(raw_test_time)
		if re_date_match:
			possible_dates = dateparser_search.search_dates(
				text=raw_test_time,
				languages=['en'],
				settings={'DATE_ORDER':'MDY','STRICT_PARSING':True}
			)
			if type(possible_dates) == list and len(possible_dates) == 1:
				test_time = possible_dates[0][1].date().isoformat()
			else:
				write_to_logfile(
					filepath=logfile_time_tested_notDate,
					fieldnames=['Filename'],
					data={'Filename':raw_sample_file_name}
				)
		else:
			write_to_logfile(
				filepath=logfile_time_tested_noneFound,
				fieldnames=['Filename'],
				data={'Filename':raw_sample_file_name}
			)

		# 7 Receipt Time
		receipt_time = None
		raw_receipt_time = get_single_value(
			tree=tree,
			xpath=xpath_time_received,
			fallback=''
		)
		re_date_match = re_date.match(raw_receipt_time)
		if re_date_match:
			possible_dates = dateparser_search.search_dates(
				text=raw_receipt_time,
				languages=['en'],
				settings={'DATE_ORDER':'MDY','STRICT_PARSING':True}
			)
			if type(possible_dates) == list and len(possible_dates) == 1:
				receipt_time = possible_dates[0][1].date().isoformat()
			else:
				write_to_logfile(
					filepath=logfile_time_received_notDate,
					fieldnames=['Filename'],
					data={'Filename':raw_sample_file_name}
				)
		else:
			write_to_logfile(
				filepath=logfile_time_received_noneFound,
				fieldnames=['Filename'],
				data={'Filename':raw_sample_file_name}
			)

		if terpenes_data == {} and cannabinoid_data == {}:
			skip_this_file = True

		sample_data = {
			'Test Result UID':test_uid,
			'Sample Name':sample_name,
			'Test Time':test_time,
			'Receipt Time':receipt_time,
			'Provider':sample_provider,
			'Terpene TOTAL':terpene_total,
			'THC TOTAL':thc_total,
			'CBD TOTAL':cbd_total,
			'Sample Type':sample_type
		}
		sample_data.update(terpenes_data)
		sample_data.update(cannabinoid_data)

		for sample_data_field in list(sample_data.keys()):
			remove_key = False
			if sample_data[sample_data_field] is None:
				remove_key = True
			if sample_data_field not in DATA_ROW_FIELDS:
				remove_key = True
			if remove_key:
				del sample_data[sample_data_field]
		if sample_data == {}:
			skip_this_file = True

		if not skip_this_file:
			if args.csv:
				write_to_csv(
					filepath=sample_database_CSVfile,
					fieldnames=DATA_ROW_FIELDS,
					data=sample_data
				)
			if args.json:
				with open(sample_database_JSONfile, "a", encoding="utf-8") as databases_file:
					if not is_first_sample:
						databases_file.write(',')
					json.dump(sample_data, databases_file, separators=(',', ':'), sort_keys=True)
					is_first_sample = False
	if args.json:
		with open(sample_database_JSONfile, "a", encoding="utf-8") as databases_file:
			databases_file.write(']')

log_this('Finished main loop.', level=3)

if args.json:
	with open(sample_database_JSONfile, "a", encoding="utf-8") as databases_file:
		databases_file.write('}}')

log_this('All files have been processed. Please check the contents of the log-files (starting with "log-"). Those list pages regarding different errors.', level=1, override=True)
log_this('Also, note the lines starting with "INFO: " or "DETAIL: ".', level=1, override=True)
