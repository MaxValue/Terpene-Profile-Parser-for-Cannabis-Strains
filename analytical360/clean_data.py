#!/usr/bin/env python3
# coding: utf-8

DATA_ROW_FIELDS = [
	'Test Result UID',
	'Sample Name',
	'Sample Type',
	'Test Time',
	'Receival Time',
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

import re, os, csv, argparse, json, urllib
from lxml import html
from lxml import etree

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
args = parser.parse_args()

# Use this to change what should be put as value for a datapoint if it was not found or could not be parsed
PLACEHOLDER_UNDEFINED = 'NaN'

def get_single_value(tree, xpath, fallback=PLACEHOLDER_UNDEFINED, fallback_file=False, fallback_data={}, join_multi=False):
	raw_value = tree.xpath(xpath)
	if len(raw_value) == 1:
		if type(raw_value[0]) == str:
			return raw_value[0].strip()
		else:
			return raw_value[0]
	else:
		if join_multi == False:
			if fallback_file:
				write_to_logfile(fallback_file, sorted(fallback_data.keys()), fallback_data)
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

def normalize_year(year):
	if re.sub('[0-9]', '', year) != '':
		raise ValueError
	if len(year) == 2:
		if year.startswith('0'):
			prefix = '20'
		if year.startswith('1'):
			prefix = '20'
		if year.startswith('2'):
			prefix = '20'
		if year.startswith('3'):
			prefix = '19'
		if year.startswith('4'):
			prefix = '19'
		if year.startswith('5'):
			prefix = '19'
		if year.startswith('6'):
			prefix = '19'
		if year.startswith('7'):
			prefix = '19'
		if year.startswith('8'):
			prefix = '19'
		if year.startswith('9'):
			prefix = '19'
		return '{}{}'.format(prefix, year)
	elif len(year) == 4:
		return year
	else:
		raise ValueError

def csv_escape(data):
	return '"{}"'.format(data)

def date_iso8601(year, month, day):
	return '{year}-{month:0>2}-{day:0>2}'.format(year=year, month=month, day=day)

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
			write_to_csv(filepath=filepath+'.csv', fieldnames=fieldnames, data=data)
		elif args.log_html:
			write_to_html(filepath=filepath+'.html', fieldnames=fieldnames, data=data, title=title)

def write_to_csv(filepath, fieldnames, data):
	if os.path.exists(filepath):
		writeheader = False
	else:
		writeheader = True
	with open(filepath, 'a', encoding='utf-8') as writefile:
		writefile_writer = csv.DictWriter(writefile, fieldnames=fieldnames, restval=PLACEHOLDER_UNDEFINED, lineterminator='\n')
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
					link.attrib['href'] = 'file://{}'.format(os.path.join(os.getcwd(),RAW_DATABASE_DUMP_PATH,data_row[fieldname]))
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
					#fieldname_element.text = PLACEHOLDER_UNDEFINED
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

RAW_DATABASE_DUMP_PATH = args.database

xpath_provider_page = """/html/body/div/div/div[@class='maincontent']/div[@id='sabai-content']/div[@id='sabai-body']//div[@class='sabai-row-fluid']"""

xpath_festival_page = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div/div[@class='maincontent']/div[@class='rehabtabs']/*[@id]"""

# Finds the text of the first header in the page content:
xpath_sample_name = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div[@class='center']/div[@class='maincontent']/*[
													self::h1
													or self::h2
													or self::h3
													or self::h4
													or self::h5
													or self::h6
												][1]/text()"""

# Finds text of all headers which text content starts with the words "available from", ignoring the case
xpath_sample_provider = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div[@class='center']/div[@class='maincontent']//*[
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
xpath_test_uid = """/html/body/div/div/div[@class='maincontent']/*[
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
xpath_time_tested = """/html/body/div/div/div[@class='maincontent']/*[
													self::h1
													or self::h2
													or self::h3
													or self::h4
													or self::h5
													or self::h6
												][
													contains(
															translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
															'date'
													)
													and contains(
															translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
															'test'
													)
												]/text()"""

xpath_canonicalURL = """/html/head/link[@rel='canonical'][@href]"""

# Finds text of all list items which are preceeded by the words "terpen" and "profil", ignoring the case
xpath_terpenes_1 = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div[@class='center']/div[@class='maincontent']/div[
						div/div/h4[
							contains(
									translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
									'terpen'
							)
							and contains(
									translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
									'profil'
							)
						]
					]/following-sibling::*[1]//li"""
xpath_terpenes_2 = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div[@class='center']/div[@class='maincontent']/h4[
						contains(
								translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
								'terpenes'
						)
					]/following-sibling::*[1]//li"""
xpath_terpenes_3 = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div[@class='center']/h4[
						contains(
								translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
								'terpen'
						)
						and contains(
								translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
								'profil'
						)
					]/following-sibling::*[1]//li"""
xpath_terpenes_total = """/html/body/div/*[
								contains(
										translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
										'terpen'
								)
								and contains(
										translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
										'profil'
								)
							]/following-sibling::*[1]//li[
								contains(
										translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
										'terpene-total'
								)
							]//text()"""

# Finds text of all list items which are preceeded by the words "poten" and "profil", ignoring the case
xpath_cannabinoids_1 = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div[@class='center']/div[@class='maincontent']/div[
							div/div/h4[
								contains(
									translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
									'poten'
								)
								and contains(
									translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
									'profil'
								)
							]
						]/following-sibling::*[1]//li"""
xpath_cannabinoids_2 = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div[@class='center']/div[
							div/div/h4[
								contains(
									translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
									'poten'
								)
								and contains(
									translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
									'profil'
								)
							]
						]/following-sibling::*[1]//li"""


# Finds the amount of total THC present in the sample
xpath_thc_total = """/html/body/div[@id='wrapper']/div[@id='mainwrapper']/div[@class='center']/div[@class='maincontent']/div[
							div/div/h4[
								contains(
									translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
									'poten'
								)
								and contains(
									translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
									'profil'
								)
							]
						]/following-sibling::*[1]//li/descendant-or-self::*[
							contains(
								translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
								'thc'
							)
							and contains(
								translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),
								'total'
							)
						]"""

# Matches strings like: "    Test   Result     UID    :    jfkgbnFGBFG34394129_fkgljh345_345dfgdg    "
re_test_uid = re.compile(r"^\s*Test\s*Result\s*UID\s*:?\s*(?P<uid>[\S]+)\s*$", re.IGNORECASE)
# Matches strings like: "   Date   Tested   01    /   23   .   2019     "
re_date = re.compile(r"^\s*Date\s*(Test[a-zA-Z_]*\s*)?:?\s*(?P<date>\s*(?P<month>(0?[0-9]|1[0-2]))\s*[-\./:]?\s*(?P<day>(0?[0-9]|1[0-9]|2[0-9]|3[0-1]))\s*[-\./:]?\s*(?P<year>2\d{3}))\s*$", re.IGNORECASE)
# Matches strings like: "   Date   Tested   23    /   01   .   2019     "
re_sample_time_europe = re.compile(r"^\s*Date\s*(Test[a-zA-Z_]*\s*)?:?\s*(?P<date>\s*(?P<day>(0?[0-9]|1[0-9]|2[0-9]|3[0-1]))\s*[-\./:]?\s*(?P<month>(0?[0-9]|1[0-2]))\s*[-\./:]?\s*(?P<year>2\d{3}))\s*$", re.IGNORECASE)
# Matches strings like: "   Date   Tested   2019    /   23   .    01    "
re_sample_time_intl = re.compile(r"^\s*Date\s*(Test[a-zA-Z_]*\s*)?:?\s*(?P<date>\s*(?P<year>2\d{3})\s*[-\./:]?\s*(?P<month>(0?[0-9]|1[0-2]))\s*[-\./:]?\s*(?P<day>(0?[0-9]|1[0-9]|2[0-9]|3[0-1])))\s*$", re.IGNORECASE)
# Match a percentage value
re_percentageValue = re.compile(r'^[0-9.,]+\s*%$')
# Match a percentage value at the beginning of the string
re_percentageValueBeginning = re.compile(r'^[0-9.,]+\s*%')
# Match a analytical360 test result path
re_sampleTypeURL = re.compile(r'^/m/(?P<type>[-._~!$&\')(*+,;=:@%a-zA-Z0-9]+)/(?P<id>\d+)')
# Match a analytical360 product page path
re_productPageURL = re.compile(r'^/product/(?P<type>[-._~!$&\')(*+,;=:@%a-zA-Z0-9]+)')
# Matches the old file names
re_oldSampleFilename = re.compile(r'^\d+\.html$')

terpenes = {
	'3-Carene':				re.compile(r'^(3|Three|Tri)[-_/\s.]*Carene$',					re.IGNORECASE),
	'Camphene':				re.compile(r'^Camphene$',										re.IGNORECASE),
	'Caryophyllene Oxide':	re.compile(r'^Caryophyllene[-_/\s.]*Oxide$',					re.IGNORECASE),
	'Eucalyptol':			re.compile(r'^Eucalyptol$',										re.IGNORECASE),
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
terpenes['Farnesene'] = 	re.compile(r'^Farnesene$',										re.IGNORECASE)

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
del cannabinoids['Moisture Content']

sample_types = {
	'Flower':				re.compile(r'^Flowers?$',										re.IGNORECASE),
	'Concentrate':			re.compile(r'^Concentrates?$',									re.IGNORECASE),
	'Edible':				re.compile(r'^Edibles?$',										re.IGNORECASE),
	'Liquid':				re.compile(r'^Liquids?$',										re.IGNORECASE),
	'Topical':				re.compile(r'^Topicals?$',										re.IGNORECASE),
}
sample_types['Archived'] =  re.compile(r'^Archived$',										re.IGNORECASE)

database = {
}

# database = {
# 	"name": "Analytical360",
# 	"terpenes": list(terpenes.keys()),
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
logfile_cbd_total_noneFound = 'log-cbd_total-none_found'
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
logfile_thc_total_noneFound = 'log-thc_total-none_found'
logfile_time_noneFound = 'log-time-none_found'
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
	logfile_cbd_total_noneFound,
	logfile_name_noneFound,
	logfile_cannabinoids_nonNumber,
	logfile_terpenes_total_nonNumber,
	logfile_terpenes_nonNumber,
	logfile_terpenes_total_notPercentage,
	logfile_terpenes_notPercentage,
	logfile_provider_noneFound,
	logfile_terpenes_total_noneFound,
	logfile_thc_total_noneFound,
	logfile_time_noneFound,
	logfile_type_noneFound,
	logfile_uid_noneFound,
	sample_database_CSVfile,
	sample_database_JSONfile,
]
if input('\nDo you want to delete the old result files? (y/n) ') == 'y':
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
if input('\nDo you want to start? (y/n) ') != 'y':
	exit('Aborted.')

if args.json:
	with open(sample_database_JSONfile, "w", encoding="utf-8") as databases_file:
		databases_file.write('{"terpenes":')
		json.dump(list(terpenes.keys()), databases_file, separators=(',', ':'))
		databases_file.write(',"Analytical360":{')

log_this('Entering main loop . . .', level=1)

type_folders = sorted(os.listdir(os.path.expanduser(RAW_DATABASE_DUMP_PATH)))
for type_index, type_folder in enumerate(type_folders):
	file_list = sorted(os.listdir(os.path.join(os.path.expanduser(RAW_DATABASE_DUMP_PATH),type_folder)))
	if args.json:
		with open(sample_database_JSONfile, "a", encoding="utf-8") as databases_file:
			if type_index > 0:
				databases_file.write(',')
			databases_file.write('"{}":['.format(type_folder))
	for file_index, file_name in enumerate(file_list):
		raw_sample_file_name = os.path.join(type_folder, file_name)
		log_this('#'*80, level=2)

		log_this('Parsing sample file {} now.'.format(raw_sample_file_name), level=2)
		with open(os.path.join(os.path.expanduser(RAW_DATABASE_DUMP_PATH),raw_sample_file_name),encoding='utf-8') as raw_sample_file:
			tree = html.fromstring(raw_sample_file.read())

		skip_this_file = False

		elem_canonicalUrl = get_single_value(
			tree,
			xpath_canonicalURL
		)
		online_URL = elem_canonicalUrl.attrib['href']
		parsed_canonical = urllib.parse.urlparse(online_URL)

		# Test if this is a provider page
		provider_page_test = tree.xpath(xpath_provider_page)
		if len(provider_page_test) != 0:
			write_to_logfile(
				'provider_page',
				['Filename'],
				{'Filename':raw_sample_file_name}
			)
			log_this('{}: Is provider'.format(raw_sample_file_name), level=3)
			continue

		# Test if this is a product page
		productPageURL_match = re_productPageURL.match(parsed_canonical.path)
		if productPageURL_match:
			log_this('{}: Is product page'.format(raw_sample_file_name), level=3)
			skip_this_file = True
			continue

		# 0 Test Data terpenes
		raw_terpenes_1 = tree.xpath(xpath_terpenes_1)
		raw_terpenes_2 = tree.xpath(xpath_terpenes_2)
		raw_terpenes_3 = tree.xpath(xpath_terpenes_3)
		terpenes_data = {}
		if len(raw_terpenes_1) > 0 and len(raw_terpenes_2) > 0 and len(raw_terpenes_3) > 0:
			log_this('{}: both terpenes queries match!', level=3)
		if len(raw_terpenes_1) == 0 and len(raw_terpenes_2) == 0 and len(raw_terpenes_3) == 0:
			log_this('no terpenes: {}'.format(raw_sample_file_name), level=3)
			write_to_logfile(logfile_terpenes_noneFound,['Filename'],{'Filename':raw_sample_file_name})
		else:
			for i, raw_terpenes in enumerate(raw_terpenes_1+raw_terpenes_2+raw_terpenes_3, 1):

				# AMOUNT AND NAME
				raw_terpenes_info = get_single_value(
					raw_terpenes,
					'descendant-or-self::*/text()',
					join_multi=True
				)

				# AMOUNT
				terpene_amount_match = re_percentageValueBeginning.match(raw_terpenes_info)
				if terpene_amount_match:
					try:
						terpene_amount = normalize_number(raw_terpenes_info[terpene_amount_match.start():terpene_amount_match.end()])
					except ValueError as e:
						log_this('terpenes number error', level=1)
						write_to_logfile(
							logfile_terpenes_nonNumber,
							['Filename','List Index', 'Amount'],
							{'Filename':raw_sample_file_name, 'List Index':i, 'Amount':raw_terpenes_info}
						)
						continue
				else:
					log_this('non percentage terpenes', level=3)
					write_to_logfile(
						logfile_terpenes_notPercentage,
						['Filename','List Index'],
						{'Filename':raw_sample_file_name, 'List Index':i}
					)
					continue

				# NAME
				## TODO: we could do levenshtein- and typewriterdistance (en-US) here
				original_terpene_name = raw_terpenes_info[terpene_amount_match.end():].strip()

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
								logfile_terpenes_oneMatchMultipleTypes,
								['Filename', 'List Index', 'Terpene'],
								{'Filename':raw_sample_file_name,'List Index':i,'Terpene':terpene_name}
							)
							skip_this_file = True
						else:
							log_this('Regex matched first time', level=3)
							regex_matched = True
						if terpene_name in terpenes_data:
							log_this('{}: Terpene already recorded: {}'.format(raw_sample_file_name, terpene_name), level=1)
							# Multiple match same regex?
							write_to_logfile(
								logfile_terpenes_multipleMatchSameType,
								['Filename', 'List Index', 'Terpene'],
								{'Filename':raw_sample_file_name,'List Index':i,'Terpene':terpene_name}
							)
							skip_this_file = True
						else:
							terpenes_data[terpene_name] = terpene_amount

				if original_terpene_name == PLACEHOLDER_UNDEFINED:
					log_this('terpene NaN', level=1)
					write_to_logfile(
						logfile_terpenes_noname,
						['Filename', 'List Index'],
						{'Filename':raw_sample_file_name, 'List Index':i}
					)
				elif not regex_matched:
					log_this('{}: terpene did not match anything: {}'.format(raw_sample_file_name, original_terpene_name), level=1)
					# Match none?
					write_to_logfile(
						logfile_terpenes_unknown,
						['Filename', 'Terpene', 'List Index'],
						{'Filename':raw_sample_file_name, 'Terpene':terpene_name, 'List Index':i}
					)
			if terpenes_data == {}:
				if args.force_terpenes:
					skip_this_file = True
				log_this('{}: no terpenes were added'.format(raw_sample_file_name), level=3)
				write_to_logfile(logfile_terpenes_allNoMatch, ['Filename', 'Amount'], {'Filename':raw_sample_file_name, 'Amount':len(raw_terpenes_1+raw_terpenes_2+raw_terpenes_3)})

		# 2 Test Data Cannabinoids
		raw_cannabinoids_1 = tree.xpath(xpath_cannabinoids_1)
		raw_cannabinoids_2 = tree.xpath(xpath_cannabinoids_2)
		cannabinoid_data = {}
		if len(raw_cannabinoids_1) > 0 and len(raw_cannabinoids_2) > 0:
			log_this('{}: both cannabinoid queries match!', level=3)
		if len(raw_cannabinoids_1) == 0 and len(raw_cannabinoids_2) == 0:
			log_this('{}: no potency'.format(raw_sample_file_name), level=3)
			write_to_logfile(
				logfile_cannabinoids_noneFound,
				['Filename'],
				{'Filename':raw_sample_file_name}
			)
		else:
			for i, raw_cannabinoid in enumerate(raw_cannabinoids_1+raw_cannabinoids_2, 1):

				# AMOUNT AND NAME
				raw_cannabinoid_info = get_single_value(
					raw_cannabinoid,
					'descendant-or-self::*/text()',
					join_multi=True
				)

				# AMOUNT
				cannabinoid_amount_match = re_percentageValueBeginning.match(raw_cannabinoid_info)
				if cannabinoid_amount_match:
					try:
						cannabinoid_amount = normalize_number(raw_cannabinoid_info[cannabinoid_amount_match.start():cannabinoid_amount_match.end()])
					except ValueError as e:
						log_this('{}: cannabinoid number error'.format(raw_sample_file_name), level=1)
						write_to_logfile(
							logfile_cannabinoids_nonNumber,
							['Filename','List Index', 'Amount'],
							{'Filename':raw_sample_file_name, 'List Index':i, 'Amount':raw_cannabinoid_info}
						)
						continue
				else:
					log_this('{}: non percentage cannabinoid'.format(raw_sample_file_name), level=3)
					write_to_logfile(
						logfile_cannabinoids_notPercentage,
						['Filename','List Index'],
						{'Filename':raw_sample_file_name, 'List Index':i}
					)
					continue

				# NAME
				## TODO: we could do levenshtein- and typewriterdistance (en-US) here
				original_cannabinoid_name = raw_cannabinoid_info[cannabinoid_amount_match.end():].strip()

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
								logfile_cannabinoids_oneMatchMultipleTypes,
								['Filename', 'List Index', 'Cannabinoid'],
								{'Filename':raw_sample_file_name,'List Index':i,'Cannabinoid':cannabinoid_name}
							)
							skip_this_file = True
						else:
							log_this('Regex matched first time', level=3)
							regex_matched = True
						if cannabinoid_name in cannabinoid_data:
							log_this('{}: Cannabinoid already recorded: {}'.format(raw_sample_file_name, cannabinoid_name), level=1)
							# Multiple items match same regex
							write_to_logfile(
								logfile_cannabinoids_multipleMatchSameType,
								['Filename', 'List Index', 'Cannabinoid'],
								{'Filename':raw_sample_file_name,'List Index':i,'Cannabinoid':cannabinoid_name}
							)
							skip_this_file = True
						else:
							cannabinoid_data[cannabinoid_name] = cannabinoid_amount

				if original_cannabinoid_name == PLACEHOLDER_UNDEFINED:
					log_this('{}: cannabinoid NaN'.format(raw_sample_file_name), level=1)
					write_to_logfile(logfile_cannabinoids_noname, ['Filename', 'List Index'], {'Filename':raw_sample_file_name, 'List Index':i})
				elif not regex_matched:
					log_this('{}: cannabinoid did not match anything: {}'.format(raw_sample_file_name, original_cannabinoid_name), level=3)
					# Match none?
					write_to_logfile(
						logfile_cannabinoids_unknown,
						['Filename', 'Cannabinoid', 'List Index'],
						{'Filename':raw_sample_file_name, 'Cannabinoid':cannabinoid_name, 'List Index':i}
					)
			if cannabinoid_data == {}:
				if args.force_cannabinoids:
					skip_this_file = True
				log_this('{}: no cannabinoids were added'.format(raw_sample_file_name), level=3)
				write_to_logfile(logfile_cannabinoids_allNoMatch, ['Filename', 'Amount'], {'Filename':raw_sample_file_name, 'Amount':len(raw_cannabinoids_1+raw_cannabinoids_2)})

		# 5 Sample Type
		sample_type = PLACEHOLDER_UNDEFINED
		sampleTypeURL_match = re_sampleTypeURL.match(parsed_canonical.path)
		if sampleTypeURL_match:
			raw_sample_type = sampleTypeURL_match.group('type')
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
							'sample_type_one_matches_multiple_types',
							['Filename', 'List Index', 'Sample Type'],
							{'Filename':raw_sample_file_name,'List Index':i,'Sample Type':sampletype_name}
						)
						skip_this_file = True
					else:
						log_this('Regex matched first time', level=3)
						regex_matched = True
						sample_type = sampletype_name
		# if re_oldSampleFilename.match(raw_sample_file_name) and sample_type!=PLACEHOLDER_UNDEFINED:
		# 	os.rename(os.path.join(os.path.expanduser(RAW_DATABASE_DUMP_PATH),raw_sample_file_name), os.path.join(os.path.expanduser(RAW_DATABASE_DUMP_PATH),sample_type[0]+sampleTypeURL_match.group('id')+'.html'))
		# 	raw_sample_file_name = sample_type[0]+sampleTypeURL_match.group('id')+'.html'
		if not os.path.exists(os.path.join(RAW_DATABASE_DUMP_PATH, sample_type)):
			os.makedirs(os.path.join(os.path.expanduser(RAW_DATABASE_DUMP_PATH),sample_type), exist_ok=True)
		if not sampleTypeURL_match or not regex_matched:
			log_this('sample type did not match anything: {}'.format(raw_sample_type), level=1)
			# Match none?
			write_to_logfile(
				logfile_type_unknown,
				['Filename', 'Sample Type', 'List Index', 'Xpath'],
				{'Filename':raw_sample_file_name, 'Sample Type':raw_sample_type, 'List Index':i, 'Xpath':xpath_canonicalURL}
			)

		# 6 Sample Name
		sample_name = get_single_value(
			tree,
			xpath_sample_name,
			fallback_file=logfile_name_noneFound,
			fallback_data={'Filename':raw_sample_file_name}
		)

		# 7 Sample Provider
		sample_provider = get_single_value(
			tree,
			xpath_sample_provider
		)
		if sample_provider == PLACEHOLDER_UNDEFINED:
			write_to_logfile(logfile_provider_noneFound, ['Filename'], {'Filename':raw_sample_file_name})
		elif sample_provider == 'Anonymous':
			sample_provider = PLACEHOLDER_UNDEFINED
		else:
			if sample_provider not in providers:
				providers.append(sample_provider)
			sample_provider = str(providers.index(sample_provider) + 1)

		# 8 Test UID
		test_uid = PLACEHOLDER_UNDEFINED
		raw_test_uid = get_single_value(
			tree,
			xpath_test_uid,
			fallback_file=logfile_uid_noneFound,
			fallback_data={'Filename':raw_sample_file_name}
		)
		test_uid_match = re_test_uid.match(raw_test_uid)
		if test_uid_match:
			test_uid = test_uid_match.group('uid')

		# 9 Test Time
		test_time = PLACEHOLDER_UNDEFINED
		raw_test_time = get_single_value(
			tree,
			xpath_time_tested
		)
		re_date_match = re_date.match(raw_test_time)
		if re_date_match:
			test_time = date_iso8601(year=normalize_year(re_date_match.group('year')),month=re_date_match.group('month'),day=re_date_match.group('day'))
		else:
			write_to_logfile(logfile_time_noneFound, ['Filename'], {'Filename':raw_sample_file_name})

		# 10 Receival Time
		receival_time = PLACEHOLDER_UNDEFINED

		if terpenes_data == {} and cannabinoid_data == {}:
			skip_this_file = True

		sample_data = {
			'Test Result UID':test_uid,
			'Sample Name':sample_name,
			'Test Time':test_time,
			'Receival Time':receival_time,
			'Provider':sample_provider,
			'Sample Type':sample_type
		}
		sample_data.update(terpenes_data)
		sample_data.update(cannabinoid_data)

		for sample_data_field in list(sample_data.keys()):
			if sample_data_field not in DATA_ROW_FIELDS:
				del sample_data[sample_data_field]

		if not skip_this_file:
			if args.csv:
				write_to_csv(
					sample_database_CSVfile,
					DATA_ROW_FIELDS,
					sample_data
				)
			if args.json:
				with open(sample_database_JSONfile, "a", encoding="utf-8") as databases_file:
					if file_index != 0:
						databases_file.write(',')
					json.dump(sample_data, databases_file, separators=(',', ':'), sort_keys=True)
	if args.json:
		with open(sample_database_JSONfile, "a", encoding="utf-8") as databases_file:
			databases_file.write(']')

log_this('Finished main loop.', level=3)

if args.json:
	with open(sample_database_JSONfile, "a", encoding="utf-8") as databases_file:
		databases_file.write('}}')

log_this('All files have been processed. Please check the contents of the log-files (starting with "log-"). Those list pages regarding different errors.', level=1, override=True)
log_this('Also, note the lines starting with "INFO: " or "DETAIL: ".', level=1, override=True)
