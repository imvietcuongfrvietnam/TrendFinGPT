import scrapy
import crawl_data.items as Items
from w3lib.html import remove_tags

class VneconomySpider(scrapy.Spider):
    name = "vneconomy"
    allowed_domains = ["vneconomy.vn"]
    start_urls = [f"https://vneconomy.vn/tai-chinh.htm?trang={page}" for page in range(1, 401)]


    def parse(self, response):
        for article in response.css("header.story__header h3.story__title a::attr(href)").getall():
            full_url = response.urljoin(article)
            yield scrapy.Request(full_url, callback=self.parse_article)
    
    def parse_article(self, response):
        item = Items.CrawlDataItem()

        item['url'] = response.url
        raw_author = response.css(".detail__author").get()
        raw_summary = response.css(".detail__summary").get()
        raw_date = response.css(".detail__meta").get()

        item['title'] = response.css("h1.detail__title::text").get(default="").strip()
        item['author'] = remove_tags(raw_author).strip() if raw_author else ""
        item['summary'] = remove_tags(raw_summary).strip() if raw_summary else ""
        item['date'] = remove_tags(raw_date).strip() if raw_date else ""
        raw_paragraphs = response.css(".detail__content ::text").getall()
        content = " ".join([p.strip() for p in raw_paragraphs if p.strip()])
        item['content'] = content

        yield item