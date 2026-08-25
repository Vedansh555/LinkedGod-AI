"""
config.py — Central configuration for LinkedGod AI.

Every tunable value (news sources, tone presets, model choice, slide
limits) lives here so nothing is hard-coded deeper in the app.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
LLM_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 2          # extra attempts after the first, on transient errors
RETRY_BACKOFF_SECONDS = 1.5

# ---------------------------------------------------------------------------
# News sources — used in "Trending News" mode
# ---------------------------------------------------------------------------
RSS_FEEDS: dict[str, str] = {
    "Product Management": "https://techcrunch.com/category/startups/feed/",
    "AI Agents": "https://www.artificialintelligence-news.com/feed/",
    "Consulting": "http://feeds.harvardbusiness.org/harvardbusiness",
    "Startup Life": "https://news.ycombinator.com/rss",
}

# ---------------------------------------------------------------------------
# Tone presets — each reshapes the caption prompt, the slide prompt, and
# the sampling temperature. Add a new tone by adding one entry here.
# ---------------------------------------------------------------------------
TONE_PROFILES: dict[str, dict] = {
    "Professional": {
        "emoji": "📊",
        "description": "Data-driven, executive voice",
        "caption_style": "authoritative, data-driven, expert tone. No hype. Clean insight-led paragraphs.",
        "slide_style": "clear, formal, evidence-based language",
        "temperature": 0.65,
    },
    "Controversial": {
        "emoji": "🔥",
        "description": "Challenges mainstream views, sparks debate",
        "caption_style": (
            "provocative and contrarian. Challenge the mainstream view. Open with a "
            "statement most people will disagree with. Make them uncomfortable enough to comment."
        ),
        "slide_style": "bold claims, challenging conventional wisdom, sparking debate",
        "temperature": 0.85,
    },
    "Scary / Urgent": {
        "emoji": "⚠️",
        "description": "High-stakes warnings, fear of missing out",
        "caption_style": (
            "alarming and urgent. Use real risk and fear of missing out. Make the reader "
            "feel they NEED to act now or fall behind permanently."
        ),
        "slide_style": "high-stakes warnings, alarming statistics, urgent calls to action",
        "temperature": 0.80,
    },
    "Motivational": {
        "emoji": "🚀",
        "description": "Inspiring stories, action-oriented energy",
        "caption_style": (
            "inspiring and energetic. Stories of real transformation. Make the reader "
            "believe they can do the same. Grounded, not fluffy."
        ),
        "slide_style": "empowering language, transformative insights, action-oriented",
        "temperature": 0.75,
    },
    "Contrarian": {
        "emoji": "🧠",
        "description": "Myth-busting, 'what they're not telling you'",
        "caption_style": (
            "deeply contrarian. Every paragraph challenges something the reader assumes "
            "is true. Use angles like 'everyone is wrong about this' and 'here is what "
            "they are not telling you'."
        ),
        "slide_style": "myth-busting framing, unpopular truth hooks, counterintuitive insights",
        "temperature": 0.90,
    },
}

# ---------------------------------------------------------------------------
# Carousel
# ---------------------------------------------------------------------------
DEFAULT_SLIDE_COUNT = 5
MIN_SLIDE_COUNT = 3
MAX_SLIDE_COUNT = 7

# LinkedIn truncates behind "...see more" around this length on mobile —
# surfaced in the UI so users can judge whether their hook lands in time.
LINKEDIN_MOBILE_TRUNCATE_CHARS = 210
LINKEDIN_MAX_CAPTION_CHARS = 3000
