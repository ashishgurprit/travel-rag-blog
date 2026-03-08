"""Reddit ingestion module."""

import time
import praw
from backend.config import settings


def fetch_posts(subreddits: list[str], destination: str, limit: int = 100) -> list[dict]:
    """Fetch top posts + comments from a list of subreddits.

    Returns one dict per post with title, body, and top 5 comments concatenated.
    """
    reddit = praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )

    results = []
    for subreddit_name in subreddits:
        sub = reddit.subreddit(subreddit_name)
        for post in sub.top(limit=limit, time_filter="month"):
            comments = post.comments.list()[:5]
            comment_bodies = [c.body for c in comments if hasattr(c, "body")]
            text = f"{post.title}\n\n{post.selftext}\n\n" + "\n".join(comment_bodies)
            results.append({
                "text": text,
                "post_id": post.id,
                "title": post.title,
                "subreddit": subreddit_name,
                "url": f"https://www.reddit.com{post.permalink}",
                "destination": destination,
                "source_type": "reddit",
                "language": "en",
            })
        time.sleep(1)
    return results
