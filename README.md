# 🧗 Instagram Intelligence PoC
### VERT — Outdoor Guiding Company

> An end-to-end pipeline that pulls Instagram data via the Meta Graph API, analyzes it with Google Gemini (free tier), and generates ready-to-publish content ideas — all automated in Python. No paid API required.

---

## What This Project Does

This proof of concept demonstrates how Generative AI can turn raw Instagram data into actionable marketing intelligence. It runs four steps automatically:

1. **Fetches** posts, engagement metrics, and comments from the Instagram Graph API
2. **Analyzes** audience sentiment and emotional themes across all comments
3. **Identifies** what makes your top-performing posts work (vs. the ones that flop)
4. **Generates** 10 ready-to-publish post ideas in Spanish, grounded in real data

No dashboards, no manual tagging — just run the script and get results.

---

## Project Structure

```
sm-analytics-vert/
│
├── instagram_poc_free.py   # Main pipeline script (Gemini)
├── .env                    # Your API keys (never commit this!)
├── .env.example            # Template for .env
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
└── output/                 # Auto-generated on first run
    ├── posts_metrics.csv       # All posts with engagement rates
    ├── content_ideas.csv       # 10 AI-generated post ideas
    └── full_report.json        # Complete analysis report
```

---

## Prerequisites

- Python 3.9+
- An **Instagram Business or Creator account** connected to a **Facebook Page**
- A **Google Gemini API key** (free, no credit card needed)
- A **Meta Developer App** with Instagram Graph API access

---

## Setup

### 1. Clone or download the project

```bash
git clone https://github.com/mseglar/sm-analytics-vert.git
cd sm-analytics-vert
```

### 2. Install dependencies

```bash
pip install google-generativeai requests python-dotenv
```

### 3. Create your `.env` file

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

Your `.env` should look like this:

```env
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxx
INSTAGRAM_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxx
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841xxxxxxxxxx
```

> ⚠️ Never commit your `.env` file. Add it to `.gitignore`.

### 4. Run the pipeline

```bash
python instagram_poc_free.py
```

Results will appear in the `/output` folder.

---

## Getting Your API Keys

### Gemini API Key (free)

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with any Google account
3. Click **Create API Key** — done, no credit card required
4. Copy the key and paste it into `.env` as `GEMINI_API_KEY`

**Free tier limits:** 1,500 requests/day and 1M tokens/minute — this PoC uses roughly 15–20 requests per full run, so you're well within limits.

---

### Meta / Instagram Access Token

This is the most involved part. Follow these steps carefully.

#### Step 1 — Create a Meta Developer App
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **My Apps → Create App**
3. Choose **Business** as the app type
4. Give it a name (e.g. `instagram-poc`) and click **Create**

#### Step 2 — Add Instagram Graph API
1. Inside your app dashboard, click **Add Product**
2. Find **Instagram Graph API** and click **Set Up**

#### Step 3 — Connect your Instagram Business Account
1. Go to **Instagram Graph API → Getting Started**
2. Connect your Facebook Page (which must be linked to your Instagram Business account)
3. Grant the following permissions:
   - `instagram_basic`
   - `instagram_manage_insights`
   - `pages_read_engagement`

#### Step 4 — Generate a short-lived token
1. Open the [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown (top right)
3. Click **Generate Access Token**
4. Select the permissions listed above
5. Copy the token — this is a **short-lived token (valid ~1 hour)**

#### Step 5 — Exchange for a long-lived token (valid 60 days)
Run this in your terminal, replacing the placeholders:

```bash
curl -i -X GET "https://graph.facebook.com/v19.0/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id=YOUR_APP_ID
  &client_secret=YOUR_APP_SECRET
  &fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
```

You'll get back a long-lived token. Paste it into `.env` as `INSTAGRAM_ACCESS_TOKEN`.

> Your App ID and App Secret are found in your Meta App Dashboard under **Settings → Basic**.

#### Step 6 — Get your Instagram Business Account ID
Run this in your terminal (replace the token):

```bash
curl -i -X GET "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_LONG_LIVED_TOKEN"
```

This returns your Facebook Pages. Then use the page ID to get the Instagram account ID:

```bash
curl -i -X GET "https://graph.facebook.com/v19.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_LONG_LIVED_TOKEN"
```

Copy the `id` value from `instagram_business_account` and paste it into `.env` as `INSTAGRAM_BUSINESS_ACCOUNT_ID`.

---

## Output Files Explained

| File | What's inside |
|------|---------------|
| `posts_metrics.csv` | Every post with likes, reach, saves, comments count, and calculated engagement rate |
| `content_ideas.csv` | 10 post ideas with format, caption (in Spanish), visual brief, and rationale |
| `full_report.json` | Full structured JSON: sentiment breakdown, top themes, unanswered audience questions, performance patterns, and all content ideas |

---

## Configuration

You can adjust these constants at the top of `instagram_poc_free.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_POSTS` | `50` | How many recent posts to fetch |
| `MAX_COMMENTS` | `30` | Max comments to fetch per post |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use |

---

## Example Terminal Output

```
============================================================
  Instagram Intelligence PoC
  Run date: 2026-05-06 10:32
============================================================
📥 Fetching posts from Instagram Graph API...
  ✓ Fetched 50 posts
  💬 Fetching comments for post 1/50...
  ...
🤖 Analyzing sentiment & themes with Claude...
  ✓ Sentiment & theme analysis complete
📊 Analyzing performance patterns with Claude...
  ✓ Performance pattern analysis complete
✨ Generating content ideas with Claude...
  ✓ Generated 10 content ideas
💾 Exporting results...
  📄 Posts CSV saved → output/posts_metrics.csv
  📄 Content ideas CSV saved → output/content_ideas.csv
  📄 Full report saved → output/full_report.json

============================================================
  SUMMARY
============================================================
📣 Sentiment: 87% positive | 10% neutral | 3% negative
   Followers respond most emotionally to fear-to-achievement posts and scenic nature content.

🏆 Top performing media type: REEL — 3.2x higher engagement than images

📌 Top themes in comments:
   • Overcoming fear (high) — inspired
   • Community & belonging (high) — grateful
   • Curiosity about routes (medium) — curious

💡 Top recommendation:
   → Post more Reels showing the emotional journey of a climb, not just the summit.

✅ Done! Check the /output folder for all files.
============================================================
```

---

## Limitations of this PoC

- The Meta long-lived token **expires after 60 days**. For a production version, implement the token refresh flow via the API.
- Instagram Graph API only returns data for **your own account's posts** — not competitors.
- Comments are capped at `MAX_COMMENTS` per post to stay within API rate limits.
- This PoC does not store historical data between runs — each run is independent.

---

## Next Steps (beyond the PoC)

- Schedule the script to run weekly with `cron` or GitHub Actions
- Store results in a database (SQLite or PostgreSQL) to track trends over time
- Build a simple dashboard with Streamlit or Looker Studio
- Add competitor analysis via third-party tools (e.g. Apify)
- Automate posting of approved content ideas via the Instagram Graph API

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.9+ | Core language |
| Meta Graph API v19 | Instagram data source |
| Google Gemini API | AI analysis & content generation |
| `requests` | HTTP calls to Meta API |
| `python-dotenv` | Environment variable management |

---

## License

This project is a proof of concept for internal use. Not for redistribution.
