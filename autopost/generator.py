"""Generate SEO blog posts using OpenRouter API with free images."""

import json
import os
import re

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"


def get_unsplash_image(query: str, width: int = 800, height: int = 450) -> str:
    """Get a free image URL from Picsum (always works, no API key needed).
    
    Returns a random image (~30-50KB at 800x450).
    Uses a seed based on the query so same topic gets same image.
    """
    import hashlib
    # Create a numeric seed from the query for consistent images per topic
    seed = int(hashlib.md5(query.encode()).hexdigest()[:8], 16) % 1000
    return f"https://picsum.photos/seed/{seed}/{width}/{height}"


def get_brand_logo(brand_name: str) -> str | None:
    """Try to get a brand/company logo using Clearbit Logo API (free).
    
    Returns logo URL or None if not found.
    """
    # Common brand domain mappings
    domain_hints = {
        "air india": "airindia.com",
        "google": "google.com",
        "apple": "apple.com",
        "microsoft": "microsoft.com",
        "amazon": "amazon.com",
        "netflix": "netflix.com",
        "samsung": "samsung.com",
        "tesla": "tesla.com",
        "meta": "meta.com",
        "facebook": "facebook.com",
        "twitter": "twitter.com",
        "instagram": "instagram.com",
        "whatsapp": "whatsapp.com",
        "youtube": "youtube.com",
        "spotify": "spotify.com",
        "uber": "uber.com",
        "zomato": "zomato.com",
        "swiggy": "swiggy.com",
        "paytm": "paytm.com",
        "flipkart": "flipkart.com",
        "myntra": "myntra.com",
        "reliance": "relianceindustries.com",
        "tata": "tata.com",
        "infosys": "infosys.com",
        "wipro": "wipro.com",
    }
    
    brand_lower = brand_name.lower().strip()
    for key, domain in domain_hints.items():
        if key in brand_lower:
            return f"https://logo.clearbit.com/{domain}"
    
    return None


SYSTEM_PROMPT = """You are an expert blog writer for stayhealthylife.in — a multi-topic blog covering health, technology, sports, lifestyle, finance, science, entertainment, and education.

You write SEO-optimized, engaging, factual articles that are:
- Easy to read (general audience)
- Well-structured with proper HTML headings
- Factually accurate with up-to-date information
- Conversational yet informative

IMPORTANT RULES:
- For health topics: never give specific medical advice, suggest consulting a doctor
- For finance topics: add disclaimer about not being financial advice
- For all topics: be balanced, factual, and engaging
- Always write the blog post in English regardless of the topic language
- If the topic is in another language, translate it to English for the article
"""

