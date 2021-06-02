# gpu-ps5-bot for Amazon UK
A bot to listen to Twitter accounts for UK stock drops and then purchase products

I wrote this to get a GPU without having to try to beat scalpers to a drop.

Loads Twitter credentials and Amazon log in data from .env file.

Uses Tweepy's StreamListener with threads to monitor PartAlert Twitter accounts. On a tweet, it will check if the product is in the products dict in products.py.

If it is a product we wish to purchase, it will attempt to buy via Amazon using Selenium.

Needs updating to get the price/buy button from the right side bar in case it appears there. Amazon listings are quite inconsistent.

https://www.youtube.com/watch?v=y3pdUg8M8-U
