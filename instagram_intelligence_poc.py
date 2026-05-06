"""
Instagram Intelligence PoC — Free Edition
==========================================
Same pipeline as before, but using Google Gemini (free tier)
instead of Anthropic Claude.

Free tier limits (as of 2026):
  - gemini-1.5-flash: 1,500 requests/day, 1M tokens/min — plenty for this PoC

Requirements:
    pip install google-generativeai requests python-dotenv

Setup:
    Create a .env file with:
        GEMINI_API_KEY=your_gemini_api_key
        INSTAGRAM_ACCESS_TOKEN=your_meta_access_token
        INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_business_account_id

Get your free Gemini API key at:
    https://aistudio.google.com/app/apikey
"""

import os
import json
import time
import requests
import csv
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IG_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
GEMINI_MODEL = "gemini-1.5-flash"  # free tier model
MAX_POSTS = 50
MAX_COMMENTS = 30

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)


# ── Helper: call Gemini and parse JSON back ───────────────────────────────────


def ask_gemini(prompt: str) -> dict | list:
    """Send a prompt to Gemini and parse the JSON response."""
    response = model.generate_content(prompt)
    raw = response.text.strip()
    # Strip markdown code fences if Gemini adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── 1. META GRAPH API ─────────────────────────────────────────────────────────