POST_PROMPT_TEMPLATE = """Write a complete SEO blog post about: "{topic}"
Category: {category}

Return ONLY valid JSON (no markdown, no code fences) in this exact format:
{{
    "title": "...",
    "slug": "...",
    "image_keywords": "...",
    "content": "..."
}}

Requirements:
- title: Under 60 characters, in English, includes the primary keyword, catchy and click-worthy
- slug: URL-friendly lowercase with hyphens (e.g. best-budget-phones-under-15000-2025)
- image_keywords: 2-3 English words describing what image would fit this post (e.g. "cricket stadium", "healthy food", "technology laptop")
- content: Full HTML blog content following this EXACT structure:

<p class="hook"><strong>[Attention-grabbing opening]</strong> — 2-3 curiosity-driven sentences about why this matters NOW.</p>

<h2>What is [Topic] and Why It Matters</h2>
<p>Explain the topic clearly in 2-3 short paragraphs. Use simple language.</p>

<h2>Key Facts & Latest Updates</h2>
<ul>
<li><strong>Fact 1</strong> — explanation in 1-2 lines</li>
<li><strong>Fact 2</strong> — explanation in 1-2 lines</li>
<li><strong>Fact 3</strong> — explanation in 1-2 lines</li>
<li><strong>Fact 4</strong> — explanation in 1-2 lines</li>
<li><strong>Fact 5</strong> — explanation in 1-2 lines</li>
</ul>

<h2>[Deep Dive — unique angle based on the topic and category]</h2>
<p>3-4 short paragraphs with detailed insights, examples, or analysis.</p>

<h2>What This Means for You</h2>
<p>Practical takeaways — what should the reader do with this information? 3-5 actionable points.</p>

<h2>Official Links & References</h2>
<ul>
<li><a href="[REAL official website URL]" target="_blank" rel="noopener">[Source Name]</a> — brief description of what this link provides</li>
<li><a href="[REAL official URL]" target="_blank" rel="noopener">[Source Name]</a> — brief description</li>
<li><a href="[REAL official URL]" target="_blank" rel="noopener">[Source Name]</a> — brief description</li>
</ul>
<p><em>Note: Always verify information from official sources before taking action.</em></p>

<h2>Frequently Asked Questions</h2>
<p><strong>Q: [Relevant Question 1]?</strong></p>
<p>Answer in 2-3 sentences.</p>
<p><strong>Q: [Relevant Question 2]?</strong></p>
<p>Answer in 2-3 sentences.</p>
<p><strong>Q: [Relevant Question 3]?</strong></p>
<p>Answer in 2-3 sentences.</p>

<p class="conclusion"><strong>Final Thoughts:</strong> Wrap up with 2-3 engaging sentences. Invite readers to share their thoughts in the comments or share this article with someone who'd find it useful.</p>

CRITICAL RULES FOR LINKS & REFERENCES:
- ALWAYS include real, working URLs to official sources (government sites, company websites, official apps, news outlets)
- If talking about a company (e.g. Air India), link to their official website (airindia.com)
- If talking about a job/form, link to the official application page
- If talking about an app, link to the official app store page or website
- If talking about a government scheme, link to the official .gov.in page
- Use ONLY real, existing URLs — do NOT make up fake URLs
- Include 2-4 reference links per post

SEO Rules:
- Write entirely in English (even if topic is in another language)
- Primary keyword in title, first 100 words, one H2, and conclusion
- Short paragraphs (2-4 lines max)
- Use <strong> tags on 4-6 key phrases throughout
- Natural, conversational tone
- Article should be 800-1200 words
- Do NOT include any <img> tags in the content — images are added separately
"""


def generate_post(topic: str, category: str = "General") -> dict | None:
    """Generate a blog post for the given topic using OpenRouter."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set")
        return None

    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://stayhealthylife.in",
                "X-OpenRouter-Title": "StayHealthyLife Blog",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": POST_PROMPT_TEMPLATE.format(
                        topic=topic, category=category
                    )},
                ],
                "temperature": 0.7,
                "max_tokens": 3000,
            },
            timeout=60,
        )

        if response.status_code != 200:
            print(f"API error ({response.status_code}): {response.text[:200]}")
            return None

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Clean up response (remove markdown code fences if present)
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)

        post_data = json.loads(content)

        # Validate required fields
        if not all(k in post_data for k in ("title", "slug", "content")):
            print(f"Missing fields in response: {post_data.keys()}")
            return None

        # Clean slug
        post_data["slug"] = re.sub(r"[^a-z0-9-]", "", post_data["slug"].lower())
        post_data["slug"] = re.sub(r"-+", "-", post_data["slug"]).strip("-")

        # Add featured image using Picsum
        image_keywords = post_data.get("image_keywords", topic)
        image_url = get_unsplash_image(image_keywords)
        
        # Check if there's a brand logo to include
        brand_logo = get_brand_logo(topic)
        
        # Build image HTML
        image_html = f'<img src="{image_url}" alt="{post_data["title"]}" style="width:100%;border-radius:8px;margin:1.5rem 0;" loading="lazy">'
        
        if brand_logo:
            image_html += f'\n<p style="text-align:center;margin:1rem 0;"><img src="{brand_logo}" alt="{topic}" style="height:40px;margin:0 auto;" loading="lazy"></p>'
        
        # Insert after first </p>
        first_p_end = post_data["content"].find("</p>")
        if first_p_end != -1:
            insert_pos = first_p_end + 4
            post_data["content"] = (
                post_data["content"][:insert_pos] 
                + "\n" + image_html + "\n" 
                + post_data["content"][insert_pos:]
            )
        else:
            post_data["content"] = image_html + "\n" + post_data["content"]

        # Add category metadata
        post_data["category"] = category

        return post_data

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return None
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
