# -*- coding: utf-8 -*-
import os
import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base as sqla_declarative_base

Base = sqla_declarative_base()

class Lab(Base):
	__tablename__ = 'online_databases'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	name = sqla.Column('name', sqla.String, nullable=False, unique=True)
	identifier = sqla.Column('identifier', sqla.String, nullable=False)
	url = sqla.Column('url', sqla.String)

class Page(Base):
	__tablename__ = 'pages'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	online_database_id = sqla.Column('online_database_id', None, sqla.ForeignKey('online_databases.id'))
	source_url = sqla.Column('source_url', sqla.String, nullable=False, unique=True)
	prev_url = sqla.Column('prev_url', sqla.String)
	status = sqla.Column('status', sqla.Integer)
	fetched_at = sqla.Column('fetched_at', sqla.TIMESTAMP)
	file = sqla.Column('file', sqla.String)
	post_time = sqla.Column('post_time', sqla.TIMESTAMP)

	online_database = sqla.orm.relationship('Lab', back_populates='pages')

class SampleProvider(Base):
	__tablename__ = 'sample_providers'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	name = sqla.Column('name', sqla.String, nullable=False)
	url = sqla.Column('url', sqla.String)
	contact_email = sqla.Column('contact_email', sqla.String)

class Sample(Base):
	__tablename__ = 'samples'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	provider_id = sqla.Column('provider_id', None, sqla.ForeignKey('sample_providers.id'))
	sample_name = sqla.Column('sample_name', sqla.String)
	sample_uid = sqla.Column('sample_uid', sqla.String)
	sample_type = sqla.Column('sample_type', sqla.String)
	receipt_time = sqla.Column('receipt_time', sqla.TIMESTAMP)

	provider = sqla.orm.relationship('SampleProvider', back_populates='samples')

class TerpeneTest(Base):
	__tablename__ = 'terpene_tests'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	page_id = sqla.Column('page_id', None, sqla.ForeignKey('pages.id'), nullable=False)
	lab_id = sqla.Column('lab_id', None, sqla.ForeignKey('online_databases.id'), nullable=False)
	sample_id = sqla.Column('sample_id', None, sqla.ForeignKey('samples.id'), nullable=False)
	lab_test_uid = sqla.Column('lab_test_uid', sqla.String)
	test_time = sqla.Column('test_time', sqla.TIMESTAMP)
	unit = sqla.Column('unit', sqla.String)
	cisNerolidol = sqla.Column('cisNerolidol', sqla.Float)
	transNerolidol = sqla.Column('transNerolidol', sqla.Float)
	transNerolidol1 = sqla.Column('transNerolidol1', sqla.Float)
	transNerolidol2 = sqla.Column('transNerolidol2', sqla.Float)
	transOcimene = sqla.Column('transOcimene', sqla.Float)
	delta3Carene = sqla.Column('delta3Carene', sqla.Float)
	Camphene = sqla.Column('Camphene', sqla.Float)
	CaryophylleneOxide = sqla.Column('CaryophylleneOxide', sqla.Float)
	Eucalyptol = sqla.Column('Eucalyptol', sqla.Float)
	Geraniol = sqla.Column('Geraniol', sqla.Float)
	Guaiol = sqla.Column('Guaiol', sqla.Float)
	Isopulegol = sqla.Column('Isopulegol', sqla.Float)
	Linalool = sqla.Column('Linalool', sqla.Float)
	Ocimene = sqla.Column('Ocimene', sqla.Float)
	Terpinolene = sqla.Column('Terpinolene', sqla.Float)
	alphaBisabolol = sqla.Column('alphaBisabolol', sqla.Float)
	alphaHumulene = sqla.Column('alphaHumulene', sqla.Float)
	alphaPinene = sqla.Column('alphaPinene', sqla.Float)
	alphaTerpinene = sqla.Column('alphaTerpinene', sqla.Float)
	betaCaryophyllene = sqla.Column('betaCaryophyllene', sqla.Float)
	betaMyrcene = sqla.Column('betaMyrcene', sqla.Float)
	betaOcimene = sqla.Column('betaOcimene', sqla.Float)
	betaPinene = sqla.Column('betaPinene', sqla.Float)
	deltaLimonene = sqla.Column('deltaLimonene', sqla.Float)
	gammaTerpinene = sqla.Column('gammaTerpinene', sqla.Float)
	pCymene = sqla.Column('pCymene', sqla.Float)

	page = sqla.orm.relationship('Page', back_populates='terpene_tests')
	lab = sqla.orm.relationship('Lab', back_populates='terpene_tests')
	sample = sqla.orm.relationship('Sample', back_populates='terpene_tests')

