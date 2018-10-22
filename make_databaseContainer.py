#!/usr/bin/env python3
# coding: utf-8

import re, csv, argparse, json, logging

parser = argparse.ArgumentParser(argument_default=False, description='Clean raw lab data.')
parser.add_argument('database', nargs='?', default='results.csv', help='The location of the database dump.')
parser.add_argument('--verbose', '-v', action='count', default=0, help='Turn on verbose mode.')
parser.add_argument('--log', help='Logfile path. If omitted, stdout is used.')
parser.add_argument('--debug', '-d', action='store_true', help='Log all messages including debug.')
args = parser.parse_args()

if args.debug:
	loglevel = logging.DEBUG
elif args.verbose:
	loglevel = logging.INFO
else:
	loglevel = logging.WARNING

if args.log:
	logging.basicConfig(filename=args.log, filemode='a', level=loglevel)
else:
	logging.basicConfig(level=loglevel)

logging.debug('Loading configurations . . .')

terpenes = {
	'delta-3-Carene':		re.compile(r'^(delta)?[-_/\s.]*(3|Three|Tri)[-_/\s.]*Carene$',	re.IGNORECASE),
	'Camphene':				re.compile(r'^Camphene$',										re.IGNORECASE),
	'Caryophyllene Oxide':	re.compile(r'^Caryophyllene[-_/\s.]*Oxide$',					re.IGNORECASE),
	'Eucalyptol':			re.compile(r'^Eucalyptol$',										re.IGNORECASE),
	'Farnesene': 			re.compile(r'^Farnesene$',										re.IGNORECASE),
	'Geraniol':				re.compile(r'^Geraniol$',										re.IGNORECASE),
	'Guaiol':				re.compile(r'^Guaiol$',											re.IGNORECASE),
	'Isopulegol':			re.compile(r'^(\(-\)[-_/\s.]+)?Isopulegol$',					re.IGNORECASE),
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

sample_types = {
	'Flower': 'Unprocessed',
	'Honey Bud, Flower, Inhalable': 'Unprocessed',
	'Flower, Inhalable': 'Unprocessed',
	'Indica, Flower, Inhalable': 'Unprocessed',
	'Hybrid, Flower, Inhalable': 'Unprocessed',
	'Sativa, Flower, Inhalable': 'Unprocessed',
	'Edible Concentrate': 'Proccessed',
	'Concentrate': 'Proccessed',
	'Edible': 'Proccessed',
	'Infusion': 'Proccessed',
	'Oil, Concentrate, Inhalable': 'Proccessed',
	'Essential Oil, Infused, Other': 'Proccessed',
	'Kief, Concentrate, Inhalable': 'Proccessed',
	'Terpene, Concentrate, Inhalable': 'Proccessed',
	'Concentrate, Inhalable': 'Proccessed',
	'Rosin, Concentrate, Inhalable': 'Proccessed',
	'Crumble, Concentrate, Inhalable': 'Proccessed',
	'Infused, Other': 'Proccessed',
	'Live Resin , Concentrate, Inhalable': 'Proccessed',
	'Wax, Concentrate, Inhalable': 'Proccessed',
	'Shatter, Concentrate, Inhalable': 'Proccessed',
	'Hash, Concentrate, Inhalable': 'Proccessed',
	'Topical': 'Proccessed',
	'Liquid': 'Proccessed',
	'Oil': 'Proccessed',
}

databasesContainer = {
	'databases': {}
}

with open('results.csv', 'r', encoding='utf-8') as resultsCSV:
	resultsCSV_reader = csv.DictReader(resultsCSV)
	logging.info('Entering main CSV parsing loop . . .')
	for row in resultsCSV_reader:
		if row['Database'] not in databasesContainer['databases']:
			databasesContainer['databases'][row['Database']] = {}
		if row['Sample Type'] in sample_types:
			if sample_types[row['Sample Type']] not in databasesContainer['databases'][row['Database']]:
				databasesContainer['databases'][row['Database']][sample_types[row['Sample Type']]] = []
		else:
			continue
		sample_data = {
			'Database': row['Database'],
			'Sample Name': row['Sample Name']
		}
		for terpene_name in terpenes.keys():
			if terpene_name in row:
				sample_data[terpene_name] = row[terpene_name]
		databasesContainer['databases'][row['Database']][sample_types[row['Sample Type']]].append(
			sample_data
		)

	logging.debug('Finished main loop.')

logging.info('Writing finished structure to file.')
with open('docs/results.json', "w", encoding="utf-8") as databasesContainer_file:
	databasesContainer_file.write('databasesContainer=')
	json.dump(databasesContainer, databasesContainer_file, separators=(',', ':'))

print('Done!')
