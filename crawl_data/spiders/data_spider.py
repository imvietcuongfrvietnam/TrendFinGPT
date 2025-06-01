import scrapy
import crawl_data.items as Items
from w3lib.html import remove_tags  # Dùng để xóa thẻ HTML
import re


class DataSpiderSpider(scrapy.Spider):
    name = "data_spider"
    allowed_domains = ["baodautu.vn"]
    start_urls = [f"https://baodautu.vn/tai-chinh-chung-khoan-d6/p{page}" for page in range(1, 775)]

    def parse(self, response):
        for article in response.css("div.desc_list_news_home a.fs22::attr(href)").getall():
            full_url = response.urljoin(article)
            yield scrapy.Request(full_url, callback=self.parse_article)

    def parse_article(self, response):
        item = Items.CrawlDataItem()

        raw_author = response.css(".author.cl_green").get()
        raw_summary = response.css(".sapo_detail").get()
        raw_date = response.css(".post-time").get()

        item['url'] = response.url
        item['title'] = response.css(".title-detail::text").get(default="").strip()
        item['author'] = remove_tags(raw_author).strip() if raw_author else ""
        item['summary'] = remove_tags(raw_summary).strip() if raw_summary else ""
        item['date'] = remove_tags(raw_date).strip() if raw_date else ""

        raw_paragraphs = response.css("#content_detail_news ::text").getall()
        content = " ".join([p.strip() for p in raw_paragraphs if p.strip()])
        item['content'] = content

        yield item