class PotencyTest(Base):
	__tablename__ = 'potency_tests'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	page_id = sqla.Column('page_id', None, sqla.ForeignKey('pages.id'), nullable=False)
	lab_id = sqla.Column('lab_id', None, sqla.ForeignKey('online_databases.id'), nullable=False)
	sample_id = sqla.Column('sample_id', None, sqla.ForeignKey('samples.id'), nullable=False)
	lab_test_uid = sqla.Column('lab_test_uid', sqla.String)
	test_time = sqla.Column('test_time', sqla.TIMESTAMP)
	unit = sqla.Column('unit', sqla.String)
	delta9THCA = sqla.Column('delta9THCA', sqla.Float)
	delta9THC = sqla.Column('delta9THC', sqla.Float)
	delta8THC = sqla.Column('delta8THC', sqla.Float)
	THCA = sqla.Column('THCA', sqla.Float)
	THCV = sqla.Column('THCV', sqla.Float)
	CBN = sqla.Column('CBN', sqla.Float)
	CBDA = sqla.Column('CBDA', sqla.Float)
	CBD = sqla.Column('CBD', sqla.Float)
	delta9CBGA = sqla.Column('delta9CBGA', sqla.Float)
	delta9CBG = sqla.Column('delta9CBG', sqla.Float)
	CBGA = sqla.Column('CBGA', sqla.Float)
	CBG = sqla.Column('CBG', sqla.Float)
	CBC = sqla.Column('CBC', sqla.Float)

	page = sqla.orm.relationship('Page', back_populates='potency_tests')
	lab = sqla.orm.relationship('Lab', back_populates='potency_tests')
	sample = sqla.orm.relationship('Sample', back_populates='potency_tests')

class PesticideTest(Base):
	__tablename__ = 'pesticide_tests'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	page_id = sqla.Column('page_id', None, sqla.ForeignKey('pages.id'), nullable=False)
	lab_id = sqla.Column('lab_id', None, sqla.ForeignKey('online_databases.id'), nullable=False)
	sample_id = sqla.Column('sample_id', None, sqla.ForeignKey('samples.id'), nullable=False)
	lab_test_uid = sqla.Column('lab_test_uid', sqla.String)
	test_time = sqla.Column('test_time', sqla.TIMESTAMP)
	Spinosad = sqla.Column('Spinosad', sqla.Float)
	Spiromesifen = sqla.Column('Spiromesifen', sqla.Float)
	Myclobutanil = sqla.Column('Myclobutanil', sqla.Float)
	Imidacloprid = sqla.Column('Imidacloprid', sqla.Float)
	Spirotetramat = sqla.Column('Spirotetramat', sqla.Float)
	Paclobutrazol = sqla.Column('Paclobutrazol', sqla.Float)
	Acequinocyl = sqla.Column('Acequinocyl', sqla.Float)
	Pyrethrins = sqla.Column('Pyrethrins', sqla.Float)
	Bifenazate = sqla.Column('Bifenazate', sqla.Float)
	Abamectin = sqla.Column('Abamectin', sqla.Float)
	Fenoxycarb = sqla.Column('Fenoxycarb', sqla.Float)
	Daminozide = sqla.Column('Daminozide', sqla.Float)

	page = sqla.orm.relationship('Page', back_populates='pesticide_tests')
	lab = sqla.orm.relationship('Lab', back_populates='pesticide_tests')
	sample = sqla.orm.relationship('Sample', back_populates='pesticide_tests')

