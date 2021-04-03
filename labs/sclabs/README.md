# SC Labs
Lab Name: `SC Labs`

Web Address: `sclabs.com`

Postal Address: `100 Pioneer Street, Suite E, Santa Cruz, CA 95060`

Postal Address: `15865 SW 74th Ave #110, Tigard, OR 97224`

Postal Address: `1822 Carnegie Ave, Santa Ana, CA 92705`

Postal Address: `1066 4th Street, Suite D, Santa Rosa, CA 95404`

TODO: Config File (SQL init, selectors)

## Description
This folder contains:
* A parser to extract the actual terpene profile from each of the downloaded HTML-pages as CSV-list
* The CSV list of extracted terpene and cannabinoid profiles, as well as a JSON version of this list

## How to use
### The parser
This parser runs multiple XPath queries and RegEx expressions to find the wanted data in those HTML-files. You can run it like this:
`python3 parser.py --csv database_dump/`

If you add `-v` (up to 3 times) you will be informed of more and more information about the extraction process.
After this is done you will have `results.csv` file and (if some extractions failed) a number of other files containing filenames where some datapoints couldn't be extracted (beginning with `log-`).

### The database
The database contains the following fields/columns/datapoints:
* Test Result UID: The UID provided by Psilabs. If it couldn't be extracted an artificial one is generated to provide reliable distinction between samples.
* Sample Name: The name of the sample. Most often this is the name of the provided strain with some additional words.
* Sample Type: The type of the sample. Can any of 'Flower', 'Concentrate', 'Edible', 'Liquid', 'Topical', 'Archived' or 'NaN' (if it couldn't be parsed). 'Archived' and 'NaN' will be removed in the future.
* Receipt Time: The date when this sample was received by the lab. We expect this to be always in american format in the source files. Gets converted to ISO-8601. Analytical360 does not record this though, so this is always 'NaN' here.
* Test Time: The date when this test was run. We expect this to be always in american format in the source files. Gets converted to ISO-8601.
* Provider: The name of the company which provided this sample. These are always numerical IDs, because they get anonymized for now to not discredit vendors if the test results are corrupted.
* cis-Nerolidol: The percentage amount of cis-Nerolidol present in this sample.
* trans-Nerolidol: The percentage amount of trans-Nerolidol present in this sample.
* trans-Nerolidol 1: The percentage amount of trans-Nerolidol 1 present in this sample.
* trans-Nerolidol 2: The percentage amount of trans-Nerolidol 2 present in this sample.
* trans-Ocimene: The percentage amount of trans-Ocimene present in this sample.
* 3-Carene: The percentage amount of 3-Carene present in this sample.
* Camphene: The percentage amount of Camphene present in this sample.
* Caryophyllene Oxide: The percentage amount of Caryophyllene Oxide present in this sample.
* Eucalyptol: The percentage amount of Eucalyptol present in this sample.
* Geraniol: The percentage amount of Geraniol present in this sample.
* Guaiol: The percentage amount of Guaiol present in this sample.
* Isopulegol: The percentage amount of Isopulegol present in this sample.
* Linalool: The percentage amount of Linalool present in this sample.
* Ocimene: The percentage amount of Ocimene present in this sample.
* Terpinolene: The percentage amount of Terpinolene present in this sample.
* alpha-Bisabolol: The percentage amount of alpha-Bisabolol present in this sample.
* alpha-Humulene: The percentage amount of alpha-Humulene present in this sample.
* alpha-Pinene: The percentage amount of alpha-Pinene present in this sample.
* alpha-Terpinene: The percentage amount of alpha-Terpinene present in this sample.
* beta-Caryophyllene: The percentage amount of beta-Caryophyllene present in this sample.
* beta-Myrcene: The percentage amount of beta-Myrcene present in this sample.
* beta-Ocimene: The percentage amount of beta-Ocimene present in this sample.
* beta-Pinene: The percentage amount of beta-Pinene present in this sample.
* delta-Limonene: The percentage amount of delta-Limonene present in this sample.
* gamma-Terpinene: The percentage amount of gamma-Terpinene present in this sample.
* p-Cymene: The percentage amount of p-Cymene present in this sample.
* delta-9 THC-A: The percentage amount of delta-9 THC-A present in this sample.
* delta-9 THC: The percentage amount of delta-9 THC present in this sample.
* delta-8 THC: The percentage amount of delta-8 THC present in this sample.
* THC-A: The percentage amount of THC-A present in this sample.
* THCV: The percentage amount of THCV present in this sample.
* CBN: The percentage amount of CBN present in this sample.
* CBD-A: The percentage amount of CBD-A present in this sample.
* CBD: The percentage amount of CBD present in this sample.
* delta-9 CBG-A: The percentage amount of delta-9 CBG-A present in this sample.
* delta-9 CBG: The percentage amount of delta-9 CBG present in this sample.
* CBG-A: The percentage amount of CBG-A present in this sample.
* CBG: The percentage amount of CBG present in this sample.
* CBC: The percentage amount of CBC present in this sample.
* Moisture Content: The percentage amount of Moisture Content present in this sample.

#### Problematic Sample Pages

## Roadmap
* Try to port this to `scrapy-splash` so this can run headless and scheduled
