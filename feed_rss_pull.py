import time

import feedparser
import requests
import schedule
from bs4 import BeautifulSoup

from config_load import CONFIG
from html_resource_extractor import HTMLResourceExtractor
from push_article_to_cms import post_article, check_article_title, upload
from text_summarizer import TextSummarizer
from util import struct_time_to_formatted_string

# 创建摘要生成器实例
summarizer = TextSummarizer(language='english')
extractor = HTMLResourceExtractor()


def fetch_and_post_feeds():
    """
    Fetches RSS feeds and posts their entries as articles.
    """
    for feed_url in CONFIG['feed_source']:
        try:
            response = requests.get(feed_url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)

            print(f"Feed Title: {feed.feed.title}")

            for entry in feed.entries:
                if check_article_title(entry.title):

                    content = entry.summary if hasattr(entry, 'summary') else ''

                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()

                    resources_dict = extractor.extract_resources(content)

                    images = []
                    for resources_type, v in resources_dict.items():
                        if v:
                            for item in v:
                                upload_url = upload(item.get("url"), resources_type)
                                if upload_url:
                                    images.append(upload_url)
                                    content = content.replace(item.get("url"), upload_url)

                    article = {
                        "editorType": 1,
                        "channelId": "9",
                        "inputType": 3,
                        "allowComment": True,
                        "customs": {},

                        "title": entry.title,
                        "tagNames": [item['term'] for item in entry.tags],
                        "publishDate": struct_time_to_formatted_string(entry.published_parsed),
                        "author": entry.author,
                        "text": content,
                        'source': entry.link,

                        "seoDescription": summarizer.generate_summary(text, top_n=3),
                        "image": images[0] if images else '',
                        "fileList": [],
                        "imageList": [],
                    }
                    post_article(article)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {feed_url}: {e}")
        except Exception as e:
            print(f"Error parsing {feed_url}: {e}")


def job():
    print("Feeds fetched Start.")
    fetch_and_post_feeds()
    print("Feeds fetched End.")


# 每两小时执行一次任务
schedule.every(2).hours.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)