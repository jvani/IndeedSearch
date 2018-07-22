# IndeedSearch

Collect data from indeed and add to elasticsearch.

## Use:
### Start elasticsearch and kibana.
`docker-compose up -d`

### Start spider.
`cd indeed/`

`scrapy crawl IndeedSpider`
