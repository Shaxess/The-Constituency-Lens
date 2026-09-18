import tweepy
import os
from .config import BEARER_TOKEN # Add to config.py
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env from root

BEARER_TOKEN = os.getenv("AAAAAAAAAAAAAAAAAAAAAI5z%2FAEAAAAAeY2%2Bxfw0nsqtsWPx5A0HN46D8Rg%3DTfu2RqiOG1VKrnlHSoleegAhUVSfxGCP0gbSZsQTxQDh3RJlxA")
SHEET_ID = os.getenv("1cTQFbM5o_GBoFmFjy-q-71PEaDxRVKEtSyzw4fBqmEA")

# 1. Go to developer.twitter.com -> Create free app -> Get Bearer Token
# Paste in config.py: BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAA...."

def scrape_twitter_api(query, count=30):
    client = tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)
    # Ojo example queries that work for ANY LGA
    # Just change LGA variable
    tweets = client.search_recent_tweets(
        query=f"{query} -is:retweet lang:en",
        max_results=count,
        tweet_fields=["created_at", "author_id", "text", "public_metrics"]
    )
    return tweets.data if tweets.data else []