"""
app.py — LinkedGod AI, Streamlit front end.

Turns a trending headline (or your own idea) into a ready-to-post
LinkedIn caption plus a designed PDF carousel, with tone control.
"""

from __future__ import annotations

import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from config import DEFAULT_SLIDE_COUNT, MAX_SLIDE_COUNT, MIN_SLIDE_COUNT, RSS_FEEDS, TONE_PROFILES
from content_generator import (
    ContentGenerationError,
    NewsItem,
    fetch_random_news,
    generate_post,
    get_api_key,
    get_client,
    split_hashtags,
)
from pdf_engine import create_carousel_pdf

st.set_page_config(page_title="LinkedGod AI", page_icon="🏛️", layout="wide")

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
api_key = get_api_key()
if not api_key:
    st.error(
        "⚠️ **GROQ_API_KEY** is missing. Add it to `.streamlit/secrets.toml` "
        "(Streamlit Cloud) or set it as an environment variable / `.env` file (local)."
    )
    st.stop()

client = get_client(api_key)

if "current" not in st.session_state:
    st.session_state.current = None
if "history" not in st.session_state:
    st.session_state.history = []  # most-recent-first list of {"topic", "tone"}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🏛️ LinkedGod AI")
st.caption("Turn a headline — or your own idea — into a ready-to-post LinkedIn caption and carousel.")

left, right = st.columns([1, 1], gap="large")

# ---------------------------------------------------------------------------
# Left column — inputs
# ---------------------------------------------------------------------------
with left:
    mode = st.radio("Content source", ["🔥 Trending News", "💡 Custom Idea"], horizontal=True)

    niche = None
    custom_title = ""
    custom_detail = ""

    if mode == "🔥 Trending News":
        niche = st.selectbox("Niche", list(RSS_FEEDS.keys()))
    else:
        custom_title = st.text_input(
            "Your idea", placeholder="e.g. AI is changing how startups build products"
        )
        custom_detail = st.text_area(
            "Extra context (optional)",
            placeholder="Any stats, examples, or angle you want the post to include...",
            height=100,
        )

    tone = st.selectbox(
        "Tone", list(TONE_PROFILES.keys()), format_func=lambda t: f"{TONE_PROFILES[t]['emoji']} {t}"
    )
    st.caption(TONE_PROFILES[tone]["description"])

    slide_count = st.slider("Carousel slides", MIN_SLIDE_COUNT, MAX_SLIDE_COUNT, DEFAULT_SLIDE_COUNT)

    generate_clicked = st.button("🏛️ Generate Post", type="primary", use_container_width=True)

    if generate_clicked:
        topic: NewsItem | None = None

        if mode == "🔥 Trending News":
            with st.spinner("Fetching a headline..."):
                topic = fetch_random_news(niche)
            if not topic:
                st.error("Couldn't fetch news from that feed right now — try another niche.")
                st.stop()
        else:
            if not custom_title.strip():
                st.error("Add an idea before generating.")
                st.stop()
            topic = NewsItem(title=custom_title.strip(), summary=custom_detail.strip())

        st.info(f"**Topic:** {topic.title}")

        with st.spinner("Writing your post and designing the carousel..."):
            try:
                result = generate_post(client, topic.title, topic.summary, tone, slide_count)
                pdf_bytes = create_carousel_pdf(result["slides"])
            except ContentGenerationError as exc:
                st.error(f"Generation failed: {exc}")
                st.stop()

        st.session_state.current = {
            "topic": topic.title,
            "tone": tone,
            "caption": result["caption"],
            "slides": result["slides"],
            "pdf": pdf_bytes,
        }
        st.session_state.history.insert(0, {"topic": topic.title, "tone": tone})
        st.session_state.history = st.session_state.history[:10]
        st.rerun()

# ---------------------------------------------------------------------------
# Right column — output
# ---------------------------------------------------------------------------
with right:
    current = st.session_state.current

    if not current:
        st.info("Generate a post to see the caption and carousel preview here.")
    else:
        body, hashtags = split_hashtags(current["caption"])

        st.subheader("Caption")
        st.text_area("Caption", body, height=260, label_visibility="collapsed")
        if hashtags:
            st.text_input("Hashtags", hashtags, label_visibility="collapsed")

        char_count = len(current["caption"])
        st.caption(f'{char_count} characters · LinkedIn shows "see more" around 210 on mobile')

        st.subheader(f"Carousel ({len(current['slides'])} slides)")
        for i, slide in enumerate(current["slides"], start=1):
            with st.expander(f"Slide {i}: {slide['title']}"):
                st.write(slide["body"].replace("*", ""))

        st.download_button(
            "📥 Download Carousel PDF",
            current["pdf"],
            file_name="linkedgod_carousel.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
if st.session_state.history:
    with st.expander(f"🕘 Recent generations ({len(st.session_state.history)})"):
        for item in st.session_state.history:
            st.markdown(f"**{item['topic']}** · _{item['tone']}_")
