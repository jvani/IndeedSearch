# -*- coding: utf-8 -*-
from scrapy import signals
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.xlib.pydispatch import dispatcher
import multiprocessing


class CrawlerWorker(multiprocessing.Process):

    def __init__(self, spider, spider_kwargs):
        multiprocessing.Process.__init__(self)
        # -- Store objects.
        self.spider = spider
        self.spider_kwargs = spider_kwargs

        self.process = CrawlerProcess()
#        self.items = []
#        dispatcher.connect(self._item_passed, signals.item_passed)


#    def _item_passed(self, item):
#        self.items.append(item)


    def run(self):
        self.process.crawl(self.spider, **self.spider_kwargs)
        self.process.start()