class ResidualsolventsTest(Base):
	__tablename__ = 'residualsolvents_tests'
	id = sqla.Column('id', sqla.INTEGER, primary_key=True)
	page_id = sqla.Column('page_id', None, sqla.ForeignKey('pages.id'), nullable=False)
	lab_id = sqla.Column('lab_id', None, sqla.ForeignKey('online_databases.id'), nullable=False)
	sample_id = sqla.Column('sample_id', None, sqla.ForeignKey('samples.id'), nullable=False)
	lab_test_uid = sqla.Column('lab_test_uid', sqla.String)
	test_time = sqla.Column('test_time', sqla.TIMESTAMP)
	unit = sqla.Column('unit', sqla.String)
	Methanol = sqla.Column('Methanol', sqla.Float)
	Isobutane = sqla.Column('Isobutane', sqla.Float)
	nButane = sqla.Column('nButane', sqla.Float)
	nHexane = sqla.Column('nHexane', sqla.Float)
	CyclohexaneBenzene = sqla.Column('CyclohexaneBenzene', sqla.Float)
	nHeptane = sqla.Column('nHeptane', sqla.Float)
	Mercaptan = sqla.Column('Mercaptan', sqla.Float)
	TwoMethylpentane = sqla.Column('2Methylpentane', sqla.Float)
	Two_2Dimethylbutane = sqla.Column('2_2Dimethylbutane', sqla.Float)
	Neopentane = sqla.Column('Neopentane', sqla.Float)
	Isopentane = sqla.Column('Isopentane', sqla.Float)
	nPentane = sqla.Column('nPentane', sqla.Float)
	Propane = sqla.Column('Propane', sqla.Float)
	ThreeMethylpentane = sqla.Column('3Methylpentane', sqla.Float)
	Isopropanol = sqla.Column('Isopropanol', sqla.Float)
	Ethanol = sqla.Column('Ethanol', sqla.Float)

	page = sqla.orm.relationship('Page', back_populates='residualsolvents_tests')
	lab = sqla.orm.relationship('Lab', back_populates='residualsolvents_tests')
	sample = sqla.orm.relationship('Sample', back_populates='residualsolvents_tests')

class MicrobiologicalTest(Base):
	__tablename__ = 'microbiological_tests'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	page_id = sqla.Column('page_id', None, sqla.ForeignKey('pages.id'), nullable=False)
	lab_id = sqla.Column('lab_id', None, sqla.ForeignKey('online_databases.id'), nullable=False)
	sample_id = sqla.Column('sample_id', None, sqla.ForeignKey('samples.id'), nullable=False)
	lab_test_uid = sqla.Column('lab_test_uid', sqla.String)
	test_time = sqla.Column('test_time', sqla.TIMESTAMP)
	unit = sqla.Column('unit', sqla.String)
	yeast_mold = sqla.Column('yeast_mold', sqla.Float)
	Ecoli = sqla.Column('Ecoli', sqla.Float)
	Coliforms = sqla.Column('Coliforms', sqla.Float)
	Pseudomonas = sqla.Column('Pseudomonas', sqla.Float)
	totalAerobicPlateCount = sqla.Column('totalAerobicPlateCount', sqla.Float)
	Salmonella = sqla.Column('Salmonella', sqla.Float)

	page = sqla.orm.relationship('Page', back_populates='microbiological_tests')
	lab = sqla.orm.relationship('Lab', back_populates='microbiological_tests')
	sample = sqla.orm.relationship('Sample', back_populates='microbiological_tests')

class MoisturecontentTest(Base):
	__tablename__ = 'moisturecontent_tests'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	page_id = sqla.Column('page_id', None, sqla.ForeignKey('pages.id'), nullable=False)
	lab_id = sqla.Column('lab_id', None, sqla.ForeignKey('online_databases.id'), nullable=False)
	sample_id = sqla.Column('sample_id', None, sqla.ForeignKey('samples.id'), nullable=False)
	lab_test_uid = sqla.Column('lab_test_uid', sqla.String)
	test_time = sqla.Column('test_time', sqla.TIMESTAMP)
	unit = sqla.Column('unit', sqla.String)
	moisture = sqla.Column('moisture', sqla.Float)

	page = sqla.orm.relationship('Page', back_populates='moisturecontent_tests')
	lab = sqla.orm.relationship('Lab', back_populates='moisturecontent_tests')
	sample = sqla.orm.relationship('Sample', back_populates='moisturecontent_tests')

class LabPostaladdress(Base):
	__tablename__ = 'labs_postal_addresses'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	lab_id = sqla.Column('lab_id', None, sqla.ForeignKey('online_databases.id'), nullable=False)
	firstname = sqla.Column('firstname', sqla.String)
	lastname = sqla.Column('lastname', sqla.String)
	company = sqla.Column('company', sqla.String)
	street = sqla.Column('street', sqla.String)
	house = sqla.Column('house', sqla.String)
	apartment = sqla.Column('apartment', sqla.String)
	city = sqla.Column('city', sqla.String)
	country = sqla.Column('country', sqla.String)
	postalcode = sqla.Column('postalcode', sqla.String)

	lab = sqla.orm.relationship('Lab', back_populates='postaladdresses')

