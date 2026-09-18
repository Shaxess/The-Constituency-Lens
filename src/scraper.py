import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import time
import logging
from datetime import datetime

logger = logging.getLogger("TCL-Ojo")

# Safe imports
try:
    import sentiment
except Exception as e:
    print(f"sentiment.py failed: {e}")
    sentiment = None

try:
    import political_tagger
except:
    political_tagger = None

try:
    import twitter_api as twitter_api_module
    HAS_TWITTER_API = True
except ImportError:
    HAS_TWITTER_API = False
    import snscrape.modules.twitter as sntwitter

try:
    import sheets_client
except:
    sheets_client = None

OJO_KEYWORDS = ["Ojo Lagos", "Iba LCDA", "Oto-Awori"]

class OjoScraper:
    def search(self, query, limit=20):
        posts = []
        # Try your twitter_api first
        if HAS_TWITTER_API:
            try:
                print(f"Trying twitter_api for {query}...")
                return twitter_api_module.search_dual_mode(query, limit=limit)
            except Exception as e:
                print(f"twitter_api failed: {e}")

        # Try snscrape
        try:
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
                if i >= limit:
                    break
                posts.append({
                    "text": tweet.rawContent,
                    "created_at": tweet.date.isoformat(),
                    "source": "snscrape",
                    "query": query
                })
        except Exception as e:
            print(f"Error retrieving https for {query}: {e}")
            print("Using SAMPLE Ojo data to keep Streamlit working")
            # Sample data so Streamlit can run
            posts = [
                {"text": f"Traffic on {query} this morning in Ojo is heavy #OjoLagos", "created_at": datetime.now().isoformat(), "source": "sample", "query": query},
                {"text": f"Need better roads in {query}, Ojo LGA neglected", "created_at": datetime.now().isoformat(), "source": "sample", "query": query},
            ]
        return posts    

    def run_ojo_pipeline(self, sheet_client, max_per_keyword=15):
        all_posts = []
        for kw in OJO_KEYWORDS:
            print(f"--> Searching: {kw}")
            try:
                posts = self.search(kw, limit=max_per_keyword)
            except Exception as e:
                print(f"Search failed for {kw}: {e}")
                continue

            for p in posts:
                p["lga"] = "Ojo"
                # Safe sentiment
                try:
                    if sentiment:
                        p["sentiment"] = sentiment.analyze(p["text"])
                    else:
                        p["sentiment"] = {"label": "NEUTRAL", "score": 0}
                except Exception as e:
                    p["sentiment"] = {"label": "NEUTRAL", "score": 0, "error": str(e)}

                p["scraped_at"] = datetime.now().isoformat()
                all_posts.append(p)
            time.sleep(2)

        if all_posts and sheet_client:
            sheet_client.append_rows("raw_posts", all_posts)
            print(f"SAVED {len(all_posts)} to raw_posts")
        return all_posts

if __name__ == "__main__":
    if sheets_client:
        scraper = OjoScraper()
        posts = scraper.run_ojo_pipeline(None, max_per_keyword=5)
        print(f"Found {len(posts)} posts - first post: {posts[0]['text'][:100] if posts else 'none'}")
    else:
        print("sheets_client not found")