import pytest
from unittest.mock import patch, MagicMock

import backend.ingestion.reddit
from backend.ingestion.reddit import fetch_posts


def _make_mock_post(post_id, title, body, permalink, comments=None):
    post = MagicMock()
    post.id = post_id
    post.title = title
    post.selftext = body
    post.permalink = permalink
    comment_list = []
    for c in (comments or ["Great tip!", "Thanks for sharing"]):
        cm = MagicMock()
        cm.body = c
        comment_list.append(cm)
    post.comments.list.return_value = comment_list
    return post


def test_fetch_posts_returns_correct_schema():
    """Each returned dict has all required keys."""
    mock_post = _make_mock_post("abc", "Best ramen in Tokyo", "Go to Ichiran", "/r/JapanTravel/abc")

    mock_reddit = MagicMock()
    mock_subreddit = MagicMock()
    mock_subreddit.top.return_value = [mock_post]
    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("backend.ingestion.reddit.praw.Reddit", return_value=mock_reddit), \
         patch("backend.ingestion.reddit.time.sleep"):
        results = fetch_posts(["JapanTravel"], destination="japan", limit=1)

    assert len(results) == 1
    r = results[0]
    assert r["post_id"] == "abc"
    assert r["title"] == "Best ramen in Tokyo"
    assert r["destination"] == "japan"
    assert r["source_type"] == "reddit"
    assert r["language"] == "en"
    assert r["url"] == "https://www.reddit.com/r/JapanTravel/abc"
    assert "text" in r
    assert "subreddit" in r


def test_text_concatenates_title_body_comments():
    """text field combines title, body, and top comments."""
    mock_post = _make_mock_post(
        "x1", "Tokyo tips", "Visit Shinjuku", "/r/JapanTravel/x1",
        comments=["Comment A", "Comment B", "Comment C"]
    )
    mock_reddit = MagicMock()
    mock_subreddit = MagicMock()
    mock_subreddit.top.return_value = [mock_post]
    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("backend.ingestion.reddit.praw.Reddit", return_value=mock_reddit), \
         patch("backend.ingestion.reddit.time.sleep"):
        results = fetch_posts(["JapanTravel"], destination="japan", limit=1)

    text = results[0]["text"]
    assert "Tokyo tips" in text
    assert "Visit Shinjuku" in text
    assert "Comment A" in text


def test_rate_limit_sleep_called_between_subreddits():
    """time.sleep(1) called once per subreddit."""
    mock_reddit = MagicMock()
    mock_subreddit = MagicMock()
    mock_subreddit.top.return_value = []
    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("backend.ingestion.reddit.praw.Reddit", return_value=mock_reddit), \
         patch("backend.ingestion.reddit.time.sleep") as mock_sleep:
        fetch_posts(["JapanTravel", "japanlife"], destination="japan")

    assert mock_sleep.call_count == 2
