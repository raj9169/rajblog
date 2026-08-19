"""Main auto-posting script. Run via cron at 6 AM and 6 PM IST."""

import os
import sys
import random
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autopost.trending import get_topics
from autopost.generator import generate_post
from autopost.poster import publish_post


def main():
    """Find a trending topic, generate a post, and publish it."""
    print(f"\n{'='*60}")
    print(f"AUTO-POST RUN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment")
        sys.exit(1)

    # Step 1: Get trending topics
    print("\n[1/3] Fetching trending health topics...")
    topics = get_topics()
    print(f"Found {len(topics)} topics:")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. [{t.get('category', 'General')}] {t['title']} ({t['source']})")

    if not topics:
        print("ERROR: No topics found")
        sys.exit(1)

    # Step 2: Try topics until one succeeds (not duplicate)
    random.shuffle(topics)
    post_data = None
    selected_topic = None

    for topic in topics:
        category = topic.get("category", "General")
        print(f"\n[2/3] Generating post for: {topic['title']} [{category}]...")
        post_data = generate_post(topic["title"], category)

        if post_data:
            selected_topic = topic
            break
        else:
            print(f"  Failed to generate, trying next topic...")

    if not post_data:
        print("ERROR: Could not generate any post")
        sys.exit(1)

    print(f"  Title: {post_data['title']}")
    print(f"  Slug: {post_data['slug']}")

    # Step 3: Publish
    print(f"\n[3/3] Publishing post...")
    success = publish_post(post_data)

    if success:
        print(f"\nSUCCESS: Post published at stayhealthylife.in/post/{post_data['slug']}")
    else:
        print(f"\nSKIPPED: Post was duplicate or failed to publish")
        # Try another topic
        for topic in topics:
            if topic == selected_topic:
                continue
            category = topic.get("category", "General")
            print(f"\nRetrying with: {topic['title']} [{category}]...")
            post_data = generate_post(topic["title"], category)
            if post_data:
                success = publish_post(post_data)
                if success:
                    print(f"SUCCESS: Post published at stayhealthylife.in/post/{post_data['slug']}")
                    break

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
