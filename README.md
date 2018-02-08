# Terpene Profile Parser for Cannabis Strains
_Parser and Database to index the Terpene Profile of different Strains Of Cannabis from Online-Databases_

## Description
This repository contains:
* A web crawler to download lab test results of different cannabis strains as HTML-pages from [Analytical360](http://archive.analytical360.com)
* A parser to extract the actual terpene profile from each of those HTML-pages as CSV-list
* The CSV list of extracted terpene profiles
* If some data points could not be extracted also an assortment of files where the extraction of a specific datapoint failed

## How to use
### The web crawler
This crawler utilizes [Scrapy](https://scrapy.org/) to go through all search results of the string `" "`. You will need:
* Python3: `sudo apt-get install python3 python3-pip`
* Scrapy:  `python3 -m pip install scrapy`

The crawler can be run like this:
`scrapy run weed_spider`

It will produce a folder called `database_dump` containing all sample pages counting upwards in order of their download.

### The parser
This parser runs multiple XPath queries and RegEx expressions to find the wanted data in those HTML-files. You can run it like this:
`python3 clean_data.py database_dump/ -d`

If you use the shown `-d` option you will be informed of any piece of data which gets extracted and every error which occurs during the extraction process.
After this is done you will have `results.csv` file and (if some extractions failed) a number of other files containing filenames where some datapoints couldn't be extracted.

### The database
The database contains the following fields/columns/datapoints:
* Test Result UID: The UID provided by Analytical360 labs. If it couldn't be extracted an artificial one is generated to provide reliable distinction between samples.
* Test Result Name: The name of the sample. Most often this is the name of the provided strain.
* Test Result Date: The date when this test was run. We expect this to be always in american format in the source files. Gets converted to ISO-8601.
* Provider: The name of the company which provided this sample.
* Linalool: The percentage amount of Linalool present in this sample.
* Caryophyllene oxide: The percentage amount of Caryophyllene oxide present in this sample.
* Myrcene: The percentage amount of Myrcene present in this sample.
* beta-Pinene: The percentage amount of beta-Pinene present in this sample.
* Limonene: The percentage amount of Limonene present in this sample.
* Terpinolene: The percentage amount of Terpinolene present in this sample.
* alpha-Pinene: The percentage amount of alpha-Pinene present in this sample.
* Humulene: The percentage amount of Humulene present in this sample.
* Caryophyllene: The percentage amount of Caryophyllene present in this sample.
* TERPENE-TOTAL: The total percentage amount of terpenes present in this sample.

## Project history
The idea for this project comes from Paul Fuxjäger who wants to find high quality medical cannabis for new health treatment options. The code was written by Max Fuxjäger.

## Copyright
Have fun. We hope you can use this data to do good for humanity.