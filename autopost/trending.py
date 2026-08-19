"""Fetch trending topics from Google Trends RSS — all categories."""

import random
import xml.etree.ElementTree as ET

import requests

# Google Trends RSS for India (all categories)
GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=IN"

# Categories we want to cover
CATEGORIES = {
    "Technology": [
        "AI", "artificial intelligence", "chatgpt", "iphone", "android", "samsung",
        "google", "apple", "microsoft", "laptop", "smartphone", "app", "software",
        "robot", "crypto", "bitcoin", "blockchain", "cybersecurity", "hack", "data",
        "5g", "internet", "cloud", "startup", "elon musk", "openai", "gadget",
        "programming", "coding", "developer", "tech", "gpu", "nvidia",
    ],
    "Health & Wellness": [
        "health", "fitness", "nutrition", "diet", "exercise", "mental health",
        "wellness", "medical", "disease", "vitamin", "protein", "weight loss",
        "yoga", "sleep", "stress", "immunity", "heart", "diabetes", "cancer",
        "skin", "gut", "supplement", "workout", "meditation", "brain", "doctor",
        "medicine", "vaccine", "therapy", "hospital",
    ],
    "Sports": [
        "cricket", "ipl", "football", "soccer", "nba", "tennis", "olympic",
        "world cup", "match", "goal", "player", "team", "championship", "league",
        "tournament", "fifa", "kohli", "messi", "ronaldo", "f1", "racing",
        "badminton", "hockey", "wrestling", "boxing", "athletics", "medal",
    ],
    "Lifestyle": [
        "travel", "food", "recipe", "fashion", "beauty", "home", "decor",
        "relationship", "dating", "wedding", "parenting", "productivity",
        "habits", "morning routine", "self care", "minimalism", "reading",
        "book", "movie", "music", "art", "photography", "garden", "pet",
        "coffee", "cooking", "skincare", "haircare",
    ],
    "Finance": [
        "stock", "market", "investment", "mutual fund", "nifty", "sensex",
        "trading", "share", "bank", "loan", "credit", "tax", "saving",
        "budget", "income", "salary", "real estate", "gold", "rupee",
        "inflation", "rbi", "economy", "gdp", "business", "startup funding",
    ],
    "Science": [
        "space", "nasa", "isro", "planet", "rocket", "satellite", "climate",
        "environment", "pollution", "solar", "energy", "research", "study",
        "discovery", "ocean", "earthquake", "volcano", "dinosaur", "fossil",
        "genetics", "dna", "evolution", "physics", "chemistry",
    ],
    "Entertainment": [
        "movie", "film", "bollywood", "hollywood", "netflix", "series",
        "actor", "actress", "singer", "album", "concert", "gaming",
        "playstation", "xbox", "anime", "manga", "celebrity", "award",
        "oscar", "grammy", "trailer", "release", "streaming",
    ],
    "Education": [
        "exam", "result", "admission", "university", "college", "school",
        "course", "online learning", "scholarship", "study abroad", "neet",
        "jee", "upsc", "career", "job", "skill", "certification", "degree",
    ],
}


def categorize_topic(title: str) -> str:
    """Determine the category of a topic based on keywords."""
    title_lower = title.lower()
    scores = {}
    for category, keywords in CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in title_lower)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return "General"


def fetch_trending_topics(max_topics=10):
    """Fetch ALL trending topics from Google Trends RSS."""
    try:
        response = requests.get(GOOGLE_TRENDS_RSS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching Google Trends: {e}")
        return []

    root = ET.fromstring(response.content)
    items = root.findall(".//item")

    topics = []
    for item in items:
        title = item.findtext("title", "").strip()
        if not title:
            continue

        traffic = item.findtext(
            "{https://trends.google.com/trending/rss}approx_traffic", ""
        )
        category = categorize_topic(title)

        topics.append({
            "title": title,
            "traffic": traffic,
            "source": "Google Trends",
            "category": category,
        })

        if len(topics) >= max_topics:
            break

    return topics


def get_fallback_topics():
    """Return diverse evergreen topics as fallback."""
    topics = [
        # Tech
        ("How AI is Changing Everyday Life in 2025", "Technology"),
        ("Best Budget Smartphones Under 15000 in India", "Technology"),
        ("Top Productivity Apps You Should Try", "Technology"),
        ("How to Protect Your Online Privacy", "Technology"),
        # Health
        ("Benefits of Walking 10000 Steps Daily", "Health & Wellness"),
        ("How to Improve Sleep Quality Naturally", "Health & Wellness"),
        ("Best Foods for Brain Health and Memory", "Health & Wellness"),
        # Sports
        ("How to Start Running as a Complete Beginner", "Sports"),
        ("Benefits of Playing Sports for Mental Health", "Sports"),
        # Lifestyle
        ("Morning Routine Habits of Successful People", "Lifestyle"),
        ("How to Save Money on Groceries Without Sacrifice", "Lifestyle"),
        ("Best Indoor Plants That Purify Air", "Lifestyle"),
        # Finance
        ("How to Start Investing with Just 500 Rupees", "Finance"),
        ("SIP vs Lump Sum Which is Better for Beginners", "Finance"),
        # Science
        ("Latest Space Discoveries That Will Blow Your Mind", "Science"),
        ("How Climate Change Affects Daily Weather", "Science"),
        # Entertainment
        ("Best Underrated Movies to Watch This Weekend", "Entertainment"),
        ("Top Podcasts for Self Improvement", "Entertainment"),
        # Education
        ("Best Free Online Courses to Learn New Skills", "Education"),
        ("How to Build a Career in Tech Without a Degree", "Education"),
    ]
    random.shuffle(topics)
    return [
        {"title": t[0], "traffic": "evergreen", "source": "fallback", "category": t[1]}
        for t in topics[:5]
    ]


def get_topics():
    """Get trending topics across all categories, with fallback."""
    topics = fetch_trending_topics()
    if not topics:
        print("No trending topics found, using fallback topics...")
        topics = get_fallback_topics()
    return topics
