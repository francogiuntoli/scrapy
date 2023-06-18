import scrapy
from scrapy_splash import SplashRequest
from scrapy.linkextractors import LinkExtractor
import markdownify
import tiktoken
from w3lib.html import remove_tags, remove_tags_with_content


script = """
function main(splash)
splash:go(splash.args.url)
splash:wait(1.0)
return {html=splash:html()}
end
"""


encoding = tiktoken.get_encoding("cl100k_base")


class ZendeskSpider(scrapy.Spider):
    name = "zendesk"
    allowed_domains = ["support.airstream.com"]
    start_urls = ["https://support.airstream.com/hc/en-us"]
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'zendesk.csv',
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
            restrict_css='section.categories ul.blocks-list',
            restrict_text=['General', 'Online Store', 'Apps & Technology']
        )

        for link in le.extract_links(response):
            yield SplashRequest(
                url=link.url,
                callback=self.parse_categories,
                endpoint='execute',
                args={'lua_source': script},
            )

    def parse_categories(self, response):

        le1 = LinkExtractor(
            allow_domains=self.allowed_domains,
            restrict_css='h2.section-tree-title',
        )
        for link in le1.extract_links(response):
            yield SplashRequest(
                url=link.url,
                callback=self.parse_subcategories,
                endpoint='execute',
                args={'lua_source': script},
                meta={'category': link.text.strip().replace('\n', '')}

            )

    def parse_subcategories(self, response):
        category = response.meta.get('category')
        le1 = LinkExtractor(
            allow_domains=self.allowed_domains,
            restrict_css='ul.article-list',
        )

        for link in le1.extract_links(response):
            yield SplashRequest(
                url=link.url,
                callback=self.parse_articles,
                endpoint='execute',
                args={'lua_source': script},
                meta={'category': category,
                      "heading": link.text.strip().replace('\n', '')}
            )

    def parse_articles(self, response):
        category = response.meta.get('category')
        heading = response.meta.get('heading')
        category = category
        title = heading,
        content_unparsed = response.css('div.article-body').get()
        content_unparsed_without_img = remove_tags(
            remove_tags_with_content(content_unparsed, ('img',)))

        content = markdownify.markdownify(
            content_unparsed_without_img, heading_style="ATX")

        tokens = len(encoding.encode(content))

        data = {
            'title': category,
            'heading': title,
            'content': content,
            'tokens': tokens
        }

        yield data
