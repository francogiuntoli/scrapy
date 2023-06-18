import scrapy
from scrapy_splash import SplashRequest
from scrapy.linkextractors import LinkExtractor
import markdownify
import tiktoken
from w3lib.html import remove_tags, remove_tags_with_content

import warnings
warnings.filterwarnings("ignore")

script = """
function main(splash)
splash:go(splash.args.url)
splash:wait(1.0)
return {html=splash:html()}
end
"""


encoding = tiktoken.get_encoding("cl100k_base")


class GorgiasSpider(scrapy.Spider):
    name = "gorgias"
    allowed_domains = ["siksilk.gorgias.help"]
    start_urls = ["https://siksilk.gorgias.help/en-US/articles"]
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'gorgias.csv',
        'FEED_EXPORT_FIELDS': ["title", "heading", "content", "tokens"],
    }

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url,
                self.parse,
                endpoint='execute',
                args={'lua_source': script}
            )

    def parse(self, response):
        le = LinkExtractor(
            allow_domains=self.allowed_domains,
            restrict_css='div.ghc-category-card-list-section__content-container',
        )

        for link in le.extract_links(response):
            category1 = link.url.split('/')
            category1 = category1[-1]
            category1 = category1.split('-')
            category1 = category1[:-1]
            category1 = ' '.join(category1)
            yield SplashRequest(
                url=link.url,
                callback=self.parse_categories,
                endpoint='execute',
                args={'lua_source': script},
                meta={'category': category1}
            )

    def parse_categories(self, response):
        category1 = response.meta.get('category')

        le1 = LinkExtractor(
            allow_domains=self.allowed_domains,
            restrict_css='div.ghc-article-card-list-section__content-container',
        )
        for link in le1.extract_links(response):
            yield SplashRequest(
                url=link.url,
                callback=self.parse_articles,
                endpoint='execute',
                args={'lua_source': script},
                meta={"category": category1}
            )

    def parse_articles(self, response):

        category = response.meta.get('category')
        title = response.css('h1::text').get(),
        content_unparsed = response.css('main.fr-view').get()
        content_unparsed_without_img = remove_tags(
            remove_tags_with_content(content_unparsed, ("img", "table",)))

        content = markdownify.markdownify(
            content_unparsed_without_img, heading_style="ATX")
        tokens = len(encoding.encode(content))

        data = {
            'title': category[0],
            'heading': title[0],
            'content': content,
            'tokens': tokens
        }

        yield data
