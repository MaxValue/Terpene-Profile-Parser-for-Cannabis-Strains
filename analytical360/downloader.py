import scrapy, os

SAVE_FOLDER = "database_dump"
counter = 1
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

class OnlineDatabaseSpider(scrapy.Spider):
    name = "analytical360_spider"

    def start_requests(self):
        for page_number in range(1,4303):
            wanted_link = "http://archive.analytical360.com/page/{page_num}?s=%22%22".format(page_num=page_number)
            self.log("Going to results page {}".format(page_number))
            yield scrapy.Request(url=wanted_link, callback=self.parse)

    def parse(self, response):
        for samplelist in response.css("#listlatestnews"):
            for sample in samplelist.css("li div.postbox h3 a::attr(href)").extract():
                self.log("Getting sample {} for download".format(sample))
                yield scrapy.Request(url=sample, callback=self.save_this)

    def save_this(self, response):
        global counter
        filename = os.path.join(SAVE_FOLDER,"{}.html".format(counter))
        while os.path.exists(filename):
            counter += 1
            filename = os.path.join(SAVE_FOLDER,"{}.html".format(counter))
        with open(filename, "wb") as f:
            f.write(response.body)
        self.log("Saved file {}".format(filename))
