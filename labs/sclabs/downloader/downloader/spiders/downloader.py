#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import scrapy, os, urllib.parse, re, datetime, scrapy.spidermiddlewares.httperror
import sqlalchemy as sqla
import db

# 'png': 1,
# 'width': 600,
# 'render_all': 1,
# 'http_method': 'GET'
MAX_NO_CONSECUTIVE_TERPENES = 100
SAVE_FOLDER = '../database_dump'
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
		if not os.path.exists(SAVE_FOLDER):
			os.makedirs(SAVE_FOLDER)
		self.session = db.init_session('../../../strainfinder.db')
		self.lab_id = self.session.query(db.Lab.id).filter(db.Lab.identifier==self.name).first().id

	def start_requests(self):
		'''Generates the client links'''

		for client_number in range(3000, -1, -1): #TODO
			wanted_link = self.template_resultspage.format(client_number=client_number, page=1)
			request = scrapy.Request(url=wanted_link, callback=self.read_client, errback=self.errback)
			request.meta['data-sclabs-client-number'] = client_number
			request.meta['data-sclabs-client-lastknown-maxpage'] = 10000
			request.meta['data-sclabs-client-currentpage'] = 1
			request.meta['data-sclabs-NTterpenes-counter'] = 0
			request.meta['dont_cache'] = True
			page = self.session.query(db.Page).filter(db.Page.source_url==wanted_link).first()
			if page:
				page.online_database_id = self.lab_id
			else:
				page = db.Page(source_url=wanted_link, online_database_id=self.lab_id)
				self.session.add(page)
			self.session.commit()
			yield request
		for sample_number in range(0,310000):
			for padding in range(0,7):
				wanted_link = self.template_savepage.format(sample_number=sample_number, padding=padding)
				page = self.session.query(db.Page).filter(db.Page.source_url==wanted_link).first()
				if page:
					page.online_database_id = self.lab_id
				else:
					page = db.Page(source_url=wanted_link, online_database_id=self.lab_id)
					self.session.add(page)
				self.session.commit()
				yield scrapy.Request(url=wanted_link, callback=self.read_sample, meta={'splash':splash_args}, errback=self.errback)

	def has_error(self, response):
		'''tests current page for errors'''

		for error_code in self.error_selectors.items():
			if response.xpath(error_code[1]):
				return error_code[0]
		else:
			return False

	def errback(self, failure):
		'''Logs failed pages'''
		now = datetime.datetime.utcnow()

		if failure.check(scrapy.spidermiddlewares.httperror.HttpError):
			source_url = failure.value.response.url
			status_code = failure.value.response.status
			page = self.session.query(db.Page).filter(db.Page.source_url==source_url).first()
			if page:
				page.status = status_code
				page.fetched_at = now
				page.online_database_id = self.lab_id
			else:
				page = db.Page(source_url=source_url, status=status_code, fetched_at=now, online_database_id=self.lab_id)
				self.session.add(page)
			self.session.commit()

	def read_client(self, response):
		'''flip through client pages'''
		now = datetime.datetime.utcnow()
		client_number = response.meta['data-sclabs-client-number']
		no_terpenes_counter = response.meta['data-sclabs-NTterpenes-counter']

		for elem_sample in response.xpath(self.xpath_samples):
			if no_terpenes_counter >= MAX_NO_CONSECUTIVE_TERPENES:
				break
			raw_totalTerpenes = elem_sample.xpath(self.xpath_samplepreview_totalterpenesNT)
			should_crawl = True
			if len(raw_totalTerpenes) > 0:
				re_totalTerpenesNT_match = re_totalTerpenesNT.match(raw_totalTerpenes[0].extract())
				if re_totalTerpenesNT_match:
					no_terpenes_counter += 1
					should_crawl = False
				else:
					no_terpenes_counter = 0
					should_crawl = True
			if should_crawl:
				relative_sample_link = elem_sample.xpath(self.xpath_savepages)[0]
				sample_link = response.urljoin(relative_sample_link.attrib['href'])
				request = scrapy.Request(url=sample_link, callback=self.read_sample, meta={'splash':splash_args}, errback=self.errback)
				request.meta['data-sclabs-client-number'] = client_number
				page = self.session.query(db.Page).filter(db.Page.source_url==sample_link).first()
				if page:
					page.prev_url = response.url
					page.online_database_id = self.lab_id
				else:
					page = db.Page(source_url=sample_link, prev_url=response.url, online_database_id=self.lab_id)
					self.session.add(page)
				self.session.commit()
				if not page.file:
					yield request

		if no_terpenes_counter < MAX_NO_CONSECUTIVE_TERPENES:
			currentpage_match = response.xpath(self.xpath_resultspage_currentpage)
			if currentpage_match:
				try:
					currentpage_num = int(currentpage_match[0].extract())
				except ValueError:
					currentpage_num = None

			if (currentpage_num == None) or (not currentpage_match):
				currentpage_num = response.meta['data-sclabs-client-currentpage']

			maxpage_match = response.xpath(self.xpath_resultspage_maxpage)
			if maxpage_match:
				try:
					maxpage_num = int(maxpage_match[0].extract())
				except ValueError:
					maxpage_num = None

			if (maxpage_num == None) or (not maxpage_match):
				maxpage_num = response.meta['data-sclabs-client-lastknown-maxpage']

			if currentpage_num < maxpage_num and currentpage_num < 10000:
				wanted_link = self.template_resultspage.format(client_number=client_number, page=currentpage_num+1)
				request = scrapy.Request(url=wanted_link, callback=self.read_client, errback=self.errback)
				request.meta['data-sclabs-client-lastknown-maxpage'] = maxpage_num
				request.meta['data-sclabs-client-currentpage'] = currentpage_num
				request.meta['data-sclabs-client-number'] = client_number
				request.meta['data-sclabs-NTterpenes-counter'] = no_terpenes_counter
				if currentpage_num+1 == maxpage_num:
					request.meta['dont_cache'] = True
				next_page = self.session.query(db.Page).filter(db.Page.source_url==wanted_link).first()
				if next_page:
					next_page.prev_url = response.url
					next_page.online_database_id = self.lab_id
				else:
					next_page = db.Page(source_url=wanted_link, prev_url=response.url, online_database_id=self.lab_id)
					self.session.add(next_page)
				self.session.commit()
				yield request

		page = self.session.query(db.Page).filter(db.Page.source_url==response.url).first()
		error_match = self.has_error(response)
		if error_match:
			page.status = error_match
		else:
			page.status = response.status
		page.fetched_at = now
		page.online_database_id = self.lab_id
		self.session.commit()

	def read_sample(self, response):
		'''detect sample page'''

		now = datetime.datetime.utcnow()

		page = self.session.query(db.Page).filter(db.Page.source_url==response.url).first()
		if page:
			page.fetched_at = now
		else:
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

		counter = 1
		parsedURL = urllib.parse.urlparse(response.url)
		re_sampleURLPath_match = re_sampleURLPath.match(parsedURL.path)
		if re_sampleURLPath_match:
			sample_id = re_sampleURLPath_match.group('sample_id')
		else:
			sample_id = 'NOID'
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
			page.file = filename
		else:
			page = db.Page(source_url=response.url, file=filename)
			self.session.add(page)
		self.session.commit()
		self.log('Saved page {} under file {}'.format(response.url, filepath))

	def closed(self, reason):
		'''Close DB Connection'''
		self.session.commit()
		self.session.close()

class SplashTestSpider(scrapy.Spider):
	name = 'splashtest'

	def start_requests(self):
		'''Generates the client links'''
		yield scrapy.Request(url='https://maxvalue.github.io/IsJavascriptWorking/', callback=self.parse, meta={'splash':splash_args})

	def parse(self, response):
		query_results = response.xpath('//span[@id="result"]/text()')
		if query_results:
			test_element = query_results[0]
			self.log('Text is "{}".'.format(test_element.extract()))
		else:
			self.log('No element found!')
