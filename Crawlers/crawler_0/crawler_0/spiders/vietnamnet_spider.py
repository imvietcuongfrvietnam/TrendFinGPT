import scrapy
from kafka import KafkaProducer
from elasticsearch import Elasticsearch
import json

class VietnamnetSpider(scrapy.Spider):
    name = "vietnamnet_spider"
    allowed_domains = ["vietnamnet.vn"]
    start_urls = ["https://vietnamnet.vn/kinh-doanh/tai-chinh-page1"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
        )
        self.es = Elasticsearch("http://elasticsearch:9200")
        self.es.indices.create(index="vietnamnet", ignore=400)

    def parse(self, response):
        page = int(response.url.split('-page')[-1])
        bottom_grids = response.css(".newsStreams div.container__left")
        all_posts = []

        for grid in bottom_grids:
            posts = grid.css("div.horizontalPost__main")
            for post in posts:
                url = post.css(".horizontalPost__main-title a::attr(href)").get()
                if url:
                    url = url.strip()
                    title = post.css(".horizontalPost__main-title a::attr(title)").get(default='').strip()
                    summary = post.css("p::text").get(default='').strip()
                    all_posts.append({
                        'url': url,
                        'title': title,
                        'summary': summary
                    })

        if not all_posts:
            self.logger.info(f"[Page {page}] Không tìm thấy bài viết nào.")
            return

        urls = [p['url'] for p in all_posts]

        query = {
            "query": {
                "terms": {
                    "url.keyword": urls
                }
            },
            "_source": ["url"],
            "size": len(urls)
        }

        res = self.es.search(index="vietnamnet", body=query)
        existing_urls = set(hit["_source"]["url"] for hit in res["hits"]["hits"])

        new_posts = [p for p in all_posts if p['url'] not in existing_urls]
        num_new = len(new_posts)

        self.logger.info(f"[Page {page}] Tổng số bài: {len(all_posts)} | Mới: {num_new} | Đã có: {len(existing_urls)}")

        if num_new == 0:
            self.logger.info(f"[Page {page}] Toàn bộ bài đã tồn tại. Dừng crawler.")
            return

        for post in new_posts:
            yield response.follow(post['url'], callback=self.parse_detail, meta={
                'title': post['title'],
                'summary': post['summary'],
                'url': post['url']
            })

        next_page = page + 1
        next_url = f"https://vietnamnet.vn/kinh-doanh/tai-chinh-page{next_page}"
        yield scrapy.Request(url=next_url, callback=self.parse)

    def parse_detail(self, response):
        item = {
            'title': response.meta['title'],
            'summary': response.meta['summary'],
            'url': response.meta['url'],
            'author': response.css("p.article-detail-author__info span.name a::attr(title)").get(default='').strip(),
            'content': ''.join([x.strip() for x in response.css("#maincontent *::text").getall() if x.strip()]),
            'date': response.css("div.bread-crumb-detail__time::text").get(default='').strip()
        }

        self.producer.send("vietnamnet_articles", item)
        self.producer.flush()

        self.logger.info(f"[PUSH] {item['title'][:60]}... -> Kafka")

        yield item
