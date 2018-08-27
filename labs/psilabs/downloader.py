#!/usr/bin/env python3
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as selenium_webdriver_support_expectedConditions
from selenium.common.exceptions import TimeoutException as selenium_common_exceptions_TimeoutException
from selenium.common.exceptions import ElementNotInteractableException as selenium_common_exceptions_ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException as selenium_common_exceptions_ElementClickInterceptedException
import argparse, time, os, re, csv, urllib, datetime

parser = argparse.ArgumentParser(argument_default=False, description='Download raw lab data.')
parser.add_argument('--verbose', '-v', action='count', default=0, help='Turn on verbose mode.')
parser.add_argument('--force-redownload', action='store_true', help='Downloads pages even if they already exist. Will not overwrite existing page.')
parser.add_argument('--check-newest', type=int, action='store', nargs='?', const=10, help='Sorts by "Desc". Stops when first 10 existing samples are encountered.')
parser.add_argument('-p', '--profile', default='../browser_profiles/firefox', help='Path to a valid Firefox profile if you wanna use a specially prepared profile.')
parser.add_argument('--wait-after-newtab', default=0, type=int, help='Whether to wait after a new tab is opened and for how many seconds.')
parser.add_argument('--newtab-url', default='about:blank', help='What page should be initially loaded when a new tab is opened.')
parser.add_argument('-s', '--save-path', default='database_dump/', help='In which folder to save the downloaded pages.')
args = parser.parse_args()

def log_this(msg, verbosity=3, override=False):
	if verbosity <= args.verbose or override:
		if verbosity == 1:
			print('INFO {}'.format(msg))
		elif verbosity == 2:
			print('DETAIL {}'.format(msg))
		elif verbosity == 3:
			print('DEBUG {}'.format(msg))

log_this('loading configs', 1)

def open_newtab(url=args.newtab_url, delay=0.05, max_tries=100):
	global browser
	'''Returns the window handle of the new tab.'''
	windows_before = set(browser.window_handles)
	browser.execute_script('window.open("{}", "_blank");'.format(url))
	for i in range(max_tries):
		new_handles = windows_before ^ set(browser.window_handles)
		if len(new_handles) == 0:
			time.sleep(delay)
		else:
			return new_handles.pop()

def wait_for_element(xpath, timeout=600):
	global browser
	try:
		selection = webdriver.support.ui.WebDriverWait(browser, timeout).until(
			selenium_webdriver_support_expectedConditions.presence_of_all_elements_located(
				(webdriver.common.by.By.XPATH,xpath)
			)
		)
	except:
		return False
	return selection

def select_dropdown_option(dropdown_id, option_selector, fallback_text, verification_selector, timeout=60):
	global browser
	dropdown = browser.find_element_by_id(dropdown_id)
	try:
		if type(dropdown) == webdriver.firefox.webelement.FirefoxWebElement:
			dropdown.click()
			dropdown_option = browser.find_element_by_xpath(option_selector)
			if type(dropdown_option) == webdriver.firefox.webelement.FirefoxWebElement:
				dropdown_option.click()
			else:
				input(fallback_text)
	except (selenium_common_exceptions_ElementNotInteractableException, selenium_common_exceptions_ElementClickInterceptedException) as e:
		input(fallback_text)
	verification_element = wait_for_element(verification_selector, timeout)
	if verification_element:
		return True
	else:
		return False

def select_checkbox(checkbox_selector, fallback_text, verification_selector, timeout=60):
	global browser
	checkbox = browser.find_element_by_xpath(checkbox_selector)
	try:
		if type(checkbox) == webdriver.firefox.webelement.FirefoxWebElement:
			checkbox.click()
		else:
			input(fallback_text)
	except (selenium_common_exceptions_ElementNotInteractableException, selenium_common_exceptions_ElementClickInterceptedException) as e:
		input(fallback_text)
	verification_element = wait_for_element(verification_selector, timeout)
	if verification_element:
		return True
	else:
		return False

def write_to_csv(filepath, fieldnames, data):
	if os.path.exists(filepath):
		writeheader = False
	else:
		writeheader = True
	with open(filepath, 'a', encoding='utf-8') as writefile:
		writefile_writer = csv.DictWriter(writefile, fieldnames=fieldnames, lineterminator='\n')
		if writeheader:
			writefile_writer.writeheader()
		writefile_writer.writerow(data)

URL_sample_result = 'https://psilabs.org/results/test-results/show/'
counter = 1
os.makedirs(args.save_path, exist_ok=True)