def fetch_posts() -> list[dict]:
    """Fetch recent posts with engagement metrics."""
    print("📥 Fetching posts from Instagram Graph API...")
    url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
    params = {
        "fields": (
            "id,caption,media_type,timestamp,"
            "like_count,comments_count,"
            "insights.metric(reach,impressions,saved)"
        ),
        "limit": MAX_POSTS,
        "access_token": IG_ACCESS_TOKEN,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    posts = response.json().get("data", [])
    print(f"  ✓ Fetched {len(posts)} posts")
    return posts


def fetch_comments(post_id: str) -> list[str]:
    """Fetch comments for a single post."""
    url = f"https://graph.facebook.com/v19.0/{post_id}/comments"
    params = {
        "fields": "text,timestamp",
        "limit": MAX_COMMENTS,
        "access_token": IG_ACCESS_TOKEN,
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return []
    return [c["text"] for c in response.json().get("data", [])]


def parse_insights(post: dict) -> dict:
    """Extract insight metrics from nested API response."""
    insights = {}
    for item in post.get("insights", {}).get("data", []):
        insights[item["name"]] = item["values"][0]["value"]
    return insights


def build_post_records(raw_posts: list[dict]) -> list[dict]:
    """Enrich posts with comments and flat metrics."""
    records = []
    for i, post in enumerate(raw_posts):
        print(f"  💬 Fetching comments for post {i+1}/{len(raw_posts)}...")
        insights = parse_insights(post)
        comments = fetch_comments(post["id"])
        records.append(
            {
                "id": post.get("id"),
                "caption": post.get("caption", ""),
                "media_type": post.get("media_type", ""),
                "timestamp": post.get("timestamp", ""),
                "likes": post.get("like_count", 0),
                "comments_count": post.get("comments_count", 0),
                "reach": insights.get("reach", 0),
                "impressions": insights.get("impressions", 0),
                "saved": insights.get("saved", 0),
                "comments": comments,
            }
        )
        time.sleep(0.3)
    return records


# ── 2. GEMINI ANALYSIS ────────────────────────────────────────────────────────


def analyze_sentiment_and_themes(posts: list[dict]) -> dict:
    """Sentiment analysis and theme extraction via Gemini."""
    print("\n🤖 Analyzing sentiment & themes with Gemini...")

    comments_payload = [
        {
            "post_id": p["id"],
            "caption_snippet": p["caption"][:120] if p["caption"] else "",
            "comments": p["comments"],
        }
        for p in posts
        if p["comments"]
    ]

    prompt = f"""You are an expert social media analyst for an outdoor guiding and climbing company.

Below is a JSON array of Instagram posts with caption snippets and user comments.

Analyze ALL comments and return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{{
  "overall_sentiment": {{
    "positive_pct": <0-100>,
    "neutral_pct": <0-100>,
    "negative_pct": <0-100>,
    "summary": "<2-3 sentence summary of overall audience sentiment>"
  }},
  "top_themes": [
    {{
      "theme": "<theme name>",
      "frequency": "<high/medium/low>",
      "example_comment": "<verbatim example>",
      "emotional_tone": "<excited/inspired/fearful/curious/grateful/other>"
    }}
  ],
  "unanswered_questions": ["<question from comments the brand should answer>"],
  "pain_points": ["<frustration or concern mentioned in comments>"],
  "standout_posts": [
    {{
      "post_id": "<id>",
      "reason": "<why this post generated strong emotional reactions>"
    }}
  ]
}}

DATA:
{json.dumps(comments_payload, ensure_ascii=False)}
"""

    result = ask_gemini(prompt)
    print("  ✓ Sentiment & theme analysis complete")
    return result


def analyze_performance_patterns(posts: list[dict]) -> dict:
    """Identify what top-performing posts have in common."""
    print("\n📊 Analyzing performance patterns with Gemini...")

    for p in posts:
        reach = p["reach"] if p["reach"] > 0 else 1
        p["engagement_rate"] = round(
            (p["likes"] + p["comments_count"] + p["saved"]) / reach * 100, 2
        )

    sorted_posts = sorted(posts, key=lambda x: x["engagement_rate"], reverse=True)
    top_posts = sorted_posts[:10]
    bottom_posts = sorted_posts[-10:]

    def summarize(post_list):
        return [
            {
                "caption": p["caption"][:200] if p["caption"] else "",
                "media_type": p["media_type"],
                "timestamp": p["timestamp"],
                "likes": p["likes"],
                "saved": p["saved"],
                "engagement_rate": p["engagement_rate"],
            }
            for p in post_list
        ]

    prompt = f"""You are a social media strategist for an outdoor guiding and climbing company.

Compare these two groups of Instagram posts and identify what drives performance.

TOP 10 POSTS (highest engagement rate):
{json.dumps(summarize(top_posts), ensure_ascii=False)}

BOTTOM 10 POSTS (lowest engagement rate):
{json.dumps(summarize(bottom_posts), ensure_ascii=False)}

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{{
  "top_post_patterns": ["<pattern observed in high-performing posts>"],
  "bottom_post_patterns": ["<pattern observed in low-performing posts>"],
  "best_media_type": "<REEL/IMAGE/CAROUSEL — which performs best and why>",
  "best_posting_themes": ["<topic or theme that drives engagement>"],
  "caption_insights": "<what makes top captions work — length, tone, CTAs, emojis>",
  "actionable_recommendations": ["<specific concrete recommendation for the brand>"]
}}
"""

    result = ask_gemini(prompt)
    result["top_posts_ranked"] = [
        {"caption_snippet": p["caption"][:100], "engagement_rate": p["engagement_rate"]}
        for p in top_posts
    ]
    print("  ✓ Performance pattern analysis complete")
    return result


def generate_content_ideas(sentiment: dict, performance: dict) -> list[dict]:
    """Generate 10 ready-to-use post ideas based on analysis findings."""
    print("\n✨ Generating content ideas with Gemini...")

    prompt = f"""You are a creative social media strategist for an outdoor guiding and climbing company in Catalonia, Spain.

Based on this audience sentiment analysis:
{json.dumps(sentiment, ensure_ascii=False)}

And these performance patterns:
{json.dumps(performance, ensure_ascii=False)}

Generate 10 Instagram post ideas that are highly likely to perform well.

Return ONLY a valid JSON array of 10 objects with this exact structure (no markdown, no explanation):
[
  {{
    "idea_number": 1,
    "format": "<REEL/CAROUSEL/SINGLE IMAGE>",
    "theme": "<theme this post targets>",
    "caption": "<full ready-to-publish caption in Spanish, with emojis and a CTA>",
    "visual_description": "<what to film or photograph>",
    "why_it_will_work": "<1 sentence connecting to the analysis findings>"
  }}
]

Make captions authentic, emotional, and specific to climbing/outdoor guiding in Catalonia.
"""

    result = ask_gemini(prompt)
    print(f"  ✓ Generated {len(result)} content ideas")
    return result


# ── 3. EXPORT ─────────────────────────────────────────────────────────────────


def export_posts_csv(posts: list[dict], path: str):
    fieldnames = [
        "id",
        "timestamp",
        "media_type",
        "caption",
        "likes",
        "comments_count",
        "saved",
        "reach",
        "impressions",
        "engagement_rate",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(posts)
    print(f"  📄 Posts CSV saved → {path}")


def export_report_json(data: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  📄 Full report saved → {path}")


def export_ideas_csv(ideas: list[dict], path: str):
    fieldnames = [
        "idea_number",
        "format",
        "theme",
        "caption",
        "visual_description",
        "why_it_will_work",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ideas)
    print(f"  📄 Content ideas CSV saved → {path}")


# ── 4. MAIN PIPELINE ──────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("  Instagram Intelligence PoC — Free Edition (Gemini)")
    print(f"  Run date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Step 1 — Fetch data
    raw_posts = fetch_posts()
    posts = build_post_records(raw_posts)

    # Step 2 — Analyze
    sentiment = analyze_sentiment_and_themes(posts)
    performance = analyze_performance_patterns(posts)
    ideas = generate_content_ideas(sentiment, performance)

    # Step 3 — Compile full report
    report = {
        "run_date": datetime.now().isoformat(),
        "model_used": GEMINI_MODEL,
        "posts_analyzed": len(posts),
        "sentiment_analysis": sentiment,
        "performance_analysis": performance,
        "content_ideas": ideas,
    }

    # Step 4 — Export
    print("\n💾 Exporting results...")
    os.makedirs("output", exist_ok=True)
    export_posts_csv(posts, "output/posts_metrics.csv")
    export_ideas_csv(ideas, "output/content_ideas.csv")
    export_report_json(report, "output/full_report.json")

    # Step 5 — Terminal summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    s = sentiment["overall_sentiment"]
    print(
        f"\n📣 Sentiment: {s['positive_pct']}% positive | "
        f"{s['neutral_pct']}% neutral | {s['negative_pct']}% negative"
    )
    print(f"   {s['summary']}")

    print(f"\n🏆 Top performing media type: {performance['best_media_type']}")
    print(f"\n📌 Top themes in comments:")
    for t in sentiment["top_themes"][:3]:
        print(f"   • {t['theme']} ({t['frequency']}) — {t['emotional_tone']}")

    print(f"\n💡 Top recommendation:")
    if performance["actionable_recommendations"]:
        print(f"   → {performance['actionable_recommendations'][0]}")

    print(f"\n✅ Done! Check the /output folder for all files.")
    print("=" * 60)


if __name__ == "__main__":
    main()
