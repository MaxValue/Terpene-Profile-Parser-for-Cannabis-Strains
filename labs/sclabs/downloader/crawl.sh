#!/usr/bin/env bash
docker run --name 'splashserver' -d -p 8050:8050 scrapinghub/splash
source ../../../venv/bin/activate
scrapy crawl sclabs
deactivate
docker container stop splashserver
