# -*- coding: utf-8 -*-
import scrapy
import logging
import datetime as dt
from urllib.parse import urlencode
from elasticsearch import Elasticsearch


class JobPosting(object):
    def __init__(self, response):
        """Indeed job posting parsing object.
        Args:
            response (Reponse) - scrapy response object.
        """
        # -- Simple xpaths.
        xpaths = {
            "Title": "//*[@class='jobtitle']//text()",
            "Company": "//*[@class='company']//text()",
            "Location": "//*[@class='location']//text()",
            "Date": "//*[@class='date']//text()",
            "Pay": "//div[@data-tn-component='jobHeader']/div/span[@class='no-wrap']/text()"
        }
        # -- Create data dictionary from simple xpaths.
        self.data = {kk: response.xpath(vv).extract_first("").strip() for kk, vv in xpaths.items()}
        # -- Populate remaining fields.
        self.data["LastCrawlDate"] = dt.datetime.isoformat(dt.datetime.utcnow())
        self.data["Description"] = "\n".join(response.xpath("//*[@class='summary']//text()").extract())
        self.data["EasyApply"] = any(response.xpath("//*[contains(@class, 'indeed-apply-button')]"))
        self.data["Source"] = response.url


class IndeedSpider(scrapy.Spider):
    """Indeed spider to scrape job postings and input data to elasticsearch.
    Search query, location, and elasticsearch index is defined by user input 
    upon loading the spider.
    """
    name  = "IndeedSpider"

    def __init__(self, **kwargs):
        """"""
        # -- Set kwargs.
        super().__init__(**kwargs)
        # -- If the keyword args are not passed get from user input.
        for attr in ["query", "location", "domain", "index"]:
            if not hasattr(self, attr):
                setattr(self, attr, input("{}:\n".format(attr.title())))
        # -- Define indeed search terms.
        query = urlencode({"q": self.query, "l": self.location})
        self.url = "https://www.indeed{}/jobs?".format(self.domain) + query
        logging.info(self.url)
        # -- Init elasticsearch client and define output index.
        self.es = Elasticsearch()

    def start_requests(self):
        """Yield the initial request as defined by user input.
        """
        yield scrapy.Request(self.url, callback=self.indeed_init)

    def indeed_init(self, response):
        """Paginate results, up to 100 pages (max returned by indeed), for the 
        given search.
        """
        # -- Extract ad links and yield requests of the the first page.
        self.search_results(response)
        # -- Extract 'Jobs n to n+20 of ii' string.
        search_count = response.xpath("//div[@id='searchCount']/text()") \
            .extract_first().strip()
        # -- Extract 'ii'.
        njobs = int("".join([ii for ii in search_count.split("of")[-1] if ii.isdigit()]))
        # -- Return search values and log number of responses.
        srchs = [ii * 10 for ii in range(1, 100) if ii * 10 <= njobs]
        logging.info("Making {} initial requests".format(len(srchs)))
        # -- Yield pagination requests.
        for srch in srchs:
            yield scrapy.Request(
                self.url + "&start={}".format(srch), 
                callback=self.search_results
            )

    def search_results(self, response):
        """Extract ad links from search results and yield requests for each job.
        """
        links = response.xpath("//a[@data-tn-element='jobTitle']/@href").extract()
        for link in [response.urljoin(link) for link in links]:
            yield scrapy.Request(link, callback=self.parse)

    def parse(self, response):
        """Parse the job posting and input data into elasticsearch.
        """
        job = JobPosting(response)
        self.es.index(
            index=self.index, 
            doc_type="job", 
            id=job.data["Company"] + "-" + job.data["Title"], 
            body=job.data
        )
        
