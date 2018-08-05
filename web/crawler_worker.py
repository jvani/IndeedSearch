# -*- coding: utf-8 -*-
import multiprocessing
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging


class CrawlerWorker(multiprocessing.Process):

    def __init__(self, spider, spider_kwargs):
        multiprocessing.Process.__init__(self)
        
        # -- Store objects.
        configure_logging()
        self.runner = CrawlerRunner()
        self.runner.crawl(spider, **spider_kwargs)

    def run(self):
        d = self.runner.join()
        d.addBoth(lambda _: reactor.stop())
        reactor.run()