class ProviderPostaladdress(Base):
	__tablename__ = 'providers_postal_addresses'
	id = sqla.Column('id', sqla.Integer, primary_key=True)
	provider_id = sqla.Column('provider_id', None, sqla.ForeignKey('sample_providers.id'), nullable=False)
	firstname = sqla.Column('firstname', sqla.String)
	lastname = sqla.Column('lastname', sqla.String)
	company = sqla.Column('company', sqla.String)
	street = sqla.Column('street', sqla.String)
	house = sqla.Column('house', sqla.String)
	apartment = sqla.Column('apartment', sqla.String)
	city = sqla.Column('city', sqla.String)
	country = sqla.Column('country', sqla.String)
	postalcode = sqla.Column('postalcode', sqla.String)

	provider = sqla.orm.relationship('SampleProvider', back_populates='postaladdresses')

Lab.pages = sqla.orm.relationship('Page', order_by=Page.source_url, back_populates='online_database')
Lab.terpene_tests = sqla.orm.relationship('TerpeneTest', order_by=TerpeneTest.id, back_populates='lab')
Lab.potency_tests = sqla.orm.relationship('PotencyTest', order_by=PotencyTest.id, back_populates='lab')
Lab.pesticide_tests = sqla.orm.relationship('PesticideTest', order_by=PesticideTest.id, back_populates='lab')
Lab.residualsolvents_tests = sqla.orm.relationship('ResidualsolventsTest', order_by=ResidualsolventsTest.id, back_populates='lab')
Lab.microbiological_tests = sqla.orm.relationship('MicrobiologicalTest', order_by=MicrobiologicalTest.id, back_populates='lab')
Lab.moisturecontent_tests = sqla.orm.relationship('MoisturecontentTest', order_by=MoisturecontentTest.id, back_populates='lab')
Lab.postaladdresses = sqla.orm.relationship('LabPostaladdress', order_by=LabPostaladdress.id, back_populates='lab')

Page.terpene_tests = sqla.orm.relationship('TerpeneTest', order_by=TerpeneTest.id, back_populates='page')
Page.potency_tests = sqla.orm.relationship('PotencyTest', order_by=PotencyTest.id, back_populates='page')
Page.pesticide_tests = sqla.orm.relationship('PesticideTest', order_by=PesticideTest.id, back_populates='page')
Page.residualsolvents_tests = sqla.orm.relationship('ResidualsolventsTest', order_by=ResidualsolventsTest.id, back_populates='page')
Page.microbiological_tests = sqla.orm.relationship('MicrobiologicalTest', order_by=MicrobiologicalTest.id, back_populates='page')
Page.moisturecontent_tests = sqla.orm.relationship('MoisturecontentTest', order_by=MoisturecontentTest.id, back_populates='page')

SampleProvider.samples = sqla.orm.relationship('Sample', order_by=Sample.id, back_populates='provider')
SampleProvider.postaladdresses = sqla.orm.relationship('ProviderPostaladdress', order_by=ProviderPostaladdress.id, back_populates='provider')

Sample.terpene_tests = sqla.orm.relationship('TerpeneTest', order_by=TerpeneTest.id, back_populates='sample')
Sample.potency_tests = sqla.orm.relationship('PotencyTest', order_by=PotencyTest.id, back_populates='sample')
Sample.pesticide_tests = sqla.orm.relationship('PesticideTest', order_by=PesticideTest.id, back_populates='sample')
Sample.residualsolvents_tests = sqla.orm.relationship('ResidualsolventsTest', order_by=ResidualsolventsTest.id, back_populates='sample')
Sample.microbiological_tests = sqla.orm.relationship('MicrobiologicalTest', order_by=MicrobiologicalTest.id, back_populates='sample')
Sample.moisturecontent_tests = sqla.orm.relationship('MoisturecontentTest', order_by=MoisturecontentTest.id, back_populates='sample')

def init_session(database_path, echo_commands=False):
	defined_labs = [
		{
			'identifier': 'analytical360',
			'name': 'Analytical 360',
			'url': 'https://analytical360.com/'
		},
		{
			'identifier': 'psilabs',
			'name': 'PSI Labs',
			'url': 'https://psilabs.org/'
		},
		{
			'identifier': 'sclabs',
			'name': 'SC Labs',
			'url': 'https://www.sclabs.com/'
		},
	]
	full_database_path = os.path.join('sqlite+pysqlite:///', database_path)
	engine = sqla.create_engine(full_database_path, echo=echo_commands)
	Base.metadata.create_all(engine)
	Session = sqla.orm.sessionmaker(bind=engine)
	session = Session()
	for lab in defined_labs:
		lab_exists = session.query(Lab).filter(Lab.identifier==lab['identifier']).first()
		if not lab_exists:
			new_lab = Lab(identifier=lab['identifier'], name=lab['name'], url=lab['url'])
			session.add(new_lab)
			session.commit()
	return session
