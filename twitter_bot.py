import json
import logging
import os
import sys
from queue import Queue
from threading import Thread

import tweepy
from dotenv import load_dotenv
from urllib3.exceptions import ProtocolError, ReadTimeoutError
from rich import pretty, print
from rich.logging import RichHandler

from productbuyer import ProductBuyer
from products import products


pretty.install()
load_dotenv()

# stream=sys.stdout,
# %(asctime)s]  %(levelname)-8s
logging.basicConfig(level=logging.INFO,
                    format='%(name)-10s %(threadName)-10s @ line %(lineno)d: %(message)s',
                    handlers=[RichHandler()])

logger = logging.getLogger(__name__)
logger.info(f"Logger started...")

CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")

# IDs for accounts:
# d_winch (me) for testing
# PartAlert for GPUs
# PA_Console for PS5
user_list = ["3373551", "1314575666130694144", "1320083775934631937"]


class MyStreamListener(tweepy.StreamListener):

    max_additional_cost = 50

    def __init__(self, api=None, q=Queue()):
        #self.api = api
        super().__init__()
        num_worker_threads = 4
        self.q = q
        for _ in range(num_worker_threads):
            t = Thread(target=self.handle_tweet)
            t.daemon = True
            t.start()

    def on_connect(self):
        logger.info("Connected. Streaming Tweets...\n")

    def on_timeout(self):
        logger.warning("Timeout... Continuing...")
        return True  # Returning True won't kill the stream.

    def on_error(self, status_code):
        if status_code == 420:
            logger.error(
                "Twitter returned error 420. Attempting to reconnect after wait exponential wait time...")
        return True

    def on_request_error(self, status_code):
        logger.error(status_code)
        return True

    def on_limit(self, track):
        logger.warning(track)
        return True

    def on_warning(self, notice):
        logger.warning(notice)
        return True

    def on_exception(self, exception):
        logger.error(exception)
        return True

    def on_status(self, status):
        self.q.put(status)

    def handle_tweet(self):
        while True:

            status = self.q.get()

            print(status.text, end="\n\n")

            if not status._json["user"]["id_str"] in user_list:
                logger.info("We don't care about this user's tweet\n")
                self.q.task_done()
                continue

            with open("out.json", "a+") as j:
                j.write(json.dumps(status._json))

            if status._json["truncated"]:
                logger.info("Tweet was truncated")
                self.parse_urls(
                    status._json["extended_tweet"]["entities"]["urls"])
            else:
                logger.info("Tweet was not truncated")
                self.parse_urls(status._json["entities"]["urls"])

            self.q.task_done()

    def parse_urls(self, urls):

        print(urls, end="\n\n")
        for url in urls:

            url = url['expanded_url']
            logger.info(f"URL: {url}")

            if "http://amazon.co.uk" == url.lower():
                logger.info(f"Not a product link\n")
                continue

            # TO-DO Restructure with regex
            # If not an Amazon UK listing
            if "amazon.co.uk" not in url.lower():
                if ("partalert.net" not in url.lower() or                                     # If not a Partalert link
                        "partalert.net" in url.lower() and "tld=.co.uk" not in url.lower()):  # If not a Partalert UK link
                    logger.info(f"Not a an Amazon.co.uk link\n")
                    continue

            for product in products:
                if product in url:
                    logger.info(
                        f"{product} - {products.get(product).get('type')} found!")
                    self.buy(product, products.get(product))
                    return
            logger.info(f"Product is not in the buyable product list\n")

    def buy(self, item_id, product_details):

        r = ProductBuyer(item_id=item_id)
        price = r.get_price()

        if price is None:
            logger.info(f"No dice this time\n")
            return

        logger.info(f"Price: {price}")

        if price > product_details.get("price") + self.max_additional_cost:
            logger.info("Too expensive\n")
            r.close()

        r.buy()
        r.login()
        r.confirm()
        sys.exit("Purchase appears successful. Check Amazon account.")


auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)


stream_listener = MyStreamListener()
stream = tweepy.Stream(auth=auth,
                       listener=stream_listener,
                       tweet_mode="extended",
                       include_rts=True)
stream.api.wait_on_rate_limit = True
stream.api.wait_on_rate_limit_notify = True


while True:
    if stream.running == False:
        try:
            stream.filter(follow=user_list,
                        is_async=True,
                        stall_warnings=True)
        except (ProtocolError, AttributeError) as e:
            logger.error(f"ENCOUNTERED ERROR: {e}")
            continue
