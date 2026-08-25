"""
content_generator.py — Talks to Groq, builds tone-aware prompts, and
turns the raw LLM response into structured data the UI can render.
"""

from __future__ import annotations

import os
import re
import time
import random
from dataclasses import dataclass

import feedparser
from groq import Groq

from config import LLM_MODEL, MAX_RETRIES, RETRY_BACKOFF_SECONDS, RSS_FEEDS, TONE_PROFILES


class ContentGenerationError(Exception):
    """Raised when the LLM call fails, or succeeds but can't be parsed."""


@dataclass
class NewsItem:
    title: str
    summary: str = ""


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def get_api_key() -> str | None:
    """Look for a Groq key in Streamlit secrets first, then the environment.

    This lets the app run unmodified on Streamlit Community Cloud
    (st.secrets) and anywhere else — local dev, Docker, CI — via a plain
    GROQ_API_KEY environment variable or a .env file.
    """
    try:
        import streamlit as st

        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY")


def get_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


# ---------------------------------------------------------------------------
# News sourcing
# ---------------------------------------------------------------------------
def fetch_random_news(niche: str, pool_size: int = 10) -> NewsItem | None:
    """Pull a random recent headline from the configured RSS feed for `niche`."""
    url = RSS_FEEDS.get(niche)
    if not url:
        return None
    feed = feedparser.parse(url)
    if not feed.entries:
        return None
    entry = random.choice(feed.entries[: min(len(feed.entries), pool_size)])
    return NewsItem(title=entry.get("title", "").strip(), summary=entry.get("summary", "").strip())


# ---------------------------------------------------------------------------
# Prompting
# ---------------------------------------------------------------------------
def _slide_instructions(slide_count: int) -> str:
    lines = ["Slide 1: [Punchy Title] | [Write a 30-word powerful intro summary]"]
    for i in range(2, slide_count):
        lines.append(
            f"Slide {i}: [Concept Name] | [Detailed paragraph making one distinct point. FILL THE SPACE.]"
        )
    if slide_count >= 2:
        lines.append(
            f"Slide {slide_count}: [The Takeaway] | [Write a strong summary paragraph and a clear Call to Action.]"
        )
    return "\n".join(lines)


def _build_prompt(topic_title: str, topic_context: str, tone: str, slide_count: int) -> str:
    profile = TONE_PROFILES[tone]
    return f"""
You are an elite LinkedIn Ghostwriter. Tone for this post: {tone.upper()}.

TOPIC: {topic_title}
CONTEXT: {topic_context[:2000]}

Output TWO parts separated by "|||".

PART 1: CAPTION
Write a hook-first, SEO-optimised LinkedIn caption (280-320 words) in {profile['caption_style']} style, built for maximum organic reach.

Structure:
- LINE 1 — THE HOOK: One sentence, MAX 12 words. Must create curiosity, tension, or shock. End with a colon or ellipsis to force "see more" clicks. This is the most critical line.
- [blank line]
- THE STORY: 3 short paragraphs (2-3 sentences each), blank line between each. Include a real stat or number. Surprising angle.
- [blank line]
- "Here is what nobody is talking about:" — sharpest counterintuitive take in 2 sentences.
- [blank line]
- One direct debate-sparking question to the reader.
- [blank line]
- HASHTAGS: Exactly 8 hashtags on one line. Mix: 2 mega tags (1M+ like #leadership #innovation), 3 mid-tier niche tags (100K-500K), 3 hyper-specific topic tags for SEO discovery.

STRICT RULES FOR CAPTION:
- ZERO asterisks (*) anywhere in the caption.
- Hook line must be under 12 words. Non-negotiable.
- ZERO fluff (no "pushing boundaries", "making waves", "game changer", "poised for success").
- Plain text only. No markdown, no bullet points, no symbols except hashtags.

|||

PART 2: CAROUSEL SLIDES ({slide_count} Slides)
- Write LONG, DETAILED paragraphs. Each slide body must be at least 50-60 words.
- Use *asterisks* only inside slide body text to highlight key phrases (this is for PDF rendering).
- Write slides in {profile['slide_style']} style matching the {tone} tone.
- Format strictly as:

{_slide_instructions(slide_count)}
"""


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate_post(client: Groq, topic_title: str, topic_context: str, tone: str, slide_count: int = 5) -> dict:
    """Call Groq and return {"caption": str, "slides": [{"title", "body"}]}.

    Retries transient failures (rate limits, timeouts) with backoff before
    raising ContentGenerationError with a user-facing message.
    """
    profile = TONE_PROFILES[tone]
    prompt = _build_prompt(topic_title, topic_context, tone, slide_count)

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=LLM_MODEL,
                temperature=profile["temperature"],
            )
            raw = completion.choices[0].message.content
            return _parse_response(raw)
        except ContentGenerationError:
            raise  # a parsing problem won't be fixed by retrying
        except Exception as exc:  # network / rate-limit / API errors
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))

    raise ContentGenerationError(
        f"Groq request failed after {MAX_RETRIES + 1} attempt(s): {last_error}"
    )


_SLIDE_LINE_RE = re.compile(r"Slide\s*\d+\s*:\s*(.+?)\s*\|\s*(.+)", re.IGNORECASE)


def _parse_response(raw: str) -> dict:
    if "|||" not in raw:
        raise ContentGenerationError(
            "The model's response was missing the '|||' separator between caption and slides."
        )

    caption_part, slides_part = raw.split("|||", 1)
    caption = re.sub(r"PART\s*1\s*:?\s*CAPTION", "", caption_part, flags=re.IGNORECASE).strip()

    slides = []
    for line in slides_part.strip().splitlines():
        match = _SLIDE_LINE_RE.search(line)
        if match:
            title, body = match.groups()
            slides.append({"title": title.strip(), "body": body.strip()})

    if not caption:
        raise ContentGenerationError("The model returned an empty caption.")
    if not slides:
        raise ContentGenerationError("Could not parse any carousel slides from the model's response.")

    return {"caption": caption, "slides": slides}


def split_hashtags(caption: str) -> tuple[str, str]:
    """Split the trailing hashtag line off the caption body, if present."""
    lines = caption.strip().splitlines()
    if lines and "#" in lines[-1]:
        return "\n".join(lines[:-1]).strip(), lines[-1].strip()
    return caption.strip(), ""