slug = ''
encountered_known_samples = 0
try:
	options = webdriver.FirefoxOptions()
	if args.profile:
		profile = webdriver.FirefoxProfile(profile_directory=args.profile)
		options._profile = profile
	options.set_preference('browser.link.open_newwindow',3)
	options.set_preference('browser.link.open_newwindow.override.external',3)
	options.set_preference('browser.link.open_newwindow.restriction',0)
	log_this('starting browser', 1)
	if args.profile:
		browser=webdriver.Firefox(firefox_profile=profile, options=options)
	else:
		browser=webdriver.Firefox(options=options)

	browser.get('https://psilabs.org/results/test-results/?page=1')
	results_list_loaded = wait_for_element(
		'//sample-card/md-card/md-card-title/md-card-title-text/span/a'
	)
	if not results_list_loaded:
		exit('Could not load initial list.')
	current_page = '0'

	# the following selectors (those with the numbers) are very likely to break soon
	select_dropdown_option(
		'select_49',
		'//md-option[@value="dateTested"][div[text()="Date Tested"]]',
		'In the "Filter" pane please click on "Sort By" > "Date Tested". If you are done, press enter here to continue.',
		'//sample-card/md-card/md-card-title/md-card-title-text/span/a'
	)

	if args.check_newest:
		select_dropdown_option(
			'select_53', #//md-input-container/md-select[md-select-value/span/div[starts-with("Desc")]]
			'//md-option[@value="desc"][div[text()="Desc"]]',
			'In the "Filter" pane please click on "Direction" > "Desc". If you are done, press enter here to continue.',
			'//sample-card/md-card/md-card-title/md-card-title-text/span/a'
		)
	else:
		select_dropdown_option(
			'select_53', #//md-input-container/md-select[md-select-value/span/div[starts-with("Asc")]]
			'//md-option[@value="asc"][div[text()="Asc"]]',
			'In the "Filter" pane please click on "Direction" > "Asc". If you are done, press enter here to continue.',
			'//sample-card/md-card/md-card-title/md-card-title-text/span/a'
		)

	select_checkbox(
		'//md-checkbox[@aria-label="Terpene Profile"]',
		'In the "Filter" pane please click on "TESTS INCLUDED" > "Terpene Profile". If you are done, press enter here to continue.',
		'//sample-card/md-card/md-card-title/md-card-title-text/span/a'
	)

	tab_results_list = browser.window_handles[0]
	browser.switch_to.window(tab_results_list)

	log_this('starting loop', 1)
	while True:
		raw_search_results = wait_for_element(
			'//sample-card/md-card/md-card-title/md-card-title-text/span/a'
		)

		previous_page = current_page
		current_url = urllib.parse.urlparse(browser.current_url)
		current_page = urllib.parse.parse_qs(current_url.query)['page'][0]

		if raw_search_results:
			if current_page == previous_page:
				log_this('Reached last page!', 1)
				break
		else:
			log_this('Could not retrieve results page {}'.format(current_page), 1)
			write_to_csv(os.path.join(args.save_path, 'failed_result_pages.csv'), ['Page URL'], {'Page URL':current_page})
			continue

		sample_urls = []
		for search_result_element in raw_search_results:
			search_result_url = search_result_element.get_attribute('href')
			if search_result_url.startswith('https://psilabs.org/results/clients'):
				continue
			sample_urls.append(search_result_url)
		for sample_url in sample_urls:
			if sample_url.startswith(URL_sample_result):
				slug = sample_url[len(URL_sample_result):]
			else:
				write_to_csv(os.path.join(args.save_path, 'link_not_sample_or_provider.csv'), ['URL'], {'URL':sample_url})
			slug = re.sub(r'[^0-9A-Za-z]', '', slug)
			log_this('Getting Sample {}'.format(sample_url), 1)
			if args.check_newest and os.path.exists(os.path.join(args.save_path, '{}.html'.format(slug))):
				encountered_known_samples += 1
				log_this('Found existing sample {}'.format(slug), 1)
				if encountered_known_samples >= args.check_newest:
					browser.quit()
					exit('Quitting')
			if not args.force_redownload and os.path.exists(os.path.join(args.save_path, '{}.html'.format(slug))):
				log_this('Already exists: skipping.', 1)
				continue
			tab_result_page = open_newtab()
			browser.switch_to.window(tab_result_page)
			time.sleep(args.wait_after_newtab)
			browser.get(sample_url)
			# SECOND TAB
			if len(wait_for_element('//md-content/div/md-card/md-card-header/md-card-header-text/span[@class="md-title"][not(text()="")]'))>1:
				time.sleep(0.5)
			else:
				log_this('Could not save sample {}'.format(sample_url), 1)
				write_to_csv(os.path.join(args.save_path, 'failed_samples.csv'), ['Sample URL'], {'Sample URL':sample_url})
				continue
			filename = os.path.join(args.save_path, '{}.html'.format(slug))
			counter = 1
			while os.path.exists(filename):
				counter += 1
				filename = os.path.join(args.save_path,'{}_{}.html'.format(slug, counter))
			with open(filename, 'w', encoding='utf-8') as sample_file:
				sample_file.write(browser.page_source)
			log_this('Saved to file {}'.format(filename), 1)
			# SECOND TAB END
			browser.close()
			browser.switch_to.window(tab_results_list)
		log_this('getting next results page', 1)
		button_next = browser.find_element_by_xpath('//page-selector/ul/li/button[md-icon[text()="chevron_right"]]')
		button_next.click()
	browser.quit()
	log_this('Finished!', 1, True)
except KeyboardInterrupt as e:
	browser.quit()
	exit('Last sample was {}'.format(slug))
