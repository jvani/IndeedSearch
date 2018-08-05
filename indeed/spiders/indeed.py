# -*- coding: utf-8 -*-
import json
import scrapy
import logging
import datetime as dt
from urllib.parse import urlencode
from elasticsearch import Elasticsearch


class Job(scrapy.Item):
    """"""
    # -- Job details.
    Title = scrapy.Field(serializer=str)
    Company = scrapy.Field(serializer=str)
    Location = scrapy.Field(serializer=str)
    Date = scrapy.Field(serializer=str)
    Pay = scrapy.Field(serializer=str)
    Description = scrapy.Field(serializer=str)
    EasyApply = scrapy.Field(serializer=str)
    # -- Crawl details.
    LastCrawlDate = scrapy.Field(serializer=str)
    Source = scrapy.Field(serializer=str)


def parse_response(response):
    """"""
    job = Job()

    xpaths = {
        "Title": {
            "join": False,
            "xpath": [
                "//*[@class='jobtitle']//text()",
                "//*[contains(@class, 'JobInfoHeader-title')]/text()"
            ]
        },
        "Company": {
            "join": False,
            "xpath": [
                "//*[@class='company']//text()",
                "//*[contains(@class, 'InlineCompanyRating')]/div[1]/text()"
            ]
        },
        "Location": {
            "join": False,
            "xpath": [
                "//*[@class='location']//text()",
                "//*[contains(@class, 'InlineCompanyRating')]/div[4]/text()"
            ]
        },
        "Date": {
            "join": False,
            "xpath": [
                "//*[@class='date']//text()",
            ]
        },
        "Pay": {
            "join": False,
            "xpath": [
                "//div[@data-tn-component='jobHeader']/div/span[@class='no-wrap']/text()",
            ]
        },
        "Description": {
            "join": True,
            "xpath": [
                "//*[@class='summary']//text()",
                "//*[contains(@class, 'JobComponent-description')]//text()"
            ]
        }
    }

    # -- For all mapped xpaths.
    for key, vals in xpaths.items():
        job.setdefault(key, "")
        # -- Try a the xpaths in order.
        for xpath in vals["xpath"]:
            # -- If join flag is true, extract all, and join.
            if vals["join"]:
                extracted = "\n".join(response.xpath(xpath).extract())
            # -- Else extract first.
            else:
                extracted = response.xpath(xpath).extract_first()
            # -- If a value was extract, set, and break looping of xpaths.
            if extracted:
                job[key] = extracted
                break

    job["EasyApply"] = any(response.xpath("//*[contains(@class, 'indeed-apply-button')]"))
    job["LastCrawlDate"] = dt.datetime.isoformat(dt.datetime.utcnow())
    job["Source"] = response.url

    return job


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
        job = dict(parse_response(response))
        idx = job["Company"] + "-" + job["Title"]
        # -- Check if the document exists before inserting it.
        if not self.es.exists(index=self.index, doc_type="job", id=idx):
            self.es.index(index=self.index, doc_type="job", id=idx, body=job)
        
