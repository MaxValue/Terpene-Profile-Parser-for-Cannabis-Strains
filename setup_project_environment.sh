#!/usr/bin/env bash

sudo apt-get update
sudo apt-get --assume-yes install python3-pip python3-venv

python3 -m venv --clear venv
source venv/bin/activate
	python3 -m pip install --upgrade pip
	python3 -m pip install --upgrade SQLAlchemy
	python3 -m pip install --upgrade dateparser
	python3 -m pip install --upgrade scrapy
	python3 -m pip install --upgrade scrapy-splash
	python3 -m pip install --upgrade selenium
deactivate
