#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import scrapy, os, urllib.parse, re, datetime, scrapy.spidermiddlewares.httperror, db, scrapy_splash

# 'png': 1,
# 'width': 600,
# 'render_all': 1,
# 'http_method': 'GET'
MAX_NO_CONSECUTIVE_TERPENES = 100
SAVE_FOLDER = '../database_dump'
DATABASE_PATH = '../../../strainfinder.db'
counter = 1
splash_args = {
	'endpoint': 'render.json',
	'args': {
		'html': 1,
		"wait": 2.0,
		'magic_response': True,
		'http_status_from_error_code': True,
	}
}
re_sampleURLPath = re.compile(r'^/sample/(?P<sample_id>\d+)/?', re.IGNORECASE)
re_totalTerpenesNT = re.compile(r'^\s*Total\s+Terpenes\s*:?\s*NT\s*', re.IGNORECASE)

class OnlineDatabaseSpider(scrapy.Spider):
	name = 'sclabs'

	error_selectors = {
		'403': '/html/body/div/div/div/div/div/div/div/div/h3/span[text()="Error 403"]/text()',
		'404': '/html/body/div/div/div/div/div/div/div/div/h3/span[text()="Error 404"]/text()'
	}
	xpath_savepage_loaded = 'div[@id="terpene-detail"]/div/div/div[@id="terpene_chart_percent"]/div[svg][div/span]'
	xpath_savepages = 'h3/a[@href]'
	xpath_samples = '/html/body/div//div[@id="client-results"]/div[@class="client-gridview"]/div/div[@class="inner-block"]'
	xpath_resultspage_maxpage = '/html/body/div//ul[@id="mysample-pagination"][li/a[@class="active"]]/li[last()]/a/@data-value'
	xpath_resultspage_currentpage = '/html/body/div//ul[@id="mysample-pagination"]/li/a[@class="active"]/@data-value'
	xpath_samplepreview_totalterpenesNT = '''ul/li[
												contains(
													translate(
														concat(' ', normalize-space(text()), ' '),
														'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
														'abcdefghijklmnopqrstuvwxyz'
													),
													'total terpenes: nt'
												)
											]/text()
										'''

	template_resultspage = 'https://client.sclabs.com/client/{client_number}/?limit=100&page={page}'
	template_savepage = 'https://client.sclabs.com/sample/{sample_number:0>{padding}}/'

	def __init__(self):
		self.logger.debug('Initializing Spider')
		if not os.path.exists(SAVE_FOLDER):
			os.makedirs(SAVE_FOLDER)
		self.logger.debug('Connecting to DB at "%s".', DATABASE_PATH)
		self.session = db.init_session(DATABASE_PATH)
		self.lab_id = self.session.query(db.Lab.id).filter(db.Lab.identifier==self.name).first().id
		self.logger.debug('Lab ID of "%s" is "%d".', self.name, self.lab_id)

	def start_requests(self):
		'''Generates the client links'''
		self.logger.debug('Launching initial requests . . .')

		for client_number in range(7600, -1, -1): #TODO
			self.logger.debug('%d: Building request for client.', client_number)
			wanted_link = self.template_resultspage.format(client_number=client_number, page=1)
			request = scrapy.Request(url=wanted_link, callback=self.read_client, errback=self.errback)
			request.meta['data-sclabs-client-number'] = client_number
			request.meta['data-sclabs-client-lastknown-maxpage'] = 10000
			request.meta['data-sclabs-client-currentpage'] = 1
			self.logger.debug('%d: Setting currentpage counter to "%d".', client_number, request.meta['data-sclabs-client-currentpage'])
			request.meta['data-sclabs-NTterpenes-counter'] = 0
			self.logger.debug('%d: Setting NTterpenes counter to "%d".', client_number, request.meta['data-sclabs-NTterpenes-counter'])
			request.meta['dont_cache'] = True
			page = self.session.query(db.Page).filter(db.Page.source_url==wanted_link).first()
			if page:
				self.logger.debug('%d: Page already in database.', client_number)
				page.online_database_id = self.lab_id
			else:
				self.logger.debug('%d: Page not in database yet.', client_number)
				page = db.Page(source_url=wanted_link, online_database_id=self.lab_id)
				self.session.add(page)
			self.session.commit()
			self.logger.debug('%d: Yielding request.', client_number)
			yield request
		# for sample_number in range(0,310000):
		# 	self.logger.debug('Building request for sample "%d".', sample_number)
		# 	for padding in range(1):
		# 		self.logger.debug('Using padding "%d".', padding)
		# 		wanted_link = self.template_savepage.format(sample_number=sample_number, padding=padding)
		# 		page = self.session.query(db.Page).filter(db.Page.source_url==wanted_link).first()
		# 		if page:
		# 			self.logger.debug('Sample page already in database.')
		# 			page.online_database_id = self.lab_id
		# 		else:
		# 			self.logger.debug('Sample page not in database yet.')
		# 			page = db.Page(source_url=wanted_link, online_database_id=self.lab_id)
		# 			self.session.add(page)
		# 		self.session.commit()
		# 		self.logger.debug('Yielding request.')
		# 		yield scrapy_splash.SplashRequest(url=wanted_link, callback=self.read_sample, args=splash_args, errback=self.errback)

	def real_statusCode(self, response):
		'''tests current page for errors'''
		client_number = response.meta['data-sclabs-client-number']

		self.logger.debug('%d: Detecting actual HTTP status code...', client_number)
		status_code = 0

		for error_code in self.error_selectors.items():
			if response.xpath(error_code[1]):
				status_code = int(error_code[0])
		else:
			status_code = response.status
		self.logger.debug('%d: Has HTTP status code "%s".', client_number, status_code)

	def errback(self, failure):
		'''Logs failed pages'''
		now = datetime.datetime.utcnow()
		source_url = failure.value.response.url
		status_code = failure.value.response.status
		self.logger.warning('Detected error while requesting page "%s".', source_url)

		if failure.check(scrapy.spidermiddlewares.httperror.HttpError):
			page = self.session.query(db.Page).filter(db.Page.source_url==source_url).first()
			if page:
				self.logger.debug('Page already exists in DB.')
				page.status = status_code
				page.fetched_at = now
				page.online_database_id = self.lab_id
			else:
				self.logger.debug('Page not existing in DB yet.')
				page = db.Page(source_url=source_url, status=status_code, fetched_at=now, online_database_id=self.lab_id)
				self.session.add(page)
			self.session.commit()

	def read_client(self, response):
		'''flip through client pages'''
		now = datetime.datetime.utcnow()
		client_number = response.meta['data-sclabs-client-number']
		no_terpenes_counter = response.meta['data-sclabs-NTterpenes-counter']
		page = self.session.query(db.Page).filter(db.Page.source_url==response.url).first()
		page.status = self.real_statusCode(response)
		page.fetched_at = now
		page.online_database_id = self.lab_id
		self.session.commit()

		self.logger.debug('%d: reading client, NTterpenes is "%d".', client_number, no_terpenes_counter)

		for elem_sample in response.xpath(self.xpath_samples):
			relative_sample_link = elem_sample.xpath(self.xpath_savepages)[0]
			sample_link = response.urljoin(relative_sample_link.attrib['href'])
			if no_terpenes_counter >= MAX_NO_CONSECUTIVE_TERPENES:
				self.logger.debug('%d consecutive samples without terpene tests, aborting page.', no_terpenes_counter)
				break
			raw_totalTerpenes = elem_sample.xpath(self.xpath_samplepreview_totalterpenesNT)
			should_crawl = True
			if len(raw_totalTerpenes) > 0:
				re_totalTerpenesNT_match = re_totalTerpenesNT.match(raw_totalTerpenes[0].extract())
				if re_totalTerpenesNT_match:
					no_terpenes_counter += 1
					should_crawl = False
					self.logger.debug('Terpene test not present, will not crawl sample "%s", counter is now "%d".', sample_link, no_terpenes_counter)
				else:
					no_terpenes_counter = 0
					should_crawl = True
					self.logger.debug('Terpene test present, will crawl sample "%s", counter has been reset.', sample_link)
			if should_crawl:
				self.logger.debug('%d: Building request for sample "%s".', client_number, sample_link)
				request = scrapy_splash.SplashRequest(url=sample_link, callback=self.read_sample, args=splash_args, errback=self.errback)
				request.meta['data-sclabs-client-number'] = client_number
				page = self.session.query(db.Page).filter(db.Page.source_url==sample_link).first()
				if page:
					self.logger.debug('%d: Sample page already in DB.', client_number)
					page.prev_url = response.url
					page.online_database_id = self.lab_id
				else:
					self.logger.debug('%d: Sample page not in DB yet.', client_number)
					page = db.Page(source_url=sample_link, prev_url=response.url, online_database_id=self.lab_id)
					self.session.add(page)
				self.session.commit()
				if page.file:
					self.logger.debug('%d: A file is already associated with sample page of URL "%s", skipping.', client_number, sample_link)
				else:
					self.logger.debug('%d: No file yet associated with sample page of URL "%s", yielding request.', client_number, sample_link)
					yield request

		self.logger.debug('%d: Now I am determining if I should crawl the next client page.', client_number)
		if no_terpenes_counter < MAX_NO_CONSECUTIVE_TERPENES:
			self.logger.debug('%d: NTterpenes counter is "%d" below limit "%d".', client_number, no_terpenes_counter, MAX_NO_CONSECUTIVE_TERPENES)
			self.logger.debug('%d: Determining current page', client_number)
			currentpage_match = response.xpath(self.xpath_resultspage_currentpage)
			if currentpage_match:
				try:
					currentpage_num = int(currentpage_match[0].extract())
				except ValueError:
					currentpage_num = None

			if (currentpage_num == None) or (not currentpage_match):
				currentpage_num = response.meta['data-sclabs-client-currentpage']
			self.logger.debug('%d: Current page seems to be "%d".', client_number, currentpage_num)

			self.logger.debug('%d: Determining last (maximum) page of client.', client_number)
			maxpage_match = response.xpath(self.xpath_resultspage_maxpage)
			if maxpage_match:
				try:
					maxpage_num = int(maxpage_match[0].extract())
				except ValueError:
					maxpage_num = None

			if (maxpage_num == None) or (not maxpage_match):
				maxpage_num = response.meta['data-sclabs-client-lastknown-maxpage']
			self.logger.debug('%d: Last client page seems to be "%d".', client_number, maxpage_num)

			if currentpage_num < maxpage_num and currentpage_num < 10000:
				self.logger.debug('%d: Current page is below limit :)', client_number)
				wanted_link = self.template_resultspage.format(client_number=client_number, page=currentpage_num+1)
				request = scrapy.Request(url=wanted_link, callback=self.read_client, errback=self.errback)
				request.meta['data-sclabs-client-lastknown-maxpage'] = maxpage_num
				request.meta['data-sclabs-client-currentpage'] = currentpage_num+1
				request.meta['data-sclabs-client-number'] = client_number
				request.meta['data-sclabs-NTterpenes-counter'] = no_terpenes_counter
				# if currentpage_num+1 == maxpage_num:
				# 	request.meta['dont_cache'] = True
				next_page = self.session.query(db.Page).filter(db.Page.source_url==wanted_link).first()
				if next_page:
					self.logger.debug('%d: Next client page already in DB.', client_number)
					next_page.prev_url = response.url
					next_page.online_database_id = self.lab_id
				else:
					self.logger.debug('%d: Next client page not in DB yet.', client_number)
					next_page = db.Page(source_url=wanted_link, prev_url=response.url, online_database_id=self.lab_id)
					self.session.add(next_page)
				self.session.commit()
				self.logger.debug('%d: Yielding request for next client page.', client_number)
				yield request

	def read_sample(self, response):
		'''detect sample page'''

		now = datetime.datetime.utcnow()
		client_number = response.meta['data-sclabs-client-number']

		self.logger.debug('%d: Reading sample "%s".', client_number, response.url)

		page = self.session.query(db.Page).filter(db.Page.source_url==response.url).first()
		if page:
			self.logger.debug('%d: Sample page already exists in DB.', client_number)
			page.fetched_at = now
		else:
			self.logger.debug('%d: Sample page does not exist in DB yet.', client_number)
			page = db.Page(source_url=response.url, status=response.status, fetched_at=now)
		self.session.commit()

		xpath_savepage_loaded_match = response.xpath(self.xpath_savepage_loaded)
		# if xpath_savepage_loaded_match:
		# 	page.status = response.status
		# 	self.save_this(response)
		# else:
		# 	self.log('PAGE {} WILL NOT BE SAVED!'.format(response.url))
		# 	page.status = -404
		page.status = response.status
		self.session.commit()
		self.save_this(response)

	def save_this(self, response):
		'''Save the given page'''
		client_number = response.meta['data-sclabs-client-number']

		self.logger.debug('%d: Saving page from URL "%s".', client_number, response.url)

		counter = 1
		parsedURL = urllib.parse.urlparse(response.url)
		re_sampleURLPath_match = re_sampleURLPath.match(parsedURL.path)
		if re_sampleURLPath_match:
			sample_id = re_sampleURLPath_match.group('sample_id')
			self.logger.debug('%d: Got sample ID "%s".', client_number, sample_id)
		else:
			sample_id = 'NOID'
			self.logger.debug('%d: No sample ID found.', client_number)
		filename = '{}.html'.format(sample_id)
		filepath = os.path.join(SAVE_FOLDER, filename)
		while os.path.exists(filepath) or self.session.query(db.Page).filter(db.Page.file==filename).first():
			counter += 1
			filename = '{}_{}.html'.format(sample_id, counter)
			filepath = os.path.join(SAVE_FOLDER, filename)
		with open(filepath, 'wb') as f:
			f.write(response.body)
		page = self.session.query(db.Page).filter(db.Page.source_url==response.url).first()
		if page:
			self.logger.debug('%d: Sample page already exists in DB.', client_number)
			page.file = filename
		else:
			self.logger.debug('%d: Sample page not existing in DB yet.', client_number)
			page = db.Page(source_url=response.url, file=filename)
			self.session.add(page)
		self.session.commit()
		self.logger.debug('%d: Saved page "%s" under file "%s".', client_number, response.url, filepath)

	def closed(self, reason):
		'''Close DB Connection'''
		self.logger.debug('Closing spider (closing DB connection).')
		self.session.commit()
		self.session.close()

class SplashTestSpider(scrapy.Spider):
	name = 'splashtest'

	def start_requests(self):
		'''Generates the client links'''
		yield scrapy_splash.SplashRequest(url='https://maxvalue.github.io/IsJavascriptWorking/', callback=self.parse, args=splash_args)

	def parse(self, response):
		query_results = response.xpath('//span[@id="result"]/text()')
		if query_results:
			test_element = query_results[0]
			self.log('Text is "{}".'.format(test_element.extract()))
		else:
			self.log('No element found!')
